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

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.NVIDIA_API_KEY
        self.rate_limiter = _global_rate_limiter
        if not self.api_key:
            print("⚠️ CẢNH BÁO: NVIDIA_API_KEY chưa được cấu hình trong codebase/.env!")

        try:
            model_kwargs = {
                "reasoning_budget": settings.NVIDIA_REASONING_BUDGET,
                "chat_template_kwargs": {"enable_thinking": settings.NVIDIA_ENABLE_THINKING}
            }
            self.client = ChatNVIDIA(
                model=settings.NVIDIA_MODEL,
                api_key=self.api_key,
                temperature=settings.NVIDIA_TEMPERATURE,
                top_p=settings.NVIDIA_TOP_P,
                max_tokens=settings.NVIDIA_MAX_TOKENS,
                model_kwargs=model_kwargs,
            )
            print(f"✅ Đã khởi tạo ChatNVIDIA thành công ({settings.NVIDIA_MODEL}) kèm Rate Limiter (40 RPM).")
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
                    print(f"⚠️ Error during ChatNVIDIA streaming ({settings.NVIDIA_MODEL}): {exc}")
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
