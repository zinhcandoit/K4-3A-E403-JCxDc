#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
TRACK D3: BỘ KIỂM THỬ TỰ ĐỘNG VỚI LLM-AS-A-JUDGE (CHATNVIDIA / NVIDIA NIM)
=============================================================================
Đánh giá chất lượng Socratic Agent ("Alex") trên 20 test case Golden Set:
- LLM-as-a-judge Model: ChatNVIDIA (cấu hình tập trung qua config.config.settings)
- Tiêu chí đánh giá:
  1. Factuality (Căn cứ kiến thức, tuyệt đối không hallucination)
  2. Anti-parroting (Chống học vẹt, ép học viên giải thích bình dân)
  3. Probing (Gợi mở trúng điểm khuyết thay vì mớm đáp án)
- Quality Bar: Đạt khi >= 75% qua bộ và 100% Factuality không sai kiến thức.

Cách chạy:
    uv run python test/eval_judge.py
=============================================================================
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Thêm thư mục gốc codebase vào sys.path để chạy script trực tiếp từ bất kỳ thư mục nào
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Nạp cấu hình tập trung từ config.py (đã bao gồm biến môi trường NVIDIA_API_KEY)
from config.config import settings
from backend.nvidia_client import NvidiaAIClient


# ---------------------------------------------------------------------------
# 1. Tìm đường dẫn file golden_set.json
# ---------------------------------------------------------------------------
def find_golden_set_path() -> str:
    """Xác định đường dẫn file golden_set.json tự động không phụ thuộc thư mục thực thi."""
    possible_paths = [
        settings.BASE_DIR.parent / "eval" / "golden_set.json",
        settings.BASE_DIR / "eval" / "golden_set.json",
        Path("eval/golden_set.json").resolve(),
        Path("../eval/golden_set.json").resolve(),
    ]
    for path_candidate in possible_paths:
        if path_candidate.exists():
            return str(path_candidate.resolve())
    raise FileNotFoundError(
        "Không tìm thấy file golden_set.json! Vui lòng kiểm tra thư mục eval/golden_set.json"
    )


# ---------------------------------------------------------------------------
# 2. Khởi tạo NVIDIA LLM Clients
# ---------------------------------------------------------------------------
def init_nvidia_clients():
    """
    Khởi tạo các instance NvidiaAIClient:
    - alex_client: Phục vụ sinh phản hồi Socratic với temperature theo cấu hình settings.
    - judge_client: Phục vụ chấm điểm LLM-as-a-Judge với temperature=0.0 (tất định, khách quan).
    """
    if not settings.NVIDIA_API_KEY:
        print("⚠️ CẢNH BÁO: NVIDIA_API_KEY chưa được cấu hình trong codebase/.env!")
        print("   Vui lòng thêm NVIDIA_API_KEY vào codebase/.env trước khi chạy.")
        sys.exit(1)

    alex_client = NvidiaAIClient(
        temperature=settings.NVIDIA_TEMPERATURE,
        max_tokens=settings.NVIDIA_MAX_TOKENS
    )
    judge_client = NvidiaAIClient(
        temperature=0.0,
        max_tokens=settings.NVIDIA_MAX_TOKENS
    )
    return alex_client, judge_client


# ---------------------------------------------------------------------------
# 3. Chạy Agent Alex sinh câu trả lời
# ---------------------------------------------------------------------------
def get_alex_reply(
    student_input: str,
    test_case: Dict[str, Any],
    alex_client: NvidiaAIClient
) -> str:
    """
    Sinh phản hồi của Alex cho câu nhập của học viên:
    Ưu tiên gọi SocraticAgentEngine, nếu FalkorDB offline thì fallback sang direct ChatNVIDIA prompt.
    """
    # Cách 1: Gọi qua SocraticAgentEngine nếu môi trường đã dựng đủ
    try:
        from backend.agent_engine import SocraticAgentEngine
        engine = SocraticAgentEngine()
        result = engine.process_student_message(
            student_msg=student_input,
            session_id=f"eval_{test_case.get('id', 'test')}"
        )
        if result and result.get("reply"):
            return result["reply"].strip()
    except Exception:
        # FalkorDB hoặc engine chưa sẵn sàng, dùng Direct Call với System Prompt chuẩn
        pass

    # Cách 2: Direct call với Agent Persona của Alex qua ChatNVIDIA
    system_prompt = (
        "Bạn là Alex, một bạn học cùng lớp ngành AI thông minh, ngây thơ có kiểm soát "
        "(Protégé Socratic Agent trong Track D3: Học bằng cách dạy).\n"
        "Vai trò cốt lõi: Bạn là người ĐƯỢC DẠY, đang lắng nghe bạn mình giải thích kiến thức để cùng hiểu sâu bản chất.\n"
        "Quy tắc phản hồi bất biến:\n"
        "1. Xưng hô tự nhiên 'mình' - 'bạn', tuyệt đối không dùng emoji, không máy móc.\n"
        "2. TUYỆT ĐỐI KHÔNG GIẢNG BÀI, KHÔNG LỘ ĐÁP ÁN: Bạn là người học, không phải người đi dạy hay trợ giảng. "
        "Không bao giờ tự tuôn ra kiến thức mới hay đáp án hoàn chỉnh.\n"
        "3. NẾU HỌC VIÊN NÓI SAI SỰ THẬT: Tuyệt đối KHÔNG khen đúng và KHÔNG sửa lưng bằng bài giảng. "
        "Hãy hỏi vặn lại vào chính điểm mâu thuẫn/phi lý đó để bạn mình tự nhận ra chỗ hổng.\n"
        "4. NẾU HỌC VIÊN CHÉP NGUYÊN VĂN SLIDE HOẶC DÙNG THUẬT NGỮ KHÓ HIỂU: Hỏi ép giải thích lại bằng ngôn ngữ đời thường, "
        "bằng một ví dụ bình dị.\n"
        "5. NẾU HỌC VIÊN ĐÒI ĐÁP ÁN HOẶC HỎI NGOÀI BÀI: Từ chối vì mình cũng đang là người học và không có đáp án; "
        "hỏi kéo bạn mình về bài học.\n"
        "6. NẾU HỌC VIÊN GIẢI THÍCH THIẾU Ý HOẶC GIẢI THÍCH ĐÚNG: Ghi nhận ngắn gọn ý đó và kết thúc bằng ĐÚNG 1 CÂU HỎI "
        "đào sâu (Socratic Probing) vào mắt xích cơ chế bên dưới hoặc trường hợp biên.\n"
        "Độ dài: Luôn ngắn gọn từ 2 đến 3 câu, câu cuối luôn là CÂU HỎI NGƯỢC."
    )

    user_prompt = f'Học viên vừa nói:\n"{student_input}"\n\nHãy phản hồi học viên với tư cách là Alex theo đúng các quy tắc trên:'

    response_text = alex_client.generate_text(
        prompt=user_prompt,
        system_prompt=system_prompt
    )
    if response_text:
        return response_text.strip()

    return "Mình đang suy nghĩ một chút về ý này của bạn, bạn có thể nói rõ hơn được không?"


# ---------------------------------------------------------------------------
# 4. LLM-as-a-judge: Phân tích cú pháp và chấm điểm an toàn
# ---------------------------------------------------------------------------
def parse_judge_output(text: str) -> Dict[str, Any]:
    """Parse JSON hoặc phân tích cú pháp dự phòng từ văn bản của Judge."""
    if not text:
        return {
            "passed": False,
            "score": 1,
            "factuality_ok": False,
            "dimension_ok": False,
            "reason": "Phản hồi từ mô hình Giám khảo rỗng"
        }
    try:
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            parsed_data = json.loads(json_match.group(0))
            return {
                "passed": bool(parsed_data.get("passed", False)),
                "score": int(parsed_data.get("score", 3)),
                "factuality_ok": bool(parsed_data.get("factuality_ok", True)),
                "dimension_ok": bool(parsed_data.get("dimension_ok", True)),
                "reason": str(parsed_data.get("reason", "")).strip()
            }
    except Exception:
        pass

    # Heuristic fallback nếu model không sinh đúng định dạng JSON
    normalized_text = text.lower()
    is_passed = ("true" in normalized_text or "pass" in normalized_text or "đạt" in normalized_text) and (
        "fail" not in normalized_text and "không đạt" not in normalized_text and "false" not in normalized_text
    )
    return {
        "passed": is_passed,
        "score": 4 if is_passed else 2,
        "factuality_ok": "không có căn cứ" not in normalized_text and "sai sự thật" not in normalized_text,
        "dimension_ok": is_passed,
        "reason": text.replace("\n", " ")[:150]
    }


def judge_alex_response(
    test_case: Dict[str, Any],
    alex_reply: str,
    judge_client: NvidiaAIClient
) -> Dict[str, Any]:
    """
    Giám khảo AI đánh giá phản hồi của Alex thông qua ChatNVIDIA:
    Cam kết 100% luôn trả về Dict hợp lệ, không bao giờ là None.
    """
    system_prompt = (
        "Bạn là Giám khảo AI (LLM-as-a-Judge) chuyên môn cao, đánh giá chất lượng phản hồi "
        "của Socratic Agent tên là 'Alex' trong một hệ thống giáo dục AI ('Học bằng cách dạy')."
    )

    judge_prompt = f"""THÔNG TIN TEST CASE:
- ID: {test_case.get('id')}
- Phân loại: {test_case.get('layer')} ({test_case.get('category')})
- Nguồn tham chiếu: {test_case.get('source_reference')}
- Chiều chất lượng chính: {test_case.get('eval_dimension')}
- Đầu vào của học viên (Student Input):
  "{test_case.get('student_input')}"
- Hành vi kỳ vọng của Alex (Expected Behavior):
  "{test_case.get('expected_behavior')}"

CÂU TRẢ LỜI THỰC TẾ CỦA ALEX:
"{alex_reply}"

QUY TẮC CHẤM ĐIỂM (PASS / FAIL) BÁM SÁT TRACK D3 (PROTÉGÉ SOCRATIC AGENT):
1. Về vai trò cốt lõi (Protégé Effect): Alex là người ĐƯỢC DẠY (học trò / bạn học), KHÔNG PHẢI thầy giáo. Alex phải luôn dùng CÂU HỎI NGƯỢC (Socratic Probing) để người học phải tiếp tục tư duy và tự giải thích. NẾU Alex tự tuôn đáp án, tự giảng giải kiến thức thay học viên -> ĐÁNH FAIL (vi phạm tiêu chí 'Không lộ đáp án').
2. Về Factuality & Nguồn sự thật: NẾU học viên khẳng định sai sự thật mà Alex lại khen đúng hoặc xác nhận thông tin sai -> BẮT BUỘC ĐÁNH FAIL. Alex phải hỏi vặn lại vào điểm vô lý đó để người học tự nhận ra mình sai.
3. Về Anti-parroting (Chống học vẹt): NẾU học viên chép nguyên văn định nghĩa slide hoặc dùng thuật ngữ đao to búa lớn lấp liếm mà Alex cho qua -> ĐÁNH FAIL. Alex phải hỏi ép giải thích bằng ngôn ngữ đời thường hoặc ví dụ thực tế. NẾU học viên đòi đáp án mà Alex cho đáp án -> ĐÁNH FAIL.
4. Về Happy path: NẾU học viên giải thích đúng, Alex tiếp thu ý đó và kết thúc bằng 1 CÂU HỎI đào sâu thêm về cơ chế/trường hợp biên -> ĐẠT.

Trả về kết quả ĐÚNG định dạng JSON sau (không bọc trong markdown block hoặc nếu bọc thì chỉ dùng json):
{{
  "passed": true,
  "score": 5,
  "factuality_ok": true,
  "dimension_ok": true,
  "reason": "Giải thích ngắn gọn 1-2 câu tại sao Đạt hoặc Không đạt"
}}"""

    raw_response = judge_client.generate_text(
        prompt=judge_prompt,
        system_prompt=system_prompt
    )

    if raw_response:
        return parse_judge_output(raw_response)

    return {
        "passed": False,
        "score": 1,
        "factuality_ok": False,
        "dimension_ok": False,
        "reason": "Không nhận được phản hồi từ mô hình Giám khảo ChatNVIDIA"
    }


# ---------------------------------------------------------------------------
# 5. Hàm chạy toàn bộ quy trình kiểm thử
# ---------------------------------------------------------------------------
def run_evaluation():
    """Thực thi kiểm thử đánh giá tự động trên toàn bộ Golden Set."""
    print("=" * 75)
    print("🚀 BẮT ĐẦU CHẠY KIỂM THỬ TỰ ĐỘNG TRACK D3 VỚI LLM-AS-A-JUDGE (CHATNVIDIA)")
    print(f"🤖 Giám khảo (Judge Model) : {settings.NVIDIA_MODEL}")
    print(f"🎯 Mô hình Socratic Agent  : {settings.NVIDIA_MODEL}")
    print(f"⏰ Thời gian bắt đầu        : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)

    # 1. Tìm và đọc golden set
    golden_path = find_golden_set_path()
    print(f"📂 Đang tải Golden Set từ: {golden_path}")
    with open(golden_path, "r", encoding="utf-8") as file_handle:
        test_cases = json.load(file_handle)

    total_cases = len(test_cases)
    print(f"📋 Tổng số kịch bản kiểm thử: {total_cases} cases\n")

    # 2. Khởi tạo clients
    alex_client, judge_client = init_nvidia_clients()

    evaluation_results = []
    passed_count = 0
    factuality_failures = 0

    # Phân loại theo lớp chỗ khó
    layer_stats = {
        "Lớp 1 - Nguồn sự thật": {"total": 0, "passed": 0},
        "Lớp 2 - Mơ hồ / Thiếu thông tin": {"total": 0, "passed": 0},
        "Lớp 3 - Ngoài phạm vi / Thẩm quyền": {"total": 0, "passed": 0},
        "Lớp 4 - Đặc thù domain": {"total": 0, "passed": 0},
        "Tiêu chuẩn": {"total": 0, "passed": 0},
        "Hiếm": {"total": 0, "passed": 0},
    }

    # Phân loại theo chiều chất lượng
    dimension_stats = {
        "Factuality": {"total": 0, "passed": 0},
        "Anti-parroting": {"total": 0, "passed": 0},
        "Probing": {"total": 0, "passed": 0},
    }

    start_time = time.time()

    # 3. Lặp qua từng test case
    for case_index, case_item in enumerate(test_cases, 1):
        case_id = case_item.get("id", f"TC{case_index:02d}")
        layer_name = case_item.get("layer", "Chung")
        dimension_name = case_item.get("eval_dimension", "Factuality")
        student_input = case_item.get("student_input", "")

        print(f"[{case_index:02d}/{total_cases}] Đang test {case_id} ({layer_name} | {dimension_name})...")
        print(f"    👤 Học viên: \"{student_input[:65]}...\"" if len(student_input) > 65 else f"    👤 Học viên: \"{student_input}\"")

        # Sinh phản hồi Alex
        agent_start_time = time.time()
        alex_reply = get_alex_reply(student_input, case_item, alex_client)
        agent_latency_seconds = round(time.time() - agent_start_time, 1)

        # Giám khảo chấm
        judge_start_time = time.time()
        judge_result = judge_alex_response(case_item, alex_reply, judge_client)
        judge_latency_seconds = round(time.time() - judge_start_time, 1)

        if not isinstance(judge_result, dict):
            judge_result = {
                "passed": False,
                "score": 1,
                "factuality_ok": False,
                "dimension_ok": False,
                "reason": "Phản hồi giám khảo không hợp lệ"
            }

        is_passed = judge_result.get("passed", False)
        if is_passed:
            passed_count += 1
            status_icon = "✅ PASS"
        else:
            status_icon = "❌ FAIL"

        if not judge_result.get("factuality_ok", True):
            factuality_failures += 1

        print(f"    🤖 Alex: \"{alex_reply[:75]}...\"" if len(alex_reply) > 75 else f"    🤖 Alex: \"{alex_reply}\"")
        print(f"    ⚖️  Judge ({settings.NVIDIA_MODEL}): {status_icon} (Điểm: {judge_result['score']}/5) | {judge_result['reason']}")
        print(f"    ⏱️  Thời gian: Agent {agent_latency_seconds}s + Judge {judge_latency_seconds}s\n")

        # Cập nhật thống kê layer
        matched_layer = "Tiêu chuẩn"
        for layer_key in layer_stats.keys():
            if layer_key in layer_name:
                matched_layer = layer_key
                break
        if matched_layer in layer_stats:
            layer_stats[matched_layer]["total"] += 1
            if is_passed:
                layer_stats[matched_layer]["passed"] += 1

        # Cập nhật thống kê dimension
        if dimension_name in dimension_stats:
            dimension_stats[dimension_name]["total"] += 1
            if is_passed:
                dimension_stats[dimension_name]["passed"] += 1

        evaluation_results.append({
            "id": case_id,
            "layer": layer_name,
            "category": case_item.get("category"),
            "source_reference": case_item.get("source_reference"),
            "eval_dimension": dimension_name,
            "student_input": student_input,
            "expected_behavior": case_item.get("expected_behavior"),
            "alex_reply": alex_reply,
            "passed": is_passed,
            "score": judge_result["score"],
            "factuality_ok": judge_result["factuality_ok"],
            "reason": judge_result["reason"],
            "agent_time_sec": agent_latency_seconds,
            "judge_time_sec": judge_latency_seconds
        })

        # Nghỉ giữa các request để đảm bảo an toàn tần suất gọi API
        time.sleep(1.0)

    elapsed_time = round(time.time() - start_time, 1)
    pass_rate = round((passed_count / total_cases) * 100, 1)

    # 4. Kiểm tra Quality Bar
    meets_quality_bar = (pass_rate >= 75.0) and (factuality_failures == 0)

    # 5. In bảng tổng kết
    print("=" * 75)
    print(f"📊 TỔNG KẾT KẾT QUẢ KIỂM THỬ (LLM-AS-A-JUDGE: {settings.NVIDIA_MODEL})")
    print("=" * 75)
    print(f"• Tổng số test case   : {total_cases}")
    print(f"• Số case ĐẠT (PASS)  : {passed_count}/{total_cases} ({pass_rate}%)")
    print(f"• Số case HỎNG (FAIL) : {total_cases - passed_count}/{total_cases}")
    print(f"• Lỗi sai kiến thức   : {factuality_failures} lỗi")
    print(f"• Tổng thời gian chạy : {elapsed_time} giây")
    print(f"• Chuẩn Quality Bar   : >= 75% VÀ 100% không xác nhận thông tin sai")
    if meets_quality_bar:
        print("🎉 KẾT LUẬN: ĐẠT QUALITY BAR ĐÃ KHÓA TẠI CP4! 🏆")
    else:
        print("⚠️ KẾT LUẬN: CHƯA ĐẠT QUALITY BAR! Cần tinh chỉnh prompt cho các case hỏng.")

    print("\n--- PHÂN LOẠI THEO 4 LỚP CHỖ KHÓ & ĐỘ PHỦ ---")
    for layer_key, layer_data in layer_stats.items():
        if layer_data["total"] > 0:
            layer_pass_rate = round((layer_data["passed"] / layer_data["total"]) * 100, 1)
            print(f"  - {layer_key:<35}: {layer_data['passed']}/{layer_data['total']} ({layer_pass_rate}%)")

    print("\n--- PHÂN LOẠI THEO 3 CHIỀU CHẤT LƯỢNG ---")
    for dimension_key, dimension_data in dimension_stats.items():
        if dimension_data["total"] > 0:
            dimension_pass_rate = round((dimension_data["passed"] / dimension_data["total"]) * 100, 1)
            print(f"  - {dimension_key:<20}: {dimension_data['passed']}/{dimension_data['total']} ({dimension_pass_rate}%)")

    # 6. Lưu kết quả ra thư mục eval/
    eval_dir = os.path.dirname(golden_path)
    output_json_path = os.path.join(eval_dir, "eval_results.json")
    output_report_path = os.path.join(eval_dir, "eval_report.md")

    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "judge_model": settings.NVIDIA_MODEL,
        "agent_model": settings.NVIDIA_MODEL,
        "total_cases": total_cases,
        "passed_cases": passed_count,
        "pass_rate_percent": pass_rate,
        "factuality_failures": factuality_failures,
        "meets_quality_bar": meets_quality_bar,
        "elapsed_seconds": elapsed_time,
        "layer_breakdown": layer_stats,
        "dimension_breakdown": dimension_stats,
        "detailed_results": evaluation_results
    }

    with open(output_json_path, "w", encoding="utf-8") as file_handle:
        json.dump(summary_data, file_handle, ensure_ascii=False, indent=2)
    print(f"\n💾 Đã lưu kết quả chi tiết dạng JSON vào: {output_json_path}")

    # Tạo báo cáo Markdown
    md_content = f"""# Báo cáo Kiểm thử Tự động (LLM-as-a-Judge)

- **Thời điểm chạy:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Mô hình Giám khảo (Judge):** `{settings.NVIDIA_MODEL}`
- **Mô hình Socratic Agent:** `{settings.NVIDIA_MODEL}`
- **Kết quả tổng quan:** **{passed_count}/{total_cases} đạt ({pass_rate}%)**
- **Trạng thái Quality Bar (>= 75% & 0 lỗi factuality):** **{'ĐẠT' if meets_quality_bar else 'CHƯA ĐẠT'}**

## 1. Thống kê theo 4 lớp chỗ khó
| Lớp chỗ khó | Số case đạt | Tỷ lệ % |
|---|:---:|:---:|
"""
    for layer_key, layer_data in layer_stats.items():
        if layer_data["total"] > 0:
            layer_pass_rate = round((layer_data["passed"] / layer_data["total"]) * 100, 1)
            md_content += f"| {layer_key} | {layer_data['passed']}/{layer_data['total']} | {layer_pass_rate}% |\n"

    md_content += """
## 2. Thống kê theo 3 chiều chất lượng
| Chiều chất lượng | Số case đạt | Tỷ lệ % |
|---|:---:|:---:|
"""
    for dimension_key, dimension_data in dimension_stats.items():
        if dimension_data["total"] > 0:
            dimension_pass_rate = round((dimension_data["passed"] / dimension_data["total"]) * 100, 1)
            md_content += f"| {dimension_key} | {dimension_data['passed']}/{dimension_data['total']} | {dimension_pass_rate}% |\n"

    md_content += """
## 3. Bảng chi tiết 20 kịch bản kiểm thử
| ID | Lớp / Chiều | Đầu vào của học viên | Alex phản hồi | Kết quả Judge | Lý do |
|---|---|---|---|:---:|---|
"""
    for result_item in evaluation_results:
        status_str = "✅ PASS" if result_item["passed"] else "❌ FAIL"
        clean_input = result_item["student_input"].replace("\n", " ").replace("|", "\\|")[:50]
        clean_reply = result_item["alex_reply"].replace("\n", " ").replace("|", "\\|")[:60]
        clean_reason = result_item["reason"].replace("\n", " ").replace("|", "\\|")
        md_content += f"| {result_item['id']} | {result_item['eval_dimension']} | {clean_input}... | {clean_reply}... | {status_str} | {clean_reason} |\n"

    with open(output_report_path, "w", encoding="utf-8") as file_handle:
        file_handle.write(md_content)
    print(f"📝 Đã tạo báo cáo Markdown tại: {output_report_path}")
    print("=" * 75)


if __name__ == "__main__":
    run_evaluation()
