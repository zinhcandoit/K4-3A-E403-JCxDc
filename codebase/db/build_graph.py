import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from falkordb import FalkorDB
from config.config import settings
from db.data_loader import RealDataLoader


class SlideGraphBuilder:
    """
    Xây dựng Đồ thị Tri thức Sư phạm Đa quan hệ bảo toàn tính cục bộ (Knowledge Locality) trên FalkorDB:
    - Mỗi tài liệu bài giảng là một không gian tri thức độc lập, chỉ liên kết nội bộ trong cùng một file.
    - Tuyệt đối không nối cạnh chéo giữa các bài học khác nhau để duy trì ngữ cảnh học tập tập trung.
    - Khởi tạo 5 loại Node thực thể và 8 loại Quan hệ Sư phạm bám sát phương pháp Feynman và AI Spec Track D3.
    """

    def __init__(
        self,
        host: str = settings.FALKOR_HOST,
        port: int = settings.FALKOR_PORT,
        graph_name: str = settings.GRAPH_NAME
    ):
        self.database_client = FalkorDB(host=host, port=port)
        self.graph = self.database_client.select_graph(graph_name)
        self.graph_name = graph_name
        self.loader = RealDataLoader()

    def reset_database(self) -> None:
        """Xóa trắng đồ thị cũ trong FalkorDB để tái tạo dữ liệu mới sạch sẽ."""
        try:
            self.graph.delete()
            print(f"Đã làm sạch đồ thị: '{self.graph_name}'")
        except Exception:
            pass
        self.graph = self.database_client.select_graph(self.graph_name)

    def _sanitize_cypher_string(self, value: Any) -> str:
        """Chuẩn hóa và thoát ký tự an toàn cho câu truy vấn Cypher."""
        if not value:
            return ""
        sanitized = str(value).replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        sanitized = sanitized.replace("\n", " ").replace("\r", " ")
        return sanitized.strip()

    def build_and_ingest(self, target_file: Optional[str] = None, include_slides: bool = False, force_refresh: bool = False) -> None:
        """
        Nạp đồ thị tri thức sư phạm cục bộ theo từng file độc lập:
        - Mặc định: Nạp tài liệu bài giảng mục tiêu.
        - Trích xuất động các khía cạnh sư phạm (bẫy ngộ nhận, đánh đổi, cơ chế, phản ví dụ) qua ChatNVIDIA.
        - Khởi tạo 5 loại Node và 8 loại Cạnh quan hệ nội bộ.
        """
        self.reset_database()
        target_document = target_file or settings.get_default_document()
        print("=" * 70, flush=True)
        print("BẮT ĐẦU KHỞI TẠO ĐỒ THỊ SƯ PHẠM ĐA QUAN HỆ (KNOWLEDGE LOCALITY)", flush=True)
        print(f"Tài liệu mục tiêu: '{target_document}'", flush=True)
        print("Nguyên tắc: Liên kết nội bộ theo từng bài học độc lập", flush=True)
        print("=" * 70, flush=True)

        # 1. Trích xuất danh sách khái niệm từ tài liệu bài giảng
        print(f"\n📂 [Bước 1/4] Đang phân tích tài liệu bài giảng: '{target_document}'...", flush=True)
        feynman_concepts = self.loader.parse_vlearn_transcripts(target_filename=target_document)
        if not feynman_concepts:
            print(f"❌ Cảnh báo: Không tìm thấy khái niệm nào từ tài liệu: {target_document}", flush=True)
            return
        print(f"   ✅ Đã trích xuất {len(feynman_concepts)} khái niệm mục tiêu từ bài giảng.", flush=True)

        # 2. Trích xuất động các khía cạnh sư phạm (Điểm mù nhận thức của học viên)
        print(f"\n🤖 [Bước 2/4] Đang trích xuất động các điểm mù sư phạm qua ChatNVIDIA ({len(feynman_concepts)} khái niệm)...", flush=True)
        pedagogical_aspects = self.loader.extract_pedagogical_aspects(
            feynman_concepts,
            cache_key=target_document,
            force_refresh=force_refresh
        )
        print(f"   ✅ Hoàn tất trích xuất điểm mù sư phạm ({len(pedagogical_aspects)}/{len(feynman_concepts)} khái niệm sẵn sàng).", flush=True)

        # 3. Tạo các Node Khái niệm và các Node Vệ tinh Sư phạm trên FalkorDB
        print(f"\n🗄️ [Bước 3/4] Đang nạp các Node và Cạnh Sư phạm vào FalkorDB...", flush=True)
        total_concepts = len(feynman_concepts)
        for idx, concept in enumerate(feynman_concepts, 1):
            if idx == 1 or idx % 5 == 0 or idx == total_concepts:
                pct = int(idx / total_concepts * 100)
                print(f"   ⚙️ Nạp Node vào FalkorDB: {idx}/{total_concepts} ({pct}%) [{concept['name'][:28]}]...", flush=True)

            concept_id = concept["id"]
            safe_name = self._sanitize_cypher_string(concept["name"])
            safe_quote = self._sanitize_cypher_string(concept["quote_text"])
            safe_truth = self._sanitize_cypher_string(concept["core_truth"])
            safe_question = self._sanitize_cypher_string(concept.get("learning_question", ""))
            safe_module = self._sanitize_cypher_string(concept.get("module", "VLearn Knowledge"))
            safe_track = self._sanitize_cypher_string(concept.get("track", settings.get_default_track()))
            safe_doc_id = self._sanitize_cypher_string(concept.get("doc_id", target_document))

            # 3.0. Node Khái niệm (:Concept:FeynmanConcept)
            concept_query = f"""
            CREATE (c:Concept:FeynmanConcept {{
                id: '{concept_id}',
                name: '{safe_name}',
                category: 'Feynman VLearn Pack',
                module: '{safe_module}',
                track: '{safe_track}',
                doc_id: '{safe_doc_id}',
                page: {concept["order"]},
                order: {concept["order"]},
                summary: '{safe_truth}',
                status: 'UNCOVERED',
                citation: '{concept["citation"]}',
                core_truth: '{safe_truth}',
                quote_text: '{safe_quote}',
                learning_question: '{safe_question}',
                child_question: '{safe_question}'
            }})
            """
            self.graph.query(concept_query)

            # Lấy thông tin 4 điểm mù sư phạm tương ứng
            aspect = pedagogical_aspects.get(concept_id, {})
            misconception_info = aspect.get("pitfall", {})
            tradeoff_info = aspect.get("tradeoff", {})
            mechanism_info = aspect.get("mechanism", {})
            counter_example_info = aspect.get("counter_example", {})

            # 3.1. Node Bẫy ngộ nhận (:Misconception) + Cạnh [:HAS_COMMON_PITFALL] & [:CONTRADICTS]
            if misconception_info:
                misc_id = f"misc_{concept_id}"
                misc_name = self._sanitize_cypher_string(misconception_info.get("name", f"Ngộ nhận về {safe_name}"))
                pitfall_text = self._sanitize_cypher_string(misconception_info.get("pitfall_text", ""))
                misc_probe = self._sanitize_cypher_string(misconception_info.get("probe_question", ""))
                truth_hint = self._sanitize_cypher_string(misconception_info.get("truth_hint", safe_truth))

                self.graph.query(f"""
                CREATE (m:Misconception {{
                    id: '{misc_id}',
                    concept_id: '{concept_id}',
                    name: '{misc_name}',
                    pitfall_text: '{pitfall_text}',
                    probe_question: '{misc_probe}',
                    truth_hint: '{truth_hint}',
                    track: '{safe_track}',
                    doc_id: '{safe_doc_id}'
                }})
                """)
                self.graph.query(f"""
                MATCH (c:Concept {{id: '{concept_id}'}}), (m:Misconception {{id: '{misc_id}'}})
                CREATE (c)-[:HAS_COMMON_PITFALL]->(m),
                       (m)-[:CONTRADICTS]->(c)
                """)

            # 3.2. Node Đánh đổi kỹ thuật (:Tradeoff) + Cạnh [:HAS_TRADEOFF]
            if tradeoff_info:
                trade_id = f"trade_{concept_id}"
                trade_name = self._sanitize_cypher_string(tradeoff_info.get("name", f"Đánh đổi trong {safe_name}"))
                dimension_a = self._sanitize_cypher_string(tradeoff_info.get("dimension_a", "Tối ưu hóa"))
                dimension_b = self._sanitize_cypher_string(tradeoff_info.get("dimension_b", "Chi phí / Rủi ro"))
                trade_probe = self._sanitize_cypher_string(tradeoff_info.get("probe_question", ""))

                self.graph.query(f"""
                CREATE (t:Tradeoff {{
                    id: '{trade_id}',
                    concept_id: '{concept_id}',
                    name: '{trade_name}',
                    dimension_a: '{dimension_a}',
                    dimension_b: '{dimension_b}',
                    probe_question: '{trade_probe}',
                    track: '{safe_track}',
                    doc_id: '{safe_doc_id}'
                }})
                """)
                self.graph.query(f"""
                MATCH (c:Concept {{id: '{concept_id}'}}), (t:Tradeoff {{id: '{trade_id}'}})
                CREATE (c)-[:HAS_TRADEOFF]->(t)
                """)

            # 3.3. Node Cơ chế nhân quả (:Mechanism) + Cạnh [:DEPENDS_ON_MECHANISM]
            if mechanism_info:
                mech_id = f"mech_{concept_id}"
                mech_name = self._sanitize_cypher_string(mechanism_info.get("name", f"Cơ chế của {safe_name}"))
                causal_chain = self._sanitize_cypher_string(mechanism_info.get("causal_chain", ""))
                mech_probe = self._sanitize_cypher_string(mechanism_info.get("probe_question", ""))

                self.graph.query(f"""
                CREATE (mech:Mechanism {{
                    id: '{mech_id}',
                    concept_id: '{concept_id}',
                    name: '{mech_name}',
                    causal_chain: '{causal_chain}',
                    probe_question: '{mech_probe}',
                    track: '{safe_track}',
                    doc_id: '{safe_doc_id}'
                }})
                """)
                self.graph.query(f"""
                MATCH (c:Concept {{id: '{concept_id}'}}), (mech:Mechanism {{id: '{mech_id}'}})
                CREATE (c)-[:DEPENDS_ON_MECHANISM]->(mech)
                """)

            # 3.4. Node Phản ví dụ / Tình huống biên (:CounterExample) + Cạnh [:HAS_COUNTER_EXAMPLE]
            if counter_example_info:
                cex_id = f"cex_{concept_id}"
                cex_name = self._sanitize_cypher_string(counter_example_info.get("name", f"Ví dụ của {safe_name}"))
                scenario_text = self._sanitize_cypher_string(counter_example_info.get("scenario", ""))
                cex_probe = self._sanitize_cypher_string(counter_example_info.get("probe_question", ""))

                self.graph.query(f"""
                CREATE (cex:CounterExample {{
                    id: '{cex_id}',
                    concept_id: '{concept_id}',
                    name: '{cex_name}',
                    scenario: '{scenario_text}',
                    probe_question: '{cex_probe}',
                    track: '{safe_track}',
                    doc_id: '{safe_doc_id}'
                }})
                """)
                self.graph.query(f"""
                MATCH (c:Concept {{id: '{concept_id}'}}), (cex:CounterExample {{id: '{cex_id}'}})
                CREATE (c)-[:HAS_COUNTER_EXAMPLE]->(cex)
                """)

        # 4. Nối các cạnh liên kết tiến trình Socratic nội bộ theo từng file
        print(f"\n🔗 [Bước 4/4] Đang kết nối các cạnh quan hệ Socratic nội bộ...", flush=True)
        concepts_by_document: Dict[str, List[Dict[str, Any]]] = {}
        for concept in feynman_concepts:
            document_id = concept["doc_id"]
            if document_id not in concepts_by_document:
                concepts_by_document[document_id] = []
            concepts_by_document[document_id].append(concept)

        prerequisite_edge_count = 0
        deep_dive_edge_count = 0
        alternative_edge_count = 0

        for document_id, concept_list in concepts_by_document.items():
            concept_list.sort(key=lambda item: item["order"])
            total_items = len(concept_list)
            for idx in range(total_items - 1):
                current_id = concept_list[idx]["id"]
                next_id = concept_list[idx + 1]["id"]

                # Cạnh PREREQUISITE_FOR: Tiến trình logic bài học
                self.graph.query(f"""
                MATCH (a:Concept {{id: '{current_id}', doc_id: '{document_id}'}}), (b:Concept {{id: '{next_id}', doc_id: '{document_id}'}})
                CREATE (a)-[:PREREQUISITE_FOR]->(b)
                """)
                prerequisite_edge_count += 1

                # Cạnh DEEP_DIVE_INTO: Nhánh đào sâu chuyên sâu
                if idx % 2 == 1:
                    self.graph.query(f"""
                    MATCH (a:Concept {{id: '{current_id}', doc_id: '{document_id}'}}), (b:Concept {{id: '{next_id}', doc_id: '{document_id}'}})
                    CREATE (a)-[:DEEP_DIVE_INTO {{branch: 'Đào sâu cơ chế chuyên biệt'}}]->(b)
                    """)
                    deep_dive_edge_count += 1

                # Cạnh ALTERNATIVE_PATH: Nhánh rẽ thay thế khi kẹt
                if idx + 2 < total_items:
                    skip_id = concept_list[idx + 2]["id"]
                    self.graph.query(f"""
                    MATCH (a:Concept {{id: '{current_id}', doc_id: '{document_id}'}}), (c:Concept {{id: '{skip_id}', doc_id: '{document_id}'}})
                    CREATE (a)-[:ALTERNATIVE_PATH {{branch: 'Hướng tiếp cận thực hành'}}]->(c)
                    """)
                    alternative_edge_count += 1

        print(
            f"   ✅ Đã tạo {prerequisite_edge_count} PREREQUISITE_FOR, "
            f"{deep_dive_edge_count} DEEP_DIVE_INTO, "
            f"{alternative_edge_count} ALTERNATIVE_PATH nội bộ trong bài học.",
            flush=True
        )

        # 5. Xử lý nạp slide PDF thành track độc lập riêng biệt (nếu được yêu cầu)
        if include_slides:
            slide_concepts = self.loader.parse_lecture_slides_pdf()
            if slide_concepts:
                print(f"\n📑 [Bổ sung] Đang nạp {len(slide_concepts)} slide thành Track độc lập riêng...", flush=True)
                for slide in slide_concepts:
                    safe_title = self._sanitize_cypher_string(slide["title"])
                    safe_summary = self._sanitize_cypher_string(slide["summary"])
                    safe_module = self._sanitize_cypher_string(slide["module"])
                    safe_track = self._sanitize_cypher_string(slide["track"])
                    safe_doc_id = self._sanitize_cypher_string(slide["doc_id"])

                    slide_query = f"""
                    CREATE (c:Concept {{
                        id: '{slide["id"]}',
                        name: '{safe_title}',
                        category: '{slide["category"]}',
                        module: '{safe_module}',
                        track: '{safe_track}',
                        doc_id: '{safe_doc_id}',
                        page: {slide["page"]},
                        order: {slide["order"]},
                        summary: '{safe_summary}',
                        status: 'UNCOVERED'
                    }})
                    """
                    self.graph.query(slide_query)

                slide_edge_count = 0
                for idx in range(len(slide_concepts) - 1):
                    current_id = slide_concepts[idx]["id"]
                    next_id = slide_concepts[idx + 1]["id"]
                    self.graph.query(f"""
                    MATCH (a:Concept {{id: '{current_id}'}}), (b:Concept {{id: '{next_id}'}})
                    CREATE (a)-[:PREREQUISITE_FOR]->(b)
                    """)
                    slide_edge_count += 1
                print(f"   ✅ Đã tạo {slide_edge_count} liên kết PREREQUISITE_FOR nội bộ trong file slide PDF.", flush=True)

        print("\n🎉 KHỞI TẠO ĐỒ THỊ SƯ PHẠM ĐA QUAN HỆ HOÀN TẤT 100%!", flush=True)
        self.verify_summary()

    def verify_summary(self) -> None:
        """In bảng tóm tắt đồ thị từ FalkorDB với 5 loại Node và 8 loại Cạnh quan hệ."""
        concept_res = self.graph.query("MATCH (c:Concept) RETURN count(c)")
        misc_res = self.graph.query("MATCH (m:Misconception) RETURN count(m)")
        trade_res = self.graph.query("MATCH (t:Tradeoff) RETURN count(t)")
        mech_res = self.graph.query("MATCH (mech:Mechanism) RETURN count(mech)")
        cex_res = self.graph.query("MATCH (cex:CounterExample) RETURN count(cex)")
        edge_res = self.graph.query("MATCH (a)-[r]->(b) RETURN type(r), count(r) ORDER BY count(r) DESC")

        concept_count = concept_res.result_set[0][0] if concept_res.result_set else 0
        misconception_count = misc_res.result_set[0][0] if misc_res.result_set else 0
        tradeoff_count = trade_res.result_set[0][0] if trade_res.result_set else 0
        mechanism_count = mech_res.result_set[0][0] if mech_res.result_set else 0
        counter_example_count = cex_res.result_set[0][0] if cex_res.result_set else 0
        total_nodes = concept_count + misconception_count + tradeoff_count + mechanism_count + counter_example_count

        print("\n" + "=" * 80, flush=True)
        print(f"BẢNG TỔNG KẾT ĐỒ THỊ SƯ PHẠM ĐA QUAN HỆ TRÊN FALKORDB: '{self.graph_name}'", flush=True)
        print(f"Tổng số Nodes: {total_nodes}", flush=True)
        print(f"   - (:Concept:FeynmanConcept): {concept_count} nodes", flush=True)
        print(f"   - (:Misconception) [Bẫy ngộ nhận]: {misconception_count} nodes", flush=True)
        print(f"   - (:Tradeoff) [Đánh đổi kỹ thuật]: {tradeoff_count} nodes", flush=True)
        print(f"   - (:Mechanism) [Cơ chế nhân quả]: {mechanism_count} nodes", flush=True)
        print(f"   - (:CounterExample) [Phản ví dụ / Biên]: {counter_example_count} nodes", flush=True)
        print("-" * 80, flush=True)
        print("Các loại Quan hệ Sư phạm (Socratic Relationships):", flush=True)
        total_edges = 0
        for row in edge_res.result_set:
            relation_name, count = row[0], row[1]
            print(f"   - [:{relation_name}]: {count} cạnh", flush=True)
            total_edges += count
        print(f"Tổng số Cạnh liên kết: {total_edges}", flush=True)
        print("=" * 80 + "\n", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Khởi tạo đồ thị tri thức cục bộ theo từng file độc lập")
    parser.add_argument("--file", type=str, default=None, help="Tên file cụ thể cần build graph")
    parser.add_argument("--all", action="store_true", help="Nạp tất cả file thành các track độc lập")
    parser.add_argument("--slides", action="store_true", help="Nạp thêm slide PDF thành track riêng biệt")
    parser.add_argument("--force", action="store_true", help="Bắt buộc gọi lại LLM trích xuất mới thay vì dùng cache")
    args = parser.parse_args()

    builder = SlideGraphBuilder()
    target = "all" if args.all else args.file
    builder.build_and_ingest(target_file=target, include_slides=args.slides, force_refresh=args.force)


if __name__ == "__main__":
    main()
