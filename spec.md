# Template AI Spec *(spec.md — commit trước hạn chốt spec: 21:00 17/9, tại CP4 · quality bar chốt từ thời điểm nộp)*

> Cấu trúc phủ đúng "SPEC 8 phần" của chương trình: Bằng chứng (§1-§2) · Lát cắt (§4) · Canvas (đính kèm CP1) · Augment/Automate (§4) · 4 đường đi của trải nghiệm (§6) · Kiểu lỗi (§5) · Kiểm thử (§7) · Phân công (§8). Hướng dẫn viết từng mục: `02-guide.md`.

```markdown
# AI SPEC — [Tên lát cắt] · Nhóm [XX] · Zone [X]
Hướng: [ ] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [ ] Tối ưu tính năng có sẵn  [ ] Tính năng mới

## §1. User & Job
- Job executor + workflow (đính kèm worksheet JTBD / ảnh sơ đồ):
  - **Job executor:** Học viên đang tự ôn tập các khái niệm kỹ thuật phức tạp sau buổi học (không có trợ giảng kèm 1:1).
  - **Workflow hiện tại:** Nhận tài liệu/slide bài giảng dài → Đọc lướt hoặc tìm bài tóm tắt các ý trọng tâm → Tự nhẩm ghi nhớ hoặc làm bài tập trắc nghiệm → Phát hiện lúng túng khi gặp câu hỏi thực tế hoặc câu hỏi kiểm tra bản chất.
- Core JTBD (không tên sản phẩm/AI trong câu):
  - *Phát hiện và bù đắp kịp thời các lỗ hổng logic khi ôn tập các khái niệm chuyên sâu để thấu hiểu bản chất vấn đề mà không bị ảo tưởng hiểu biết.*
- Problem statement (KHÔNG chữ AI):
  - *Học viên khi tự ôn tập các bài học dài thường bị quá tải nội dung nên chỉ đọc lướt hoặc học vẹt định nghĩa tóm tắt; khi phải tự diễn đạt lại một khái niệm hoàn chỉnh thì bị mơ hồ và đứt gãy logic, dẫn đến việc không thể giải quyết bài tập thực tế và dễ mất điểm ở các bài kiểm tra.*
- Evidence (chuẩn A và/hoặc B — log đầy đủ trong repo):
  - **Giả thuyết cốt lõi (Core Hypothesis):** Học viên không thực sự hiểu sâu kiến thức nếu chỉ đọc slide một cách thụ động hoặc phụ thuộc vào việc xem tóm tắt có sẵn. Chỉ khi đảo ngược vai trò—bắt học viên phải đóng vai người hướng dẫn, giải thích/dạy lại kiến thức cho một người khác—họ mới phát hiện ra lỗ hổng kiến thức của chính mình và chủ động tự bù đắp.
  - **Số liệu khảo sát thực tế (Chuẩn A: n = 23 học viên ngoài nhóm, log lưu tại repo):**
    - **78.3% (18/23 học viên)** phản hồi tài liệu/slide quá dài, dẫn đến tâm lý đọc lướt hoặc bỏ qua các phần quan trọng (Painpoint 1).
    - **65.2% (15/23 học viên)** xác nhận khi chỉ tập trung học ý trọng tâm hoặc đọc tóm tắt, họ cảm thấy mơ hồ và không đủ tự tin giải thích lại một khái niệm hoàn chỉnh khi được hỏi sâu (Painpoint 2 & Impact 1).
    - **82.6% (19/23 học viên)** từng thử dùng các công cụ tóm tắt từng slide nhưng đánh giá cách này rời rạc, tốn thời gian và không tạo được động lực ghi nhớ dài hạn (Impact 2).
    - **87.0% (20/23 học viên)** bày tỏ nhu cầu cấp thiết về một phương pháp tự kiểm tra kiến thức nhẹ nhàng, không bị áp lực điểm số nhưng giúp chỉ ra ngay mắt xích logic mình chưa nắm chắc.
  - **≥5 quote/ví dụ nguyên văn + nguồn:**
    1. *"Slide mỗi buổi tới 60-70 trang ngập chữ và công thức, mình đọc được 15 trang đầu là đuối, sau đó chỉ lướt lướt cho xong."* — [Học viên 03, Khảo sát lớp 3A]
    2. *"Lúc đọc tóm tắt các gạch đầu dòng thì thấy gật gù hiểu hết, nhưng đến khi bạn cùng bàn hỏi 'tại sao chỗ này lại suy ra được bước kia' là mình cứng họng."* — [Học viên 12, Phỏng vấn trực tiếp]
    3. *"Mình hay paste slide nhờ tóm tắt, nhưng kết quả chỉ là một đống chữ khác ngắn hơn, đọc xong qua ngày hôm sau lại quên vì đầu không phải vận động."* — [Học viên 08, Khảo sát lớp 3A]
    4. *"Đi thi quiz hay gặp mấy câu hỏi lắt léo về bản chất là mình sai ngay, vì lúc ôn chỉ học thuộc vẹt bề nổi chứ không hiểu luồng vận hành bên dưới."* — [Học viên 17, Khảo sát lớp 3A]
    5. *"Làm bài test có điểm số thì rất áp lực và sợ sai, nhưng nếu chỉ tự đọc thì không biết mình đang ngộ nhận đúng chỗ nào. Rất cần ai đó vặn vẹo nhẹ nhàng để tự vỡ ra."* — [Học viên 21, Phỏng vấn trực tiếp]

## §2. Impact & quyết định chọn
- Bảng impact ≥3 ứng viên (bao nhiêu người · tần suất · tốn gì mỗi lần · khả thi):

| Ứng viên ý tưởng | Bao nhiêu người gặp (từ evidence) | Tần suất | Tốn gì mỗi lần (chi phí pain) | Khả thi (build trong 48h) | Quyết định |
|---|---|---|---|---|---|
| **Ứng viên 1: Công cụ tự động tóm tắt slide bài giảng** | 78.3% học viên quá tải slide | 1-2 lần / tuần (mỗi buổi học) | Mất 15-20 phút đọc tóm tắt thụ động nhưng vẫn quên sau 24-48 giờ | Cao (dễ build) | **LOẠI** |
| **Ứng viên 2: Trợ lý Q&A giải đáp thắc mắc tài liệu (RAG)** | 82.6% học viên từng thử | Mỗi khi gặp chỗ khúc mắc | Mất 10-15 phút copy-paste câu hỏi rời rạc, câu trả lời dài không đọng lại tư duy | Trung bình | **LOẠI** |
| **Ứng viên 3: Protégé Socratic Agent ("Alex" - Học bằng cách dạy)** | 87.0% học viên có nhu cầu tự kiểm tra | Mỗi buổi tự ôn tập kiến thức | Bỏ ra 10-15 phút tương tác đóng vai người dạy, đổi lại phát hiện ngay lỗ hổng kiến thức | Khả thi với Graph + Structured Output | **CHỌN** |

- Ứng viên ĐÃ LOẠI + vì sao:
  - **Đã loại Ứng viên 1 (Tóm tắt slide):** Dù giải quyết được cảm giác quá tải tài liệu trước mắt (~78%), nhưng khảo sát cho thấy >80% học viên nhận thấy phương pháp này thụ động, rời rạc và 65.2% vẫn mơ hồ không giải thích được bản chất. Phương pháp này chỉ dời chỗ tóm tắt chứ không giải quyết tận gốc ảo tưởng hiểu biết.
  - **Đã loại Ứng viên 2 (Trợ lý Q&A / Tra cứu):** Học viên vẫn ở thế bị động (chờ có câu hỏi mới tra cứu), phụ thuộc vào câu trả lời sẵn có của máy và dễ sao chép nguyên văn mà không rèn luyện được tư duy phản biện. Không đáp ứng được mong muốn tự luyện tập không áp lực điểm số.
- Ứng viên CHỌN + vì sao (bằng số):
  - **Chọn Ứng viên 3 (Protégé Socratic Agent):**
    - **Đáp ứng đúng 87.0% mong muốn của học viên:** Tạo môi trường tự kiểm tra kiến thức chủ động, an toàn về mặt tâm lý (không chấm điểm phán xét).
    - **Triệt tiêu lỗ hổng cho 65.2% học viên:** Kỹ thuật đảo ngược vai trò (Protégé effect / Feynman method) buộc học viên phải cấu trúc lại kiến thức bằng ngôn ngữ của chính mình, biến việc học từ thụ động sang kiến tạo (Constructive learning theo ICAP).
    - **Hiệu quả vượt trội so với 82.6% phương pháp cũ:** Chỉ với 1 phiên tương tác 10-15 phút, học viên được hỏi vặn trúng mắt xích logic còn thiếu, giúp tiết kiệm 1-2 giờ học vẹt lại slide và ghi nhớ bền vững hơn gấp nhiều lần.

## §3. Giải pháp tương tự đã nghiên cứu
- [Sản phẩm 1]: flow / đáng học / đáng né / mình khác gì
- [Sản phẩm 2]: ...

## §4. Thiết kế
- Lát cắt MỘT CÂU (1 user · 1 việc · 1 quyết định AI · 1 kết quả):
- Non-goals (≥3 thứ KHÔNG build):
- Mức prototype nhắm tới: [ ] Sketch [ ] Mock [ ] Working — phần nào mock, phần nào thật:
- Automation: [ ] augment [ ] conditional [ ] automate — lý do theo cost-of-error:
- §4b. Nguyên tắc đã áp dụng (≥4 — HAX/PAIR, xem guide):
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8) [bảng theo guide §2.5]

## §6. Bốn đường đi của trải nghiệm
- Happy path: · Low-confidence (②): · Failure/không căn cứ (①): · Correction (user sửa):
- Khi bị đòi ngoài phạm vi (③): · Case đặc thù domain (④):

## §7. Kiểm thử
- Chiều chất lượng + định nghĩa kiểm chứng được:
- Golden set (≥20 case theo cơ cấu trong guide §2.6, file trong eval/):
- Quality bar (chốt từ hạn chốt spec của khoá, giữ nguyên sau đó): "Đạt khi ≥ ___% qua bộ, và ___"
- Kết quả các lượt chạy (bảng % — cập nhật đến trước CP6):

## §8. Phân công & kế hoạch
- Phân công có tên: spec / evidence / prompt / code / demo
- Willing users (≥2 tên) + kế hoạch vòng validation *(bonus, nếu làm)*:
- Multi-prototype (nếu làm): trục khác biệt của ≥2 phương án + lý do chọn:

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
```
