# 🎓 VLearn Track D3 — Protégé Socratic Agent (Betty's Brain · Feynman Method)

> **Học bằng cách Dạy (Learning by Teaching / The Protégé Effect)**  
> Người học đóng vai trò người dạy kiến thức cho Agent học trò **"Alex"**. Alex sở hữu Persona ngây thơ có kiểm soát (*Controlled Naivety*) nhưng nắm giữ tri thức ẩn (*Hidden Grounding*) được bóc tách trực tiếp từ transcript và slide thực tế, liên tục hỏi vặn Socratic để bóc trần những chỗ chưa hiểu sâu, dùng thuật ngữ lấp liếm hoặc chép vẹt.

---

## 🌟 Tính Năng Nổi Bật & Kiến Trúc Kỹ Thuật

1. **Triệt tiêu 100% Dummy Data & Bias**:
   - Bóc tách dữ liệu trung gian **100% từ file thật**:
     - `data/vlearn-pack/transcript/*.md`: Quét toàn bộ các bài giảng thực tế, bóc tách cấu trúc `## Tiêu đề bài giảng` và mã trích dẫn `**[Txx-NNN]**`.
     - `codebase/db/input/*.pdf`: Thích ứng với bất kỳ file PDF nào được đưa vào, tự động phân chia các nhánh chuyên đề động và trích xuất tiêu đề slide trực tiếp.
   - Tuyệt đối không dùng kịch bản tĩnh, không dùng file JSON tự tạo, không dùng danh sách từ khóa lọc cứng.

2. **LLM-as-a-Judge với `with_structured_output()` & Pydantic**:
   - Sử dụng `langchain_google_genai` kết hợp Pydantic Schema `PedagogicalEvaluation` và hàm `with_structured_output()` trên duy nhất model `gemma-4-26b-a4b-it` (không fallback, kèm `ThinkingLevel.MINIMAL` và `max_output_tokens=1024`):
     - **Binary Classification** `is_parroting`: Phát hiện sao chép nguyên văn tài liệu/slide.
     - **Multi-label Classification** `unexplained_buzzwords`: Chỉ ra các thuật ngữ kỹ thuật bị lạm dụng để lấp liếm mà chưa làm rõ cơ chế.
     - **Binary Classification** `has_causal_reasoning`: Đánh giá lập luận chuỗi nguyên nhân - kết quả ("tại sao", "cơ chế vì sao").
     - **Binary Classification** `is_mastered`: Quyết định mở khóa đồ thị khi người học chứng minh được sự thấu suốt bản chất theo chuẩn Feynman.

3. **Bộ nhớ Hội thoại 2 Dạng (Dual-Form Conversation Memory)**:
   - **Dạng 1 (Sliding Window)**: Lưu và duy trì **6 lượt Ask - Answer gần nhất** để Agent kế thừa ngữ cảnh hội thoại mượt mà, không hỏi lặp lại.
   - **Dạng 2 (Global Incremental Summarization - Append-only)**: Với mỗi lượt hỏi đáp mới, AI tự động tóm tắt đúng **1 câu ngắn duy nhất** mô tả mấu chốt của lượt đó và append vào chuỗi tóm tắt toàn cục của phiên học.

4. **Đồ thị Tri thức Đa nhánh trên FalkorDB**:
   - Quản lý tiến trình học tập theo đồ thị tri thức mạng Graph (Cypher query).
   - Khi hoàn thành nhánh nền tảng (The End of Graph), mở ra các nhánh rẽ chuyên đề mới (`ALTERNATIVE_PATH` / `DEEP_DIVE_INTO`).

5. **Giao diện Trải nghiệm ChatGPT Dark Mode Cao Cấp**:
   - Frontend Streamlit phong cách ChatGPT hiện đại.
   - Tích hợp biểu đồ tiến độ Graph thời gian thực, bảng kiểm soát bộ nhớ Ask - Answer và tóm tắt tiến trình toàn cục trong Sidebar.

---

## 🏗️ Cấu Trúc Thư Mục (Codebase Structure)

```text
codebase/
├── run_all.py                  # Script 1-click khởi động cả FastAPI Backend & Streamlit
├── pyproject.toml              # Quản lý dependencies qua uv
├── .env                        # Biến môi trường (GEMINI_API_KEY, FALKOR_HOST, v.v.)
│
├── ui/
│   ├── app.py                  # Frontend Streamlit (Giao diện ChatGPT Dark Mode)
│   ├── visualize_graph.py      # Bộ visualizer đồ thị FalkorDB Browser Star-cluster
│   └── index.html              # Template giao diện đồ thị FalkorDB
│
├── backend/
│   ├── main.py                 # FastAPI Backend REST API
│   ├── agent_engine.py         # Socratic Protégé Agent Engine (Track D3 Core)
│   ├── guardrails.py           # LLM-as-a-Judge với LangChain with_structured_output()
│   ├── memory.py               # Dual-Form Conversation Memory (Sliding Window + Global Summary)
│   ├── prompt.py               # Persona Alex (Socratic Peer Learner) súc tích, không emoji
│   └── google_genai_client.py  # Client chính thức kết nối google-genai SDK
│
├── db/
│   ├── data_loader.py          # Bóc tách 100% dữ liệu thực tế từ transcript & PDF
│   ├── build_graph.py          # Nạp Đồ thị Tri thức đa nhánh hoàn chỉnh vào FalkorDB
│   ├── ingest_feynman_pack.py  # Script tích hợp Primary Track vào FalkorDB
│   ├── graph_service.py        # Cypher query service quản lý tiến độ và traversal
│   ├── chat_history.json       # Persistent storage cho bộ nhớ hội thoại
│   └── input/                  # Thư mục chứa file PDF bài giảng (người dùng tự nạp)
│       └── *.pdf
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Hệ Thống Từ A Đến Z

### Bước 1: Cài đặt Package Manager `uv`

`uv` là công cụ quản lý package và môi trường Python hiện đại, tốc độ cực nhanh:

- **Trên Windows (PowerShell)**:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Trên macOS / Linux**:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Kiểm tra cài đặt**:
  ```bash
  uv --version
  ```

---

### Bước 2: Chuẩn Bị File Môi Trường `.env`

Di chuyển vào thư mục `codebase/` và tạo file `.env` (nếu chưa có):
```bash
cd codebase
```

Tạo file `.env` với nội dung sau:
```env
# Google GenAI / Gemini API Key
GEMINI_API_KEY=AIzaSy...your_gemini_api_key...

# Cấu hình FalkorDB
FALKOR_HOST=localhost
FALKOR_PORT=6379
GRAPH_NAME=VLearn_Knowledge_Graph

# Cấu hình Backend URL
BACKEND_URL=http://localhost:8000
```

---

### Bước 3: Cài Đặt Dependencies Tự Động Qua `uv`

Chỉ cần chạy lệnh sau trong thư mục `codebase/`, `uv` sẽ tự động tạo virtual environment và cài đặt đầy đủ các thư viện (`fastapi`, `streamlit`, `falkordb`, `langchain-google-genai`, `google-genai`, `pymupdf`, v.v.):

```bash
uv sync
```

---

### Bước 4: Khởi Động FalkorDB Docker Container

Hệ thống sử dụng **FalkorDB** để quản lý Đồ thị Tri thức. Hãy mở Docker Desktop và chạy container:

```bash
docker run -p 6379:6379 -d --name falkordb-learning falkordb/falkordb:latest
```

*Kiểm tra container đang chạy:*
```bash
docker ps
```

---

### Bước 5: Nạp Đồ Thị Tri Thức Từ Dữ Liệu Thực Tế

Chạy script nạp đồ thị để bóc tách dữ liệu từ `data/vlearn-pack/transcript/*.md` và `codebase/db/input/*.pdf` vào FalkorDB:

```bash
uv run python db/build_graph.py
```

*Kết quả mong đợi trên màn hình console:*
```text
🗑️ Đã làm sạch graph: 'VLearn_Knowledge_Graph'
🚀 Bắt đầu nạp toàn bộ dữ liệu thực tế vào FalkorDB...
✅ Đã trích xuất thành công 8 khái niệm mục tiêu từ transcript thực tế.
📄 Đang đọc file PDF thực tế: fsdl-2022-lecture2-development-infrastructure-and-tooling.pdf...
📊 Đã trích lọc 3 khái niệm chuyên đề từ 127 slide thực tế.
🎉 Nạp dữ liệu thực tế vào FalkorDB hoàn tất 100%!
```

---

### Bước 6: Khởi Chạy Toàn Bộ Hệ Thống với 1 Lệnh Duy Nhất

Chỉ cần thực thi script `run_all.py`, hệ thống sẽ đồng thời khởi động cả **FastAPI Backend (port 8000)** và **Streamlit Frontend (port 8501)**:

```bash
uv run python run_all.py
```

*Console sẽ hiển thị:*
```text
=================================================================
🚀 KHỞI ĐỘNG HỆ THỐNG VLEARN TRACK D3 (FALKORDB + FASTAPI + STREAMLIT)
=================================================================
📦 1. Kiểm tra FalkorDB (port 6379)...
   ✅ FalkorDB Docker container đang hoạt động bình thường!

⚡ 2. Khởi động FastAPI Backend tại http://localhost:8000 ...

🖥️ 3. Khởi động Streamlit Frontend tại http://localhost:8501 ...

🎉 HỆ THỐNG ĐÃ SẴN SÀNG:
👉 Streamlit UI : http://localhost:8501
👉 FastAPI Docs : http://localhost:8000/docs
👉 Nhấn Ctrl+C để dừng toàn bộ hệ thống.
```

---

### Bước 7: Trải Nghiệm Trên Trình Duyệt

Mở trình duyệt tại:
- **Giao diện Học tập Feynman**: [http://localhost:8501](http://localhost:8501)
- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🎯 Kịch Bản Trải Nghiệm Sư Phạm (Feynman Test Cases)

| Hành vi của Học viên | Câu nói ví dụ | Phản hồi của Agent Alex | Nhãn Sư phạm |
|---|---|---|---|
| **1. Dùng Buzzword thiếu căn cứ** | *"Mô hình áp dụng softmax, multi-head attention và backpropagation để tính toán."* | Alex ghi nhận thuật ngữ nhưng hỏi vặn: *"Cụ thể cơ chế bên dưới mô hình thực sự tính toán điều gì để dẫn đến hiện tượng này?"* | `Dùng thuật ngữ nhưng thiếu căn cứ ❓` |
| **2. Chép vẹt nguyên văn tài liệu** | Dán nguyên văn đoạn trích dẫn từ transcript/slide. | Alex lịch sự phát hiện và yêu cầu: *"Đoạn này nghe giống trích dẫn tài liệu quá, bạn có thể tự diễn giải lại bằng cách hiểu của riêng bạn không?"* | `Phát hiện chép nguyên văn tài liệu 🚨` |
| **3. Giải thích nhân quả chuẩn Feynman** | Phân tích rõ nguyên nhân, cơ chế và mối liên hệ logic (tại sao hiện tượng xảy ra). | Alex reo lên vui mừng vì đã thông suốt, tự tóm tắt lại 1 câu nhân quả cốt lõi vừa học được, và chuyển sang thắc mắc về mắt xích tiếp theo. | `Lập luận nhân quả chặt chẽ ✓` |

---

## 🛠️ API Endpoints Chính (FastAPI)

- `POST /api/chat`: Nhận lời giải thích của học viên, kích hoạt LLM-as-a-Judge, cập nhật Graph & Dual-Form Memory, trả về câu hỏi Socratic.
- `GET /api/history`: Lấy lịch sử 6 lượt gần nhất và chuỗi Global Summary của session.
- `GET /api/progress`: Lấy tỷ lệ hoàn thành đồ thị thời gian thực từ FalkorDB.
- `GET /api/graph`: Xuất danh sách Nodes và Links để hiển thị đồ thị mạng.
- `POST /api/choose_branch`: Lựa chọn nhánh rẽ mới sau khi hoàn thành The End of Graph.
- `POST /api/reset`: Đặt lại tiến độ học và bộ nhớ hội thoại về 0.
