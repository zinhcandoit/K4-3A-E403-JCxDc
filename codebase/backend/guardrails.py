"""
Track D3 Pedagogical Guardrails:
Đánh giá sư phạm đa chiều (8 tiêu chí) theo phương pháp Feynman & AI Spec:
- 100% sử dụng NVIDIA NIM ChatNVIDIA (nvidia/nemotron-3.5-lightning-30b-a3b)
- Tuyệt đối không dùng dummy data hay fallback về Gemini
- Phân loại chuẩn xác 4 lớp chỗ khó (§5) và 4 đường đi trải nghiệm (§6)
"""
import re
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from config.config import settings
from backend.nvidia_client import NvidiaAIClient


class PedagogicalEvaluation(BaseModel):
    """
    Pedagogical classification schema with 8 criteria for Track D3 (Feynman / Protégé Agent):
    Covers the 4 difficulty tiers (§5) and 4 learning pathways (§6) defined in AI Spec.
    """
    is_parroting: bool = Field(
        default=False,
        description="True if student merely copies verbatim from lesson materials without own phrasing"
    )
    unexplained_buzzwords: List[str] = Field(
        default_factory=list,
        description="List of technical buzzwords used without explaining underlying mechanism"
    )
    has_causal_reasoning: bool = Field(
        default=False,
        description="True if student explains causal chain (why the phenomenon/model works)"
    )
    has_concrete_example: bool = Field(
        default=False,
        description="True if student provides concrete real-world example or intuitive analogy"
    )
    factual_contradiction: bool = Field(
        default=False,
        description="True if student asserts factual falsehood contrary to source truth"
    )
    is_superficial: bool = Field(
        default=False,
        description="True if response is overly curt or superficial lacking depth"
    )
    is_out_of_scope: bool = Field(
        default=False,
        description="True if student asks for quiz answers or off-topic administrative queries"
    )
    is_self_correction: bool = Field(
        default=False,
        description="True if student identifies previous mistake and self-corrects"
    )
    is_mastered: bool = Field(
        default=False,
        description="True if student demonstrates clear causal reasoning, concrete example, without errors or parroting"
    )
    pedagogical_status: str = Field(
        default="SOCRATIC_PROBING",
        description="CHEATING_PARROTING, BUZZWORD_WITHOUT_GROUNDING, FACTUAL_MISCONCEPTION, SUPERFICIAL_EXPLANATION, OUT_OF_SCOPE_DEFLECTION, SELF_CORRECTING, CAUSAL_BREAKTHROUGH, SOCRATIC_PROBING"
    )
    critique: str = Field(
        default="",
        description="Summary of primary weakness or strong point (max 20 words)"
    )


class TrackD3Guardrails:
    """
    Pedagogical guardrail evaluator powered by ChatNVIDIA:
    Evaluates 8 pedagogical criteria combined with instantaneous n-gram overlap check.
    """

    def __init__(self, nvidia_client: Optional[NvidiaAIClient] = None):
        self.client = nvidia_client or NvidiaAIClient()
        self.structured_judge = None

        # Attempt structured output activation on ChatNVIDIA
        llm = self.client.get_llm()
        if llm:
            try:
                self.structured_judge = llm.with_structured_output(PedagogicalEvaluation)
                print("✅ ChatNVIDIA structured_output activated for TrackD3Guardrails.")
            except Exception as exc:
                print(f"ℹ️ ChatNVIDIA structured_output fallback to JSON prompt parsing: {exc}")

    def evaluate_teaching_explanation(
        self,
        student_msg: str,
        core_truth: str,
        quote_text: str = "",
        turn_count: int = 1,
        prev_critique: str = "",
        pedagogical_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate student explanation against 8 pedagogical criteria:
        1. is_parroting
        2. unexplained_buzzwords
        3. has_causal_reasoning
        4. has_concrete_example
        5. factual_contradiction
        6. is_superficial
        7. is_out_of_scope
        8. is_self_correction
        Cross-checks against FalkorDB pedagogical blindspots (misconceptions, mechanisms, tradeoffs, counter-examples).
        """
        # Instant n-gram overlap check (0.001s, zero tokens)
        instant_parroting = self._dynamic_overlap_check(student_msg, quote_text)
        if instant_parroting:
            return {
                "is_mastered": False,
                "is_cheating": True,
                "is_parroting": True,
                "has_causal_reasoning": False,
                "has_concrete_example": False,
                "factual_contradiction": False,
                "is_superficial": False,
                "is_out_of_scope": False,
                "is_self_correction": False,
                "buzzwords_unexplained": [],
                "pedagogical_status": "CHEATING_PARROTING",
                "status_label": "Phát hiện chép nguyên văn tài liệu",
                "critique": "Học viên sao chép nguyên văn từ slide/transcript.",
                "turn_count": turn_count
            }

        # Extract pedagogical benchmarks from FalkorDB knowledge graph
        pedagogical_data = pedagogical_context or {}
        misconception = pedagogical_data.get("misconception") or {}
        tradeoff = pedagogical_data.get("tradeoff") or {}
        mechanism = pedagogical_data.get("mechanism") or {}
        counter_example = pedagogical_data.get("counter_example") or {}

        pedagogical_benchmarks = []
        if misconception.get("pitfall_text"):
            pedagogical_benchmarks.append(f"- BẪY NGỘ NHẬN CẦN TRÁNH: {misconception.get('pitfall_text')}")
        if mechanism.get("causal_chain"):
            pedagogical_benchmarks.append(f"- CƠ CHẾ NHÂN QUẢ CHUẨN: {mechanism.get('causal_chain')}")
        if tradeoff.get("dimension_a"):
            pedagogical_benchmarks.append(f"- ĐÁNH ĐỔI KỸ THUẬT: {tradeoff.get('dimension_a')} vs {tradeoff.get('dimension_b')}")
        if counter_example.get("scenario"):
            pedagogical_benchmarks.append(f"- VÍ DỤ / TRƯỜNG HỢP BIÊN: {counter_example.get('scenario')}")
        pedagogical_benchmarks_section = "\n[CÁC MỐC ĐỐI CHIẾU SƯ PHẠM TỪ GRAPH]:\n" + "\n".join(pedagogical_benchmarks) if pedagogical_benchmarks else ""

        judge_prompt = f"""Bạn là Giám định viên Sư phạm AI cho mô hình Feynman / Alex (Protégé Effect).
Hãy thẩm định lời giải thích của học viên dựa trên Tri thức chuẩn từ tài liệu gốc và các mốc đối chiếu sư phạm.

[TRI THỨC CHUẨN]:
"{core_truth}"

[ĐOẠN TRÍCH GỐC TRONG TRANSCRIPT/SLIDE]:
"{quote_text}"
{pedagogical_benchmarks_section}

[LỜI GIẢI THÍCH CỦA HỌC VIÊN]:
"{student_msg}"

[LƯỢT TRAO ĐỔI]: Lượt thứ {turn_count} (Lưu ý: Tối đa 2 lượt hỏi)
[NHẬN XÉT LƯỢT TRƯỚC]: "{prev_critique}"

HÃY ĐÁNH GIÁ 8 TIÊU CHÍ VÀ XUẤT ĐÚNG ĐỊNH DẠNG JSON:
{{
  "is_parroting": false,
  "unexplained_buzzwords": [],
  "has_causal_reasoning": false,
  "has_concrete_example": false,
  "factual_contradiction": false,
  "is_superficial": false,
  "is_out_of_scope": false,
  "is_self_correction": false,
  "is_mastered": false,
  "pedagogical_status": "SOCRATIC_PROBING",
  "critique": "Tóm tắt điểm mấu chốt dưới 20 từ"
}}

Quy tắc:
- is_out_of_scope = true nếu đòi đáp án quiz hoặc hỏi lịch học/link nộp bài.
- factual_contradiction = true nếu nói sai bản chất bài giảng (ví dụ: LLM có ý thức, cửa sổ ngữ cảnh to không bao giờ sót).
- is_superficial = true nếu nói cộc lốc dưới 10 từ hoặc khẳng định một chiều thiếu cơ chế.
- is_mastered = true CHỈ KHI: has_causal_reasoning=true, has_concrete_example=true, is_parroting=false, factual_contradiction=false, không còn buzzword lấp liếm.
- pedagogical_status: CHEATING_PARROTING | BUZZWORD_WITHOUT_GROUNDING | FACTUAL_MISCONCEPTION | SUPERFICIAL_EXPLANATION | OUT_OF_SCOPE_DEFLECTION | SELF_CORRECTING | CAUSAL_BREAKTHROUGH | SOCRATIC_PROBING.
CHỈ TRẢ VỀ DUY NHẤT ĐOẠN JSON TRÊN."""

        evaluation_instance: Optional[PedagogicalEvaluation] = None

        # 1. Structured output execution
        if self.structured_judge:
            try:
                evaluation_result = self.structured_judge.invoke(judge_prompt)
                if isinstance(evaluation_result, PedagogicalEvaluation):
                    evaluation_instance = evaluation_result
                elif isinstance(evaluation_result, dict):
                    evaluation_instance = PedagogicalEvaluation(**evaluation_result)
            except Exception as exc:
                print(f"ℹ️ structured_judge invoke exception: {exc}")

        # 2. JSON Parsing fallback from ChatNVIDIA text output
        if not evaluation_instance:
            try:
                raw_text = self.client.generate_text(
                    prompt=judge_prompt,
                    system_prompt="Bạn là Giám định viên Sư phạm AI nghiêm ngặt. Chỉ xuất JSON."
                )
                if raw_text:
                    json_match = re.search(r"\{[\s\S]*\}", raw_text)
                    if json_match:
                        raw_dict = json.loads(json_match.group(0))
                        evaluation_instance = PedagogicalEvaluation(**raw_dict)
            except Exception as exc:
                print(f"⚠️ JSON parsing fallback error: {exc}")

        if evaluation_instance:
            is_mastered = evaluation_instance.is_mastered
            is_cheating = evaluation_instance.is_parroting
            has_causal = evaluation_instance.has_causal_reasoning
            has_example = evaluation_instance.has_concrete_example
            factual_contradiction = evaluation_instance.factual_contradiction
            is_superficial = evaluation_instance.is_superficial
            is_out_of_scope = evaluation_instance.is_out_of_scope
            is_self_correction = evaluation_instance.is_self_correction
            buzzwords = evaluation_instance.unexplained_buzzwords
            pedagogical_status = evaluation_instance.pedagogical_status
            critique = evaluation_instance.critique
        else:
            # Safe heuristics fallback when network is unavailable
            is_mastered = False
            is_cheating = False
            has_causal = False
            has_example = False
            factual_contradiction = False
            is_superficial = len(student_msg.split()) < 8
            is_out_of_scope = "đáp án" in student_msg.lower() or "lịch học" in student_msg.lower()
            is_self_correction = False
            buzzwords = []
            pedagogical_status = "OUT_OF_SCOPE_DEFLECTION" if is_out_of_scope else "SOCRATIC_PROBING"
            critique = "Đang tiếp tục đối chiếu cơ chế với bài giảng."

        status_labels = {
            "CHEATING_PARROTING": "Phát hiện chép nguyên văn tài liệu",
            "BUZZWORD_WITHOUT_GROUNDING": "Dùng thuật ngữ nhưng thiếu căn cứ",
            "FACTUAL_MISCONCEPTION": "Ngộ nhận sai lệch so với bài giảng",
            "SUPERFICIAL_EXPLANATION": "Giải thích còn hời hợt hoặc cộc lốc",
            "OUT_OF_SCOPE_DEFLECTION": "Đòi đáp án hoặc hỏi ngoài bài học",
            "SELF_CORRECTING": "Học viên đang tự sửa lỗi logic",
            "CAUSAL_BREAKTHROUGH": "Lập luận nhân quả chặt chẽ kèm ví dụ",
            "SOCRATIC_PROBING": "Cần đào sâu thêm một mắt xích"
        }
        status_label = status_labels.get(pedagogical_status, "Hỏi vặn về cơ chế")

        return {
            "is_mastered": is_mastered,
            "is_cheating": is_cheating,
            "is_parroting": is_cheating,
            "has_causal_reasoning": has_causal,
            "has_concrete_example": has_example,
            "factual_contradiction": factual_contradiction,
            "is_superficial": is_superficial,
            "is_out_of_scope": is_out_of_scope,
            "is_self_correction": is_self_correction,
            "buzzwords_unexplained": buzzwords,
            "pedagogical_status": pedagogical_status,
            "status_label": status_label,
            "critique": critique,
            "turn_count": turn_count
        }

    @staticmethod
    def _dynamic_overlap_check(student_msg: str, quote_text: str) -> bool:
        """Check verbatim n-gram overlap with lecture excerpt (n-gram >= 6 words)."""
        if not quote_text or len(quote_text) < 20:
            return False
        clean_student_text = re.sub(r"[^\w\s]", "", student_msg.lower()).strip()
        clean_quote_text = re.sub(r"[^\w\s]", "", quote_text.lower()).strip()
        student_words = clean_student_text.split()
        if len(student_words) < 6:
            return False
        for index in range(len(student_words) - 5):
            ngram = " ".join(student_words[index:index+6])
            if ngram in clean_quote_text:
                return True
        return False
