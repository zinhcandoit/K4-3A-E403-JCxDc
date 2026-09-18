import os
import sys
import json
import re
from typing import Dict, Any, Optional, List, Generator

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from config.config import settings, clean_lesson_title
from db.graph_service import GraphService
from db.data_loader import RealDataLoader
from backend.prompt import (
    PROTEGE_SYSTEM_PROMPT,
    build_opening_question_prompt,
    build_protege_probing_prompt
)
from backend.guardrails import TrackD3Guardrails
from backend.nvidia_client import NvidiaAIClient
from backend.memory import SimpleConversationMemory


class SocraticAgentEngine:
    """
    Protégé Agent Socratic Engine for Track D3 (Learning by Teaching — Feynman Method):
    - Powered exclusively by ChatNVIDIA (nvidia/nemotron-3.5-lightning-30b-a3b).
    - Persona: Sharp peer student practicing Controlled Naivety.
    - Hidden Grounding: Retains core ground truth citations from FalkorDB knowledge graph.
    - Two-tiered Conversation Memory: Sliding window of recent turns + Global incremental digest.
    - Multidimensional pedagogical guardrails (8 criteria) with hidden reasoning extraction.
    - Rate limited to 36 RPM, max 2 probing turns per concept.
    - Zero fallback to Gemini.
    """

    def __init__(self):
        try:
            self.graph_service = GraphService(
                host=settings.FALKOR_HOST,
                port=settings.FALKOR_PORT,
                graph_name=settings.GRAPH_NAME
            )
        except Exception as e:
            print(f"ℹ️ FalkorDB offline ({e}), using local data fallback.")
            self.graph_service = None
        self.nvidia_client = NvidiaAIClient()
        self.guardrails = TrackD3Guardrails(nvidia_client=self.nvidia_client)
        self.memory = SimpleConversationMemory()
        self.data_loader = RealDataLoader()
        self.concept_turns: Dict[str, int] = {}
        self._concept_cache: Dict[str, Dict[str, Any]] = {}
        print(f"✅ SocraticAgentEngine (ChatNVIDIA: {settings.NVIDIA_MODEL}) initialized successfully.")

    def generate_smart_opening_question(self, concept_name: str, quote_text: str = "", core_truth: str = "") -> str:
        """Generate focused opening question targeting technical trade-offs using ChatNVIDIA."""
        prompt = build_opening_question_prompt(
            concept_name=concept_name,
            quote_text=quote_text,
            core_truth=core_truth
        )

        try:
            generation_result = self.nvidia_client.generate_text(
                prompt=prompt,
                system_prompt=PROTEGE_SYSTEM_PROMPT
            )
            if generation_result:
                raw_text = generation_result.strip()

                # Bóc tách nếu có Draft hoặc nhiều dòng: lấy câu hỏi hoàn chỉnh kết thúc bằng ?
                lines = raw_text.splitlines()
                candidate_question = ""
                for line in reversed(lines):
                    stripped_line = line.strip()
                    if "?" in stripped_line and not any(kw in stripped_line.lower() for kw in ["count:", "under", "ends with", "draft", "good."]):
                        candidate_question = stripped_line
                        break

                if not candidate_question:
                    candidate_question = raw_text

                # Làm sạch số đếm từ (1), (2)... và các nhãn Draft, Count, metadata
                clean_question = re.sub(r'\(\d+\)', '', candidate_question)
                clean_question = re.sub(r'Draft\s*\d+:?', '', clean_question, flags=re.IGNORECASE)
                clean_question = re.sub(r'Count:.*', '', clean_question, flags=re.IGNORECASE)
                clean_question = re.sub(r'Under\s+\d+\s+words.*', '', clean_question, flags=re.IGNORECASE)
                clean_question = re.sub(r'[\U00004e00-\U00009fff]', '', clean_question)
                clean_question = re.sub(r'["\'\*]', '', clean_question).strip()
                clean_question = re.sub(r'\s+', ' ', clean_question).strip()

                if len(clean_question) > 15 and "?" in clean_question:
                    return clean_question
        except Exception as exc:
            print(f"⚠️ Error generating opening question with ChatNVIDIA: {exc}")

        # Safe fallback aligned with core concept pedagogy
        return f"Theo bạn, thách thức kỹ thuật lớn nhất và sự đánh đổi cần cân nhắc khi triển khai {concept_name} là gì?"

    def get_current_feynman_concept(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Retrieve the active concept node from FalkorDB preserving local track context."""
        active_track = self.graph_service.current_track if self.graph_service else settings.get_default_track()
        if not force_refresh and active_track in self._concept_cache:
            return self._concept_cache[active_track]

        res = None
        if self.graph_service:
            try:
                # 1. Look for next uncovered concept within the active track
                query_result = self.graph_service.graph.query(f"""
                MATCH (fc:FeynmanConcept {{status: 'UNCOVERED', track: '{active_track}'}})
                RETURN fc.id, fc.name, fc.citation, fc.core_truth, fc.child_question, fc.quote_text, fc.learning_question, fc.track
                ORDER BY fc.order
                LIMIT 1
                """)
                if not query_result.result_set:
                    # 2. If all covered, retrieve by track to maintain topical locality
                    query_result = self.graph_service.graph.query(f"""
                    MATCH (fc:FeynmanConcept {{track: '{active_track}'}})
                    RETURN fc.id, fc.name, fc.citation, fc.core_truth, fc.child_question, fc.quote_text, fc.learning_question, fc.track
                    ORDER BY fc.order
                    LIMIT 1
                    """)

                if query_result.result_set:
                    concept_record = query_result.result_set[0]
                    question_text = concept_record[6] if len(concept_record) > 6 and concept_record[6] else concept_record[4]
                    if not question_text or "lại vận hành như vậy" in question_text or "Cơ chế cốt lõi và nguyên nhân" in question_text:
                        question_text = self.generate_smart_opening_question(concept_record[1], concept_record[5] or "", concept_record[3] or "")
                        try:
                            sanitized_question = question_text.replace("'", "\\'").replace('"', '\\"')
                            self.graph_service.graph.query(
                                f"MATCH (fc:FeynmanConcept {{id: '{concept_record[0]}'}}) "
                                f"SET fc.learning_question = '{sanitized_question}', fc.child_question = '{sanitized_question}'"
                            )
                        except Exception as update_exc:
                            print(f"Update node error: {update_exc}")
                    res = {
                        "id": concept_record[0],
                        "name": concept_record[1],
                        "citation": concept_record[2],
                        "core_truth": concept_record[3],
                        "child_question": question_text,
                        "learning_question": question_text,
                        "quote": concept_record[5],
                        "track": concept_record[7] if len(concept_record) > 7 else active_track
                    }
                    self._concept_cache[active_track] = res
                    return res
            except Exception as query_exc:
                print(f"ℹ️ Query concept error from FalkorDB: {query_exc}")

            # Fallback to slide concept from FalkorDB
            target = self.graph_service.get_next_probing_target()
            if target:
                question_text = target.get("probe_question", "")
                if not question_text or "lại vận hành như vậy" in question_text:
                    question_text = self.generate_smart_opening_question(target["concept_name"], target.get("summary", ""), target.get("truth_hint", ""))
                res = {
                    "id": target["concept_id"],
                    "name": target["concept_name"],
                    "citation": f"[Slide P.{target['page']}]",
                    "core_truth": target["truth_hint"],
                    "child_question": question_text,
                    "learning_question": question_text,
                    "quote": target["summary"]
                }
                self._concept_cache[active_track] = res
                return res

        # Fallback đọc trực tiếp từ RealDataLoader (quét transcript markdown thực tế)
        try:
            real_concepts = self.data_loader.parse_vlearn_transcripts()
            if real_concepts:
                first = real_concepts[0]
                res = {
                    "id": first["id"],
                    "name": first["name"],
                    "citation": first["citation"],
                    "core_truth": first["core_truth"],
                    "child_question": first["learning_question"],
                    "learning_question": first["learning_question"],
                    "quote": first["quote_text"]
                }
                self._concept_cache[active_track] = res
                return res
        except Exception as e:
            print(f"Fallback loader error: {e}")

        # Fallback an toàn nếu chưa nạp đồ thị: không tiết lộ bất kỳ nội dung thực tế nào của bài giảng
        res = {
            "id": "concept_pending",
            "name": "Nội dung học tập",
            "citation": "[Tài liệu tham khảo]",
            "core_truth": "Kiến thức chuyên môn đang được cập nhật từ tài liệu.",
            "child_question": "Bạn có thể giải thích theo cách hiểu của bạn về chủ đề này được không?",
            "learning_question": "Bạn có thể giải thích theo cách hiểu của bạn về chủ đề này được không?",
            "quote": ""
        }
        self._concept_cache[active_track] = res
        return res

    def generate_topic_intro_directions(self, concept_node: Dict[str, Any]) -> List[str]:
        """
        Tạo các hướng gợi ý gợi mở để học viên bắt đầu giảng bài cho Alex.
        Ưu tiên trích xuất từ đồ thị tri thức đa thực thể FalkorDB (Mechanism, Tradeoff, Misconception),
        kết hợp fallback sư phạm tự nhiên, không tốn token LLM và độ trễ 0ms.
        """
        concept_id = concept_node.get("id", "")
        raw_name = concept_node.get("name", "chủ đề này")
        concept_name = clean_lesson_title(raw_name)

        directions = []
        try:
            pedagogical = self.graph_service.get_concept_pedagogical_context(concept_id)
            if pedagogical:
                # 1. Hướng cơ chế
                mech = pedagogical.get("mechanism")
                if mech and mech.get("name"):
                    directions.append(f"**Cơ chế cốt lõi:** {mech['name']} (bản chất và cách thức vận hành)")

                # 2. Hướng đánh đổi / thách thức
                tradeoff = pedagogical.get("tradeoff")
                if tradeoff and tradeoff.get("name"):
                    dim_a = tradeoff.get("dimension_a")
                    dim_b = tradeoff.get("dimension_b")
                    if dim_a and dim_b:
                        directions.append(f"**Sự đánh đổi:** {tradeoff['name']} (cân nhắc giữa {dim_a} và {dim_b})")
                    else:
                        directions.append(f"**Sự đánh đổi thực tế:** {tradeoff['name']}")

                # 3. Hướng sai lầm / góc nhìn phản biện
                misconception = pedagogical.get("misconception")
                if misconception and misconception.get("name"):
                    directions.append(f"**Góc nhìn phản biện / Hiểu lầm thường gặp:** {misconception['name']}")

                # 4. Hướng ví dụ / tình huống
                counter = pedagogical.get("counter_example")
                if counter and counter.get("name") and len(directions) < 3:
                    directions.append(f"**Ví dụ / Tình huống áp dụng:** {counter['name']}")
        except Exception as e:
            print(f"Lỗi khi trích xuất hướng gợi ý từ đồ thị: {e}")

        # Fallback nếu đồ thị chưa có liên kết cụ thể: đảm bảo luôn có 3 hướng mở gợi ý hấp dẫn
        if not directions:
            directions = [
                f"**Bản chất & Vai trò:** Định nghĩa {concept_name} là gì và giải quyết bài toán quan trọng nào?",
                f"**Cơ chế hoạt động:** Các thành phần cấu tạo hoặc quy trình các bước vận hành cốt lõi.",
                f"**Ứng dụng & Đánh đổi:** Một ví dụ thực tế hoặc thách thức kỹ thuật lớn nhất khi triển khai."
            ]
        elif len(directions) < 3:
            if not any("Định nghĩa" in d or "Bản chất" in d for d in directions):
                directions.insert(0, f"**Bản chất & Vai trò:** Khái niệm {concept_name} và mục tiêu chính trong bài học.")
            if len(directions) < 3:
                directions.append(f"**Ứng dụng thực tế:** Một ví dụ hoặc trường hợp cụ thể bạn thấy tâm đắc nhất.")

        return directions[:3]

    def process_student_message(self, student_msg: str, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Quy trình đối chiếu sư phạm Track D3 kết hợp ChatNVIDIA:
        1. Lấy Hidden Ground Truth từ bài giảng gốc.
        2. Đánh giá 8 tiêu chí phân loại sư phạm qua Guardrails (parroting, buzzwords, causal, example, truth, out_of_scope...).
        3. Sinh phản hồi Socratic bằng ChatNVIDIA và bóc tách reasoning_content ngầm.
        4. Kiểm soát giới hạn tối đa 2 câu hỏi ngược cho 1 concept.
        5. Cập nhật trạng thái đồ thị và bộ nhớ hội thoại 2 dạng.
        """
        current_concept = self.get_current_feynman_concept()
        concept_id = current_concept["id"]
        concept_name = current_concept["name"]
        citation = current_concept["citation"]
        core_truth = current_concept["core_truth"]
        quote_text = current_concept.get("quote", "")

        current_question = self.memory.get_last_question(session_id)
        if not current_question:
            current_question = current_concept.get("learning_question") or current_concept.get("child_question", "")

        # Track number of conversational turns on current concept
        turn_count = self.concept_turns.get(concept_id, 0) + 1
        self.concept_turns[concept_id] = turn_count

        # 0. Query pedagogical blindspots from FalkorDB (Misconceptions, Trade-offs, Mechanisms, Counter-examples)
        pedagogical_context = self.graph_service.get_concept_pedagogical_context(concept_id) if self.graph_service else {}

        # 1. Evaluate teaching explanation across 8 pedagogical criteria
        evaluation_result = self.guardrails.evaluate_teaching_explanation(
            student_msg=student_msg,
            core_truth=core_truth,
            quote_text=quote_text,
            turn_count=turn_count,
            pedagogical_context=pedagogical_context
        )

        is_cheating = evaluation_result.get("is_cheating", False)
        is_mastered = evaluation_result.get("is_mastered", False)
        has_causal = evaluation_result.get("has_causal_reasoning", False)
        has_example = evaluation_result.get("has_concrete_example", False)
        factual_contradiction = evaluation_result.get("factual_contradiction", False)
        is_out_of_scope = evaluation_result.get("is_out_of_scope", False)
        is_superficial = evaluation_result.get("is_superficial", False)
        buzzwords = evaluation_result.get("buzzwords_unexplained", [])
        status_label = evaluation_result.get("status_label", "Hỏi vặn về cơ chế")
        critique = evaluation_result.get("critique", "Đang đào sâu cơ chế.")
        pedagogical_status = evaluation_result.get("pedagogical_status", "SOCRATIC_PROBING")

        is_end_of_graph = False
        alternative_paths = []
        model_thinking = ""

        # 2. Formulate Alex's response based on pedagogical classification
        if is_cheating:
            reply = (
                f"Đoạn này nghe giống như trích dẫn từ tài liệu {citation} quá bạn ơi. "
                f"Nếu để bạn tự diễn đạt lại bằng ngôn ngữ của riêng bạn về {concept_name}, "
                f"thì bạn giải thích điểm mấu chốt ở đây như thế nào?"
            )
            model_thinking = "Phát hiện sao chép nguyên văn từ slide bài giảng. Yêu cầu bạn học tự diễn giải bằng ngôn từ cá nhân."
            self.memory.set_last_question(session_id, reply)
            event_type = "parroting_alert"
            detail = f"Trùng khớp nguyên văn {citation} — yêu cầu tự diễn giải"
        elif is_out_of_scope:
            reply = "Mấy việc đó bạn xem trên kênh thông báo của lớp nha! Mình cũng là sinh viên đang học nè, đâu có đáp án đâu. Hai đứa mình cùng tập trung giải thích lại chỗ cơ chế này đi bạn ơi?"
            model_thinking = "Học viên đang đòi đáp án hoặc hỏi việc ngoài bài học. Kiên định giữ vai bạn học ngây thơ, từ chối khéo và kéo về bài giảng."
            self.memory.set_last_question(session_id, reply)
            event_type = "out_of_scope_deflection"
            detail = "Từ chối việc ngoài thẩm quyền, kéo về bài giảng"
        else:
            # Generate Socratic probing with ChatNVIDIA grounded in FalkorDB pedagogical blindspots
            memory_context = self.memory.format_memory_for_prompt(session_id)
            probing_prompt = build_protege_probing_prompt(
                concept_name=concept_name,
                citation=citation,
                core_truth=core_truth,
                student_msg=student_msg,
                analysis_report=evaluation_result,
                pedagogical_context=pedagogical_context,
                conversation_history=memory_context
            )

            generation_result = self.nvidia_client.generate_text_and_thinking(
                prompt=probing_prompt,
                system_prompt=PROTEGE_SYSTEM_PROMPT
            )
            reply = generation_result.get("reply", "")
            model_thinking = generation_result.get("thinking", "")

            if not reply or len(reply.strip()) < 10:
                reply = "Ý bạn giải thích nghe rất có lý, nhưng ở khía cạnh kỹ thuật cụ thể thì cơ chế bên dưới xử lý bài toán này như thế nào? Bạn phân tích sâu hơn một chút giúp mình nhé."

            # Enforce max probing turn limit
            if not is_mastered and turn_count >= settings.MAX_PROBING_TURNS:
                reply += f"\n\n(Gợi ý nhỏ: Mình thấy chỗ này còn hơi trừu tượng, bạn thử mở lại {citation} xem phần cơ chế cốt lõi rồi hai đứa mình cùng bàn tiếp nhé!)"

            if is_mastered:
                event_type = "causal_breakthrough"
                detail = f"Đã làm chủ {concept_name}"
                try:
                    self.graph_service.graph.query(f"MATCH (fc:FeynmanConcept {{id: '{concept_id}'}}) SET fc.status = 'COVERED'")
                except Exception:
                    pass
                self.graph_service.mark_concept_covered(concept_id)
                is_end_of_graph, end_message, alternative_paths = self.graph_service.is_end_of_graph()

                if not is_end_of_graph:
                    next_concept = self.get_current_feynman_concept()
                    next_question = next_concept.get("learning_question") or next_concept.get("child_question", "")
                    reply += f"\n\nSang phần tiếp theo về **{next_concept['name']}**, mình đang băn khoăn:\n> *\"{next_question}\"*"
                    self.memory.set_last_question(session_id, next_question)
                else:
                    reply += "\n\nTuyệt vời, bạn đã giúp mình nắm vững toàn bộ chuỗi mắt xích kiến thức nền tảng của bài học này bằng lập luận rất chặt chẽ kèm ví dụ sinh động."
                    self.memory.set_last_question(session_id, "Đã hoàn thành toàn bộ mắt xích nền tảng")
            else:
                event_type = "socratic_probing"
                detail = f"Hỏi vặn căn cứ {concept_name}"
                self.memory.set_last_question(session_id, reply)

        # 3. Construct Thinking Phases for UI presentation
        pedagogical_spotlight_description = "Đang rà soát toàn diện"
        if pedagogical_context:
            misconception_info = pedagogical_context.get("misconception")
            mechanism_info = pedagogical_context.get("mechanism")
            tradeoff_info = pedagogical_context.get("tradeoff")
            counter_example_info = pedagogical_context.get("counter_example")
            if factual_contradiction and misconception_info:
                pedagogical_spotlight_description = f"⚠️ Bẫy ngộ nhận: {misconception_info.get('name')}"
            elif not has_causal and mechanism_info:
                pedagogical_spotlight_description = f"⚙️ Cơ chế nhân quả: {mechanism_info.get('name')}"
            elif not has_example and counter_example_info:
                pedagogical_spotlight_description = f"💡 Ví dụ thực tế: {counter_example_info.get('name')}"
            elif tradeoff_info:
                pedagogical_spotlight_description = f"⚖️ Đánh đổi kỹ thuật: {tradeoff_info.get('dimension_a')} vs {tradeoff_info.get('dimension_b')}"

        phase1_details = [
            f"Nhận xét sư phạm: {critique}",
            f"Điểm mù Graph FalkorDB: {pedagogical_spotlight_description}",
            f"Cơ chế nhân quả: {'Đạt chuẩn chuỗi nguyên nhân - kết quả' if has_causal else 'Chưa làm rõ cơ chế nhân quả bên dưới'}",
            f"Ví dụ thực tế: {'Đã có ví dụ cụ thể / đời thường' if has_example else 'Chưa có ví dụ minh họa'}",
            f"Nguồn sự thật (§5 ①): {'Phát hiện ngộ nhận mâu thuẫn bài giảng' if factual_contradiction else 'Đúng bản chất kiến thức'}",
            f"Phạm vi thẩm quyền (§5 ③): {'Ngoài phạm vi / đòi đáp án' if is_out_of_scope else 'Đúng trọng tâm bài học'}",
            f"Thuật ngữ chuyên môn: {', '.join(buzzwords) if buzzwords else 'Không lạm dụng buzzword'}",
            f"Đánh giá tổng quát: {status_label} (Lượt {turn_count}/{settings.MAX_PROBING_TURNS})"
        ]

        thinking_phases = [
            {
                "phase_name": "Phase 1: Thẩm định 8 tiêu chí sư phạm Feynman",
                "badge": "Giám định",
                "details": phase1_details
            }
        ]

        if model_thinking and len(model_thinking.strip()) > 10:
            thinking_phases.append({
                "phase_name": "Phase 2: Chuỗi suy ngẫm nội tại của Alex (NVIDIA Nemotron Reasoning)",
                "badge": "Tư duy ngầm",
                "raw_thought": model_thinking.strip()
            })
        else:
            thinking_phases.append({
                "phase_name": "Phase 2: Định hình chiến lược phản biện Socratic",
                "badge": "Phản biện",
                "details": [
                    f"Bám sát lời giải thích: \"{student_msg[:75]}...\"",
                    f"Mục tiêu: Đào sâu vào cơ chế mắt xích của '{concept_name}', tránh dùng câu hỏi rập khuôn."
                ]
            })

        # 4. Record interaction turn into two-tiered memory
        turn_record = self.memory.add_turn(
            session_id=session_id,
            ask=current_question,
            answer=student_msg,
            agent_reply=reply,
            concept_id=concept_id,
            concept_name=concept_name,
            event_label=status_label,
            critique=critique
        )

        return {
            "agent_reply": reply,
            "thinking_phases": thinking_phases,
            "event_type": event_type,
            "event_label": status_label,
            "detail": detail,
            "citation": citation,
            "is_end_of_graph": is_end_of_graph,
            "available_paths": alternative_paths,
            "progress": self.graph_service.get_progress(),
            "turn_record": turn_record,
            "history": self.memory.get_history(session_id),
            "recent_turns": self.memory.get_recent_turns(session_id, limit=6),
            "global_summary": self.memory.get_global_summary(session_id)
        }

    def process_student_message_stream(
        self,
        student_msg: str,
        session_id: str = "default_session"
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Quy trình xử lý phản hồi học viên dạng STREAMING:
        1. Giám định 8 tiêu chí Feynman & đối chiếu FalkorDB (yield event 'thinking')
        2. Stream từng token/chunk của Alex về UI bằng ChatNVIDIA qua client.stream (yield event 'token')
        3. Ghi log hội thoại vào codebase/db/logs/, cập nhật bộ nhớ và đồ thị (yield event 'done')
        """
        current_concept = self.get_current_feynman_concept()
        concept_id = current_concept["id"]
        concept_name = current_concept["name"]
        citation = current_concept["citation"]
        core_truth = current_concept["core_truth"]
        quote_text = current_concept.get("quote", "")

        current_question = self.memory.get_last_question(session_id)
        if not current_question:
            current_question = current_concept.get("learning_question") or current_concept.get("child_question", "")

        turn_count = self.concept_turns.get(concept_id, 0) + 1
        self.concept_turns[concept_id] = turn_count

        pedagogical_context = self.graph_service.get_concept_pedagogical_context(concept_id) if self.graph_service else {}

        evaluation_result = self.guardrails.evaluate_teaching_explanation(
            student_msg=student_msg,
            core_truth=core_truth,
            quote_text=quote_text,
            turn_count=turn_count,
            pedagogical_context=pedagogical_context
        )

        is_cheating = evaluation_result.get("is_cheating", False)
        is_mastered = evaluation_result.get("is_mastered", False)
        has_causal = evaluation_result.get("has_causal_reasoning", False)
        has_example = evaluation_result.get("has_concrete_example", False)
        factual_contradiction = evaluation_result.get("factual_contradiction", False)
        is_out_of_scope = evaluation_result.get("is_out_of_scope", False)
        buzzwords = evaluation_result.get("buzzwords_unexplained", [])
        status_label = evaluation_result.get("status_label", "Hỏi vặn về cơ chế")
        critique = evaluation_result.get("critique", "Đang đào sâu cơ chế.")

        pedagogical_spotlight_description = "Đang rà soát toàn diện"
        if pedagogical_context:
            misconception_info = pedagogical_context.get("misconception")
            mechanism_info = pedagogical_context.get("mechanism")
            tradeoff_info = pedagogical_context.get("tradeoff")
            counter_example_info = pedagogical_context.get("counter_example")
            if factual_contradiction and misconception_info:
                pedagogical_spotlight_description = f"⚠️ Bẫy ngộ nhận: {misconception_info.get('name')}"
            elif not has_causal and mechanism_info:
                pedagogical_spotlight_description = f"⚙️ Cơ chế nhân quả: {mechanism_info.get('name')}"
            elif not has_example and counter_example_info:
                pedagogical_spotlight_description = f"💡 Ví dụ thực tế: {counter_example_info.get('name')}"
            elif tradeoff_info:
                pedagogical_spotlight_description = f"⚖️ Đánh đổi kỹ thuật: {tradeoff_info.get('dimension_a')} vs {tradeoff_info.get('dimension_b')}"

        phase1_details = [
            f"Nhận xét sư phạm: {critique}",
            f"Điểm mù Graph FalkorDB: {pedagogical_spotlight_description}",
            f"Cơ chế nhân quả: {'Đạt chuẩn chuỗi nguyên nhân - kết quả' if has_causal else 'Chưa làm rõ cơ chế nhân quả bên dưới'}",
            f"Ví dụ thực tế: {'Đã có ví dụ cụ thể / đời thường' if has_example else 'Chưa có ví dụ minh họa'}",
            f"Nguồn sự thật (§5 ①): {'Phát hiện ngộ nhận mâu thuẫn bài giảng' if factual_contradiction else 'Đúng bản chất kiến thức'}",
            f"Phạm vi thẩm quyền (§5 ③): {'Ngoài phạm vi / đòi đáp án' if is_out_of_scope else 'Đúng trọng tâm bài học'}",
            f"Thuật ngữ chuyên môn: {', '.join(buzzwords) if buzzwords else 'Không lạm dụng buzzword'}",
            f"Đánh giá tổng quát: {status_label} (Lượt {turn_count}/{settings.MAX_PROBING_TURNS})"
        ]

        thinking_phases = [
            {
                "phase_name": "Phase 1: Thẩm định 8 tiêu chí sư phạm Feynman",
                "badge": "Giám định",
                "details": phase1_details
            }
        ]

        # 1. Phát tán sự kiện Thinking ngay lập tức khi hoàn tất giám định
        yield {
            "type": "thinking",
            "thinking_phases": thinking_phases,
            "evaluation": evaluation_result,
            "event_label": status_label,
            "citation": citation,
            "concept_name": concept_name
        }

        reply_chunks = []
        model_thinking_chunks = []
        event_type = "socratic_probing"
        detail = f"Hỏi vặn căn cứ {concept_name}"

        # 2. Xử lý các nhánh và Stream Tokens
        if is_cheating:
            reply = (
                f"Đoạn này nghe giống như trích dẫn từ tài liệu {citation} quá bạn ơi. "
                f"Nếu để bạn tự diễn đạt lại bằng ngôn ngữ của riêng bạn về {concept_name}, "
                f"thì bạn giải thích điểm mấu chốt ở đây như thế nào?"
            )
            for word in reply.split(" "):
                chunk_str = word + " "
                reply_chunks.append(chunk_str)
                yield {"type": "token", "chunk": chunk_str}
            event_type = "parroting_alert"
            detail = f"Trùng khớp nguyên văn {citation} — yêu cầu tự diễn giải"
            self.memory.set_last_question(session_id, reply)

        elif is_out_of_scope:
            reply = "Mấy việc đó bạn xem trên kênh thông báo của lớp nha! Mình cũng là sinh viên đang học nè, đâu có đáp án đâu. Hai đứa mình cùng tập trung giải thích lại chỗ cơ chế này đi bạn ơi?"
            for word in reply.split(" "):
                chunk_str = word + " "
                reply_chunks.append(chunk_str)
                yield {"type": "token", "chunk": chunk_str}
            event_type = "out_of_scope_deflection"
            detail = "Từ chối việc ngoài thẩm quyền, kéo về bài giảng"
            self.memory.set_last_question(session_id, reply)

        else:
            memory_context = self.memory.format_memory_for_prompt(session_id)
            probing_prompt = build_protege_probing_prompt(
                concept_name=concept_name,
                citation=citation,
                core_truth=core_truth,
                student_msg=student_msg,
                analysis_report=evaluation_result,
                pedagogical_context=pedagogical_context,
                conversation_history=memory_context
            )

            is_inside_think = False
            for chunk_data in self.nvidia_client.generate_stream_chunks(
                prompt=probing_prompt,
                system_prompt=PROTEGE_SYSTEM_PROMPT
            ):
                reasoning = chunk_data.get("reasoning", "")
                if reasoning:
                    model_thinking_chunks.append(reasoning)

                content = chunk_data.get("content", "")
                if content:
                    if "<think>" in content:
                        is_inside_think = True
                        content = content.replace("<think>", "")
                    if "</think>" in content:
                        is_inside_think = False
                        parts = content.split("</think>")
                        model_thinking_chunks.append(parts[0])
                        content = parts[1] if len(parts) > 1 else ""

                    if is_inside_think:
                        model_thinking_chunks.append(content)
                    elif content:
                        reply_chunks.append(content)
                        yield {"type": "token", "chunk": content}

            reply = "".join(reply_chunks).strip()
            if not reply or len(reply) < 10:
                fallback_msg = "Ý bạn giải thích có điểm đáng chú ý, nhưng về mặt cơ chế vận hành bên dưới thì bài toán này được xử lý cụ thể như thế nào bạn nhỉ?"
                yield {"type": "token", "chunk": fallback_msg}
                reply = fallback_msg

            if not is_mastered and turn_count >= settings.MAX_PROBING_TURNS:
                hint_str = f"\n\n(Gợi ý nhỏ: Mình thấy chỗ này còn hơi trừu tượng, bạn thử mở lại {citation} xem phần cơ chế cốt lõi rồi hai đứa mình cùng bàn tiếp nhé!)"
                reply += hint_str
                yield {"type": "token", "chunk": hint_str}

            is_end_of_graph = False
            if is_mastered:
                event_type = "causal_breakthrough"
                detail = f"Đã làm chủ {concept_name}"
                try:
                    self.graph_service.graph.query(f"MATCH (fc:FeynmanConcept {{id: '{concept_id}'}}) SET fc.status = 'COVERED'")
                except Exception:
                    pass
                self.graph_service.mark_concept_covered(concept_id)
                if self.graph_service and self.graph_service.current_track:
                    self._concept_cache.pop(self.graph_service.current_track, None)
                is_end_of_graph, _, _ = self.graph_service.is_end_of_graph()

                if not is_end_of_graph:
                    next_concept = self.get_current_feynman_concept()
                    next_question = next_concept.get("learning_question") or next_concept.get("child_question", "")
                    next_str = f"\n\nSang phần tiếp theo về **{next_concept['name']}**, mình đang băn khoăn:\n> *\"{next_question}\"*"
                    reply += next_str
                    yield {"type": "token", "chunk": next_str}
                    self.memory.set_last_question(session_id, next_question)
                else:
                    congrats_str = "\n\nTuyệt vời, bạn đã giúp mình nắm vững toàn bộ chuỗi mắt xích kiến thức nền tảng của bài học này bằng lập luận rất chặt chẽ kèm ví dụ sinh động."
                    reply += congrats_str
                    yield {"type": "token", "chunk": congrats_str}
                    self.memory.set_last_question(session_id, "Đã hoàn thành toàn bộ mắt xích nền tảng")
            else:
                event_type = "socratic_probing"
                detail = f"Hỏi vặn căn cứ {concept_name}"
                self.memory.set_last_question(session_id, reply)

        full_thinking = "".join(model_thinking_chunks).strip()
        if full_thinking and len(full_thinking) > 10:
            thinking_phases.append({
                "phase_name": "Phase 2: Chuỗi suy ngẫm nội tại của Alex (NVIDIA Nemotron Reasoning)",
                "badge": "Tư duy ngầm",
                "raw_thought": full_thinking
            })
        else:
            thinking_phases.append({
                "phase_name": "Phase 2: Định hình chiến lược phản biện Socratic",
                "badge": "Phản biện",
                "details": [
                    f"Bám sát lời giải thích: \"{student_msg[:75]}...\"",
                    f"Mục tiêu: Đào sâu vào cơ chế mắt xích của '{concept_name}', tránh dùng câu hỏi rập khuôn."
                ]
            })

        turn_record = self.memory.add_turn(
            session_id=session_id,
            ask=current_question,
            answer=student_msg,
            agent_reply=reply,
            concept_id=concept_id,
            concept_name=concept_name,
            event_label=status_label,
            critique=critique
        )

        yield {
            "type": "done",
            "reply": reply,
            "thinking_phases": thinking_phases,
            "event_type": event_type,
            "event_label": status_label,
            "detail": detail,
            "citation": citation,
            "is_end_of_graph": is_end_of_graph if 'is_end_of_graph' in locals() else False,
            "progress": self.graph_service.get_progress(),
            "turn_record": turn_record
        }

    def get_session_history(self, session_id: str = "default_session") -> List[Dict[str, Any]]:
        """Retrieve complete turn history records for session."""
        return self.memory.get_history(session_id)

    def get_recent_memory(self, session_id: str = "default_session", limit: int = 6) -> List[Dict[str, Any]]:
        """Retrieve recent Ask-Answer turns within sliding window."""
        return self.memory.get_recent_turns(session_id, limit=limit)

    def get_global_summary(self, session_id: str = "default_session") -> str:
        """Retrieve global incremental summary text for session."""
        return self.memory.get_global_summary(session_id)

    def clear_session_history(self, session_id: str = "default_session"):
        """Clear history records and summaries for a session."""
        self.memory.clear_history(session_id)

    def choose_alternative_path(self, track_id: str) -> Dict[str, Any]:
        """Switch traversal to an alternative learning path."""
        self.graph_service.set_active_track(track_id)
        return {
            "agent_reply": f"Rất hay! Mình cùng bạn chuyển sang tìm hiểu nhánh chuyên đề mới: '{track_id}'.",
            "event_type": "branch_activated",
            "event_label": "Mở nhánh tri thức mới",
            "progress": self.graph_service.get_progress()
        }

    def switch_lesson(self, track_id: str, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Switch active lesson track on FalkorDB:
        - Update active track
        - Fetch first concept for new track
        - Generate topic intro directions
        - Update last question in session memory
        """
        self.graph_service.set_active_track(track_id)
        self.concept_turns.clear()
        self._concept_cache.pop(track_id, None)

        current_concept = self.get_current_feynman_concept()
        directions = self.generate_topic_intro_directions(current_concept)
        clean_name = clean_lesson_title(current_concept.get("name", "chủ đề mới"))
        self.memory.set_last_question(session_id, f"Khởi đầu ôn tập: {clean_name}")

        return {
            "status": "success",
            "active_track": track_id,
            "concept": current_concept,
            "topic_directions": directions,
            "progress": self.graph_service.get_progress(track=track_id)
        }
