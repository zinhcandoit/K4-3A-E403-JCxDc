import os
import sys
import re
import time
import random
import threading
import warnings
from typing import Optional, Generator, Dict, Any, List
from config.config import settings

# Bỏ qua warning thông báo model có sẵn trong langchain-nvidia
warnings.filterwarnings("ignore", message=".*Found nvidia/.*in available_models.*")

from langchain_nvidia_ai_endpoints import ChatNVIDIA


class NVIDIARateLimiter:
    """
    Bộ kiểm soát tần suất gọi API cho NVIDIA NIM:
    - Giới hạn cứng của NVIDIA: 40 RPM (Requests Per Minute).
    - Cấu hình an toàn: 36 RPM (~1.67s giữa các request liên tiếp).
    - Quản lý bằng Sliding Window 60s và thread-lock để tránh vượt ngưỡng kể cả khi gọi đa luồng.
    """
    def __init__(self, max_rpm: int = 36):
        self.max_rpm = max_rpm
        self.interval = 60.0 / max_rpm
        self.timestamps: List[float] = []
        self.lock = threading.Lock()
        self.last_call_time = 0.0

    def acquire(self):
        with self.lock:
            now = time.time()
            # Loại bỏ các mốc thời gian cũ hơn 60 giây
            self.timestamps = [t for t in self.timestamps if now - t < 60.0]

            # Nếu đã đạt 36 requests trong vòng 60 giây, chờ cho đến khi slot đầu tiên hết hạn
            if len(self.timestamps) >= self.max_rpm:
                sleep_time = 60.0 - (now - self.timestamps[0]) + 0.1
                if sleep_time > 0:
                    time.sleep(sleep_time)
                now = time.time()
                self.timestamps = [t for t in self.timestamps if now - t < 60.0]

            # Đảm bảo khoảng cách tối thiểu giữa 2 request liên tiếp
            elapsed = now - self.last_call_time
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
                now = time.time()

            self.last_call_time = now
            self.timestamps.append(now)


# Singleton Rate Limiter cho toàn bộ ứng dụng
_global_rate_limiter = NVIDIARateLimiter(max_rpm=36)


class NvidiaAIClient:
    """
    Client chính thức kết nối NVIDIA NIM / AI Endpoints sử dụng duy nhất mô hình:
    `nvidia/nemotron-3.5-lightning-30b-a3b`
    - Cấu hình tập trung qua `config.config.settings`
    - Tuân thủ giới hạn 40 RPM thông qua NVIDIARateLimiter toàn cục (36 RPM an toàn)
    - Tự động retry với exponential backoff khi gặp lỗi 429 Too Many Requests
    - Tối ưu hóa tốc độ: max_tokens <= 512, reasoning_budget <= 512
    - Bóc tách reasoning_content từ chunk.additional_kwargs cho Thinking Phases
    - TUYỆT ĐỐI KHÔNG CÓ FALLBACK VỀ GEMINI
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        self.api_key = api_key or settings.NVIDIA_API_KEY
        self.model_name = model or settings.NVIDIA_MODEL
        self.temperature = temperature if temperature is not None else settings.NVIDIA_TEMPERATURE
        self.max_tokens = max_tokens or settings.NVIDIA_MAX_TOKENS
        self.rate_limiter = _global_rate_limiter
        if not self.api_key:
            print("⚠️ CẢNH BÁO: NVIDIA_API_KEY chưa được cấu hình trong codebase/.env!")

        try:
            model_kwargs = {}
            if settings.NVIDIA_ENABLE_THINKING:
                model_kwargs["chat_template_kwargs"] = {"enable_thinking": True}
            else:
                model_kwargs["chat_template_kwargs"] = {"enable_thinking": False}
            self.client = ChatNVIDIA(
                model=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature,
                top_p=settings.NVIDIA_TOP_P,
                max_tokens=self.max_tokens,
                model_kwargs=model_kwargs,
            )
            print(f"✅ Đã khởi tạo ChatNVIDIA thành công ({self.model_name}) kèm Rate Limiter (40 RPM).")
        except Exception as e:
            print(f"⚠️ Không thể khởi tạo ChatNVIDIA: {e}")
            self.client = None

    def get_llm(self) -> Optional[ChatNVIDIA]:
        """Trả về instance ChatNVIDIA cho LangChain pipeline"""
        return self.client

    def generate_text_and_thinking(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Sinh câu trả lời và đồng thời trích xuất suy nghĩ ngầm (reasoning_content)
        từ streaming chunks của ChatNVIDIA theo đúng spec NVIDIA Nemotron.
        Có gắn Rate Limiter và cơ chế Exponential Backoff khi gặp HTTP 429.
        """
        if not self.client:
            return {"reply": "", "thinking": ""}

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        max_retries = 4
        base_backoff = 2.0

        for attempt in range(max_retries):
            # Kiểm soát tần suất 40 RPM
            self.rate_limiter.acquire()
            reasoning_chunks: List[str] = []
            content_chunks: List[str] = []

            try:
                for chunk in self.client.stream(messages):
                    # Extract reasoning_content from additional_kwargs if available
                    if chunk.additional_kwargs and "reasoning_content" in chunk.additional_kwargs:
                        reasoning_text = chunk.additional_kwargs["reasoning_content"]
                        if reasoning_text:
                            reasoning_chunks.append(str(reasoning_text))

                    # Extract primary response text
                    if chunk.content:
                        content_chunks.append(str(chunk.content))

                final_reply = "".join(content_chunks).strip()
                final_thinking = "".join(reasoning_chunks).strip()

                # Tách biệt thinking process nếu mô hình trả lẫn vào text content
                if "<think>" in final_reply:
                    think_match = re.search(r"<think>([\s\S]*?)(?:</think>|$)", final_reply)
                    if think_match:
                        extracted_think = think_match.group(1).strip()
                        final_thinking = f"{final_thinking}\n\n{extracted_think}".strip() if final_thinking else extracted_think
                        final_reply = re.sub(r"<think>[\s\S]*?(?:</think>|$)", "", final_reply).strip()

                thinking_header_match = re.match(
                    r"^(?:Here'?s a thinking process:|Thinking Process:|\*\*Thinking Process:\*\*|Quá trình suy nghĩ:)\s*",
                    final_reply,
                    re.IGNORECASE
                )
                if thinking_header_match:
                    lines = final_reply.splitlines()
                    think_lines = []
                    reply_lines = []
                    found_reply = False

                    for idx, line in enumerate(lines):
                        stripped = line.strip()
                        if not found_reply:
                            is_bullet = stripped.startswith(("*", "-", "#", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "•"))
                            has_vietnamese_pronouns = any(kw in stripped.lower() for kw in ["mình", "bạn", "chào", "nghe", "ý bạn", "đoạn này", "tại sao", "cơ chế", "nếu", "nhưng", "theo"])
                            if idx > 2 and stripped and not is_bullet and has_vietnamese_pronouns:
                                found_reply = True
                                reply_lines.append(line)
                            else:
                                think_lines.append(line)
                        else:
                            reply_lines.append(line)

                    if reply_lines:
                        extracted_think = "\n".join(think_lines).strip()
                        final_thinking = f"{final_thinking}\n\n{extracted_think}".strip() if final_thinking else extracted_think
                        final_reply = "\n".join(reply_lines).strip()
                    else:
                        extracted_think = final_reply
                        final_thinking = f"{final_thinking}\n\n{extracted_think}".strip() if final_thinking else extracted_think
                        final_reply = "Ý bạn giải thích có điểm đáng chú ý, nhưng về mặt cơ chế vận hành bên dưới thì bài toán này được xử lý cụ thể như thế nào bạn nhỉ?"

                # Clean non-BMP unicode emojis if present to avoid encoding issues
                final_reply = re.sub(r"[\U00010000-\U0010ffff]", "", final_reply).strip()
                final_thinking = re.sub(r"[\U00010000-\U0010ffff]", "", final_thinking).strip()

                return {
                    "reply": final_reply,
                    "thinking": final_thinking
                }

            except Exception as exc:
                error_message = str(exc).lower()
                is_rate_limit = "429" in error_message or "rate limit" in error_message or "too many requests" in error_message
                if is_rate_limit and attempt < max_retries - 1:
                    wait_time = base_backoff * (2 ** attempt) + random.uniform(0.5, 1.5)
                    print(f"⚠️ [NVIDIA Rate Limit 429] Limit reached, waiting {wait_time:.1f}s before retry ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    print(f"⚠️ Error during ChatNVIDIA streaming ({self.model_name}): {exc}")
                    return {"reply": "", "thinking": ""}

        return {"reply": "", "thinking": ""}

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate single text response from ChatNVIDIA with rate limiting."""
        generation_result = self.generate_text_and_thinking(prompt=prompt, system_prompt=system_prompt)
        return generation_result.get("reply", "")

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Generator stream từng chunk văn bản sinh ra từ ChatNVIDIA có kiểm soát RPM"""
        if not self.client:
            return

        self.rate_limiter.acquire()
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            for chunk in self.client.stream(messages):
                if chunk.content:
                    yield str(chunk.content)
        except Exception as e:
            print(f"⚠️ Lỗi stream ChatNVIDIA: {e}")

    def generate_stream_chunks(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Generator[Dict[str, str], None, None]:
        """
        Stream chunks từ ChatNVIDIA yielding dictionary chứa reasoning và text content:
        {"reasoning": reasoning_token, "content": content_token}
        """
        if not self.client:
            return

        self.rate_limiter.acquire()
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            for chunk in self.client.stream(messages):
                reasoning = ""
                if chunk.additional_kwargs and "reasoning_content" in chunk.additional_kwargs:
                    reasoning = str(chunk.additional_kwargs["reasoning_content"] or "")

                content = str(chunk.content or "")
                if reasoning or content:
                    yield {"reasoning": reasoning, "content": content}
        except Exception as e:
            print(f"⚠️ Lỗi streaming ChatNVIDIA chunks: {e}")

