import os
import sys
import json
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from config.config import settings
from backend.agent_engine import SocraticAgentEngine
from backend.voice_model import transcribe_audio

app = FastAPI(
    title="VLearn Track D3 Socratic Engine",
    description="Backend FastAPI điều phối Agent học trò Socratic (Feynman Method) kết nối FalkorDB",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = SocraticAgentEngine()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_session"


class BranchRequest(BaseModel):
    track_id: str


class SwitchLessonRequest(BaseModel):
    track_id: str
    session_id: Optional[str] = "default_session"


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "VLearn Track D3 Socratic Engine (ChatNVIDIA)",
        "model": settings.NVIDIA_MODEL,
        "active_track": engine.graph_service.current_track,
        "endpoints": ["/api/lessons", "/api/switch_lesson", "/api/chat", "/api/history", "/api/progress", "/api/graph", "/api/reset"]
    }


@app.websocket("/")
@app.websocket("/ws")
async def websocket_root_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint hỗ trợ kết nối realtime/healthcheck cho các client
    hoặc browser extension kết nối tới root WebSocket mà không bị lỗi 403.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({
                "status": "online",
                "service": "VLearn Track D3 Socratic Engine",
                "received": data
            }, ensure_ascii=False))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


@app.get("/api/lessons")
def get_lessons():
    """Retrieve available lessons list with current learning progress for each lesson."""
    lessons = settings.get_available_lessons()
    for lesson in lessons:
        progress_info = engine.graph_service.get_progress(track=lesson["track"])
        lesson["progress"] = progress_info
    return {"lessons": lessons, "active_track": engine.graph_service.current_track}


@app.post("/api/switch_lesson")
def switch_lesson_endpoint(request: SwitchLessonRequest):
    """Switch the currently active lesson track in the knowledge graph."""
    session_id = request.session_id or "default_session"
    switch_result = engine.switch_lesson(track_id=request.track_id, session_id=session_id)
    return switch_result


@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    """Process student message: evaluate comprehension, query graph, and formulate Socratic response."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Tin nhắn không được để trống")
    
    session_id = request.session_id or "default_session"
    result = engine.process_student_message(request.message, session_id=session_id)
    return result


@app.post("/api/chat_stream")
def chat_stream_endpoint(request: ChatRequest):
    """
    Streaming endpoint trả về luồng sự kiện (SSE / Server-Sent Events):
    - Khối Thinking & Giám định sư phạm (type: 'thinking')
    - Từng token văn bản sinh ra theo thời gian thực (type: 'token')
    - Tổng kết lượt tương tác và đồng bộ đồ thị (type: 'done')
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Tin nhắn không được để trống")

    session_id = request.session_id or "default_session"

    def event_stream():
        for event in engine.process_student_message_stream(request.message, session_id=session_id):
            payload = json.dumps(event, ensure_ascii=False)
            yield f"data: {payload}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/history")
def get_chat_history(session_id: str = "default_session"):
    """Retrieve conversation history and two-tiered memory (recent turns and global summary)."""
    return {
        "session_id": session_id,
        "history": engine.get_session_history(session_id),
        "recent_turns": engine.get_recent_memory(session_id, limit=6),
        "global_summary": engine.get_global_summary(session_id)
    }


@app.get("/api/progress")
def get_progress(track: Optional[str] = None):
    """Retrieve graph coverage progress for active or specified track."""
    return engine.graph_service.get_progress(track=track)


@app.get("/api/graph")
def get_graph_data(track: Optional[str] = None):
    """Retrieve nodes and edges formatted for network graph visualization."""
    return engine.graph_service.export_graph_for_ui(track=track)


@app.post("/api/choose_branch")
def choose_branch_endpoint(request: BranchRequest):
    """Handle switching to an alternative pedagogical path upon reaching graph completion."""
    return engine.choose_alternative_path(request.track_id)


@app.post("/api/reset")
def reset_progress(session_id: str = "default_session", track: Optional[str] = None):
    """Reset graph node states and clear conversation history."""
    if track:
        engine.graph_service.reset_track_progress(track)
    else:
        engine.graph_service.reset_all_progress()
    engine.clear_session_history(session_id)
    return {"status": "success", "message": "Đã đặt lại tiến độ đồ thị và bộ nhớ hội thoại"}


@app.post("/api/transcribe")
async def transcribe_endpoint(request: Request):
    """Transcribe audio with NVIDIA Riva ASR."""
    try:
        audio_bytes = await request.body()
        if not audio_bytes:
            print("⚠️ [FastAPI /api/transcribe] Dữ liệu âm thanh rỗng")
            return {"status": "error", "text": "", "detail": "Empty audio data"}
        print(f"🎙️ [FastAPI /api/transcribe] Đang xử lý {len(audio_bytes)} bytes audio từ trình duyệt...")
        text = transcribe_audio(audio_bytes)
        print(f"✅ [FastAPI /api/transcribe] Kết quả ASR: '{text}'")
        return {"status": "success", "text": text}
    except Exception as e:
        print(f"❌ [FastAPI /api/transcribe] Lỗi: {e}")
        return {"status": "error", "text": "", "detail": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
