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

from backend.agent_engine import SocraticAgentEngine
from config.config import settings
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

    /* Gemini UI Thinking Pattern */
    .gemini-thinking-container {
        background: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        margin: 6px 0 14px 0;
        overflow: hidden;
        transition: all 0.25s ease;
    }
    .gemini-thinking-container:hover {
        border-color: rgba(255, 255, 255, 0.16);
        background: rgba(255, 255, 255, 0.035);
    }
    .gemini-thinking-summary {
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
    .gemini-thinking-summary:hover {
        color: #e5e7eb;
    }
    .gemini-thinking-body {
        padding: 12px 16px 14px 16px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        background: rgba(0, 0, 0, 0.25);
    }
    .gemini-phase-card {
        margin-bottom: 12px;
        padding-left: 12px;
        border-left: 2px solid #10a37f88;
    }
    .gemini-phase-card:last-child {
        margin-bottom: 0;
    }
    .gemini-phase-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
    }
    .gemini-phase-title {
        font-size: 12px;
        font-weight: 600;
        color: #6ee7b7;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .gemini-phase-badge {
        font-size: 10px;
        padding: 1px 6px;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.08);
        color: #94a3b8;
    }
    .gemini-phase-content {
        font-size: 12.5px;
        line-height: 1.6;
        color: #94a3b8;
        opacity: 0.72;
    }
    .gemini-final-text {
        font-size: 15px !important;
        line-height: 1.65 !important;
        color: #f8fafc !important;
        opacity: 1.0 !important;
        font-weight: 400 !important;
    }
</style>
""", unsafe_allow_html=True)


# Khởi tạo Engine
engine = SocraticAgentEngine()
st.session_state.engine = engine


def render_gemini_thinking_box(thinking_phases: list) -> str:
    """Render collapsible Gemini-style thinking container grouped by pedagogical phases."""
    if not thinking_phases:
        return ""

    phases_html = []
    for phase_item in thinking_phases:
        title = phase_item.get("phase_name", "Giai đoạn suy nghĩ")
        badge = phase_item.get("badge", "")
        badge_html = f"<span class='gemini-phase-badge'>{badge}</span>" if badge else ""

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
        <div class="gemini-phase-card">
            <div class="gemini-phase-header">
                <span class="gemini-phase-title">{title}</span>
                {badge_html}
            </div>
            <div class="gemini-phase-content">{content_html}</div>
        </div>
        """)

    all_phases = "".join(phases_html)
    return f"""
    <details class="gemini-thinking-container">
        <summary class="gemini-thinking-summary">
            <span>💭</span>
            <span>Xem quá trình suy nghĩ & thẩm định ({len(thinking_phases)} giai đoạn)</span>
        </summary>
        <div class="gemini-thinking-body">
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


# Track and lesson state initialization
if "selected_track" not in st.session_state:
    st.session_state.selected_track = settings.get_default_track()

engine.graph_service.set_active_track(st.session_state.selected_track)
current_feynman_concept = engine.get_current_feynman_concept()


def get_live_socratic_opening(concept_node: dict) -> str:
    """Generate or retrieve opening Socratic probe from lecture content without formulaic phrases."""
    raw_question = concept_node.get('learning_question') or concept_node.get('child_question') or ''
    if not raw_question or 'lại vận hành như vậy' in raw_question or 'Cơ chế cốt lõi' in raw_question or 'thách thức kỹ thuật lớn nhất khi giải quyết vấn đề' in raw_question or len(raw_question) < 15:
        return engine.generate_smart_opening_question(concept_node['name'], concept_node.get('quote', ''), concept_node.get('core_truth', ''))
    return raw_question


# Auto-clean legacy messages containing formulaic robotic phrases
if "messages" in st.session_state and st.session_state.messages:
    first_content = st.session_state.messages[0].get("content", "")
    if "lại vận hành như vậy" in first_content or "Cơ chế cốt lõi và nguyên nhân" in first_content or "thách thức kỹ thuật lớn nhất khi giải quyết vấn đề" in first_content:
        del st.session_state["messages"]


if "messages" not in st.session_state:
    opening_question = get_live_socratic_opening(current_feynman_concept)
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"Chào bạn, mình là Alex. Mình đang cùng bạn tìm hiểu về chủ đề **{current_feynman_concept['name']}** trên VLearn.\n\n"
                       f"Đọc qua bài giảng, mình có một thắc mắc về mặt kỹ thuật muốn hỏi bạn:\n"
                       f"> *\"{opening_question}\"*\n\n"
                       f"Theo bạn thì vấn đề này nên được tiếp cận và xử lý như thế nào?",
            "event_type": "probing",
            "citation": current_feynman_concept.get("citation", "[VLearn]"),
            "event_label": "Thắc mắc về cơ chế",
            "time": datetime.now().strftime("%H:%M")
        }
    ]


if "events" not in st.session_state:
    st.session_state.events = []

if "is_ended" not in st.session_state:
    st.session_state.is_ended = False

if "session_finished" not in st.session_state:
    st.session_state.session_finished = False

if "active_view" not in st.session_state:
    st.session_state.active_view = "chat"


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    # 0. Lesson selection preserving knowledge locality
    available_lessons = call_api_lessons()
    lesson_map = {lesson["track"]: lesson for lesson in available_lessons}
    track_keys = list(lesson_map.keys()) if lesson_map else [st.session_state.selected_track]

    current_idx = 0
    if st.session_state.selected_track in track_keys:
        current_idx = track_keys.index(st.session_state.selected_track)

    selected_track_id = st.selectbox(
        "📚 Chọn bài học ôn tập:",
        options=track_keys,
        index=current_idx,
        format_func=lambda k: lesson_map.get(k, {}).get("title", k),
        help="Đồ thị tri thức được cách ly độc lập theo từng bài giảng/slide để bảo toàn tính cục bộ."
    )

    if selected_track_id != st.session_state.selected_track:
        st.session_state.selected_track = selected_track_id
        switch_info = call_api_switch_lesson(selected_track_id, session_id="vlearn_default")
        new_concept = switch_info.get("concept", engine.get_current_feynman_concept())
        new_opening = switch_info.get("opening_question") or get_live_socratic_opening(new_concept)
        lesson_title = lesson_map.get(selected_track_id, {}).get("title", selected_track_id)
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": f"Chào bạn, mình là Alex. Chúng ta cùng bắt đầu ôn tập:\n**{lesson_title}** 🎓\n\n"
                           f"Bắt đầu với phần trọng tâm: **{new_concept['name']}**.\n\n"
                           f"Mình có một thắc mắc kỹ thuật muốn cùng bạn làm rõ:\n"
                           f"> *\"{new_opening}\"*\n\n"
                           f"Bạn phân tích và giải thích cơ chế giúp mình nhé!",
                "event_type": "probing",
                "citation": new_concept.get("citation", "[VLearn]"),
                "event_label": "Bắt đầu bài học mới",
                "time": datetime.now().strftime("%H:%M")
            }
        ]
        st.session_state.is_ended = False
        st.session_state.session_finished = False
        st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 1. New Chat & Finish Session controls
    col_sidebar_new, col_sidebar_finish = st.columns(2)
    with col_sidebar_new:
        if st.button("➕ Mới (Reset)", use_container_width=True):
            engine.graph_service.reset_track_progress(st.session_state.selected_track)
            engine.clear_session_history("vlearn_default")
            engine.concept_turns.clear()
            try:
                with httpx.Client(timeout=2.0) as client:
                    client.post(f"{BACKEND_URL}/api/reset", params={"session_id": "vlearn_default", "track": st.session_state.selected_track})
            except Exception:
                pass

            current_feynman_concept = engine.get_current_feynman_concept()
            opening_question = get_live_socratic_opening(current_feynman_concept)
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": f"Chào bạn, mình cùng bạn bắt đầu lại từ đầu về chủ đề **{current_feynman_concept['name']}**.\n\n"
                               f"> *\"{opening_question}\"*",
                    "event_type": "probing",
                    "citation": current_feynman_concept.get("citation", "[VLearn]"),
                    "event_label": "Bắt đầu lại lộ trình",
                    "time": datetime.now().strftime("%H:%M")
                }
            ]
            st.session_state.is_ended = False
            st.session_state.session_finished = False
            st.rerun()

    with col_sidebar_finish:
        if st.button("🏁 Kết thúc", use_container_width=True):
            st.session_state.session_finished = True
            st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 2. FalkorDB Learning Progress Metrics
    progress_info = call_api_progress(st.session_state.selected_track)
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
        <strong style="color:#10a37f;">Phương pháp Feynman:</strong> Bạn hiểu sâu kiến thức bằng cách tự mình giải thích và truyền đạt lại theo logic mạch lạc, có căn cứ rõ ràng.
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
        <span>Alex · Socratic Protégé (ChatNVIDIA)</span>
        <span style="color:#777; font-size:11px;">| {current_lesson_title} · {current_feynman_concept.get('name', 'Bài học')}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# VIEW 1: GIAO DIỆN CHAT CHÍNH
if st.session_state.active_view == "chat":
    # Nếu kết thúc session (Chủ động từ người dùng hoặc sau khi hoàn thành đồ thị)
    if st.session_state.session_finished:
        global_summary = engine.get_global_summary("vlearn_default")
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
                <div>⚡ <strong>Phương pháp:</strong> Học chủ động qua giải thích (Feynman)</div>
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
                engine.clear_session_history("vlearn_default")
                engine.concept_turns.clear()
                try:
                    with httpx.Client(timeout=2.0) as client:
                        client.post(f"{BACKEND_URL}/api/reset", params={"session_id": "vlearn_default", "track": st.session_state.selected_track})
                except Exception:
                    pass

                current_feynman_concept = engine.get_current_feynman_concept()
                opening_question = get_live_socratic_opening(current_feynman_concept)
                st.session_state.messages = [
                    {
                        "role": "assistant",
                        "content": f"Chào bạn, mình là **Alex**! Mình đang cùng bạn tìm hiểu phần **'{current_feynman_concept['name']}'** trên VLearn 🎓.\n\n"
                                   f"Có một thắc mắc cốt lõi về mặt cơ chế mà mình nghĩ mãi vẫn chưa thật sự thông suốt:\n"
                                   f"> *\"{opening_question}\"*\n\n"
                                   f"Bạn có thể phân tích nguyên nhân và giải thích cơ chế giúp mình được không?",
                        "event_type": "probing",
                        "citation": current_feynman_concept.get("citation", "[VLearn]"),
                        "event_label": "Thắc mắc về cơ chế 🔍",
                        "time": datetime.now().strftime("%H:%M")
                    }
                ]
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
    with chat_box:
        for msg in st.session_state.messages:
            role = msg["role"]
            avatar = "👤" if role == "user" else "🎓"
            with st.chat_message(role, avatar=avatar):
                # Khối Thinking kiểu Gemini UI: đóng mở được, opacity mờ hơn, chia theo phase
                if role == "assistant" and msg.get("thinking_phases"):
                    st.markdown(render_gemini_thinking_box(msg["thinking_phases"]), unsafe_allow_html=True)

                # Nội dung kết quả cuối cùng rõ ràng, nổi bật nhất (100% opacity)
                st.markdown(f"<div class='gemini-final-text'>{msg['content']}</div>", unsafe_allow_html=True)

                if role == "assistant" and msg.get("event_label"):
                    tag_color = "tag-green" if "nhân quả" in msg.get("event_label", "") or "Đạt" in msg.get("event_label", "") else ("tag-red" if "nguyên văn" in msg.get("event_label", "") else "tag-orange")
                    st.markdown(f"""
                    <div style="display:flex; gap:6px; align-items:center; margin-top:8px;">
                        <span class="tag-badge {tag_color}">{msg.get('event_label')}</span>
                    </div>
                    """, unsafe_allow_html=True)

    # Hiển thị The End of Graph nếu chạm đích (khi đã đi qua hết các concept của bài học hiện tại)
    if st.session_state.is_ended:
        global_summary = engine.get_global_summary("vlearn_default")
        active_lesson_label = lesson_map.get(st.session_state.selected_track, {}).get("title", st.session_state.selected_track)
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
                st.session_state.session_finished = True
                st.rerun()

        with col_option_next:
            st.markdown("**🌿 Khám phá các bài học & chuyên đề tiếp theo:**")
            other_lessons = [lesson for lesson in available_lessons if lesson["track"] != st.session_state.selected_track]
            if other_lessons:
                for other_lesson in other_lessons[:4]:
                    if st.button(f"👉 {other_lesson['title']}", key=f"end_opt_{other_lesson['track']}", use_container_width=True):
                        st.session_state.selected_track = other_lesson["track"]
                        switch_info = call_api_switch_lesson(other_lesson["track"], session_id="vlearn_default")
                        new_concept = switch_info.get("concept", engine.get_current_feynman_concept())
                        new_opening = switch_info.get("opening_question") or get_live_socratic_opening(new_concept)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Chào bạn, chúc mừng bạn đã hoàn thành bài học trước! Chúng ta cùng bước sang bài tiếp theo:\n**{other_lesson['title']}** 🚀\n\n"
                                       f"Vấn đề đầu tiên cần giải quyết:\n> *\"{new_opening}\"*\n\n"
                                       f"Theo bạn thì cơ chế này hoạt động ra sao?",
                            "event_type": "branch_activated",
                            "event_label": "Chủ đề mới 🌿",
                            "time": datetime.now().strftime("%H:%M")
                        })
                        st.session_state.is_ended = False
                        st.rerun()
            else:
                st.info("Bạn đã hoàn thành tất cả các bài học hiện có!")

    # Nhập liệu Chat Input kiểu ChatGPT
    if not st.session_state.is_ended:
        col_toolbar_empty, col_toolbar_finish = st.columns([7, 3])
        with col_toolbar_finish:
            if st.button("🏁 Kết thúc phiên & Xem tổng kết", use_container_width=True):
                st.session_state.session_finished = True
                st.rerun()

        student_input = st.chat_input("Giải thích rõ ràng bằng lập luận của bạn...")
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
                with st.spinner("⚡ Alex đang phân tích lập luận và đối chiếu tri thức..."):
                    response = call_api_chat(student_input)

                thinking_phases = response.get("thinking_phases", [])
                if thinking_phases:
                    st.markdown(render_gemini_thinking_box(thinking_phases), unsafe_allow_html=True)

                reply_text = response.get("agent_reply", "")
                st.markdown(f"<div class='gemini-final-text'>{reply_text}</div>", unsafe_allow_html=True)

                if response.get("event_label"):
                    tag_color = "tag-green" if "nhân quả" in response.get("event_label", "") or "Đạt" in response.get("event_label", "") else ("tag-red" if "nguyên văn" in response.get("event_label", "") else "tag-orange")
                    st.markdown(f"""
                    <div style="display:flex; gap:6px; align-items:center; margin-top:8px;">
                        <span class="tag-badge {tag_color}">{response.get('event_label')}</span>
                    </div>
                    """, unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": reply_text,
                "thinking_phases": thinking_phases,
                "event_label": response.get("event_label"),
                "time": datetime.now().strftime("%H:%M")
            })
            if response.get("is_end_of_graph", False):
                st.session_state.is_ended = True
            
            current_progress = call_api_progress(st.session_state.selected_track)
            if current_progress.get("is_end", False) and current_progress.get("total", 0) > 0:
                st.session_state.is_ended = True

            st.rerun()

    st.markdown("<p style='text-align:center; font-size:11.5px; color:#666; margin-top:10px;'>VLearn — Nền tảng học tập tương tác chủ động cùng AI.</p>", unsafe_allow_html=True)


# =========================================================================
# VIEW 2: GIAO DIỆN BẢN ĐỒ ĐỒ THỊ TRI THỨC (FALKORDB GRAPH VISUALIZER)
# =========================================================================
elif st.session_state.active_view == "graph":
    col_header_title, col_header_back = st.columns([8, 2])
    with col_header_title:
        st.markdown("### 📊 Sơ Đồ Lộ Trình Kiến Thức Trực Quan")
        active_title = lesson_map.get(st.session_state.selected_track, {}).get("title", st.session_state.selected_track)
        st.caption(f"Đang hiển thị đồ thị bài học: {active_title}. Kéo thả, phóng to/thu nhỏ và nhấp vào từng chủ đề để xem chi tiết.")
    with col_header_back:
        if st.button("💬 Quay lại Chat", use_container_width=True, type="primary"):
            st.session_state.active_view = "chat"
            st.rerun()

    # Lấy dữ liệu đồ thị từ FalkorDB theo track hiện tại
    graph_data = call_api_graph(st.session_state.selected_track)

    # Nhúng trực tiếp bản đồ mạng đồ thị Vis.js Network
    graph_html = generate_graph_html(graph_data, height="720px")
    components.html(graph_html, height=740, scrolling=False)
