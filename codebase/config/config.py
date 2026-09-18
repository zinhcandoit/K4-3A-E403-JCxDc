import os
import re
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def clean_lesson_title(raw_title: str) -> str:
    if not raw_title:
        return ""
    title = raw_title.strip()
    title = re.sub(r"^[#📘📑\s]+(?:Slide:\s*)?", "", title, flags=re.IGNORECASE)
    title = re.sub(
        r"^Transcript\s+bài\s+giảng\s*(?:\([^)]*\))?\s*[-—–:]?\s*(?:(?:Day|Buổi|Bài)\s*\d+\s*[-—–:.]?)?\s*",
        "",
        title,
        flags=re.IGNORECASE,
    )
    title = re.sub(r"^(?:Day|Buổi|Bài)\s*\d+\s*[-—–:.]\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\([^)]*(?:phần|part)\s*[^)]*\)\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\(phần\s+(?:sau|đầu)\s+buổi\)\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*[-—–:]\s*$", "", title)
    return title.strip()


class Config:
    # Directories
    BASE_DIR = BASE_DIR
    DB_DIR = BASE_DIR / "db"
    INPUT_DIR = DB_DIR / "input"
    LOGS_DIR = DB_DIR / "logs"
    CHAT_HISTORY_FILE = DB_DIR / "chat_history.json"
    TRANSCRIPT_DIR = BASE_DIR.parent / "data" / "vlearn-pack" / "transcript"

    # API Keys (only credentials from .env)
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

    # NVIDIA NIM LLM Settings
    NVIDIA_MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"
    NVIDIA_MAX_TOKENS = 512
    NVIDIA_REASONING_BUDGET = 1024
    NVIDIA_TEMPERATURE = 0.2
    NVIDIA_TOP_P = 0.95
    NVIDIA_ENABLE_THINKING = True
    MAX_RPM = 36

    # Pedagogical & Graph Settings
    MAX_PROBING_TURNS = 2
    SLIDING_WINDOW_LIMIT = 6
    FALKOR_HOST = "localhost"
    FALKOR_PORT = 6379
    GRAPH_NAME = "VLearn_Knowledge_Graph"
    LLM_TIMEOUT = 60.0

    ACTIVE_DOCUMENT = ""
    ACTIVE_TRACK = ""

    @classmethod
    def get_available_lessons(cls) -> list:
        lessons = []
        if cls.TRANSCRIPT_DIR.exists():
            for p in sorted(cls.TRANSCRIPT_DIR.glob("*.md")):
                if p.name.lower() == "readme.md":
                    continue
                title = p.stem.replace("-", " ").replace("_", " ").title()
                try:
                    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines()[:10]:
                        clean_line = line.strip()
                        if clean_line.startswith("# ") and len(clean_line) > 3:
                            title = clean_lesson_title(clean_line)
                            break
                except Exception:
                    pass
                lessons.append({
                    "id": p.stem,
                    "filename": p.name,
                    "title": f"📘 {title}",
                    "type": "transcript",
                    "track": p.stem,
                })

        if cls.INPUT_DIR.exists():
            for p in sorted(cls.INPUT_DIR.glob("*.pdf")):
                slide_title = clean_lesson_title(p.stem.replace("_", " ").title())
                lessons.append({
                    "id": f"slide_{p.stem}",
                    "filename": p.name,
                    "title": f"📑 Slide: {slide_title}",
                    "type": "pdf",
                    "track": f"slide_{p.stem}",
                })
        return lessons

    @classmethod
    def get_default_track(cls) -> str:
        if cls.ACTIVE_TRACK:
            return cls.ACTIVE_TRACK
        lessons = cls.get_available_lessons()
        return lessons[0]["track"] if lessons else "primary"

    @classmethod
    def get_default_document(cls) -> str:
        if cls.ACTIVE_DOCUMENT:
            return cls.ACTIVE_DOCUMENT
        lessons = cls.get_available_lessons()
        return lessons[0]["filename"] if lessons else ""


settings = Config()
