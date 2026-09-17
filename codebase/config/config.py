import os
from pathlib import Path
from dotenv import load_dotenv

# Root directory of codebase
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """
    Centralized configuration manager for VLearn Track D3 (Protégé Socratic Agent):
    - Single source of truth for ChatNVIDIA, FalkorDB, memory, and file paths.
    - Preserves knowledge locality per independent document track.
    """

    # Core data directories
    BASE_DIR = BASE_DIR
    DB_DIR = BASE_DIR / "db"
    INPUT_DIR = DB_DIR / "input"
    CHAT_HISTORY_FILE = DB_DIR / "chat_history.json"
    VLEARN_DATA_DIR = BASE_DIR.parent / "data" / "vlearn-pack"
    TRANSCRIPT_DIR = VLEARN_DATA_DIR / "transcript"

    # Active document track configuration
    ACTIVE_DOCUMENT = os.getenv("ACTIVE_DOCUMENT", "")
    ACTIVE_TRACK = os.getenv("ACTIVE_TRACK", "")

    @classmethod
    def get_available_lessons(cls) -> list:
        """
        Dynamically scan available lesson materials from data directories without hardcoding names.
        Preserves data privacy and zero data leakage in source code.
        """
        lessons = []
        if cls.TRANSCRIPT_DIR.exists():
            for transcript_path in sorted(cls.TRANSCRIPT_DIR.glob("*.md")):
                if transcript_path.name.lower() == "readme.md":
                    continue
                # Extract clean title from document header or filename stem
                title = transcript_path.stem.replace("-", " ").replace("_", " ").title()
                try:
                    for line in transcript_path.read_text(encoding="utf-8", errors="ignore").splitlines()[:10]:
                        clean_line = line.strip()
                        if clean_line.startswith("# ") and len(clean_line) > 3:
                            title = clean_line.replace("#", "").strip()
                            break
                except Exception:
                    pass

                lessons.append({
                    "id": transcript_path.stem,
                    "filename": transcript_path.name,
                    "title": f"📘 {title}",
                    "type": "transcript",
                    "track": transcript_path.stem
                })

        if cls.INPUT_DIR.exists():
            for pdf_file in sorted(cls.INPUT_DIR.glob("*.pdf")):
                lessons.append({
                    "id": f"slide_{pdf_file.stem}",
                    "filename": pdf_file.name,
                    "title": f"📑 Slide: {pdf_file.stem.replace('_', ' ').title()}",
                    "type": "pdf",
                    "track": f"slide_{pdf_file.stem}"
                })

        return lessons

    @classmethod
    def get_default_track(cls) -> str:
        """Lấy track mặc định tự động mà không hardcode"""
        if cls.ACTIVE_TRACK:
            return cls.ACTIVE_TRACK
        lessons = cls.get_available_lessons()
        return lessons[0]["track"] if lessons else "primary"

    @classmethod
    def get_default_document(cls) -> str:
        """Lấy document mặc định tự động mà không hardcode"""
        if cls.ACTIVE_DOCUMENT:
            return cls.ACTIVE_DOCUMENT
        lessons = cls.get_available_lessons()
        return lessons[0]["filename"] if lessons else ""

    # NVIDIA LLM CONFIG (DUY NHẤT, KHÔNG FALLBACK GEMINI)
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")

    # SIÊU THAM SỐ TỐI ƯU TỐC ĐỘ VÀ ĐỘ SẮC BÉN SOCRATIC
    # max_tokens = 768 đảm bảo câu trả lời luôn hoàn chỉnh 100%, không bị cụt câu (xử lý lỗi Lượt 1 spec §9 dòng 168)
    NVIDIA_MAX_TOKENS = int(os.getenv("NVIDIA_MAX_TOKENS", 768))
    # reasoning_budget = 512 đủ cho suy nghĩ ngầm nhận diện lỗ hổng mà không gây trễ
    NVIDIA_REASONING_BUDGET = int(os.getenv("NVIDIA_REASONING_BUDGET", 512))
    # temperature = 0.35: Precise (chính xác bám sát transcript, không bịa), đủ nhạy để hỏi ngược
    NVIDIA_TEMPERATURE = float(os.getenv("NVIDIA_TEMPERATURE", 0.35))
    # top_p = 0.85: Loại bỏ token ngẫu nhiên, tập trung từ vựng kỹ thuật cốt lõi
    NVIDIA_TOP_P = float(os.getenv("NVIDIA_TOP_P", 0.85))
    # enable_thinking = True: Kích hoạt reasoning_content từ Nemotron
    NVIDIA_ENABLE_THINKING = True
    # GIỚI HẠN TẦN SUẤT NVIDIA (RPM LIMIT = 40)
    MAX_RPM = int(os.getenv("MAX_RPM", 36))  # 36 RPM an toàn dưới ngưỡng cứng 40

    # QUY TẮC SƯ PHẠM SOCRATIC (TRACK D3 · FEYNMAN TECHNIQUE · SPEC.MD)
    MAX_PROBING_TURNS = int(os.getenv("MAX_PROBING_TURNS", 2))   # Tối đa 2 câu hỏi ngược cho 1 concept (§4)
    SLIDING_WINDOW_LIMIT = int(os.getenv("SLIDING_WINDOW_LIMIT", 6))  # 6 lượt Ask - Answer gần nhất

    # CẤU HÌNH FALKORDB (GRAPH DATABASE)
    FALKOR_HOST = os.getenv("FALKOR_HOST", "localhost")
    FALKOR_PORT = int(os.getenv("FALKOR_PORT", 6379))
    GRAPH_NAME = os.getenv("GRAPH_NAME", "VLearn_Knowledge_Graph")

    # DỊCH VỤ PHỤ TRỢ (NẾU CÓ)
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

    # TIMEOUT KIỂM SOÁT
    LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", 60.0))


settings = Config()
