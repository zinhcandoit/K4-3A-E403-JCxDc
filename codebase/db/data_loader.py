import os
import sys
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import pymupdf  # PyMuPDF

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from config.config import settings
from backend.nvidia_client import NvidiaAIClient


class RealDataLoader:
    """
    Trích xuất dữ liệu thực tế bảo toàn tính cục bộ tri thức (Knowledge Locality):
    1. data/vlearn-pack/transcript/*.md (Mỗi file transcript là 1 bài học độc lập)
    2. codebase/db/input/*.pdf (Mỗi file slide PDF là 1 chuyên đề độc lập)
    TUYỆT ĐỐI KHÔNG TRỘN CÁC FILE LẠI VỚI NHAU để tránh làm mất tính cục bộ khiến AI bị lú lẫn.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.transcript_dir = settings.TRANSCRIPT_DIR
        self.input_dir = settings.INPUT_DIR
        self.nvidia_client = NvidiaAIClient()

    def _extract_json_array_from_text(self, text: str) -> List[str]:
        """Safely extract JSON array from LLM response text."""
        if not text:
            return []
        
        codeblock_match = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text)
        if codeblock_match:
            try:
                parsed_array = json.loads(codeblock_match.group(1))
                if isinstance(parsed_array, list):
                    return parsed_array
            except Exception:
                pass

        start_index = text.find("[")
        end_index = text.rfind("]")
        if start_index != -1 and end_index != -1 and end_index > start_index:
            try:
                parsed_array = json.loads(text[start_index:end_index + 1])
                if isinstance(parsed_array, list):
                    return parsed_array
            except Exception:
                pass

        return []

    def _classify_knowledge_sections_with_llm(self, candidate_headings: List[str]) -> List[str]:
        """
        Use ChatNVIDIA to identify core technical concept headings,
        filtering out introductory greetings, roll call, and administrative logistics.
        """
        if not candidate_headings:
            return []

        selected_headings: List[str] = []
        batch_size = 15
        total_batches = (len(candidate_headings) + batch_size - 1) // batch_size
        print(f"   🔎 Đang phân loại {len(candidate_headings)} tiêu đề chuyên môn ({total_batches} batches)...", flush=True)

        for index in range(0, len(candidate_headings), batch_size):
            batch = candidate_headings[index:index + batch_size]
            batch_idx = index // batch_size + 1
            print(f"      ⏳ [Phân loại {batch_idx}/{total_batches}] Đang kiểm duyệt {len(batch)} tiêu đề...", end="", flush=True)
            t0 = time.time()
            prompt = f"""Bạn là Giám định viên Nội dung Sư phạm AI.
Dưới đây là danh sách các tiêu đề mục được trích xuất từ file transcript bài giảng:
{json.dumps(batch, ensure_ascii=False, indent=2)}

Nhiệm vụ: Hãy chọn ra các mục là bài giảng/khái niệm chuyên môn kỹ thuật cốt lõi (ví dụ: AI, Machine Learning, Deep Learning, Transformer, Attention, Token, Hallucination, Training, Model, Architecture, System, v.v.).
Loại bỏ hoàn toàn các phần chào hỏi, giới thiệu bản thân, thủ tục hành chính lớp học, khảo sát học viên, trò chuyện phiếm bên lề.

CHỈ TRẢ VỀ DUY NHẤT 1 MẢNG JSON CÁC TIÊU ĐỀ ĐƯỢC CHỌN (KHÔNG THÊM MARKDOWN):
[
  "Tiêu đề chuyên môn 1",
  "Tiêu đề chuyên môn 2"
]
"""
            try:
                response_text = self.nvidia_client.generate_text(
                    prompt=prompt,
                    system_prompt="Bạn là Giám định viên Nội dung Sư phạm AI. Chỉ xuất duy nhất một mảng JSON."
                )
                added_this_batch = 0
                if response_text:
                    items = self._extract_json_array_from_text(response_text)
                    for item in items:
                        if isinstance(item, str) and item in batch:
                            selected_headings.append(item)
                            added_this_batch += 1
                        elif isinstance(item, dict):
                            heading_title = item.get("heading", item.get("title", ""))
                            if heading_title and heading_title in batch and item.get("is_knowledge_concept", True):
                                selected_headings.append(heading_title)
                                added_this_batch += 1
                t_elapsed = time.time() - t0
                print(f" -> ✅ Xong trong {t_elapsed:.1f}s (chọn {added_this_batch}/{len(batch)})", flush=True)
            except Exception as exc:
                t_elapsed = time.time() - t0
                print(f" -> ⚠️ Lỗi ({t_elapsed:.1f}s: {exc})", flush=True)

        # Fallback heuristic if LLM returns empty list
        if not selected_headings:
            for heading_item in candidate_headings:
                heading_lower = heading_item.lower()
                if not any(stopword in heading_lower for stopword in ["chào lớp", "giới thiệu", "thủ tục", "nghỉ", "nội dung ngày học"]):
                    selected_headings.append(heading_item)

        return selected_headings

    def parse_vlearn_transcripts(self, target_filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Parse lecture transcript files from data/vlearn-pack/transcript/*.md.
        - Default: Process active document (settings.ACTIVE_DOCUMENT) preserving knowledge locality.
        - target_filename == 'all': Parse all transcripts into distinct independent tracks.
        """
        if not self.transcript_dir.exists():
            raise FileNotFoundError(f"Transcript directory not found at: {self.transcript_dir}")

        filename = target_filename or settings.get_default_document()
        if filename and filename != "all":
            selected_files = [self.transcript_dir / filename]
            if not selected_files[0].exists():
                found = list(self.transcript_dir.glob(f"*{filename}*"))
                selected_files = [found[0]] if found else []
            if not selected_files or not selected_files[0].exists():
                raise FileNotFoundError(f"Target transcript file not found: {filename} in {self.transcript_dir}")
        else:
            selected_files = sorted([
                transcript_file for transcript_file in self.transcript_dir.glob("*.md")
                if transcript_file.is_file() and transcript_file.name.lower() != "readme.md"
            ])

        turn_pattern = re.compile(r"\*\*\[([A-Za-z0-9_-]+)\]\*\*\s*(.*?)(?=\n\n\*\*\[|\n##|\Z)", re.DOTALL)
        feynman_concepts: List[Dict[str, Any]] = []

        # Process each transcript independently to maintain topical locality
        for file_path in selected_files:
            file_track = file_path.stem
            file_doc_id = file_path.name
            content = file_path.read_text(encoding="utf-8")
            sections = re.split(r"\n(?=##\s+)", content)
            
            raw_sections = []
            for section in sections:
                lines = section.strip().split("\n")
                if not lines or not lines[0].startswith("##"):
                    continue
                heading = lines[0].replace("##", "").strip()
                section_turns = [(match.group(1), match.group(2).strip()) for match in turn_pattern.finditer(section)]
                if section_turns:
                    raw_sections.append({
                        "heading": heading,
                        "file": file_path,
                        "turns": section_turns
                    })

            candidate_headings = [sec["heading"] for sec in raw_sections]
            approved_headings = set(self._classify_knowledge_sections_with_llm(candidate_headings))

            # Number concepts sequentially within current file track
            file_concept_index = 1
            for section in raw_sections:
                heading = section["heading"]
                if approved_headings and heading not in approved_headings:
                    continue

                section_turns = section["turns"]
                citation_code = section_turns[0][0]
                speech_texts = [turn_tuple[1] for turn_tuple in section_turns if len(turn_tuple[1]) > 50]
                if not speech_texts:
                    continue

                combined_speech = " ".join(speech_texts)
                cleaned_speech = re.sub(r"\s+", " ", combined_speech).strip()

                sentences = re.split(r"(?<=[.!?])\s+", cleaned_speech)
                core_truth = " ".join(sentences[:2]) if len(sentences) >= 2 else cleaned_speech[:250]
                if len(core_truth) > 300:
                    core_truth = core_truth[:297] + "..."

                feynman_concepts.append({
                    "id": f"{file_track}_c{file_concept_index}",
                    "name": heading,
                    "citation": f"[{citation_code}]",
                    "source_file": file_doc_id,
                    "doc_id": file_doc_id,
                    "turn_id": citation_code,
                    "core_truth": core_truth,
                    "quote_text": cleaned_speech[:500],
                    "learning_question": "",
                    "child_question": "",
                    "order": file_concept_index,
                    "track": file_track,
                    "module": f"Bài học: {file_track}"
                })
                file_concept_index += 1

        print(f"✅ Extracted {len(feynman_concepts)} concepts from {len(selected_files)} transcript file(s).")
        return feynman_concepts

    def extract_pedagogical_aspects(
        self,
        concepts: List[Dict[str, Any]],
        cache_key: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract 4 pedagogical blindspots dynamically per concept:
        1. Misconception -> HAS_COMMON_PITFALL, CONTRADICTS
        2. Tradeoff -> HAS_TRADEOFF
        3. Mechanism -> DEPENDS_ON_MECHANISM
        4. CounterExample -> HAS_COUNTER_EXAMPLE
        Enforces 36 RPM rate limiting with comprehensive fallback.
        Tự động cache kết quả vào db/cache để tăng tốc các lần chạy sau.
        """
        if not concepts:
            return {}

        # 0. Kiểm tra Cache trên ổ đĩa để tái sử dụng ngay lập tức nếu có
        cache_file = None
        if cache_key:
            safe_key = re.sub(r"[^a-zA-Z0-9_-]", "_", cache_key)
            cache_dir = settings.DB_DIR / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / f"aspects_{safe_key}.json"
            if cache_file.exists() and not force_refresh:
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                    if all(c["id"] in cached_data for c in concepts):
                        print(f"   ⚡ [Cache Hit] Đã nạp sẵn {len(cached_data)} điểm mù sư phạm từ '{cache_file.name}' (0s)!", flush=True)
                        return cached_data
                except Exception as exc:
                    print(f"   ℹ️ Đọc cache thất bại ({exc}), bắt đầu trích xuất mới...", flush=True)

        results: Dict[str, Dict[str, Any]] = {}
        batch_size = 5
        total_concepts = len(concepts)
        total_batches = (total_concepts + batch_size - 1) // batch_size
        print(f"   📊 Tổng cộng {total_concepts} khái niệm cần trích xuất ({total_batches} batches, mỗi batch {batch_size} concepts)...", flush=True)

        for index in range(0, total_concepts, batch_size):
            batch = concepts[index:index + batch_size]
            batch_num = index // batch_size + 1
            batch_names = ", ".join([f"'{c['name'][:22]}...'" if len(c['name']) > 22 else f"'{c['name']}'" for c in batch[:2]])
            if len(batch) > 2:
                batch_names += f" (+{len(batch)-2} khác)"

            print(f"      ⏳ [Batch {batch_num}/{total_batches}] Đang gọi ChatNVIDIA cho: {batch_names}...", end="", flush=True)
            t_start = time.time()
            prompt_items = [
                {
                    "id": concept_item["id"],
                    "name": concept_item["name"],
                    "truth": concept_item.get("core_truth") or concept_item.get("summary", "")
                }
                for concept_item in batch
            ]
            prompt = f"""Bạn là Chuyên gia Thiết kế Đồ thị Sư phạm Feynman & Socratic.
Dưới đây là các khái niệm chuyên môn trong một bài giảng:
{json.dumps(prompt_items, ensure_ascii=False, indent=2)}

Nhiệm vụ: Với MỖI khái niệm, hãy chỉ ra 4 điểm mù quan trọng mà sinh viên thường KHÔNG nhận ra hoặc giải thích sai:
1. pitfall: Ngộ nhận phổ biến nhất (học viên tưởng đúng nhưng sai), kèm câu hỏi vặn Socratic (probe_question) để học viên tự thấy mâu thuẫn.
2. tradeoff: Sự đánh đổi kỹ thuật (dimension_a vs dimension_b), kèm câu hỏi vặn về sự đánh đổi.
3. mechanism: Cơ chế nhân quả bên dưới (causal_chain: A dẫn đến B, B dẫn đến C), kèm câu hỏi đào sâu cơ chế.
4. counter_example: Ví dụ thực tế hoặc trường hợp biên (scenario), kèm câu hỏi thách đố.

CHỈ XUẤT DUY NHẤT 1 MẢNG JSON HỢP LỆ VỚI CẤU TRÚC:
[
  {{
    "id": "concept_id",
    "pitfall": {{
      "name": "Tên ngộ nhận",
      "pitfall_text": "Mô tả ngộ nhận",
      "probe_question": "Câu hỏi hỏi vặn",
      "truth_hint": "Bản chất chuẩn"
    }},
    "tradeoff": {{
      "name": "Tên đánh đổi",
      "dimension_a": "Lợi ích",
      "dimension_b": "Cái giá phải trả",
      "probe_question": "Câu hỏi về sự đánh đổi"
    }},
    "mechanism": {{
      "name": "Tên cơ chế",
      "causal_chain": "Chuỗi nhân quả",
      "probe_question": "Câu hỏi đào sâu cơ chế"
    }},
    "counter_example": {{
      "name": "Tên ví dụ biên",
      "scenario": "Mô tả trường hợp thực tế",
      "probe_question": "Câu hỏi về ví dụ"
    }}
  }}
]"""
            extracted_count = 0
            try:
                raw_response = self.nvidia_client.generate_text(
                    prompt=prompt,
                    system_prompt="Bạn là Chuyên gia Thiết kế Đồ thị Sư phạm AI. Chỉ xuất duy nhất một mảng JSON."
                )
                if raw_response:
                    aspects_list = self._extract_json_array_from_text(raw_response)
                    for item in aspects_list:
                        if isinstance(item, dict) and "id" in item:
                            results[item["id"]] = item
                            extracted_count += 1
                t_elapsed = time.time() - t_start
                if extracted_count > 0:
                    print(f" -> ✅ Xong trong {t_elapsed:.1f}s ({extracted_count}/{len(batch)} items)", flush=True)
                else:
                    print(f" -> ⚠️ Không parse được JSON ({t_elapsed:.1f}s), dùng fallback", flush=True)
            except Exception as exc:
                t_elapsed = time.time() - t_start
                print(f" -> ❌ Lỗi ({t_elapsed:.1f}s: {exc}), dùng fallback", flush=True)

            # Ensure complete fallback for any unextracted concepts
            for concept_item in batch:
                concept_id = concept_item["id"]
                concept_name = concept_item["name"]
                concept_truth = concept_item.get("core_truth") or concept_item.get("summary", "")
                if concept_id not in results:
                    results[concept_id] = {
                        "id": concept_id,
                        "pitfall": {
                            "name": f"Ngộ nhận về {concept_name}",
                            "pitfall_text": f"Học viên thường nghĩ {concept_name} hoạt động theo quy luật cứng nhắc mà không thấy được yếu tố xác suất và phạm vi ngữ cảnh.",
                            "probe_question": f"Nếu chỉ theo cách hiểu thông thường, bạn giải thích thế nào về trường hợp mâu thuẫn của '{concept_name}'?",
                            "truth_hint": concept_truth[:180]
                        },
                        "tradeoff": {
                            "name": f"Sự đánh đổi trong {concept_name}",
                            "dimension_a": "Tốc độ xử lý & Khả năng mở rộng",
                            "dimension_b": "Chi phí tài nguyên & Rủi ro sai lệch",
                            "probe_question": f"Khi tối ưu hóa cho '{concept_name}', hệ thống phải đánh đổi điều gì về mặt chi phí hoặc độ chính xác?"
                        },
                        "mechanism": {
                            "name": f"Cơ chế điều phối {concept_name}",
                            "causal_chain": f"Đầu vào bài toán -> Cơ chế tính toán của {concept_name} -> Trọng số phân phối kết quả",
                            "probe_question": f"Về mặt thuật toán bên dưới, cơ chế nào trực tiếp chịu trách nhiệm cho '{concept_name}'?"
                        },
                        "counter_example": {
                            "name": f"Trường hợp thực tế của {concept_name}",
                            "scenario": f"Tình huống xử lý trường hợp biên hoặc dữ liệu đặc thù khi vận hành {concept_name}.",
                            "probe_question": f"Bạn có thể đưa ra một ví dụ đời thường cụ thể chứng minh cơ chế này không?"
                        }
                    }

        # Lưu kết quả vào cache đĩa để tái sử dụng tức thì cho các lần build sau
        if cache_file and results:
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"   💾 Đã lưu kết quả trích xuất vào cache: {cache_file.name}", flush=True)
            except Exception as e:
                print(f"   ⚠️ Lỗi lưu cache: {e}", flush=True)

        return results

    def parse_lecture_slides_pdf(self, pdf_filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Parse lecture PDF slides into independent graph tracks.
        """
        if not self.input_dir.exists():
            return []

        if pdf_filename:
            target_pdf = self.input_dir / pdf_filename
            if not target_pdf.exists():
                found = list(self.input_dir.glob(f"*{pdf_filename}*"))
                target_pdf = found[0] if found else None
            pdf_files = [target_pdf] if target_pdf and target_pdf.exists() else []
        else:
            pdf_files = list(self.input_dir.glob("*.pdf"))

        if not pdf_files:
            return []

        pdf_path = pdf_files[0]
        pdf_track = f"slide_{pdf_path.stem}"
        pdf_doc_id = pdf_path.name
        print(f"📄 Reading PDF slide file: {pdf_path.name}...")

        doc = pymupdf.open(str(pdf_path))
        total_pages = len(doc)
        print(f"📊 Total pages in PDF slide: {total_pages} pages.")

        raw_slides = []
        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text("text").strip()
            lines = [
                line_text.strip() for line_text in text.split("\n")
                if line_text.strip() and not line_text.strip().isdigit() and not line_text.strip().startswith("http")
            ]
            title = lines[0] if lines else f"Slide {page_num + 1}"
            title = re.sub(r"^[•\-\–\—\*\s]+", "", title).strip()
            if not title or len(title) < 2:
                title = f"Slide {page_num + 1}"

            summary = ". ".join(lines[1:5]) if len(lines) > 1 else title
            raw_slides.append({
                "page": page_num + 1,
                "title": title,
                "summary": summary[:250],
                "raw_text": text[:500]
            })

        # Filter out redundant or empty slides
        filtered = []
        seen = set()
        for slide_data in raw_slides:
            slide_title_clean = slide_data["title"].lower()
            if len(slide_data["title"]) > 3 and slide_title_clean not in seen and not slide_title_clean.startswith("slide"):
                seen.add(slide_title_clean)
                filtered.append(slide_data)

        extracted_slides = []
        for index, slide_item in enumerate(filtered):
            extracted_slides.append({
                "id": f"{pdf_track}_p{slide_item['page']}",
                "page": slide_item["page"],
                "order": index + 1,
                "title": slide_item["title"],
                "summary": slide_item["summary"],
                "track": pdf_track,
                "source_file": pdf_doc_id,
                "doc_id": pdf_doc_id,
                "module": f"Slide: {pdf_path.stem}",
                "category": f"Slide P.{slide_item['page']}",
                "raw_text": slide_item["raw_text"]
            })

        return extracted_slides
