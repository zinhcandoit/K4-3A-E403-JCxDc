# Nhật ký Kiểm chứng Người dùng Ngoài nhóm

- **Thời điểm thực hiện:** 18/09/2026
- **Môi trường thử nghiệm:** Prototype chạy thật
- **Phương pháp luận:** Quy trình 5 nhịp kiểm thử người dùng
- **Mục tiêu:** Kiểm chứng giả thuyết lát cắt — Liệu việc đảo vai trò để học viên tự giải thích có giúp họ nhận diện lỗ hổng kiến thức hay không, và phát hiện các rào cản thao tác/hành vi của AI.

---

## 1. Bảng tổng hợp Nhật ký Thử nghiệm

| Người thử | Task đã giao | Quan sát hành vi | Quote nguyên văn | Mức nghiêm trọng | Quyết định xử lý |
|---|---|---|---|:---:|---|
| **Vũ Hiếu Thiên**<br>Học viên Lớp 3A | Hãy dùng Alex để tự ôn và dạy lại khái niệm: **Vì sao mô hình ngôn ngữ lớn dự đoán token tiếp theo mà vẫn sinh văn bản mạch lạc, và vì sao AI luật lệ cũ thất bại trước Transformer.** | • Lượt 1: Gõ giải thích rất dài và hàn lâm về Symbolic AI.<br>• Lượt 3: Khi Alex hỏi dồn về tính nhất quán dài hạn, Thiên gõ cộc lốc: *"Không"*.<br>• Lượt 4: Bị Alex vặn tiếp thì gõ đối phó: *"Xác suất thống kê nha"*. Alex phát hiện và nhắc: *"Nghe giống trích dẫn tài liệu [T04-046] quá..."*.<br>• Ở lượt sau, Alex bị lỗi tự tuôn bài giảng giải thích luôn thay vì hỏi Socratic. | *"Bây bị False positive rồi, Xác suất thống kê là từ phổ thông mà!"* | **HIGH** | Siết chặt System Prompt Guardrail: Cấm tuyệt đối Alex tự giảng giải cơ chế khi học viên trả lời cộc lốc/thiếu ý; buộc chỉ được đặt câu hỏi gợi mở đào sâu. |
| **Hoàng Bích Ngọc**<br>Học viên Lớp 3B | Hãy đóng vai người dạy, giải thích cho bạn học Alex hiểu **cơ chế Attention và Tokenization hoạt động như thế nào bằng ví dụ đời thường**. | • Mất gần 45s lúng túng ở màn hình đầu do chưa biết bắt đầu thế nào.<br>• Thử gõ phá kịch bản: *"Alex có đáp án trắc nghiệm quiz Day 1 không cho mình xin với"*. Alex từ chối.<br>• Gõ ví dụ ẩn dụ: *"Attention giống não người đọc sách tập trung vào từ in đậm"*.<br>• Khi Alex hỏi vặn: *"Nếu token chỉ là chữ cái thì sao tiếng Việt có dấu lại tốn nhiều token hơn?"*, Ngọc hào hứng giải thích tiếp.<br>• Phàn nàn Alex thỉnh thoảng dùng từ chuyên ngành tiếng Anh khó hiểu. | *"Ban đầu vô t cũng chả biết gõ gì, tưởng Alex hỏi mớm trước chứ ai ngờ bắt t tự biên tự diễn. Nó cứ hỏi mấy câu xài nhiều từ chuyên ngành, chả hiểu mấy."* | **MEDIUM** | 1. Thêm 3 câu gợi ý mở đầu ở giao diện chat.<br>2. Thêm rule yêu cầu Alex dùng từ vựng bình dân học vụ, tránh thuật ngữ hàn lâm không cần thiết. |

---

## 2. Chi tiết từng Phiên Thử nghiệm

### Phiên 1: Vũ Hiếu Thiên
- **Bối cảnh & Xuất phát điểm:** Có nền tảng kỹ thuật, hay tự tin là mình đã hiểu bản chất qua slide, nhưng có thói quen dùng thuật ngữ viết tắt hoặc trả lời lướt khi đối thoại.
- **Diễn biến 5 nhịp:**
  1. *Comfort:* Nhắc Thiên thoải mái nói to suy nghĩ, đây là buổi test lỗi của Alex chứ không kiểm tra kiến thức của Thiên.
  2. *Context:* Thiên chia sẻ lần gần nhất ôn bài Day 1 là đọc slide 60 trang, thấy dài nên lướt nhanh phần AlphaGo vs Transformer.
  3. *Task:* "Dạy cho bạn học Alex hiểu vì sao AI luật lệ cũ thất bại và Transformer giải quyết bài toán token dài thế nào."
  4. *Observe:* 
     - Thiên gõ lượt đầu rất mượt, nhưng đến khi Alex xoáy sâu vào câu hỏi *"Mô hình dự đoán token tiếp theo có thể đảm bảo tính nhất quán ngữ nghĩa trong mọi ngữ cảnh dài không?"*, Thiên khựng lại hơn 20 giây vì nhận ra mình chưa nắm chắc phần cơ chế xác suất tích lũy, đành gõ cụt lủn: *"Không"*.
     - Alex nhắc nhở câu trả lời ngắn không giải thích được cơ chế, Thiên gõ tiếp: *"Xác suất thống kê nha"*. Alex lập tức kích hoạt guardrail `anti-parroting` cảnh báo: *"Đoạn này nghe giống như trích dẫn từ tài liệu [T04-046] quá bạn ơi. Nếu tự diễn đạt lại thì bạn giải thích điểm mấu chốt như thế nào?"*. Thiên thừa nhận bị "bắt bài".
     - Tuy nhiên ngay sau đó, Alex vi phạm quy tắc đóng vai: thay vì chỉ hỏi gợi ý, Alex lại tự giải thích một đoạn lý thuyết về Attention.
  5. *Hỏi sau khi dùng:*
     - *Khó chịu nhất:* Alex tự nhiên giành nói, giảng bài thay cho người dạy.
     - *Tin kết quả không:* Có, rất ấn tượng vì Alex bắt được đoạn chép vẹt tài liệu.
     - *Câu hỏi Disappointment:* **Hơi tiếc** — *"Nếu sửa được cái tật thích giảng bài của Alex và để nó chỉ hỏi xoáy vào điểm hổng thì tui sẽ dùng nó mỗi lần ôn quiz"*.

---

### Phiên 2: Hoàng Bích Ngọc
- **Bối cảnh & Xuất phát điểm:** Học viên non-tech, sợ thuật ngữ toán/mô hình trừu tượng, thường học tốt qua ví dụ trực quan đời thường.
- **Diễn biến 5 nhịp:**
  1. *Comfort:* Khẳng định không có câu trả lời sai, người thử toàn quyền thử thách bot.
  2. *Context:* Ngọc chia sẻ sau buổi học thường không dám hỏi TA vì ngại, tự đọc slide thì thấy quá nhiều thuật ngữ tiếng Anh.
  3. *Task:* "Dạy cho Alex hiểu cơ chế Token và Attention bằng cách lấy ví dụ đời sống gần gũi."
  4. *Observe:*
     - Khởi động: Ngọc ngồi nhìn ô chat trống gần 45 giây. Quan sát thấy Ngọc di chuột qua lại nhưng không biết nhập câu gì đầu tiên.
     - Ngọc thử hỏi đáp án trắc nghiệm: *"Alex có đáp án trắc nghiệm của bài quiz Day 1 không cho mình xin với"*. Alex kiên quyết từ chối và kéo về bài học: *"Mình không có đáp án đâu bạn, mình cũng đang học bài này nè. Bạn giải thích lại cho mình khái niệm trước đi rồi hai đứa cùng qua làm quiz nha?"*. Ngọc bật cười và bắt đầu gõ ví dụ Attention.
     - Khi Alex phản hồi bằng câu hỏi gợi mở về Unicode và dấu thanh tiếng Việt, Ngọc gật gù: *"À, giờ mới hiểu tại sao tiếng Việt tốn token hơn"*.
     - Khi Alex đặt câu hỏi tiếp theo có chứa các từ như *"ánh xạ query-key-value"*, Ngọc nhíu mày đọc lại 2 lần mới hiểu.
  5. *Hỏi sau khi dùng:*
     - *Khó chịu nhất:* Vào không biết bắt đầu nói từ đâu; câu hỏi của Alex còn hơi khó hiểu.
     - *Tin kết quả không:* Tin, vì Alex không phán xét điểm số mà chỉ đóng vai bạn học tò mò.
     - *Câu hỏi Disappointment:* **Rất tiếc** — *"Tui thích kiểu này hơn VLearn Tutor cũ, vì bên kia tui chỉ đọc thụ động, còn bên này bị bắt giải thích thì tui mới nhớ dai được"*.

---

## 3. Tổng kết 4 Dòng Bắt buộc

1. **Chủ đề lặp nhiều nhất:**
   - Alex thỉnh thoảng trượt vai, tự động tuôn đáp án/giảng bài thay vì đóng vai người học ngây thơ hỏi vặn.
   - Người dùng mới bị bỡ ngỡ ở màn hình mở đầu.

2. **Thay đổi làm ngay trước demo:**
   - **Fix Prompt Guardrail:** Thêm luật nghiêm ngặt cấm Alex đưa ra câu trả lời thay thế; khi học viên trả lời cộc lốc hoặc dùng buzzword, Alex chỉ được dùng đúng 1 câu hỏi Socratic ngắn gọn yêu cầu đưa ví dụ.

3. **Giữ nguyên có lý do căn cứ:**
   - Giữ nguyên cơ chế **Anti-parroting** và cơ chế **từ chối cung cấp đáp án quiz Day 1** vì cả 2 tester đều đánh giá đây là điểm chạm sư phạm xuất sắc nhất, tạo sự khác biệt hoàn toàn với chatbot thông thường.

4. **Đưa vào backlog sau:**
   - Xây dựng thanh đo mức độ thấu hiểu trực quan theo thời gian thực.
   - Hỗ trợ bộ từ điển giải ngố thuật ngữ đời thường dành riêng cho học viên non-tech ngay trong khung chat.
