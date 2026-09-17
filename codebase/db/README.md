# Module Database & Đồ Thị Tri Thức (FalkorDB) — Track D3

Thư mục này chịu trách nhiệm:
1. Đọc slide bài giảng định dạng PDF trong thư mục `input/` bằng `PyMuPDF`.
2. Trích xuất các khái niệm (`Concept`), thứ tự phụ thuộc (`[:PREREQUISITE_FOR]`) và các bẫy hiểu sai (`Misconception`).
3. Nạp và quản lý dữ liệu trên **FalkorDB** (Graph Database chạy trên Docker).
4. Cung cấp API theo dõi tiến độ học tập và xác định thời điểm chạm **"The End of Graph"** (học viên đã giải thích bao phủ 100% đồ thị).

---

## 📁 Cấu trúc thư mục

```
codebase/db/
├── input/                  ← Nơi đặt file Slide PDF đầu vào (vd: fsdl-2022-lecture2...pdf)
├── build_graph.py          ← Script đọc PDF và nạp đồ thị vào FalkorDB
├── graph_service.py        ← Service cung cấp API truy vấn tiến độ, câu hỏi hỏi ngược, và check End of Graph
└── README.md               ← Tài liệu hướng dẫn này
```

---

## 🚀 Hướng dẫn chạy

### 1. Đảm bảo FalkorDB Docker container đang chạy
```powershell
docker ps
# Nếu chưa chạy:
docker run -p 6379:6379 -d --name falkordb-learning falkordb/falkordb:latest
```

### 2. Xây dựng đồ thị từ PDF
Đặt file PDF vào `codebase/db/input/` rồi chạy:
```powershell
cd codebase
uv run python db/build_graph.py
```

### 3. Kiểm tra API dịch vụ (Graph Service)
```powershell
uv run python db/graph_service.py
```

---

## 🎯 Cách hoạt động với Agent D3

* **Hỏi ngược (Socratic Probing):** Khi học sinh giải thích bài, Agent gọi `service.get_next_probing_target()` để biết concept nào chưa được giải thích (`status: 'UNCOVERED'`) và lấy câu hỏi vặn kèm bẫy nhận thức (`probe_question`).
* **Cập nhật tiến độ:** Khi học sinh bổ sung câu trả lời đúng, gọi `service.mark_concept_covered(concept_id)`.
* **The End of Graph:** Hàm `service.is_end_of_graph()` trả về `True` khi toàn bộ các Node trong đồ thị chuyển sang `COVERED`, kích hoạt lời khen và kết thúc phiên học theo phương pháp Feynman!
