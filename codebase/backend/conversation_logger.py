"""
Conversation Logging Service for VLearn Track D3:
- Lưu trữ toàn bộ hội thoại và các sự kiện sư phạm dưới định dạng .log trong codebase/db/logs/
- Ghi nhật ký chi tiết: Session ID, Turn, Topic, Ask, Student Answer, Pedagogical Evaluation, Reasoning, Alex Reply.
- Hỗ trợ đồng bộ/backfill các lượt trò chuyện từ chat_history.json.
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config.config import settings


class ConversationLogger:
    """Manages persistent human-readable .log records in codebase/db/logs/"""

    def __init__(self, log_dir: Optional[Path] = None):
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = settings.DB_DIR / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.main_log_file = self.log_dir / "conversation.log"

    def _format_turn_log(
        self,
        session_id: str,
        turn: int,
        concept_name: str,
        event_label: str,
        ask: str,
        answer: str,
        agent_reply: str,
        critique: str = "",
        timestamp: Optional[str] = None
    ) -> str:
        ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "=" * 80,
            f"[{ts}] [SESSION: {session_id}] [LƯỢT: {turn}] [CHỦ ĐỀ: {concept_name}]",
            f"[ĐÁNH GIÁ SƯ PHẠM / EVENT]: {event_label or 'Socratic Probing'}",
            "-" * 80,
            "[ALEX / CÂU HỎI MỞ ĐẦU HOẶC GỢI Ý]:",
            f"{ask.strip() if ask else '(Khởi đầu bài học)'}",
            "",
            "[HỌC VIÊN / GIẢI THÍCH]:",
            f"{answer.strip()}",
            ""
        ]
        if critique:
            lines.extend([
                "[NHẬN XÉT SƯ PHẠM]:",
                f"{critique.strip()}",
                ""
            ])
        lines.extend([
            "[ALEX / PHẢN HỒI PHẢN BIỆN]:",
            f"{agent_reply.strip()}",
            "=" * 80,
            ""
        ])
        return "\n".join(lines)

    def log_turn(
        self,
        session_id: str,
        turn: int,
        concept_name: str,
        event_label: str,
        ask: str,
        answer: str,
        agent_reply: str,
        critique: str = "",
        timestamp: Optional[str] = None
    ):
        """Append turn interaction to both unified conversation.log and session-specific .log file."""
        log_entry = self._format_turn_log(
            session_id=session_id,
            turn=turn,
            concept_name=concept_name,
            event_label=event_label,
            ask=ask,
            answer=answer,
            agent_reply=agent_reply,
            critique=critique,
            timestamp=timestamp
        )

        try:
            with open(self.main_log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")

            session_log_file = self.log_dir / f"conversation_{session_id}.log"
            with open(session_log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as exc:
            print(f"⚠️ Lỗi ghi file log cuộc trò chuyện: {exc}")

    def log_event(self, session_id: str, event_name: str, detail: str, topic: str = ""):
        """Log administrative or milestone event (lesson switch, reset, topic introduction)."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "-" * 80,
            f"[{ts}] [SESSION: {session_id}] [SỰ KIỆN: {event_name}]" + (f" [CHỦ ĐỀ: {topic}]" if topic else ""),
            f"{detail.strip()}",
            "-" * 80,
            ""
        ]
        log_entry = "\n".join(lines)
        try:
            with open(self.main_log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")

            session_log_file = self.log_dir / f"conversation_{session_id}.log"
            with open(session_log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as exc:
            print(f"⚠️ Lỗi ghi event log: {exc}")

    def sync_history_to_log(self, sessions_dict: Dict[str, List[Dict[str, Any]]]):
        """Backfill existing sessions from chat_history.json into conversation.log if log is empty."""
        if self.main_log_file.exists() and self.main_log_file.stat().st_size > 50:
            return  # Already populated

        try:
            with open(self.main_log_file, "w", encoding="utf-8") as f:
                f.write("# ================================================================================\n")
                f.write("# NHẬT KÝ CUỘC TRÒ CHUYỆN HỌC TẬP VLEARN SOCRATIC AGENT (.LOG)\n")
                f.write(f"# Khởi tạo lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# ================================================================================\n\n")

            for session_id, turns in sessions_dict.items():
                for turn_item in turns:
                    self.log_turn(
                        session_id=session_id,
                        turn=turn_item.get("turn", 1),
                        concept_name=turn_item.get("concept_name", "Chủ đề học tập"),
                        event_label=turn_item.get("event_label", ""),
                        ask=turn_item.get("ask", ""),
                        answer=turn_item.get("answer", ""),
                        agent_reply=turn_item.get("agent_reply", ""),
                        critique=turn_item.get("summary_sentence", ""),
                        timestamp=turn_item.get("timestamp")
                    )
        except Exception as exc:
            print(f"⚠️ Lỗi đồng bộ lịch sử hội thoại sang file .log: {exc}")


# Global singleton instance
conversation_logger = ConversationLogger()
