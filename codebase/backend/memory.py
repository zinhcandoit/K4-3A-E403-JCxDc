"""
Dual-Form Conversation Memory for Socratic Agent (Track D3):
1. Quản lý hội thoại phân tách theo từng session_id.
2. Dạng 1: Sliding Window 6 lượt Ask - Answer gần nhất (settings.SLIDING_WINDOW_LIMIT).
3. Dạng 2: Global Incremental Summarization (Append-only) — mỗi lượt trao đổi được đúc kết 1 câu ngắn.
4. Lưu trữ bền vững xuống settings.CHAT_HISTORY_FILE.
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from config.config import settings
from backend.nvidia_client import NvidiaAIClient


class SimpleConversationMemory:
    """
    Two-tiered Conversation Memory manager per session:
    - Stores complete history of Ask-Answer turns.
    - Tier 1: Sliding Window of the most recent turns (default 6).
    - Tier 2: Global Incremental Summarization (append-only single-sentence digest per turn).
    - Persists state to disk in JSON format.
    """

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.storage_file = Path(storage_path)
        else:
            self.storage_file = settings.CHAT_HISTORY_FILE

        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
        self.global_summaries: Dict[str, str] = {}  # Global summary string per session
        self.last_asked: Dict[str, str] = {}        # Most recent question asked by Alex
        self.nvidia_client = NvidiaAIClient()
        from backend.conversation_logger import conversation_logger
        self.logger = conversation_logger
        self.load_from_disk()
        self.logger.sync_history_to_log(self.sessions)

    def set_last_question(self, session_id: str, question: str):
        """Record the most recent question asked by the agent."""
        self.last_asked[session_id] = question

    def get_last_question(self, session_id: str, default_question: str = "") -> str:
        """Retrieve the most recent question asked by the agent."""
        return self.last_asked.get(session_id, default_question)

    def summarize_and_append_turn(
        self,
        session_id: str,
        turn_number: int,
        ask: str,
        answer: str,
        concept_name: str,
        critique: str = ""
    ) -> str:
        """
        Tier 2: Generate immediate single-sentence summary for current turn from pedagogical critique.
        Eliminates additional synchronous LLM calls for lower latency.
        """
        if critique and len(critique.strip()) > 5:
            summary_sentence = f"Học viên: {answer[:75]}... ({critique.strip()})"
        else:
            clean_answer = answer.strip().replace("\n", " ")
            summary_sentence = f"Học viên trao đổi về {concept_name}: {clean_answer[:80]}..."

        new_entry = f"• [Lượt {turn_number} | {concept_name}]: {summary_sentence}"
        
        current_global = self.global_summaries.get(session_id, "").strip()
        if current_global:
            self.global_summaries[session_id] = f"{current_global}\n{new_entry}"
        else:
            self.global_summaries[session_id] = new_entry

        self.save_to_disk()
        return summary_sentence

    def add_turn(
        self,
        session_id: str,
        ask: str,
        answer: str,
        agent_reply: str = "",
        concept_id: str = "",
        concept_name: str = "",
        event_label: str = "",
        critique: str = ""
    ) -> Dict[str, Any]:
        """Record a single Ask-Answer turn into session memory and update summaries."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        turn_number = len(self.sessions[session_id]) + 1
        record = {
            "turn": turn_number,
            "ask": ask,
            "answer": answer,
            "agent_reply": agent_reply,
            "concept_id": concept_id,
            "concept_name": concept_name,
            "event_label": event_label,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.sessions[session_id].append(record)
        
        summary_sentence = self.summarize_and_append_turn(
            session_id=session_id,
            turn_number=turn_number,
            ask=ask,
            answer=answer,
            concept_name=concept_name,
            critique=critique
        )
        record["summary_sentence"] = summary_sentence
        self.save_to_disk()

        # Ghi log hội thoại ra định dạng .log trong codebase/db/logs/
        try:
            self.logger.log_turn(
                session_id=session_id,
                turn=turn_number,
                concept_name=concept_name,
                event_label=event_label,
                ask=ask,
                answer=answer,
                agent_reply=agent_reply,
                critique=critique or summary_sentence,
                timestamp=record["timestamp"]
            )
        except Exception as log_exc:
            print(f"Logger error: {log_exc}")

        return record

    def get_recent_turns(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Tier 1: Retrieve recent Ask-Answer turns within sliding window limit."""
        effective_limit = limit or settings.SLIDING_WINDOW_LIMIT
        history = self.sessions.get(session_id, [])
        return history[-effective_limit:] if effective_limit > 0 else history

    def get_global_summary(self, session_id: str) -> str:
        """Retrieve global incremental summary text for a session."""
        return self.global_summaries.get(session_id, "").strip()

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve turn history records for session display."""
        history = self.sessions.get(session_id, [])
        return history[-limit:] if limit > 0 else history

    def format_memory_for_prompt(self, session_id: str) -> str:
        """Format two-tiered memory into structured context sections for prompt synthesis."""
        global_summary = self.get_global_summary(session_id)
        recent_turns = self.get_recent_turns(session_id)

        if not global_summary and not recent_turns:
            return "Chưa có lượt trao đổi nào trước đó (Đây là lượt bắt đầu phiên học)."

        sections = []

        if global_summary:
            sections.append(
                f"[TÓM TẮT TOÀN CỤC TIẾN TRÌNH HỘI THOẠI (GLOBAL INCREMENTAL SUMMARY)]:\n"
                f"{global_summary}"
            )

        if recent_turns:
            turn_lines = []
            for turn_item in recent_turns:
                reply_short = turn_item.get('agent_reply', '')
                if len(reply_short) > 100:
                    reply_short = reply_short[:97] + "..."
                turn_lines.append(
                    f"• Lượt {turn_item['turn']} [{turn_item.get('concept_name', 'Chung')}]:\n"
                    f"  - Alex đã hỏi (Ask): \"{turn_item['ask']}\"\n"
                    f"  - Học viên trả lời (Answer): \"{turn_item['answer']}\"\n"
                    f"  - Phản hồi của Alex: \"{reply_short}\""
                )
            sections.append(
                f"[6 LƯỢT ASK - ANSWER GẦN NHẤT (SLIDING WINDOW MEMORY)]:\n" +
                "\n".join(turn_lines)
            )

        return "\n\n".join(sections)

    def clear_history(self, session_id: str):
        """Xóa lịch sử của một session"""
        if session_id in self.sessions:
            self.sessions[session_id] = []
        if session_id in self.global_summaries:
            del self.global_summaries[session_id]
        if session_id in self.last_asked:
            del self.last_asked[session_id]
        self.save_to_disk()

    def clear_all(self):
        """Xóa toàn bộ lịch sử"""
        self.sessions.clear()
        self.global_summaries.clear()
        self.last_asked.clear()
        self.save_to_disk()

    def save_to_disk(self):
        """Lưu dữ liệu xuống file JSON"""
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump({
                    "sessions": self.sessions,
                    "global_summaries": self.global_summaries,
                    "last_asked": self.last_asked
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Không thể lưu chat history xuống disk: {e}")

    def load_from_disk(self):
        """Đọc dữ liệu từ file JSON"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.sessions = data.get("sessions", {})
                    self.global_summaries = data.get("global_summaries", {})
                    self.last_asked = data.get("last_asked", {})
            except Exception as e:
                print(f"⚠️ Lỗi đọc chat history từ disk: {e}")
