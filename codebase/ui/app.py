import os
import sys
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
import httpx
from dotenv import load_dotenv

# Ensure import paths from codebase root
ui_dir = os.path.abspath(os.path.dirname(__file__))
codebase_dir = os.path.abspath(os.path.join(ui_dir, ".."))
if codebase_dir not in sys.path:
    sys.path.insert(0, codebase_dir)

load_dotenv(os.path.join(codebase_dir, ".env"))

import re
from backend.agent_engine import SocraticAgentEngine
from config.config import settings


def clean_lesson_title(raw_title: str) -> str:
    """Loại bỏ sạch các tiền tố, hậu tố rác như (sáng), (chiều), dấu gạch ngang, v.v."""
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
    title = re.sub(r"^\s*\((?:sáng|chiều|tối)\)\s*[-—–:]?\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\((?:sáng|chiều|tối)\)\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\([^)]*(?:phần|part)\s*[^)]*\)\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\(phần\s+(?:sau|đầu)\s+buổi\)\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^[-—–:\s]+", "", title)
    title = re.sub(r"\s*[-—–:]\s*$", "", title)
    return title.strip()


from backend.voice_model import transcribe_audio
try:
    from ui.visualize_graph import generate_graph_html
except ImportError:
    from visualize_graph import generate_graph_html

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="VLearn — Trợ lý Học tập Thông minh",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS phong cách ChatGPT Dark Mode cao cấp
st.markdown("""
<style>
    /* ChatGPT Color Palette */
    :root {
        --chatgpt-main: #212121;
        --chatgpt-sidebar: #171717;
        --chatgpt-card: #2f2f2f;
        --chatgpt-hover: #2a2a2a;
        --chatgpt-border: #383838;
        --chatgpt-text: #ececec;
        --chatgpt-subtext: #b4b4b4;
        --chatgpt-green: #10a37f;
        --chatgpt-blue: #3b82f6;
    }

    /* Toàn bộ app full black ChatGPT */
    .stApp {
        background-color: var(--chatgpt-main) !important;
        color: var(--chatgpt-text) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Sidebar ChatGPT */
    section[data-testid="stSidebar"] {
        background-color: var(--chatgpt-sidebar) !important;
        border-right: 1px solid #262626 !important;
    }
    section[data-testid="stSidebar"] * {
        color: var(--chatgpt-text) !important;
    }

    /* Top Model Selector Pill (ChatGPT style) */
    .model-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #2a2a2a;
        border: 1px solid #3d3d3d;
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 500;
        color: #ececec;
        margin-bottom: 12px;
    }
    .model-dot {
        width: 8px;
        height: 8px;
        background: #10a37f;
        border-radius: 50%;
        box-shadow: 0 0 8px #10a37f;
    }

    /* Nút bấm ChatGPT style (Sidebar New Chat & Action buttons) */
    div.stButton > button,
    .stButton > button,
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"] {
        background-color: #2f2f2f !important;
        color: #ececec !important;
        border: 1px solid #3d3d3d !important;
        border-radius: 10px !important;
        padding: 8px 14px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
        box-shadow: none !important;
    }
    div.stButton > button p,
    .stButton > button p {
        color: #ececec !important;
    }
    div.stButton > button:hover,
    .stButton > button:hover {
        background-color: #383838 !important;
        border-color: #505050 !important;
        color: #ffffff !important;
    }

    /* Chat Messages ChatGPT style */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #2a2a2a !important;
        border-radius: 0px !important;
        padding: 16px 20px !important;
        max-width: 860px !important;
        margin: 0 auto !important;
    }
    div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-user"]) {
        background-color: rgba(255, 255, 255, 0.02) !important;
    }
    div[data-testid="stChatMessage"] p {
        color: #ececec !important;
        font-size: 14.5px !important;
        line-height: 1.6 !important;
    }

    /* Floating Chat Input (ChatGPT Pill) */
    [data-testid="stChatInput"] {
        background-color: #2f2f2f !important;
        border: 1px solid #3d3d3d !important;
        border-radius: 24px !important;
        max-width: 860px !important;
        margin: 0 auto !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2) !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #ececec !important;
        background-color: transparent !important;
        font-size: 14px !important;
    }

    /* Status Badge Tags */
    .tag-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        margin-top: 6px;
    }
    .tag-green { background: #10a37f22; color: #10a37f; border: 1px solid #10a37f55; }
    .tag-orange { background: #f59e0b22; color: #f59e0b; border: 1px solid #f59e0b55; }
    .tag-red { background: #ef444422; color: #ef4444; border: 1px solid #ef444455; }
    .tag-blue { background: #3b82f622; color: #60a5fa; border: 1px solid #3b82f655; }

    /* End of Graph banner */
    .end-of-graph-box {
        background: linear-gradient(135deg, #0d3b2e 0%, #08241c 100%);
        border: 1px solid #10a37f;
        border-radius: 14px;
        padding: 20px;
        margin: 15px auto;
        max-width: 860px;
        box-shadow: 0 0 25px rgba(16, 163, 127, 0.25);
    }

    /* Collapsible Pedagogical Thinking Box */
    .thinking-box-container {
        background: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        margin: 6px 0 14px 0;
        overflow: hidden;
        transition: all 0.25s ease;
    }
    .thinking-box-container:hover {
        border-color: rgba(255, 255, 255, 0.16);
        background: rgba(255, 255, 255, 0.035);
    }
    .thinking-box-summary {
        cursor: pointer;
        padding: 9px 14px;
        font-size: 13px;
        font-weight: 500;
        color: #9ca3af;
        display: flex;
        align-items: center;
        gap: 8px;
        user-select: none;
        outline: none;
    }
    .thinking-box-summary:hover {
        color: #e5e7eb;
    }
    .thinking-box-body {
        padding: 12px 16px 14px 16px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        background: rgba(0, 0, 0, 0.25);
    }
    .thinking-phase-card {
        margin-bottom: 12px;
        padding-left: 12px;
        border-left: 2px solid #10a37f88;
    }
    .thinking-phase-card:last-child {
        margin-bottom: 0;
    }
    .thinking-phase-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
    }
    .thinking-phase-title {
        font-size: 12px;
        font-weight: 600;
        color: #6ee7b7;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .thinking-phase-badge {
        font-size: 10px;
        padding: 1px 6px;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.08);
        color: #94a3b8;
    }
    .thinking-phase-content {
        font-size: 12.5px;
        line-height: 1.6;
        color: #94a3b8;
        opacity: 0.72;
    }
    .final-reply-text {
        font-size: 15px !important;
        line-height: 1.65 !important;
        color: #f8fafc !important;
        opacity: 1.0 !important;
        font-weight: 400 !important;
    }

    /* Bottom pinned bar styling */
    div[data-testid="stBottom"] {
        background: #212121 !important;
        border-top: none !important;
    }
    div[data-testid="stBottom"] > div {
        background: transparent !important;
        padding-top: 6px !important;
        padding-bottom: 14px !important;
    }
    .main .block-container,
    section[data-testid="stMain"] .block-container {
        padding-bottom: 140px !important;
    }

    /* Bottom Bar Centered Outer Layout */
    .st-key-chatgpt_bottom_outer {
        max-width: 860px !important;
        margin: 0 auto !important;
    }

    /* Prompt Input Container */
    .st-key-chatgpt_prompt_outer,
    .chatgpt-prompt-outer {
        background: #2f2f2f !important;
        border: 1px solid #3d3d3d !important;
        border-radius: 26px !important;
        padding: 4px 14px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .st-key-chatgpt_prompt_outer:focus-within,
    .chatgpt-prompt-outer:focus-within {
        border-color: #565856 !important;
        box-shadow: 0 4px 26px rgba(0, 0, 0, 0.6) !important;
    }
    .st-key-chatgpt_prompt_outer div[data-testid="stForm"],
    .chatgpt-prompt-outer div[data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
    }
    /* Auto-expand vertical textarea */
    .st-key-chatgpt_prompt_outer textarea,
    .chatgpt-prompt-outer textarea {
        background: transparent !important;
        border: none !important;
        color: #ececec !important;
        font-size: 15px !important;
        line-height: 1.5 !important;
        resize: none !important;
        field-sizing: content !important;
        min-height: 26px !important;
        max-height: 180px !important;
        overflow-y: auto !important;
        padding: 6px 0 !important;
        box-shadow: none !important;
    }
    .st-key-chatgpt_prompt_outer textarea:focus,
    .chatgpt-prompt-outer textarea:focus {
        border: none !important;
        box-shadow: none !important;
    }
    .st-key-chatgpt_prompt_outer div[data-testid="stTextArea"],
    .st-key-chatgpt_prompt_outer div[data-testid="stTextArea"] > div,
    .chatgpt-prompt-outer div[data-testid="stTextArea"],
    .chatgpt-prompt-outer div[data-testid="stTextArea"] > div {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        box-shadow: none !important;
    }

    /* Send button styling */
    .chatgpt-send-btn button,
    .chatgpt-send-btn button[data-testid="baseButton-secondary"] {
        background: #2563eb !important;
        color: #ffffff !important;
        border-radius: 50% !important;
        border: none !important;
        width: 36px !important;
        height: 36px !important;
        min-width: 36px !important;
        min-height: 36px !important;
        padding: 0 !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.4) !important;
        transition: transform 0.1s ease, background 0.15s ease !important;
    }
    .chatgpt-send-btn button:hover {
        background: #1d4ed8 !important;
        transform: scale(1.05);
    }
    .chatgpt-send-btn button p {
        color: #ffffff !important;
        margin: 0 !important;
        line-height: 1 !important;
    }
    .chatgpt-send-btn button:disabled {
        background: #3a3a3a !important;
        color: #737373 !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
    }
    .chatgpt-send-btn button:disabled p {
        color: #737373 !important;
    }

    /* Shimmer Pulse Typing Card (Alex thinking animation) */
    .alex-thinking-card {
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(16, 163, 127, 0.3);
        border-radius: 12px;
        padding: 10px 16px;
        margin: 8px 0;
        width: fit-content;
        animation: breathing-glow 1.8s ease-in-out infinite alternate;
    }
    @keyframes breathing-glow {
        0% { border-color: rgba(16, 163, 127, 0.2); box-shadow: 0 0 8px rgba(16, 163, 127, 0.05); }
        100% { border-color: rgba(16, 163, 127, 0.6); box-shadow: 0 0 16px rgba(16, 163, 127, 0.2); }
    }
    .alex-thinking-text {
        font-size: 13.5px;
        color: #b4b4b4;
        font-weight: 500;
    }
    .typing-dots {
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .typing-dot {
        width: 5px;
        height: 5px;
        background-color: #10a37f;
        border-radius: 50%;
        animation: typingBounce 1.4s infinite ease-in-out both;
    }
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    .typing-dot:nth-child(3) { animation-delay: 0s; }
    @keyframes typingBounce {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.3; }
        40% { transform: scale(1.1); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)


# Khởi tạo Engine (Cached để không bao giờ khởi tạo lại khi rerun)
@st.cache_resource
def get_engine():
    return SocraticAgentEngine()

engine = get_engine()
st.session_state.engine = engine


def render_thinking_box(thinking_phases: list) -> str:
    """Render collapsible thinking container grouped by pedagogical phases."""
    if not thinking_phases:
        return ""

    phases_html = []
    for phase_item in thinking_phases:
        title = phase_item.get("phase_name", "Giai đoạn suy nghĩ")
        badge = phase_item.get("badge", "")
        badge_html = f"<span class='thinking-phase-badge'>{badge}</span>" if badge else ""

        if "details" in phase_item:
            lines = [f"<div>• {line}</div>" if not line.startswith("•") else f"<div>{line}</div>" for line in phase_item["details"]]
            content_html = "".join(lines)
        elif "raw_thought" in phase_item:
            thought_snippet = phase_item["raw_thought"][:600] + ("..." if len(phase_item["raw_thought"]) > 600 else "")
            safe_text = thought_snippet.replace("<", "&lt;").replace(">", "&gt;")
            content_html = f"<div style='font-family:monospace; font-size:11.5px; line-height:1.5; white-space:pre-wrap;'>{safe_text}</div>"
        else:
            content_html = f"<div>{phase_item.get('content', '')}</div>"

        phases_html.append(f"""
        <div class="thinking-phase-card">
            <div class="thinking-phase-header">
                <span class="thinking-phase-title">{title}</span>
                {badge_html}
            </div>
            <div class="thinking-phase-content">{content_html}</div>
        </div>
        """)

    all_phases = "".join(phases_html)
    return f"""
    <details class="thinking-box-container">
        <summary class="thinking-box-summary">
            <span>💭</span>
            <span>Xem quá trình suy nghĩ & thẩm định ({len(thinking_phases)} giai đoạn)</span>
        </summary>
        <div class="thinking-box-body">
            {all_phases}
        </div>
    </details>
    """


def call_api_chat(message: str, session_id: str = "vlearn_default"):
    """Call backend chat API endpoint with session persistence."""
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{BACKEND_URL}/api/chat", json={"message": message, "session_id": session_id})
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return engine.process_student_message(message, session_id=session_id)


def call_api_history(session_id: str = "vlearn_default"):
    """Fetch session interaction history."""
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{BACKEND_URL}/api/history", params={"session_id": session_id})
            if resp.status_code == 200:
                return resp.json().get("history", [])
    except Exception:
        pass
    return engine.get_session_history(session_id)


def call_api_lessons():
    """Scan and retrieve available lesson tracks dynamically."""
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{BACKEND_URL}/api/lessons")
            if resp.status_code == 200:
                return resp.json().get("lessons", [])
    except Exception:
        pass
    return settings.get_available_lessons()


def call_api_switch_lesson(track_id: str, session_id: str = "vlearn_default"):
    """Switch active lesson track."""
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(f"{BACKEND_URL}/api/switch_lesson", json={"track_id": track_id, "session_id": session_id})
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return engine.switch_lesson(track_id, session_id=session_id)


def call_api_choose_branch(track_id: str):
    """Switch to alternative traversal path."""
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.post(f"{BACKEND_URL}/api/choose_branch", json={"track_id": track_id})
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return engine.choose_alternative_path(track_id)


def call_api_progress(track: str = None):
    """Retrieve learning progress metrics for track."""
    if track is None:
        track = st.session_state.get("selected_track", settings.get_default_track())
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{BACKEND_URL}/api/progress", params={"track": track})
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return engine.graph_service.get_progress(track=track)


def call_api_graph(track: str = None):
    """Fetch nodes and edges from FalkorDB for visual rendering."""
    if track is None:
        track = st.session_state.get("selected_track", settings.get_default_track())
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{BACKEND_URL}/api/graph", params={"track": track})
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return engine.graph_service.export_graph_for_ui(track=track)


# Track and lesson state initialization (Cached in session_state)
if "available_lessons" not in st.session_state:
    st.session_state.available_lessons = call_api_lessons()
available_lessons = st.session_state.available_lessons
lesson_map = {lesson["track"]: lesson for lesson in available_lessons}

if "selected_track" not in st.session_state:
    st.session_state.selected_track = settings.get_default_track()

if "current_feynman_concept" not in st.session_state or st.session_state.get("_last_cached_track") != st.session_state.selected_track:
    if engine.graph_service:
        engine.graph_service.set_active_track(st.session_state.selected_track)
    st.session_state.current_feynman_concept = engine.get_current_feynman_concept()
    st.session_state._last_cached_track = st.session_state.selected_track

current_feynman_concept = st.session_state.current_feynman_concept
current_lesson_title = lesson_map.get(st.session_state.selected_track, {}).get("title", "")


def generate_llm_topic_intro(concept_node: dict, clean_topic: str) -> str:
    """
    Dùng LLM để sinh lời chào mở đầu và gợi ý 3 hướng đi sâu sắc, cụ thể theo chủ đề bài học,
    tuyệt đối không dùng các mẫu rập khuôn hoặc fallback string mặc định.
    """
    core_truth = concept_node.get("core_truth", "")
    concept_name = clean_lesson_title(concept_node.get("name", clean_topic))

    prompt = (
        f"Bạn là Alex — một người bạn học cùng lớp (Socratic Protégé) thân thiện, khiêm tốn, ham học hỏi.\n"
        f"Bạn và bạn học đang bắt đầu cùng nhau ôn tập chuyên đề: '{clean_topic}'.\n"
        f"Nội dung trọng tâm bài giảng: '{core_truth if core_truth else concept_name}'.\n\n"
        f"Nhiệm vụ của bạn:\n"
        f"Viết lời mở đầu tự nhiên, gần gũi và gợi mở:\n"
        f"1. Chào bạn học vui vẻ và giới thiệu chủ đề ôn tập dạng in đậm: **{clean_topic}** 🎓\n"
        f"2. Gợi ý đúng 3 hướng đi cụ thể, hấp dẫn để bạn học có thể chọn bắt đầu giảng lại cho bạn nghe.\n"
        f"   - Hướng 1: Về bài toán thực tế hoặc thách thức mà khái niệm này giải quyết.\n"
        f"   - Hướng 2: Về cơ chế hoạt động cốt lõi hoặc các bước tiến hành.\n"
        f"   - Hướng 3: Về sự đánh đổi, rủi ro hoặc một ví dụ thực tế điển hình.\n"
        f"   LƯU Ý QUAN TRỌNG: Hãy đặt câu hỏi hoặc gợi mở tình huống cụ thể gắn liền với '{clean_topic}'. TUYỆT ĐỐI KHÔNG dùng các tiêu đề nhạt nhẽo như 'Bản chất & Vai trò', 'Cơ chế hoạt động', 'Ứng dụng & Đánh đổi'.\n"
        f"3. Khích lệ bạn học chọn một hướng hoặc bắt đầu giảng theo cách hiểu riêng.\n"
        f"4. Văn phong: Bạn bè cùng lớp, xưng hô 'mình - bạn', ngắn gọn, ấm áp (dưới 120 từ)."
    )

    try:
        res = engine.nvidia_client.generate_text(
            prompt=prompt,
            enable_thinking=False
        )
        if res and len(res.strip()) > 30:
            return res.strip()
        return f"⚠️ [Lỗi LLM]: Mô hình trả về kết quả rỗng khi khởi tạo chủ đề '{clean_topic}'."
    except Exception as exc:
        return f"⚠️ [Lỗi kết nối LLM]: Không thể sinh lời mở đầu cho chủ đề '{clean_topic}'. Chi tiết: {exc}"


def generate_llm_parroting_stream(student_msg: str, concept_name: str, citation: str, core_truth: str = ""):
    """
    Sinh phản hồi Socratic bằng LLM khi học viên nói máy móc hoặc chép nguyên văn tài liệu.
    Tuyệt đối không dùng fallback string mặc định nếu có lỗi.
    """
    prompt = (
        f"Bạn là Alex — một người bạn học cùng lớp (Socratic Protégé) đang học chung với bạn học.\n"
        f"Chủ đề đang ôn: '{concept_name}'.\n"
        f"Tài liệu tham chiếu: {citation}.\n"
        f"Câu học viên vừa trả lời:\n\"{student_msg}\"\n\n"
        f"Đánh giá: Câu trả lời này bị chép nguyên văn từ tài liệu hoặc trả lời rất máy móc, học vẹt.\n\n"
        f"Nhiệm vụ của Alex:\n"
        f"1. Phản ứng tự nhiên, hóm hỉnh như bạn bè (TUYỆT ĐỐI KHÔNG dùng câu rập khuôn 'Đoạn này nghe giống như trích dẫn từ tài liệu...').\n"
        f"2. Khéo léo nhận xét rằng câu vừa rồi nghe chuẩn sách vở quá, nhưng Alex muốn hiểu bản chất thật sự.\n"
        f"3. Đặt một câu hỏi gợi mở, khích lệ bạn học dùng ngôn từ đời thường hoặc một ví dụ thực tế giản dị để giải thích lại điểm mấu chốt.\n"
        f"4. Giọng điệu: Bạn học cùng lớp, xưng hô 'mình - bạn', ngắn gọn (2-3 câu, dưới 60 từ)."
    )

    try:
        has_any = False
        for chunk in engine.nvidia_client.generate_stream(prompt=prompt):
            if chunk:
                has_any = True
                yield chunk
        if not has_any:
            yield f"⚠️ [Lỗi LLM]: Mô hình không phản hồi khi sinh câu hỏi gợi mở cho '{concept_name}'."
    except Exception as exc:
        yield f"⚠️ [Lỗi kết nối LLM]: Không thể sinh phản hồi từ mô hình AI ({exc})."


def build_initial_topic_message(concept_node: dict, lesson_title: str = "") -> dict:
    """
    Tạo thông điệp mở đầu phiên học bằng LLM: Alex chào hỏi, giới thiệu chủ đề
    và gợi ý các hướng đi cụ thể theo chủ đề để học viên bắt đầu giảng.
    """
    topic_raw = lesson_title if lesson_title else concept_node.get("name", "Kiến thức trọng tâm")
    clean_topic = clean_lesson_title(topic_raw)
    content = generate_llm_topic_intro(concept_node, clean_topic)

    # Đặt gợi ý ban đầu vào memory
    engine.memory.set_last_question("vlearn_default", f"Khởi đầu ôn tập: {clean_topic}")

    return {
        "role": "assistant",
        "content": content,
        "event_type": "topic_intro",
        "citation": concept_node.get("citation", "[VLearn]"),
        "event_label": "Gợi ý chủ đề 🎓",
        "time": datetime.now().strftime("%H:%M")
    }


def end_and_clear_session():
    """
    Tự động dọn dẹp sạch bộ nhớ hội thoại và xóa file db/chat_history.json trên ổ đĩa
    mỗi khi kết thúc phiên học (hoặc chuyển/đặt lại bài học).
    """
    if "final_summary" not in st.session_state or not st.session_state.final_summary:
        st.session_state.final_summary = engine.get_global_summary("vlearn_default")
    engine.clear_session_history("vlearn_default")
    engine.memory.clear_all()
    try:
        if settings.CHAT_HISTORY_FILE.exists():
            settings.CHAT_HISTORY_FILE.unlink()
    except Exception as exc:
        print(f"⚠️ Lỗi khi xóa file chat_history.json: {exc}")


def get_live_socratic_opening(concept_node: dict) -> str:
    """Generate or retrieve opening Socratic probe from lecture content without formulaic phrases."""
    raw_question = concept_node.get('learning_question') or concept_node.get('child_question') or ''
    if not raw_question or 'lại vận hành như vậy' in raw_question or 'Cơ chế cốt lõi' in raw_question or 'thách thức kỹ thuật lớn nhất khi giải quyết vấn đề' in raw_question or len(raw_question) < 15:
        return engine.generate_smart_opening_question(concept_node['name'], concept_node.get('quote', ''), concept_node.get('core_truth', ''))
    return raw_question


# Auto-clean legacy messages containing formulaic robotic phrases, token drafts or previous question openings
if "messages" in st.session_state and st.session_state.messages:
    first_content = st.session_state.messages[0].get("content", "")
    if (
        "Bản chất & Vai trò" in first_content
        or "(sáng)" in first_content
        or "lại vận hành như vậy" in first_content
        or "Cơ chế cốt lõi và nguyên nhân" in first_content
        or "thách thức kỹ thuật lớn nhất khi giải quyết vấn đề" in first_content
        or "Đọc qua bài giảng, mình có một thắc mắc về mặt kỹ thuật muốn hỏi bạn" in first_content
        or "(12)" in first_content
        or "Draft 2:" in first_content
        or "Under 35 words" in first_content
        or "> *\"" in first_content
        or "Chào bạn, mình là Alex nè! Chúng ta cùng bắt đầu ôn tập:" in first_content
        or "Một vài hướng bạn có thể chọn để bắt đầu chia sẻ:" in first_content
        or "ttemperature" in first_content
    ):
        del st.session_state["messages"]


if "messages" not in st.session_state:
    st.session_state.messages = []


if "events" not in st.session_state:
    st.session_state.events = []

if "is_ended" not in st.session_state:
    st.session_state.is_ended = False

if "session_finished" not in st.session_state:
    st.session_state.session_finished = False

if "active_view" not in st.session_state:
    st.session_state.active_view = "chat"

if "prompt_version" not in st.session_state:
    st.session_state.prompt_version = 0

if "voice_version" not in st.session_state:
    st.session_state.voice_version = 0

if "draft_prompt" not in st.session_state:
    st.session_state.draft_prompt = ""

if "is_recording" not in st.session_state:
    st.session_state.is_recording = False


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    # 0. Lesson selection preserving knowledge locality
    track_keys = list(lesson_map.keys()) if lesson_map else [st.session_state.selected_track]

    current_idx = 0
    if st.session_state.selected_track in track_keys:
        current_idx = track_keys.index(st.session_state.selected_track)

    def format_lesson_item(k: str) -> str:
        lesson = lesson_map.get(k, {})
        raw_title = lesson.get("title", k)
        cleaned = clean_lesson_title(raw_title)
        if lesson.get("type") == "pdf" or "slide_" in k:
            return f"📑 Slide: {cleaned}"
        return f"📘 {cleaned}"

    selected_track_id = st.selectbox(
        "📚 Chọn bài học ôn tập:",
        options=track_keys,
        index=current_idx,
        format_func=format_lesson_item,
        help="Đồ thị tri thức được cách ly độc lập theo từng bài giảng/slide để bảo toàn tính cục bộ."
    )

    if selected_track_id != st.session_state.selected_track:
        st.session_state.selected_track = selected_track_id
        end_and_clear_session()
        st.session_state.final_summary = ""
        if engine.graph_service:
            engine.graph_service.set_active_track(selected_track_id)
        switch_info = call_api_switch_lesson(selected_track_id, session_id="vlearn_default")
        new_concept = switch_info.get("concept", engine.get_current_feynman_concept(force_refresh=True))
        st.session_state.current_feynman_concept = new_concept
        st.session_state._last_cached_track = selected_track_id
        st.session_state.cached_progress = call_api_progress(selected_track_id)
        st.session_state._progress_track = selected_track_id
        lesson_title = lesson_map.get(selected_track_id, {}).get("title", selected_track_id)
        st.session_state.messages = []
        st.session_state.is_ended = False
        st.session_state.session_finished = False
        st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 1. New Chat & Finish Session controls
    col_sidebar_new, col_sidebar_finish = st.columns(2)
    with col_sidebar_new:
        if st.button("➕ Mới (Reset)", use_container_width=True):
            if engine.graph_service:
                engine.graph_service.reset_track_progress(st.session_state.selected_track)
            end_and_clear_session()
            st.session_state.final_summary = ""
            engine.concept_turns.clear()
            try:
                with httpx.Client(timeout=2.0) as client:
                    client.post(f"{BACKEND_URL}/api/reset", params={"session_id": "vlearn_default", "track": st.session_state.selected_track})
            except Exception:
                pass

            current_feynman_concept = engine.get_current_feynman_concept(force_refresh=True)
            st.session_state.current_feynman_concept = current_feynman_concept
            st.session_state._last_cached_track = st.session_state.selected_track
            st.session_state.cached_progress = call_api_progress(st.session_state.selected_track)
            st.session_state._progress_track = st.session_state.selected_track
            lesson_title = lesson_map.get(st.session_state.selected_track, {}).get("title", "")
            st.session_state.messages = []
            st.session_state.is_ended = False
            st.session_state.session_finished = False
            st.rerun()

    with col_sidebar_finish:
        if st.button("🏁 Kết thúc", use_container_width=True):
            end_and_clear_session()
            st.session_state.session_finished = True
            st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 2. FalkorDB Learning Progress Metrics (Cached)
    if "cached_progress" not in st.session_state or st.session_state.get("_progress_track") != st.session_state.selected_track:
        st.session_state.cached_progress = call_api_progress(st.session_state.selected_track)
        st.session_state._progress_track = st.session_state.selected_track
    progress_info = st.session_state.cached_progress
    percent = progress_info.get("percent", 0.0)
    covered = progress_info.get("covered", 0)
    total = progress_info.get("total", 0)

    st.markdown(f"""
    <div style="background:#212121; border:1px solid #333; border-radius:8px; padding:10px 12px; margin-bottom:14px;">
        <div style="display:flex; justify-content:space-between; font-size:12px; color:#aaa; margin-bottom:4px;">
            <span>Tiến độ bài học này</span>
            <span style="color:#10a37f; font-weight:600;">{percent}%</span>
        </div>
        <div style="background:#333; border-radius:4px; height:6px; overflow:hidden;">
            <div style="background:#10a37f; width:{percent}%; height:100%;"></div>
        </div>
        <div style="font-size:11px; color:#888; margin-top:4px;">Đã hoàn thành: {covered}/{total} nội dung trọng tâm</div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Lesson roadmap nodes
    st.markdown("<p style='font-size:11px; font-weight:600; color:#888; text-transform:uppercase; margin-bottom:6px;'>Lộ trình bài học</p>", unsafe_allow_html=True)
    nodes = progress_info.get("nodes", [])
    for node_item in nodes:
        icon = "✓" if node_item.get("status") == "COVERED" else "○"
        color = "#10a37f" if node_item.get("status") == "COVERED" else "#888888"
        name_trunc = node_item.get("name", "")[:28]
        st.markdown(f"<div style='font-size:12.5px; padding:4px 6px; color:{color}; border-radius:4px;'>{icon} {name_trunc}</div>", unsafe_allow_html=True)

    st.divider()

    # 4. View Mode toggle: Chat vs FalkorDB Graph
    st.markdown("<p style='font-size:11px; font-weight:600; color:#888; text-transform:uppercase; margin-bottom:6px;'>Chế độ hiển thị</p>", unsafe_allow_html=True)
    col_tab_chat, col_tab_graph = st.columns(2)
    with col_tab_chat:
        if st.button("💬 Chat", use_container_width=True):
            st.session_state.active_view = "chat"
            st.rerun()
    with col_tab_graph:
        if st.button("📊 Đồ thị", use_container_width=True):
            st.session_state.active_view = "graph"
            st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#1e1e1e; border:1px solid #333; border-radius:8px; padding:10px; margin-bottom:10px; font-size:11px; color:#aaa;">
        <strong style="color:#10a37f;">Phương pháp học:</strong> Bạn hiểu sâu kiến thức bằng cách tự mình giải thích và truyền đạt lại theo logic mạch lạc, có căn cứ rõ ràng.
    </div>
    <div style="display:flex; align-items:center; gap:8px; font-size:12px; color:#aaa;">
        <div style="width:28px; height:28px; border-radius:50%; background:#333; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:bold;">V</div>
        <div>
            <div style="color:#ececec; font-weight:500;">Vinh (Học viên)</div>
            <div style="font-size:10px; color:#777;">Học tập tương tác chủ động</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# KHÔNG GIAN CHÍNH (MAIN VIEW CHATGPT)
# ==========================================
# Lấy tiêu đề bài học hiển thị
current_lesson_title = lesson_map.get(st.session_state.selected_track, {}).get("title", st.session_state.selected_track)
if len(current_lesson_title) > 35:
    current_lesson_title = current_lesson_title[:32] + "..."

st.markdown(f"""
<div style="display:flex; justify-content:center; align-items:center; margin-top:-20px;">
    <div class="model-pill">
        <span class="model-dot"></span>
        <span>Alex · Trợ lý Học tập</span>
        <span style="color:#777; font-size:11px;">| {current_lesson_title} · {current_feynman_concept.get('name', 'Bài học')}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# VIEW 1: GIAO DIỆN CHAT CHÍNH
if st.session_state.active_view == "chat":
    # Nếu kết thúc session (Chủ động từ người dùng hoặc sau khi hoàn thành đồ thị)
    if st.session_state.session_finished:
        global_summary = st.session_state.get("final_summary") or engine.get_global_summary("vlearn_default")
        progress_info = call_api_progress(st.session_state.selected_track)
        percent = progress_info.get("percent", 0.0)
        covered = progress_info.get("covered", 0)
        total = progress_info.get("total", 0)

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #152720 0%, #1e1e1e 100%); border: 1px solid #10a37f; border-radius: 14px; padding: 24px; margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <span class="tag-badge tag-green" style="font-size:12px; padding:4px 10px;">🏁 PHIÊN HỌC ĐÃ HOÀN THÀNH</span>
                <span style="color:#aaa; font-size:12px;">Chế độ: <strong style="color:#10a37f;">Học tương tác chủ động</strong></span>
            </div>
            <h2 style="color:#10a37f; margin:0 0 8px 0; font-size:22px;">🎓 TỔNG KẾT NỘI DUNG BUỔI HỌC</h2>
            <p style="color:#ccc; font-size:14px; margin:0 0 14px 0; line-height:1.5;">
                Dưới đây là toàn bộ kiến thức trọng tâm được đúc kết từ quá trình bạn giải thích và làm rõ các cơ chế cùng Alex:
            </p>
            <div style="display:flex; gap:16px; font-size:13px; color:#aaa; flex-wrap:wrap;">
                <div>🎯 <strong>Nội dung hoàn thành:</strong> {covered}/{total} ({percent}%)</div>
                <div>⚡ <strong>Phương pháp:</strong> Học chủ động qua giải thích</div>
                <div>🛡️ <strong>Tiêu chí:</strong> Lập luận logic & Có căn cứ rõ ràng</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:14px; font-weight:600; color:#10a37f; margin-bottom:10px; text-transform:uppercase; letter-spacing:0.5px;">
            📝 Đúc kết nội dung buổi học:
        </div>
        """, unsafe_allow_html=True)

        if global_summary and global_summary.strip():
            st.markdown(f"""
            <div style="background:#1a1a1a; border:1px solid #2d4a3e; border-left:4px solid #10a37f; border-radius:8px; padding:18px 20px; margin-bottom:20px; line-height:1.8; font-size:14px; color:#f0fdf4; white-space:pre-line;">
{global_summary}
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📋 Xem & Sao chép định dạng Markdown đầy đủ"):
                st.code(global_summary, language="markdown")
        else:
            st.info("ℹ️ Chưa có lượt trao đổi nào được ghi nhận để tóm tắt trong phiên này. Bạn có thể nhấn 'Bắt đầu phiên học mới' bên dưới để trao đổi và dạy lại cho Alex.")

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("### 🛠️ Lựa chọn tiếp theo:")
        col_finish_new, col_finish_graph = st.columns(2)
        with col_finish_new:
            if st.button("🔄 Bắt đầu phiên học mới", use_container_width=True, type="primary"):
                engine.graph_service.reset_track_progress(st.session_state.selected_track)
                end_and_clear_session()
                st.session_state.final_summary = ""
                engine.concept_turns.clear()
                try:
                    with httpx.Client(timeout=2.0) as client:
                        client.post(f"{BACKEND_URL}/api/reset", params={"session_id": "vlearn_default", "track": st.session_state.selected_track})
                except Exception:
                    pass

                current_feynman_concept = engine.get_current_feynman_concept()
                lesson_title = lesson_map.get(st.session_state.selected_track, {}).get("title", "")
                st.session_state.messages = []
                st.session_state.is_ended = False
                st.session_state.session_finished = False
                st.rerun()

        with col_finish_graph:
            if st.button("📊 Xem Sơ đồ Lộ trình Kiến thức", use_container_width=True):
                st.session_state.active_view = "graph"
                st.rerun()

        st.stop()

    # Khung cuộn tin nhắn ChatGPT
    chat_box = st.container()
    intro_placeholder = None
    with chat_box:
        for msg in st.session_state.messages:
            role = msg["role"]
            avatar = "👤" if role == "user" else "🎓"
            with st.chat_message(role, avatar=avatar):
                # Nội dung kết quả rõ ràng, nổi bật nhất
                st.markdown(f"<div class='final-reply-text'>{msg['content']}</div>", unsafe_allow_html=True)

                if role == "assistant" and msg.get("event_label"):
                    tag_color = "tag-green" if "nhân quả" in msg.get("event_label", "") or "Đạt" in msg.get("event_label", "") else ("tag-red" if "nguyên văn" in msg.get("event_label", "") else "tag-orange")
                    st.markdown(f"""
                    <div style="display:flex; gap:6px; align-items:center; margin-top:8px;">
                        <span class="tag-badge {tag_color}">{msg.get('event_label')}</span>
                    </div>
                    """, unsafe_allow_html=True)

        if not st.session_state.messages:
            intro_placeholder = st.empty()

    # Hiển thị The End of Graph nếu chạm đích (khi đã đi qua hết các concept của bài học hiện tại)
    if st.session_state.is_ended:
        global_summary = engine.get_global_summary("vlearn_default")
        active_lesson_label = clean_lesson_title(lesson_map.get(st.session_state.selected_track, {}).get("title", st.session_state.selected_track))
        st.markdown(f"""
        <div class="end-of-graph-box">
            <h3 style="color:#10a37f; margin:0 0 6px 0;">🎉 CHÚC MỪNG BẠN ĐÃ LÀM CHỦ TOÀN BỘ BÀI HỌC!</h3>
            <p style="margin:0 0 10px 0; font-size:14px; color:#ececec;">
                Bạn đã hoàn thành xuất sắc toàn bộ các mắt xích kiến thức trong <strong>{active_lesson_label}</strong>.
            </p>
            <p style="margin:0 0 12px 0; font-size:13px; color:#b4b4b4;">
                Bằng cách giải thích và làm sáng tỏ cơ chế nhân quả cho Alex, bạn đã ghi nhớ sâu sắc các kiến thức nền tảng mà không bị nhầm lẫn hay chép vẹt.
            </p>
            <div style="background:#13261f; border:1px solid #10a37f88; border-radius:8px; padding:14px; margin:12px 0;">
                <div style="color:#10a37f; font-weight:600; font-size:13px; margin-bottom:8px;">
                    📋 TỔNG KẾT NỘI DUNG ĐÃ ĐẠT ĐƯỢC:
                </div>
                <div style="white-space:pre-line; color:#f0fdf4; font-size:13.5px; line-height:1.7;">
{global_summary if (global_summary and global_summary.strip()) else "• Đã hoàn thành và làm chủ toàn bộ chuỗi kiến thức trọng tâm của bài học."}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_option_finish, col_option_next = st.columns(2)
        with col_option_finish:
            if st.button("🏁 Hoàn thành buổi học & Xem tổng kết", use_container_width=True, type="primary"):
                end_and_clear_session()
                st.session_state.session_finished = True
                st.rerun()

        with col_option_next:
            st.markdown("**🌿 Khám phá các bài học & chuyên đề tiếp theo:**")
            other_lessons = [lesson for lesson in available_lessons if lesson["track"] != st.session_state.selected_track]
            if other_lessons:
                for other_lesson in other_lessons[:4]:
                    clean_other_title = clean_lesson_title(other_lesson["title"])
                    if st.button(f"👉 {clean_other_title}", key=f"end_opt_{other_lesson['track']}", use_container_width=True):
                        st.session_state.selected_track = other_lesson["track"]
                        end_and_clear_session()
                        st.session_state.final_summary = ""
                        switch_info = call_api_switch_lesson(other_lesson["track"], session_id="vlearn_default")
                        new_concept = switch_info.get("concept", engine.get_current_feynman_concept())
                        st.session_state.messages = []
                        st.session_state.is_ended = False
                        st.rerun()
            else:
                st.info("Bạn đã hoàn thành tất cả các bài học hiện có!")

    # Nhập liệu Chat Input (Ghim cố định ở đáy màn hình với Voice Recorder tách riêng)
    if not st.session_state.is_ended:
        student_input = None

        with st.bottom:
            with st.container(key="chatgpt_bottom_outer"):
                col_prompt_box, col_voice_box = st.columns([7.2, 2.8], vertical_alignment="center")

                current_prompt_key = f"user_prompt_{st.session_state.get('prompt_version', 0)}"
                if current_prompt_key not in st.session_state:
                    st.session_state[current_prompt_key] = ""

                with col_prompt_box:
                    with st.container(key="chatgpt_prompt_outer"):
                        col_text, col_send = st.columns([8.8, 1.2], vertical_alignment="center")
                        with col_text:
                            user_typed_prompt = st.text_area(
                                "Prompt",
                                placeholder="Nhắn tin cho Alex...",
                                label_visibility="collapsed",
                                key=current_prompt_key,
                                height=36
                            )
                        with col_send:
                            st.markdown('<div class="chatgpt-send-btn">', unsafe_allow_html=True)
                            send_submitted = st.button("↑", key="btn_send_prompt", help="Gửi tin nhắn")
                            st.markdown('</div>', unsafe_allow_html=True)

                voice_key = f"voice_input_{st.session_state.get('voice_key_idx', 0)}"
                with col_voice_box:
                    recorded_voice = st.audio_input(
                        "Voice",
                        key=voice_key,
                        label_visibility="collapsed"
                    )

                # Xử lý âm thanh thu âm từ Microphone
                if recorded_voice is not None:
                    audio_bytes = recorded_voice.getvalue()
                    if audio_bytes:
                        st.session_state.voice_key_idx = st.session_state.get("voice_key_idx", 0) + 1
                        with st.spinner("🎙️ Đang nhận diện giọng nói..."):
                            transcribed_text = transcribe_audio(audio_bytes)
                        if transcribed_text and transcribed_text.strip():
                            st.session_state.prompt_version = st.session_state.get("prompt_version", 0) + 1
                            new_prompt_key = f"user_prompt_{st.session_state.prompt_version}"
                            st.session_state[new_prompt_key] = transcribed_text.strip()
                            st.toast(f"✅ Đã nhận diện: {transcribed_text.strip()}", icon="✍️")
                            st.rerun()
                        else:
                            st.toast("⚠️ Không nhận diện được âm thanh. Hãy thử nói lại rõ ràng hơn.", icon="⚠️")
                            st.rerun()

                if send_submitted and user_typed_prompt.strip():
                    student_input = user_typed_prompt.strip()
                    st.session_state.prompt_version = st.session_state.get("prompt_version", 0) + 1
                    st.session_state[f"user_prompt_{st.session_state.prompt_version}"] = ""
                    st.session_state.voice_key_idx = st.session_state.get("voice_key_idx", 0) + 1

            st.markdown("<p style='text-align:center; font-size:11px; color:#666; margin:4px 0 0 0;'>VLearn — Nền tảng học tập tương tác chủ động.</p>", unsafe_allow_html=True)

        # Tải lời mở đầu & gợi ý từ backend sau khi toàn bộ UI đã được hiển thị xong
        if intro_placeholder is not None:
            with intro_placeholder.container():
                with st.chat_message("assistant", avatar="🎓"):
                    with st.spinner("⚡ Alex đang chuẩn bị các hướng gợi ý ôn tập..."):
                        init_msg = build_initial_topic_message(current_feynman_concept, current_lesson_title)
                    st.session_state.messages.append(init_msg)
                    st.markdown(f"<div class='final-reply-text'>{init_msg['content']}</div>", unsafe_allow_html=True)
                    tag_color = "tag-orange"
                    st.markdown(f"""
                    <div style="display:flex; gap:6px; align-items:center; margin-top:8px;">
                        <span class="tag-badge {tag_color}">{init_msg.get('event_label', 'Gợi ý chủ đề 🎓')}</span>
                    </div>
                    """, unsafe_allow_html=True)

        if student_input:
            user_msg = {
                "role": "user",
                "content": student_input,
                "time": datetime.now().strftime("%H:%M")
            }
            st.session_state.messages.append(user_msg)
            with st.chat_message("user", avatar="👤"):
                st.markdown(student_input)

            with st.chat_message("assistant", avatar="🎓"):
                status_placeholder = st.empty()
                response_placeholder = st.empty()
                tag_placeholder = st.empty()

                # Hiệu ứng Shimmer Typing Card sống động (không đơ cứng, không lộ reasoning)
                status_placeholder.markdown("""
                <div class="alex-thinking-card">
                    <div class="typing-dots">
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                    </div>
                    <span class="alex-thinking-text">Alex đang suy ngẫm câu trả lời...</span>
                </div>
                """, unsafe_allow_html=True)

                meta = {
                    "event_label": "Hỏi vặn về cơ chế",
                    "is_end": False
                }

                def stream_tokens():
                    first_token = True
                    is_parroting_case = False
                    eval_data = {}

                    for event in engine.process_student_message_stream(student_input, session_id="vlearn_default"):
                        if event["type"] == "thinking":
                            meta["event_label"] = event.get("event_label", "")
                            eval_data = event.get("evaluation", {})
                            meta["citation"] = event.get("citation", "[VLearn]")
                            meta["concept_name"] = event.get("concept_name", "")
                            if eval_data.get("is_cheating") or "nguyên văn" in meta["event_label"]:
                                is_parroting_case = True
                        elif event["type"] == "token":
                            if is_parroting_case:
                                # Bỏ qua token mẫu mặc định của engine, chuẩn bị stream từ LLM
                                continue
                            if first_token:
                                status_placeholder.empty()
                                first_token = False
                            yield event["chunk"]
                        elif event["type"] == "done":
                            meta["is_end"] = event.get("is_end_of_graph", False)

                    # Khi học viên nói máy móc / chép bài: Sinh câu hỏi Socratic bằng LLM!
                    if is_parroting_case:
                        status_placeholder.empty()
                        current_concept = st.session_state.get("current_feynman_concept", {})
                        core_truth = current_concept.get("core_truth", "")
                        concept_name = clean_lesson_title(meta.get("concept_name") or current_concept.get("name", ""))
                        citation = meta.get("citation", "[VLearn]")

                        llm_reply_chunks = []
                        for tok in generate_llm_parroting_stream(student_input, concept_name, citation, core_truth):
                            llm_reply_chunks.append(tok)
                            yield tok

                        full_reply = "".join(llm_reply_chunks)
                        engine.memory.set_last_question("vlearn_default", full_reply)

                streamed_reply = response_placeholder.write_stream(stream_tokens())
                status_placeholder.empty()

                tag_color = "tag-green" if "nhân quả" in meta["event_label"] or "Đạt" in meta["event_label"] else ("tag-red" if "nguyên văn" in meta["event_label"] else "tag-orange")
                tag_placeholder.markdown(f"""
                <div style="display:flex; gap:6px; align-items:center; margin-top:8px;">
                    <span class="tag-badge {tag_color}">{meta['event_label']}</span>
                </div>
                """, unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": streamed_reply,
                "event_label": meta["event_label"],
                "time": datetime.now().strftime("%H:%M")
            })
            if meta["is_end"]:
                st.session_state.is_ended = True

            current_progress = call_api_progress(st.session_state.selected_track)
            st.session_state.cached_progress = current_progress
            st.session_state.current_feynman_concept = engine.get_current_feynman_concept(force_refresh=True)
            if current_progress.get("is_end", False) and current_progress.get("total", 0) > 0:
                st.session_state.is_ended = True

            st.rerun()

    st.markdown("<p style='text-align:center; font-size:11.5px; color:#666; margin-top:10px;'>VLearn — Nền tảng học tập tương tác chủ động.</p>", unsafe_allow_html=True)


# =========================================================================
# VIEW 2: GIAO DIỆN BẢN ĐỒ ĐỒ THỊ TRI THỨC (FALKORDB GRAPH VISUALIZER)
# =========================================================================
elif st.session_state.active_view == "graph":
    col_header_title, col_header_back = st.columns([8, 2])
    with col_header_title:
        st.markdown("### 📊 Sơ Đồ Lộ Trình Kiến Thức Trực Quan")
        active_title = clean_lesson_title(lesson_map.get(st.session_state.selected_track, {}).get("title", st.session_state.selected_track))
        st.caption(f"Đang hiển thị đồ thị bài học: {active_title}. Kéo thả, phóng to/thu nhỏ và nhấp vào từng chủ đề để xem chi tiết.")
    with col_header_back:
        if st.button("💬 Quay lại Chat", use_container_width=True, type="primary"):
            st.session_state.active_view = "chat"
            st.rerun()

    # Lấy dữ liệu đồ thị từ FalkorDB theo track hiện tại
    graph_data = call_api_graph(st.session_state.selected_track)

    # Nhúng trực tiếp bản đồ mạng đồ thị Vis.js Network
    graph_html = generate_graph_html(graph_data, height="720px")
    if hasattr(st, "iframe"):
        st.iframe(graph_html, height=740)
    else:
        components.html(graph_html, height=740, scrolling=False)
