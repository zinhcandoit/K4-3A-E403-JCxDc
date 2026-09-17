import os
import sys
from typing import Dict, Any, List, Optional, Tuple

from falkordb import FalkorDB
from config.config import settings

FALKOR_HOST = settings.FALKOR_HOST
FALKOR_PORT = settings.FALKOR_PORT
GRAPH_NAME = settings.GRAPH_NAME


class GraphService:
    """
    Dịch vụ quản lý truy vấn Đồ thị Tri thức cục bộ trên FalkorDB cho Track D3:
    - Theo dõi tiến độ học theo từng nhánh / file độc lập (Knowledge Locality).
    - Nhận diện thời điểm chạm 'The End of Graph'.
    - Xuất dữ liệu Nodes & Links đa quan hệ để vẽ mạng đồ thị trực quan trên Web UI.
    """

    def __init__(self, host: str = FALKOR_HOST, port: int = FALKOR_PORT, graph_name: str = GRAPH_NAME):
        self.database_client = FalkorDB(host=host, port=port)
        self.graph = self.database_client.select_graph(graph_name)
        self.current_track = settings.get_default_track()

    def set_active_track(self, track_name: str) -> None:
        """Chuyển đổi bài học / chuyên đề đang hoạt động."""
        self.current_track = track_name

    def get_progress(self, track: Optional[str] = None) -> Dict[str, Any]:
        """Tính toán tỷ lệ hoàn thành đồ thị theo track (hoặc toàn bộ đồ thị)."""
        active_track = track or self.current_track

        if active_track == "all":
            query = "MATCH (c:Concept) RETURN c.id, c.name, c.status, c.page, c.track, c.category ORDER BY c.order"
        else:
            query = f"MATCH (c:Concept {{track: '{active_track}'}}) RETURN c.id, c.name, c.status, c.page, c.track, c.category ORDER BY c.order"

        query_result = self.graph.query(query)
        nodes = query_result.result_set
        total_nodes = len(nodes)

        if total_nodes == 0:
            return {
                "total": 0,
                "covered": 0,
                "percent": 0.0,
                "is_end": False,
                "track": active_track,
                "nodes": []
            }

        covered_nodes = sum(1 for node in nodes if node[2] == "COVERED")
        completion_percent = round((covered_nodes / total_nodes) * 100, 1)

        node_list = [
            {
                "id": node[0],
                "name": node[1],
                "status": node[2],
                "page": node[3],
                "track": node[4],
                "category": node[5]
            }
            for node in nodes
        ]

        return {
            "total": total_nodes,
            "covered": covered_nodes,
            "percent": completion_percent,
            "is_end": (covered_nodes == total_nodes),
            "track": active_track,
            "nodes": node_list
        }

    def get_next_probing_target(self, track: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Lấy khái niệm chưa hoàn thành (UNCOVERED) tiếp theo kèm câu hỏi hỏi vặn và gợi ý."""
        active_track = track or self.current_track
        query = f"""
        MATCH (c:Concept {{status: 'UNCOVERED', track: '{active_track}'}})
        OPTIONAL MATCH (c)-[:HAS_COMMON_PITFALL]->(m:Misconception)
        RETURN c.id, c.name, c.page, c.summary, m.probe_question, m.truth_hint, c.track
        ORDER BY c.order
        LIMIT 1
        """
        query_result = self.graph.query(query)
        if not query_result.result_set:
            return None

        row = query_result.result_set[0]
        concept_id, concept_name, page, summary, probe_question, truth_hint, track_name = row

        default_probe = f"Bạn có thể phân tích cơ chế và giải thích giúp mình về '{concept_name}' (ở trang {page}) được không?"
        return {
            "concept_id": concept_id,
            "concept_name": concept_name,
            "page": page,
            "summary": summary,
            "probe_question": probe_question or default_probe,
            "truth_hint": truth_hint or summary,
            "track": track_name
        }

    def mark_concept_covered(self, concept_id: str) -> bool:
        """Đánh dấu một khái niệm đã được học viên giải thích thấu suốt."""
        query = f"""
        MATCH (c:Concept {{id: '{concept_id}'}})
        SET c.status = 'COVERED'
        RETURN c.name, c.status
        """
        result = self.graph.query(query)
        return len(result.result_set) > 0

    def is_end_of_graph(self, track: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, str]]]:
        """
        Kiểm tra bài học hiện tại đã hoàn thành toàn bộ các khái niệm chưa.
        Nếu đã xong, trả về danh sách các nhánh rẽ và chuyên đề mở rộng tiếp theo.
        """
        active_track = track or self.current_track
        count_query = f"MATCH (c:Concept {{status: 'UNCOVERED', track: '{active_track}'}}) RETURN count(c)"
        count_result = self.graph.query(count_query)
        uncovered_count = count_result.result_set[0][0] if count_result.result_set else 0

        if uncovered_count == 0:
            branch_query = """
            MATCH (a:Concept)-[r:ALTERNATIVE_PATH|DEEP_DIVE_INTO]->(b:Concept)
            RETURN DISTINCT b.track, type(r), r.branch, b.category
            """
            branch_result = self.graph.query(branch_query)
            available_paths = [
                {
                    "track_id": branch[0],
                    "relation": branch[1],
                    "name": branch[2] or branch[3],
                    "category": branch[3]
                }
                for branch in branch_result.result_set
            ]

            completion_message = f"Chúc mừng: Bạn đã hoàn thành toàn bộ mắt xích kiến thức của bài học '{active_track}'!"
            return True, completion_message, available_paths

        remaining_message = f"Còn {uncovered_count} khái niệm chưa được làm rõ trong bài học '{active_track}'."
        return False, remaining_message, []

    def reset_track_progress(self, track: Optional[str] = None) -> None:
        """Đặt lại trạng thái UNCOVERED cho các khái niệm trong track được chỉ định."""
        active_track = track or self.current_track
        try:
            if active_track == "all":
                self.graph.query("MATCH (c:Concept) SET c.status = 'UNCOVERED'")
            else:
                self.graph.query(f"MATCH (c:Concept {{track: '{active_track}'}}) SET c.status = 'UNCOVERED'")
        except Exception as error:
            print(f"Lỗi khi đặt lại tiến độ track: {error}")

    def get_concept_pedagogical_context(self, concept_id: str) -> Dict[str, Any]:
        """
        Truy vấn toàn bộ 4 khía cạnh điểm mù sư phạm (ngộ nhận, đánh đổi, cơ chế, phản ví dụ)
        liên kết với khái niệm từ FalkorDB để trang bị cho Alex hỏi vặn chính xác điểm học viên chưa nhận ra.
        """
        query = f"""
        MATCH (c:Concept {{id: '{concept_id}'}})
        OPTIONAL MATCH (c)-[:HAS_COMMON_PITFALL]->(m:Misconception)
        OPTIONAL MATCH (c)-[:HAS_TRADEOFF]->(t:Tradeoff)
        OPTIONAL MATCH (c)-[:DEPENDS_ON_MECHANISM]->(mech:Mechanism)
        OPTIONAL MATCH (c)-[:HAS_COUNTER_EXAMPLE]->(cex:CounterExample)
        RETURN 
            c.id, c.name, c.core_truth,
            m.name, m.pitfall_text, m.probe_question, m.truth_hint,
            t.name, t.dimension_a, t.dimension_b, t.probe_question,
            mech.name, mech.causal_chain, mech.probe_question,
            cex.name, cex.scenario, cex.probe_question
        LIMIT 1
        """
        try:
            result = self.graph.query(query)
            if not result.result_set:
                return {}

            row = result.result_set[0]
            concept_key = row[0]
            concept_name = row[1]
            core_truth = row[2] or ""

            misconception_data = {
                "name": row[3],
                "pitfall_text": row[4],
                "probe_question": row[5],
                "truth_hint": row[6]
            } if row[3] else None

            tradeoff_data = {
                "name": row[7],
                "dimension_a": row[8],
                "dimension_b": row[9],
                "probe_question": row[10]
            } if row[7] else None

            mechanism_data = {
                "name": row[11],
                "causal_chain": row[12],
                "probe_question": row[13]
            } if row[11] else None

            counter_example_data = {
                "name": row[14],
                "scenario": row[15],
                "probe_question": row[16]
            } if row[14] else None

            return {
                "concept_id": concept_key,
                "concept_name": concept_name,
                "core_truth": core_truth,
                "misconception": misconception_data,
                "tradeoff": tradeoff_data,
                "mechanism": mechanism_data,
                "counter_example": counter_example_data
            }
        except Exception as error:
            print(f"Lỗi khi truy vấn khía cạnh sư phạm từ FalkorDB: {error}")
            return {}

    def export_graph_for_ui(self, track: Optional[str] = None) -> Dict[str, Any]:
        """Xuất toàn bộ cấu trúc đồ thị đa thực thể (5 loại Nodes & 8 loại Edges) hiển thị trực quan."""
        active_track = track or self.current_track
        nodes = []
        edges = []

        try:
            track_filter = "" if active_track == "all" else f"{{track: '{active_track}'}}"

            # 1. Truy vấn các Node Khái niệm (Concepts)
            concept_query = f"""
            MATCH (c:Concept {track_filter})
            RETURN c.id, c.name, c.status, c.page, c.track, c.category, c.citation, c.core_truth, c.child_question, c.learning_question, c.quote_text
            ORDER BY c.order
            """
            concept_result = self.graph.query(concept_query)

            for row in concept_result.result_set:
                concept_id, name, status, page, track_name, category, citation, core_truth, child_q, learning_q, quote_text = row
                is_covered = (status == "COVERED")
                background_color = "#10b981" if is_covered else ("#38bdf8" if track_name == "primary" else "#0284c7")
                border_color = "#059669" if is_covered else "#0369a1"

                nodes.append({
                    "id": concept_id,
                    "label": f"P.{page} {name[:20]}",
                    "full_name": name,
                    "status": status,
                    "node_type": "Concept",
                    "page": page,
                    "category": category or "Feynman Pack",
                    "track": track_name,
                    "citation": citation or "",
                    "core_truth": core_truth or "",
                    "child_question": child_q or learning_q or "",
                    "quote_text": quote_text or "",
                    "shape": "dot",
                    "size": 26 if is_covered else 24,
                    "color": {
                        "background": background_color,
                        "border": border_color,
                        "highlight": {"background": "#ffffff", "border": background_color}
                    },
                    "font": {"color": "#ffffff", "size": 12, "face": "Inter, sans-serif"},
                    "title": f"<b>{name}</b><br>Trạng thái: <b>{status}</b><br>{citation}<br>{(core_truth or '')[:120]}..."
                })

            # 2. Truy vấn các Node Bẫy ngộ nhận (Misconceptions)
            misc_query = f"""
            MATCH (m:Misconception {track_filter})
            RETURN m.id, m.name, m.pitfall_text, m.probe_question, m.truth_hint, m.track
            """
            misc_result = self.graph.query(misc_query)
            for row in misc_result.result_set:
                misc_id, misc_name, pitfall_text, probe_question, truth_hint, misc_track = row
                nodes.append({
                    "id": misc_id,
                    "label": f"⚠️ {misc_name[:18]}",
                    "full_name": misc_name,
                    "status": "POINT_OF_INTEREST",
                    "node_type": "Misconception",
                    "pitfall_text": pitfall_text or "",
                    "probe_question": probe_question or "",
                    "truth_hint": truth_hint or "",
                    "track": misc_track,
                    "shape": "diamond",
                    "size": 18,
                    "color": {
                        "background": "#f43f5e",
                        "border": "#be123c",
                        "highlight": {"background": "#fda4af", "border": "#f43f5e"}
                    },
                    "font": {"color": "#fecdd3", "size": 11, "face": "Inter, sans-serif"},
                    "title": f"<b>⚠️ Bẫy ngộ nhận:</b> {misc_name}<br><b>Hỏi vặn:</b> {probe_question}<br>{(pitfall_text or '')[:120]}..."
                })

            # 3. Truy vấn các Node Đánh đổi kỹ thuật (Tradeoffs)
            trade_query = f"""
            MATCH (t:Tradeoff {track_filter})
            RETURN t.id, t.name, t.dimension_a, t.dimension_b, t.probe_question, t.track
            """
            trade_result = self.graph.query(trade_query)
            for row in trade_result.result_set:
                trade_id, trade_name, dimension_a, dimension_b, probe_question, trade_track = row
                nodes.append({
                    "id": trade_id,
                    "label": f"⚖️ {trade_name[:18]}",
                    "full_name": trade_name,
                    "status": "POINT_OF_INTEREST",
                    "node_type": "Tradeoff",
                    "dimension_a": dimension_a or "",
                    "dimension_b": dimension_b or "",
                    "probe_question": probe_question or "",
                    "track": trade_track,
                    "shape": "triangle",
                    "size": 18,
                    "color": {
                        "background": "#f59e0b",
                        "border": "#b45309",
                        "highlight": {"background": "#fde68a", "border": "#f59e0b"}
                    },
                    "font": {"color": "#fef3c7", "size": 11, "face": "Inter, sans-serif"},
                    "title": f"<b>⚖️ Đánh đổi:</b> {trade_name}<br><b>{dimension_a}</b> vs <b>{dimension_b}</b><br><b>Hỏi vặn:</b> {probe_question}"
                })

            # 4. Truy vấn các Node Cơ chế nhân quả (Mechanisms)
            mech_query = f"""
            MATCH (mech:Mechanism {track_filter})
            RETURN mech.id, mech.name, mech.causal_chain, mech.probe_question, mech.track
            """
            mech_result = self.graph.query(mech_query)
            for row in mech_result.result_set:
                mech_id, mech_name, causal_chain, probe_question, mech_track = row
                nodes.append({
                    "id": mech_id,
                    "label": f"⚙️ {mech_name[:18]}",
                    "full_name": mech_name,
                    "status": "POINT_OF_INTEREST",
                    "node_type": "Mechanism",
                    "causal_chain": causal_chain or "",
                    "probe_question": probe_question or "",
                    "track": mech_track,
                    "shape": "square",
                    "size": 18,
                    "color": {
                        "background": "#8b5cf6",
                        "border": "#6d28d9",
                        "highlight": {"background": "#ddd6fe", "border": "#8b5cf6"}
                    },
                    "font": {"color": "#ede9fe", "size": 11, "face": "Inter, sans-serif"},
                    "title": f"<b>⚙️ Cơ chế nhân quả:</b> {mech_name}<br><b>Chuỗi:</b> {causal_chain}<br><b>Hỏi vặn:</b> {probe_question}"
                })

            # 5. Truy vấn các Node Phản ví dụ / Tình huống biên (CounterExamples)
            cex_query = f"""
            MATCH (cex:CounterExample {track_filter})
            RETURN cex.id, cex.name, cex.scenario, cex.probe_question, cex.track
            """
            cex_result = self.graph.query(cex_query)
            for row in cex_result.result_set:
                cex_id, cex_name, scenario, probe_question, cex_track = row
                nodes.append({
                    "id": cex_id,
                    "label": f"💡 {cex_name[:18]}",
                    "full_name": cex_name,
                    "status": "POINT_OF_INTEREST",
                    "node_type": "CounterExample",
                    "scenario": scenario or "",
                    "probe_question": probe_question or "",
                    "track": cex_track,
                    "shape": "star",
                    "size": 18,
                    "color": {
                        "background": "#06b6d4",
                        "border": "#0e7490",
                        "highlight": {"background": "#a5f3fc", "border": "#06b6d4"}
                    },
                    "font": {"color": "#cffafe", "size": 11, "face": "Inter, sans-serif"},
                    "title": f"<b>💡 Ví dụ thực tế:</b> {cex_name}<br><b>Tình huống:</b> {scenario}<br><b>Hỏi vặn:</b> {probe_question}"
                })

            # 6. Truy vấn toàn bộ các Cạnh Quan hệ (Edges)
            edge_query = """
            MATCH (a)-[r]->(b)
            RETURN a.id, b.id, type(r)
            """
            edge_result = self.graph.query(edge_query)
            for row in edge_result.result_set:
                source_id, target_id, relation_type = row[0], row[1], row[2]

                edge_styles = {
                    "PREREQUISITE_FOR": {"color": "#10b981bb", "dashes": False, "width": 2},
                    "DEEP_DIVE_INTO": {"color": "#6366f1bb", "dashes": [4, 4], "width": 1.5},
                    "ALTERNATIVE_PATH": {"color": "#f59e0bbb", "dashes": [6, 4], "width": 1.5},
                    "HAS_COMMON_PITFALL": {"color": "#f43f5ebb", "dashes": False, "width": 1.5},
                    "CONTRADICTS": {"color": "#ef4444bb", "dashes": [2, 4], "width": 1.5},
                    "HAS_TRADEOFF": {"color": "#f97316bb", "dashes": False, "width": 1.5},
                    "DEPENDS_ON_MECHANISM": {"color": "#a855f7bb", "dashes": False, "width": 1.5},
                    "HAS_COUNTER_EXAMPLE": {"color": "#06b6d4bb", "dashes": False, "width": 1.5}
                }
                style = edge_styles.get(relation_type, {"color": "#64748bbb", "dashes": False, "width": 1})

                edges.append({
                    "from": source_id,
                    "to": target_id,
                    "source": source_id,
                    "target": target_id,
                    "type": relation_type,
                    "label": relation_type,
                    "color": {"color": style["color"], "highlight": "#38bdf8"},
                    "dashes": style["dashes"],
                    "width": style["width"],
                    "arrows": "to",
                    "font": {"color": "#94a3b8", "size": 9, "align": "middle"}
                })

        except Exception as error:
            print(f"Lỗi khi xuất đồ thị cho giao diện UI: {error}")

        return {"nodes": nodes, "edges": edges, "active_track": active_track}

    def reset_all_progress(self) -> bool:
        """Đặt lại toàn bộ trạng thái khái niệm về UNCOVERED và đưa active track về mặc định."""
        self.graph.query("MATCH (c:Concept) SET c.status = 'UNCOVERED'")
        self.current_track = "primary"
        return True
