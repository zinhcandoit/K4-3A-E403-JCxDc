# Reflection Cá Nhân

- **Họ và tên:** Thiều Quang Vinh
- **Mã học viên:** 2A202602877
- **Lớp:** 3A · **Phòng:** E403 · **Nhóm:** JCxDc

---

### 1. Vai trò
AI Engineer và Technical Leader.

### 2. Phần việc đã làm
- Thiết kế kiến trúc sơ đồ bài học và cơ chế lưu trữ lịch sử tương tác nhiều lượt.
- Tích hợp và tối ưu hóa lời gọi API mô hình để kiểm soát độ trễ của phiên trò chuyện.
- Xây dựng các tầng Guardrail kỹ thuật nhằm kiểm soát đầu ra của mô hình và bám sát tài liệu bài giảng.

### 3. AI hỗ trợ thế nào
- Dùng AI hỗ trợ viết các hàm kết nối và cấu trúc dữ liệu JSON lưu trữ trạng thái bài học.
- Dùng AI để phân tích và tối ưu hóa cấu trúc prompt giúp giảm lượng token tiêu thụ.

### 4. Bài học từ case fail của nhóm
Ở lượt chạy đầu tiên với 20 case, tỷ lệ đạt chỉ có 15% vì câu trả lời của Alex bị đứt đoạn giữa chừng do cấu hình max tokens quá thấp. Sang lượt hai, dù đã sửa độ dài thì lại vướng lỗi mô hình tự biên tự diễn giải thích sai một số chi tiết kỹ thuật ở case TC13. Bài học rút ra là xây dựng sản phẩm AI không chỉ dựa vào việc gọi API thành công, mà phải kiểm soát chặt chẽ cả tham số sinh mẫu và kiểm chứng độ chính xác factual trước khi đưa kết quả tới người dùng.
