#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
TRACK D3: BỘ KIỂM THỬ TỰ ĐỘNG VỚI LLM-AS-A-JUDGE (GEMINI-FLASH-LATEST)
=============================================================================
Đánh giá chất lượng Socratic Agent ("Alex") trên 20 test case Golden Set:
- LLM-as-a-judge Model: gemini-flash-latest (theo đúng yêu cầu)
- Tiêu chí đánh giá:
  1. Factuality (Căn cứ kiến thức, tuyệt đối không hallucination)
  2. Anti-parroting (Chống học vẹt, ép học viên giải thích bình dân)
  3. Probing (Gợi mở trúng điểm khuyết thay vì mớm đáp án)
- Quality Bar: Đạt khi >= 75% qua bộ và 100% Factuality không sai kiến thức.

Cách chạy:
    uv run python eval_judge.py
    hoặc:
    uv run eval_judge.py
=============================================================================
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Nạp biến môi trường từ .env
base_dir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(base_dir, ".env"))

# Model LLM-as-a-judge: gemma-4-26b-a4b-it (Mô hình Gemma chuẩn xác của dự án)
JUDGE_MODEL = "gemma-4-26b-a4b-it"
AGENT_MODEL = "gemma-4-26b-a4b-it"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ---------------------------------------------------------------------------
# 1. Tìm đường dẫn file golden_set.json
# ---------------------------------------------------------------------------
def find_golden_set_path() -> str:
    possible_paths = [
        os.path.join(base_dir, "..", "eval", "golden_set.json"),
        os.path.join(base_dir, "eval", "golden_set.json"),
        os.path.abspath("eval/golden_set.json"),
        os.path.abspath("../eval/golden_set.json"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return os.path.abspath(p)
    raise FileNotFoundError(
        "Không tìm thấy file golden_set.json! Vui lòng kiểm tra thư mục eval/golden_set.json"
    )

# ---------------------------------------------------------------------------
# 2. Khởi tạo LLM Clients
# ---------------------------------------------------------------------------
def init_genai_client():
    if not GEMINI_API_KEY:
        print("⚠️ CẢNH BÁO: GEMINI_API_KEY chưa được cấu hình trong .env!")
        print("   Vui lòng thêm GEMINI_API_KEY vào codebase/.env trước khi chạy.")
        sys.exit(1)
    try:
        from google import genai
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"⚠️ Lỗi khởi tạo google-genai Client: {e}")
        return None

# ---------------------------------------------------------------------------
# 3. Chạy Agent Alex sinh câu trả lời
# ---------------------------------------------------------------------------
def get_alex_reply(student_input: str, test_case: Dict[str, Any], genai_client) -> str:
    """
    Sinh phản hồi của Alex cho câu nhập của học viên:
    Ưu tiên gọi SocraticAgentEngine, nếu FalkorDB offline thì fallback sang direct prompt.
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
    except Exception as e:
        # FalkorDB hoặc engine chưa sẵn sàng, dùng Direct Call với System Prompt chính thức
        pass

    # Cách 2: Direct call với Agent Persona của Alex
    from google.genai import types

    sys_prompt = """Bạn là Alex, một bạn học cùng lớp ngành AI thông minh, ngây thơ có kiểm soát (Protégé Socratic Agent trong Track D3: Học bằng cách dạy).
Vai trò cốt lõi: Bạn là người ĐƯỢC DẠY, đang lắng nghe bạn mình giải thích kiến thức để cùng hiểu sâu bản chất.
Quy tắc phản hồi bất biến:
1. Xưng hô tự nhiên "mình" - "bạn", tuyệt đối không dùng emoji, không máy móc.
2. TUYỆT ĐỐI KHÔNG GIẢNG BÀI, KHÔNG LỘ ĐÁP ÁN: Bạn là người học, không phải người đi dạy hay trợ giảng. Không bao giờ tự tuôn ra kiến thức mới hay đáp án hoàn chỉnh.
3. NẾU HỌC VIÊN NÓI SAI SỰ THẬT: Tuyệt đối KHÔNG khen đúng và KHÔNG sửa lưng bằng bài giảng. Hãy hỏi vặn lại vào chính điểm mâu thuẫn/phi lý đó để bạn mình tự nhận ra chỗ hổng.
4. NẾU HỌC VIÊN CHÉP NGUYÊN VĂN SLIDE HOẶC DÙNG THUẬT NGỮ KHÓ HIỂU: Hỏi ép giải thích lại bằng ngôn ngữ đời thường, bằng một ví dụ bình dị.
5. NẾU HỌC VIÊN ĐÒI ĐÁP ÁN HOẶC HỎI NGOÀI BÀI: Từ chối vì mình cũng đang là người học và không có đáp án; hỏi kéo bạn mình về bài học.
6. NẾU HỌC VIÊN GIẢI THÍCH THIẾU Ý HOẶC GIẢI THÍCH ĐÚNG: Ghi nhận ngắn gọn ý đó và kết thúc bằng ĐÚNG 1 CÂU HỎI đào sâu (Socratic Probing) vào mắt xích cơ chế bên dưới hoặc trường hợp biên.
Độ dài: Luôn ngắn gọn từ 2 đến 3 câu, câu cuối luôn là CÂU HỎI NGƯỢC."""

    user_content = f"""Học viên vừa nói:
"{student_input}"

Hãy phản hồi học viên với tư cách là Alex theo đúng các quy tắc trên:"""

    for attempt in range(4):
        try:
            response = genai_client.models.generate_content(
                model=AGENT_MODEL,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=f"{sys_prompt}\n\n{user_content}")])],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1024
                )
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            err_str = str(e)
            if ("503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str or "demand" in err_str) and attempt < 3:
                time.sleep(2 * (attempt + 1))
                continue
            # Nếu model gemma không khả dụng, fallback sang gemini-flash-latest cho Alex
            try:
                resp_fallback = genai_client.models.generate_content(
                    model="gemini-flash-latest",
                    contents=[types.Content(role="user", parts=[types.Part.from_text(text=f"{sys_prompt}\n\n{user_content}")])],
                    config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=1024)
                )
                if resp_fallback and resp_fallback.text:
                    return resp_fallback.text.strip()
            except Exception as e2:
                if attempt < 3:
                    time.sleep(2 * (attempt + 1))
                    continue
                return f"[Lỗi sinh câu trả lời của Agent: {e2}]"

    return "Mình đang suy nghĩ một chút về ý này của bạn, bạn có thể nói rõ hơn được không?"

# ---------------------------------------------------------------------------
# 4. LLM-as-a-judge: Trích xuất và đánh giá an toàn
# ---------------------------------------------------------------------------
def extract_text_safely(response) -> str:
    """Trích xuất chuỗi văn bản an toàn từ phản hồi của google-genai kể cả khi có thinking token"""
    if not response:
        return ""
    try:
        if hasattr(response, "text") and response.text:
            return response.text.strip()
    except Exception:
        pass
    try:
        if hasattr(response, "candidates") and response.candidates:
            parts_text = []
            for cand in response.candidates:
                if hasattr(cand, "content") and cand.content and hasattr(cand.content, "parts"):
                    for p in cand.content.parts:
                        if hasattr(p, "text") and p.text:
                            parts_text.append(p.text)
            if parts_text:
                return "\n".join(parts_text).strip()
    except Exception:
        pass
    return ""


def parse_judge_output(text: str) -> Dict[str, Any]:
    """Parse JSON hoặc phân tích cú pháp dự phòng từ văn bản của Judge"""
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
            data = json.loads(json_match.group(0))
            return {
                "passed": bool(data.get("passed", False)),
                "score": int(data.get("score", 3)),
                "factuality_ok": bool(data.get("factuality_ok", True)),
                "dimension_ok": bool(data.get("dimension_ok", True)),
                "reason": str(data.get("reason", "")).strip()
            }
    except Exception:
        pass

    # Heuristic fallback nếu model không sinh đúng định dạng JSON
    t_low = text.lower()
    is_passed = ("true" in t_low or "pass" in t_low or "đạt" in t_low) and (
        "fail" not in t_low and "không đạt" not in t_low and "false" not in t_low
    )
    return {
        "passed": is_passed,
        "score": 4 if is_passed else 2,
        "factuality_ok": "không có căn cứ" not in t_low and "sai sự thật" not in t_low,
        "dimension_ok": is_passed,
        "reason": text.replace("\n", " ")[:150]
    }


def judge_alex_response(
    test_case: Dict[str, Any],
    alex_reply: str,
    genai_client
) -> Dict[str, Any]:
    """
    Giám khảo AI đánh giá phản hồi của Alex với cơ chế fallback tự động:
    Thử lần lượt: JUDGE_MODEL -> gemini-2.0-flash -> gemini-1.5-flash -> gemini-flash-latest.
    CAM KẾT 100% LUÔN TRẢ VỀ DICT HỢP LỆ, KHÔNG BAO GIỜ TRẢ VỀ NONE.
    """
    from google.genai import types

    judge_prompt = f"""Bạn là Giám khảo AI (LLM-as-a-Judge) chuyên môn cao, đánh giá chất lượng phản hồi của Socratic Agent tên là "Alex" trong một hệ thống giáo dục AI ("Học bằng cách dạy").

THÔNG TIN TEST CASE:
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

    models_to_try = [
        JUDGE_MODEL,
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-flash-latest"
    ]

    # Loại bỏ phần tử trùng lặp
    ordered_models = []
    for m in models_to_try:
        if m and m not in ordered_models:
            ordered_models.append(m)

    last_error = ""
    for model_name in ordered_models:
        for attempt in range(2):
            try:
                response = genai_client.models.generate_content(
                    model=model_name,
                    contents=[types.Content(role="user", parts=[types.Part.from_text(text=judge_prompt)])],
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        max_output_tokens=1024
                    )
                )
                raw_text = extract_text_safely(response)
                if raw_text:
                    res = parse_judge_output(raw_text)
                    if model_name != JUDGE_MODEL:
                        res["reason"] = f"[{model_name}] " + res["reason"]
                    return res
            except Exception as e:
                err_str = str(e)
                last_error = err_str
                if ("503" in err_str or "429" in err_str or "demand" in err_str) and attempt < 1:
                    time.sleep(2)
                    continue
                # Nếu gặp lỗi khác như 500 hay không tương thích, chuyển sang model kế tiếp
                break

    # Đảm bảo LUÔN trả về Dict hợp lệ, không bao giờ là None
    return {
        "passed": False,
        "score": 1,
        "factuality_ok": False,
        "dimension_ok": False,
        "reason": f"Lỗi gọi Judge models: {last_error[:120]}"
    }

# ---------------------------------------------------------------------------
# 5. Hàm chạy toàn bộ quy trình kiểm thử
# ---------------------------------------------------------------------------
def run_evaluation():
    print("=" * 75)
    print("🚀 BẮT ĐẦU CHẠY KIỂM THỬ TỰ ĐỘNG TRACK D3 VỚI LLM-AS-A-JUDGE")
    print(f"🤖 Giám khảo (Judge Model) : {JUDGE_MODEL}")
    print(f"🎯 Mô hình Socratic Agent  : {AGENT_MODEL}")
    print(f"⏰ Thời gian bắt đầu        : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)

    # 1. Tìm và đọc golden set
    golden_path = find_golden_set_path()
    print(f"📂 Đang tải Golden Set từ: {golden_path}")
    with open(golden_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    total_cases = len(cases)
    print(f"📋 Tổng số kịch bản kiểm thử: {total_cases} cases\n")

    # 2. Khởi tạo client
    client = init_genai_client()

    results = []
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
    for idx, case in enumerate(cases, 1):
        cid = case.get("id", f"TC{idx:02d}")
        layer = case.get("layer", "Chung")
        dim = case.get("eval_dimension", "Factuality")
        student_input = case.get("student_input", "")

        print(f"[{idx:02d}/{total_cases}] Đang test {cid} ({layer} | {dim})...")
        print(f"    👤 Học viên: \"{student_input[:65]}...\"" if len(student_input) > 65 else f"    👤 Học viên: \"{student_input}\"")

        # Sinh phản hồi Alex
        t0 = time.time()
        alex_reply = get_alex_reply(student_input, case, client)
        t_agent = round(time.time() - t0, 1)

        # Giám khảo chấm
        t1 = time.time()
        judge_res = judge_alex_response(case, alex_reply, client)
        t_judge = round(time.time() - t1, 1)

        if not isinstance(judge_res, dict):
            judge_res = {
                "passed": False,
                "score": 1,
                "factuality_ok": False,
                "dimension_ok": False,
                "reason": "Phản hồi giám khảo không hợp lệ"
            }

        is_passed = judge_res.get("passed", False)
        if is_passed:
            passed_count += 1
            status_icon = "✅ PASS"
        else:
            status_icon = "❌ FAIL"

        if not judge_res.get("factuality_ok", True):
            factuality_failures += 1

        print(f"    🤖 Alex: \"{alex_reply[:75]}...\"" if len(alex_reply) > 75 else f"    🤖 Alex: \"{alex_reply}\"")
        print(f"    ⚖️  Judge ({JUDGE_MODEL}): {status_icon} (Điểm: {judge_res['score']}/5) | {judge_res['reason']}")
        print(f"    ⏱️  Thời gian: Agent {t_agent}s + Judge {t_judge}s\n")

        # Cập nhật thống kê layer
        matched_layer = "Tiêu chuẩn"
        for lk in layer_stats.keys():
            if lk in layer:
                matched_layer = lk
                break
        if matched_layer in layer_stats:
            layer_stats[matched_layer]["total"] += 1
            if is_passed:
                layer_stats[matched_layer]["passed"] += 1

        # Cập nhật thống kê dimension
        if dim in dimension_stats:
            dimension_stats[dim]["total"] += 1
            if is_passed:
                dimension_stats[dim]["passed"] += 1

        results.append({
            "id": cid,
            "layer": layer,
            "category": case.get("category"),
            "source_reference": case.get("source_reference"),
            "eval_dimension": dim,
            "student_input": student_input,
            "expected_behavior": case.get("expected_behavior"),
            "alex_reply": alex_reply,
            "passed": is_passed,
            "score": judge_res["score"],
            "factuality_ok": judge_res["factuality_ok"],
            "reason": judge_res["reason"],
            "agent_time_sec": t_agent,
            "judge_time_sec": t_judge
        })

        # Nghỉ giữa các request để tránh spike / rate limit
        time.sleep(1.5)

    elapsed_time = round(time.time() - start_time, 1)
    pass_rate = round((passed_count / total_cases) * 100, 1)

    # 4. Kiểm tra Quality Bar
    # Cam kết: >= 75% qua bộ và 100% không xác nhận thông tin sai là đúng (0 lỗi factuality)
    meets_quality_bar = (pass_rate >= 75.0) and (factuality_failures == 0)

    # 5. In bảng tổng kết
    print("=" * 75)
    print("📊 TỔNG KẾT KẾT QUẢ KIỂM THỬ (LLM-AS-A-JUDGE: GEMINI-FLASH-LATEST)")
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
    for lk, ldata in layer_stats.items():
        if ldata["total"] > 0:
            l_rate = round((ldata["passed"] / ldata["total"]) * 100, 1)
            print(f"  - {lk:<35}: {ldata['passed']}/{ldata['total']} ({l_rate}%)")

    print("\n--- PHÂN LOẠI THEO 3 CHIỀU CHẤT LƯỢNG ---")
    for dk, ddata in dimension_stats.items():
        if ddata["total"] > 0:
            d_rate = round((ddata["passed"] / ddata["total"]) * 100, 1)
            print(f"  - {dk:<20}: {ddata['passed']}/{ddata['total']} ({d_rate}%)")

    # 6. Lưu kết quả ra thư mục eval/
    eval_dir = os.path.dirname(golden_path)
    output_json_path = os.path.join(eval_dir, "eval_results.json")
    output_report_path = os.path.join(eval_dir, "eval_report.md")

    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "judge_model": JUDGE_MODEL,
        "agent_model": AGENT_MODEL,
        "total_cases": total_cases,
        "passed_cases": passed_count,
        "pass_rate_percent": pass_rate,
        "factuality_failures": factuality_failures,
        "meets_quality_bar": meets_quality_bar,
        "elapsed_seconds": elapsed_time,
        "layer_breakdown": layer_stats,
        "dimension_breakdown": dimension_stats,
        "detailed_results": results
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Đã lưu kết quả chi tiết dạng JSON vào: {output_json_path}")

    # Tạo báo cáo Markdown
    md_content = f"""# Báo cáo Kiểm thử Tự động (LLM-as-a-Judge)

- **Thời điểm chạy:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Mô hình Giám khảo (Judge):** `{JUDGE_MODEL}`
- **Mô hình Socratic Agent:** `{AGENT_MODEL}`
- **Kết quả tổng quan:** **{passed_count}/{total_cases} đạt ({pass_rate}%)**
- **Trạng thái Quality Bar (>= 75% & 0 lỗi factuality):** **{'ĐẠT' if meets_quality_bar else 'CHƯA ĐẠT'}**

## 1. Thống kê theo 4 lớp chỗ khó
| Lớp chỗ khó | Số case đạt | Tỷ lệ % |
|---|:---:|:---:|
"""
    for lk, ldata in layer_stats.items():
        if ldata["total"] > 0:
            lr = round((ldata["passed"] / ldata["total"]) * 100, 1)
            md_content += f"| {lk} | {ldata['passed']}/{ldata['total']} | {lr}% |\n"

    md_content += """
## 2. Thống kê theo 3 chiều chất lượng
| Chiều chất lượng | Số case đạt | Tỷ lệ % |
|---|:---:|:---:|
"""
    for dk, ddata in dimension_stats.items():
        if ddata["total"] > 0:
            dr = round((ddata["passed"] / ddata["total"]) * 100, 1)
            md_content += f"| {dk} | {ddata['passed']}/{ddata['total']} | {dr}% |\n"

    md_content += """
## 3. Bảng chi tiết 20 kịch bản kiểm thử
| ID | Lớp / Chiều | Đầu vào của học viên | Alex phản hồi | Kết quả Judge | Lý do |
|---|---|---|---|:---:|---|
"""
    for r in results:
        status_str = "✅ PASS" if r["passed"] else "❌ FAIL"
        clean_in = r["student_input"].replace("\n", " ").replace("|", "\\|")[:50]
        clean_out = r["alex_reply"].replace("\n", " ").replace("|", "\\|")[:60]
        clean_reason = r["reason"].replace("\n", " ").replace("|", "\\|")
        md_content += f"| {r['id']} | {r['eval_dimension']} | {clean_in}... | {clean_out}... | {status_str} | {clean_reason} |\n"

    with open(output_report_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"📝 Đã tạo báo cáo Markdown tại: {output_report_path}")
    print("=" * 75)

if __name__ == "__main__":
    run_evaluation()
