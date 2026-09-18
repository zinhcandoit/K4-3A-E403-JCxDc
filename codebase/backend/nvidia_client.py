import os
import re
import time
import random
import threading
import warnings
from typing import Optional, Generator, Dict, Any, List, Type
from pydantic import BaseModel
from openai import OpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from config.config import settings

warnings.filterwarnings("ignore", message=".*Found nvidia/.*in available_models.*")
warnings.filterwarnings("ignore", message=".*is not known to support structured output.*")


class NVIDIARateLimiter:
    """Sliding-window rate limiter for NVIDIA NIM API (safe ceiling: 36 RPM)."""
    def __init__(self, max_rpm: int = 36):
        self.max_rpm = max_rpm
        self.interval = 60.0 / max_rpm
        self.timestamps: List[float] = []
        self.lock = threading.Lock()
        self.last_call_time = 0.0

    def acquire(self):
        with self.lock:
            now = time.time()
            self.timestamps = [t for t in self.timestamps if now - t < 60.0]

            if len(self.timestamps) >= self.max_rpm:
                sleep_time = 60.0 - (now - self.timestamps[0]) + 0.1
                if sleep_time > 0:
                    time.sleep(sleep_time)
                now = time.time()
                self.timestamps = [t for t in self.timestamps if now - t < 60.0]

            elapsed = now - self.last_call_time
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
                now = time.time()

            self.last_call_time = now
            self.timestamps.append(now)


_global_rate_limiter = NVIDIARateLimiter(max_rpm=settings.MAX_RPM)


class NvidiaAIClient:
    """
    NVIDIA NIM API Client:
    - Heavy reasoning tasks: reasoning_budget = settings.NVIDIA_REASONING_BUDGET (enable_thinking=True)
    - Lightweight structured JSON tasks: with_structured_output (enable_thinking=False)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        reasoning_budget: Optional[int] = None,
    ):
        self.api_key = api_key or settings.NVIDIA_API_KEY
        self.model_name = model or settings.NVIDIA_MODEL
        self.temperature = temperature if temperature is not None else settings.NVIDIA_TEMPERATURE
        self.max_tokens = max_tokens or settings.NVIDIA_MAX_TOKENS
        self.reasoning_budget = reasoning_budget or settings.NVIDIA_REASONING_BUDGET
        self.rate_limiter = _global_rate_limiter

        self.openai_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key or "missing_key",
        )

    def get_llm(
        self,
        enable_thinking: bool = True,
        reasoning_budget: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ChatNVIDIA:
        """Return ChatNVIDIA instance for LangChain integration."""
        temp = temperature if temperature is not None else self.temperature
        model_kwargs: Dict[str, Any] = {}
        if enable_thinking:
            model_kwargs["chat_template_kwargs"] = {"enable_thinking": True}
            model_kwargs["reasoning_budget"] = reasoning_budget or self.reasoning_budget
        else:
            model_kwargs["chat_template_kwargs"] = {"enable_thinking": False}

        return ChatNVIDIA(
            model=self.model_name,
            api_key=self.api_key,
            temperature=temp,
            top_p=settings.NVIDIA_TOP_P,
            max_tokens=self.max_tokens,
            model_kwargs=model_kwargs,
        )

    def with_structured_output(self, schema: Type[BaseModel], **kwargs):
        """
        Chuẩn LangChain BaseChatModel.with_structured_output:
        Gọi trực tiếp .with_structured_output() trên ChatNVIDIA với enable_thinking=False.
        """
        llm = self.get_llm(enable_thinking=False)
        return llm.with_structured_output(schema, **kwargs)

    # Alias tiện ích
    get_structured_llm = with_structured_output

    def generate_stream_chunks(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        reasoning_budget: Optional[int] = None,
    ) -> Generator[Dict[str, str], None, None]:
        """
        Stream chunks yielding both reasoning tokens and response content:
        {"reasoning": str, "content": str}
        Uses reasoning_budget for deep reasoning.
        """
        self.rate_limiter.acquire()
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        budget = reasoning_budget or self.reasoning_budget
        try:
            stream = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                top_p=settings.NVIDIA_TOP_P,
                max_tokens=self.max_tokens,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": True},
                    "reasoning_budget": budget,
                },
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue
                reasoning = getattr(delta, "reasoning_content", None) or ""
                content = getattr(delta, "content", None) or ""
                if reasoning or content:
                    yield {"reasoning": str(reasoning), "content": str(content)}
        except Exception as e:
            print(f"⚠️ Error streaming from NVIDIA NIM ({self.model_name}): {e}")

    def generate_text_and_thinking(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        reasoning_budget: Optional[int] = None,
    ) -> Dict[str, str]:
        """Generate response with thinking extracted, retrying on 429."""
        max_retries = 3
        base_backoff = 2.0

        for attempt in range(max_retries):
            reasoning_chunks: List[str] = []
            content_chunks: List[str] = []
            try:
                for chunk in self.generate_stream_chunks(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    reasoning_budget=reasoning_budget,
                ):
                    if chunk["reasoning"]:
                        reasoning_chunks.append(chunk["reasoning"])
                    if chunk["content"]:
                        content_chunks.append(chunk["content"])

                final_reply = "".join(content_chunks).strip()
                final_thinking = "".join(reasoning_chunks).strip()

                # Cleanup potential inline <think> tags if present in content
                if "<think>" in final_reply:
                    think_match = re.search(r"<think>([\s\S]*?)(?:</think>|$)", final_reply)
                    if think_match:
                        extracted = think_match.group(1).strip()
                        final_thinking = f"{final_thinking}\n\n{extracted}".strip() if final_thinking else extracted
                        final_reply = re.sub(r"<think>[\s\S]*?(?:</think>|$)", "", final_reply).strip()

                return {"reply": final_reply, "thinking": final_thinking}

            except Exception as exc:
                err = str(exc).lower()
                if ("429" in err or "rate limit" in err) and attempt < max_retries - 1:
                    wait_time = base_backoff * (2 ** attempt) + random.uniform(0.5, 1.5)
                    print(f"⚠️ [NVIDIA Rate Limit 429] Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    print(f"⚠️ NVIDIA call error: {exc}")
                    return {"reply": "", "thinking": ""}

        return {"reply": "", "thinking": ""}

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        enable_thinking: bool = False,
        reasoning_budget: Optional[int] = None,
    ) -> str:
        """
        Generate text response:
        - If enable_thinking=False (default for simple tasks): zero reasoning tokens, fast execution.
        - If enable_thinking=True: applies reasoning_budget.
        """
        if enable_thinking:
            res = self.generate_text_and_thinking(
                prompt=prompt,
                system_prompt=system_prompt,
                reasoning_budget=reasoning_budget,
            )
            return res.get("reply", "")

        self.rate_limiter.acquire()
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            resp = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                top_p=settings.NVIDIA_TOP_P,
                max_tokens=self.max_tokens,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            print(f"⚠️ Error in generate_text: {e}")
            return ""

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Stream content tokens only."""
        for chunk in self.generate_stream_chunks(prompt=prompt, system_prompt=system_prompt):
            if chunk["content"]:
                yield chunk["content"]
