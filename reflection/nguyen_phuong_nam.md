# Reflection Cá Nhân

- **Họ và tên:** Nguyễn Phương Nam
- **Mã học viên:** 2A202602869
- **Lớp:** 3A · **Phòng:** E403 · **Nhóm:** JCxDc

---

### 1. Vai trò
Software Engineer và Prompt Engineer.

### 2. Phần việc đã làm
- Xây dựng luồng xử lý API backend và giao diện ứng dụng trên Streamlit.
- Thiết kế hệ thống System Prompt và quy tắc đóng vai Protégé cho Alex.
- Xây dựng bộ golden set gồm 20 kịch bản kiểm thử phủ đủ 4 lớp chỗ khó và chạy đánh giá tự động bằng LLM-as-a-Judge.

### 3. AI hỗ trợ thế nào
- Dùng AI để sinh nhanh các trường hợp thử nghiệm biên và sinh mã nguồn các hàm tiền xử lý văn bản.
- Dùng mô hình ngôn ngữ lớn làm giám khảo tự động để chấm 20 test case theo 3 chiều chất lượng.

### 4. Bài học từ case fail của nhóm
Ở lượt kiểm thử thứ hai, nhóm chỉ đạt 11 trên 20 case vì Alex liên tục trượt vai, tự động giải thích luôn kiến thức về Transformer thay vì chỉ hỏi Socratic như thiết kế. Tôi nhận ra LLM có xu hướng tự nhiên là thích làm gia sư giảng giải. Nếu prompt chỉ nói hãy là bạn học mà không kèm theo các câu lệnh cấm tuyệt đối việc đưa ra câu trả lời trực tiếp thì mô hình sẽ luôn vô tình vi phạm nguyên tắc sư phạm cốt lõi.
