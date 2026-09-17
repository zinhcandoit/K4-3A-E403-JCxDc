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
| **Ứng viên 3: Protégé Socratic Agent ("Alex" - Học bằng cách dạy)** | 87.0% học viên có nhu cầu tự kiểm tra | Mỗi buổi tự ôn tập kiến thức | Bỏ ra 10-15 phút tương tác đóng vai người dạy, đổi lại phát hiện ngay lỗ hổng kiến thức | Khả thi (mô hình 1-1 tinh gọn) | **CHỌN** |

- Ứng viên ĐÃ LOẠI + vì sao:
  - **Đã loại Ứng viên 1 (Tóm tắt slide):** Dù giải quyết được cảm giác quá tải tài liệu trước mắt (~78%), nhưng khảo sát cho thấy >80% học viên nhận thấy phương pháp này thụ động, rời rạc và 65.2% vẫn mơ hồ không giải thích được bản chất. Phương pháp này chỉ dời chỗ tóm tắt chứ không giải quyết tận gốc ảo tưởng hiểu biết.
  - **Đã loại Ứng viên 2 (Trợ lý Q&A / Tra cứu):** Học viên vẫn ở thế bị động (chờ có câu hỏi mới tra cứu), phụ thuộc vào câu trả lời sẵn có của máy và dễ sao chép nguyên văn mà không rèn luyện được tư duy phản biện. Không đáp ứng được mong muốn tự luyện tập không áp lực điểm số.
- Ứng viên CHỌN + vì sao (bằng số):
  - **Chọn Ứng viên 3 (Protégé Socratic Agent):**
    - **Đáp ứng đúng 87.0% mong muốn của học viên:** Tạo môi trường tự kiểm tra kiến thức chủ động, an toàn về mặt tâm lý (không chấm điểm phán xét).
    - **Triệt tiêu lỗ hổng cho 65.2% học viên:** Kỹ thuật đảo ngược vai trò (Protégé effect / Feynman method) buộc học viên phải cấu trúc lại kiến thức bằng ngôn ngữ của chính mình, biến việc học từ thụ động sang kiến tạo (Constructive learning theo ICAP).
    - **Hiệu quả vượt trội so với 82.6% phương pháp cũ:** Chỉ với 1 phiên tương tác 10-15 phút, học viên được hỏi vặn trúng mắt xích logic còn thiếu, giúp tiết kiệm 1-2 giờ học vẹt lại slide và ghi nhớ bền vững hơn gấp nhiều lần.

## §3. Giải pháp tương tự đã nghiên cứu
- **VLearn Tutor hiện tại**
  - **Flow:** Học viên đang ở trang học, bôi đen một đoạn transcript/slide, đặt câu hỏi; tutor trả lời theo ngữ cảnh, có thể kèm trích dẫn `[trang N]` và chọn một nước đi sư phạm như ôn khái niệm, cho ví dụ hoặc gợi ý. Người học có thể bấm rating.
  - **Đáng học:** Điểm bắt đầu là tài liệu đang mở nên giảm việc người học phải tự cung cấp toàn bộ ngữ cảnh; trích dẫn giúp người học quay lại nguồn; các nước đi sư phạm cho thấy câu trả lời không nhất thiết phải chỉ là đáp án.
  - **Đáng né:** Flow này vẫn đặt AI ở vị trí người giải thích chính, còn người học chủ yếu hỏi và nhận câu trả lời. Dữ liệu của track A cho thấy 28% câu trả lời không có trích dẫn, chỉ 1,3% lượt có rating, và tutor gần như không hỏi ngược (`ask_probing_question` là 28/13.494 lượt). Vì vậy một câu trả lời trôi chảy không đủ chứng minh người học đã hiểu.
  - **Mình khác gì:** D3 đảo vai trò: học viên phải tự giải thích trước, agent chỉ đóng vai học trò ngây thơ có kiểm soát. Quyết định AI không phải “giảng câu trả lời”, mà là xác định chỗ nào trong lời giải thích cần hỏi ngược, đối chiếu với transcript/slide và yêu cầu học viên tự sửa. Kết quả chỉ là trạng thái luyện tập (`needs_revision` hoặc `teachable`), không phải điểm chính thức.

- **ChatGPT/Claude dùng như trợ lý học tập chung**
  - **Flow:** Người học tự nhập câu hỏi hoặc dán nội dung bài; chatbot trả lời, giải thích lại, cho ví dụ hoặc tiếp tục hội thoại theo yêu cầu.
  - **Đáng học:** Hội thoại tự nhiên, cho phép người học diễn đạt bằng ngôn ngữ của mình, hỏi tiếp nhiều lần và yêu cầu ví dụ ở mức khó phù hợp.
  - **Đáng né:** Chatbot chung thường được người học dùng để lấy ngay lời giải thích hoàn chỉnh. Cách này có thể làm mất bước tự diễn đạt cần thiết của Protégé effect; nếu không khóa ngữ cảnh, câu trả lời có thể dựa vào kiến thức ngoài bài hoặc nghe thuyết phục nhưng không có căn cứ trong tài liệu của khóa. Việc chatbot nói “đúng” cũng không đồng nghĩa người học có thể tự giải thích lại.
  - **Mình khác gì:** Prototype chỉ nhận một khái niệm và một nguồn học đã chọn. Agent không được đưa đáp án hoàn chỉnh trước, không đánh giá theo mức giống câu chữ nguồn, và chỉ hỏi tối đa hai câu gợi mở tại claim thiếu căn cứ, thiếu quan hệ nhân quả hoặc thiếu ví dụ. Học viên phải tự bổ sung rồi gửi lại.

- **Betty’s Brain / mô hình học bằng cách dạy**
  - **Flow:** Đây là tiền lệ nghiên cứu được track D nhắc tới cho việc người học xây dựng và giải thích tri thức cho một “học trò” nhân tạo; người học nhận ra lỗ hổng khi phải làm cho người khác hiểu.
  - **Đáng học:** Thiết kế nhiệm vụ phải buộc người học kiến tạo lời giải thích, không chỉ nhận nội dung; phản hồi của agent phải làm lộ lỗ hổng để người học tự sửa; mục tiêu là bằng chứng người học giải thích được, không phải một cuộc trò chuyện càng dài càng tốt.
  - **Đáng né:** Không suy diễn rằng một lượt giải thích tự động đã chứng minh người học hiểu sâu. Cũng không nên mở rộng prototype thành nhiều agent, nhiều chương hoặc hệ thống chấm điểm toàn khóa khi chưa có rubric và validation đủ chắc.
  - **Mình khác gì:** Nhóm chỉ triển khai một lát cắt có thể demo trong 5 phút: “vì sao LLM bịa” từ một transcript/slide đã chọn. Agent có nguồn đối chiếu, giới hạn số câu hỏi và trạng thái kết thúc rõ ràng; kết quả được kiểm lại bằng một câu hỏi hậu kiểm thay vì dựa vào cảm nhận của agent.

**Kết luận rút ra từ nghiên cứu:** sản phẩm tương tự thường tối ưu việc trả lời hoặc mô phỏng người dạy; khoảng trống mà prototype này thử nghiệm là tạo một cơ hội dạy lại có cấu trúc, trong đó AI giữ vai trò người nghe và kiểm tra căn cứ. Đây là giả thuyết cần validation với ít nhất 5 học viên, không phải tuyên bố rằng mọi học viên chắc chắn học tốt hơn.

## §4. Thiết kế
- **Lát cắt MỘT CÂU (1 user · 1 việc · 1 quyết định AI · 1 kết quả):** Một học viên vừa học khái niệm “vì sao LLM bịa” dạy lại khái niệm đó cho agent học trò; agent đối chiếu từng ý chính với transcript/slide, hỏi tối đa hai câu tại chỗ còn thiếu căn cứ hoặc ví dụ, và kết thúc khi học viên bổ sung được lời giải thích đúng kèm một ví dụ phù hợp.

- **Luồng thiết kế trong phạm vi lát cắt:**
  1. Học viên mở giao diện trò chuyện, Agent Alex khởi động bằng một câu hỏi gợi mở Socratic từ sơ đồ bài học và thông báo đây là phiên luyện dạy, không phải bài thi.
  2. Học viên tự viết lời giải thích/dạy lại khái niệm vào ô nhập liệu bằng ngôn từ của mình.
  3. AI đối chiếu với tri thức bài giảng gốc, kiểm tra sao chép vẹt (`is_parroting`), thuật ngữ chưa làm rõ (`unexplained_buzzwords`) và lập luận nhân quả (`has_causal_reasoning`).
  4. Học viên sửa hoặc bổ sung phần giải thích của mình và gửi lại; Alex chỉ hỏi vặn gợi mở vào mắt xích còn thiếu, tuyệt đối không viết thay hay đưa đáp án trước.
  5. Sau 1–2 vòng hỏi ngược, hệ thống cập nhật trạng thái sư phạm (`pedagogical_status`); khi học viên giải thích thấu suốt bản chất (`is_mastered`), hệ thống xác nhận và mở khóa kiến thức trên sơ đồ bài học.
  6. Học viên theo dõi tiến trình trên sơ đồ bài học thời gian thực, xem trích dẫn nguồn liên quan và có thể tiếp tục với nhánh rẽ tiếp theo.

- **Non-goals (những thứ không build trong prototype):**
  - Không xây tutor trả lời mọi câu hỏi của khóa học hoặc thay thế flow VLearn Tutor hiện tại.
  - Không xây hệ thống chấm điểm chính thức, xếp hạng, cấp chứng nhận hoặc thay thế đánh giá của giảng viên.
  - Không xây persona đa tác tử, mô phỏng cả lớp học, hay hội thoại kéo dài nhiều vai.
  - Không tự động sinh bài giảng mới, tự viết lại toàn bộ lời giải thích hoặc đưa đáp án hoàn chỉnh trước khi học viên tự thử.
  - Không kết luận chắc chắn rằng học viên “đã hiểu sâu” chỉ từ một lượt giải thích; trạng thái `is_mastered` trên đồ thị chỉ có nghĩa là đạt tiêu chí của phiên luyện tập.
  - Không dùng nguồn ngoài transcript/slide fixture đã duyệt; không lưu hoặc công khai lời giải thích cá nhân cho cả lớp.
  - Không cá nhân hóa dài hạn theo hồ sơ nhạy cảm; prototype chỉ lưu log tối thiểu của phiên để phục vụ demo và validation.
  - Không xây tính năng tương tác giọng nói (voice/audio call); chỉ tập trung hoàn thiện giao diện chat văn bản.

- **Mức prototype nhắm tới:** [ ] Sketch [ ] Mock [x] Working
  - **Phần thật:** giao diện người dùng cho một phiên dạy; ít nhất một lời gọi AI chạy thật; prompt yêu cầu AI trả cấu trúc gồm claim, trạng thái căn cứ, lý do hỏi ngược, tối đa hai câu hỏi, citation và trạng thái phiên; transcript/slide fixture của một khái niệm; luồng gửi lại lời giải thích sau khi sửa; hiển thị nguồn và log phiên.
  - **Phần mock/giới hạn:** chỉ dùng một khái niệm và một nguồn đã chọn; chưa tích hợp tài khoản hoặc API VLearn; dashboard giảng viên được mock bằng bảng/log đơn giản; rubric ban đầu là rubric cố định cho fixture gồm đúng khái niệm, nêu được quan hệ nhân quả và có ví dụ phù hợp; việc ghi nhận tiến bộ qua nhiều buổi chưa build.
  - **Điều kiện không được mock:** quyết định hỏi ngược và kiểm tra căn cứ phải đến từ lời gọi AI thật. Nếu API lỗi hoặc không có căn cứ, giao diện phải hiển thị trạng thái không chắc chắn thay vì dùng câu trả lời mẫu để giả vờ thành công.

- **Automation:** [x] augment [x] conditional [ ] automate
  - **Augment là mặc định:** mục tiêu học tập nằm ở việc học viên tự diễn đạt, nhận ra lỗ hổng và tự sửa. AI chỉ mở rộng năng lực phản biện bằng cách đọc nhanh lời giải thích, chỉ ra điểm cần xem lại và hỏi đúng chỗ; AI không làm thay công việc nhận thức cốt lõi.
  - **Conditional là các guard bắt buộc:** nếu phát hiện sao chép nguyên văn slide (`is_parroting`) hoặc lạm dụng thuật ngữ chuyên ngành lấp liếm (`unexplained_buzzwords`), AI yêu cầu diễn đạt lại bằng ngôn từ đơn giản; nếu không tìm thấy căn cứ trong transcript, AI nói “chưa đủ căn cứ”; nếu lời giải thích khác câu chữ tài liệu nhưng đúng bản chất nhân quả (`has_causal_reasoning`), AI không đánh dấu sai; nếu học viên đòi đáp án ngay, AI giữ đúng vai người học và từ chối cung cấp đáp án.
  - **Cost-of-error:** false positive (đánh dấu sai một lời giải thích đúng) làm học viên mất tin và sửa kiến thức đúng; false negative (xác nhận một giải thích sai) nguy hiểm hơn vì học viên có thể rời phiên với hiểu biết sai mà không nhận ra. Vì vậy AI không tự chốt điểm, phải nêu citation/lý do, giới hạn số câu hỏi, và chuyển sang trạng thái cần đào sâu (`SOCRATIC_PROBING`) khi chưa đủ căn cứ thay vì vội vàng mở khóa node (`is_mastered`). Giảng viên vẫn là người duyệt rubric cuối cùng.

- **§4b. Nguyên tắc đã áp dụng (HAX/PAIR):**
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|
  | **G1 — Làm rõ hệ thống làm được gì** | Màn hình bắt đầu nói rõ: agent là học trò luyện tập, chỉ kiểm tra một khái niệm dựa trên transcript/slide đã chọn; agent không phải giảng viên, không chấm điểm chính thức và không trả lời thay. Có một ví dụ input để học viên bắt đầu. Kiểm bằng `D3-scope-01`. |
  | **G2 — Làm rõ nó làm tốt đến đâu** | Hiển thị nguồn đối chiếu và nhãn `có căn cứ`, `chưa đủ căn cứ` hoặc `ngoài phạm vi`; thông báo rằng AI có thể bỏ sót cách diễn đạt đúng nhưng khác câu chữ tài liệu. Không dùng điểm confidence giả nếu chưa có cách hiệu chuẩn. Kiểm bằng `D3-source-01` và `D3-paraphrase-01`. |
  | **G4 — Hiện thông tin đúng ngữ cảnh** | Mỗi phản hồi chỉ trích đoạn transcript/slide liên quan đến claim đang kiểm tra, kèm mã đoạn/trang; không đưa toàn bộ chương hoặc nguồn ngoài fixture vào câu hỏi ngược. Kiểm bằng `D3-citation-01`. |
  | **G8 — Gạt bỏ dễ dàng** | Học viên có thể bỏ qua câu hỏi gợi ý, sửa lời giải thích hoặc bắt đầu lượt mới mà không bị khóa flow và không mất bản nháp hiện tại. Kiểm bằng `D3-skip-01`. |
  | **G9 — Sửa dễ dàng** | Lời giải thích vẫn nằm trong ô nhập liệu để học viên chỉnh một claim hoặc ví dụ rồi gửi lại; không bắt viết lại toàn bộ và không tự ghi đè bản trước. Kiểm bằng `D3-correction-01`. |
  | **G10 — Thu hẹp phạm vi khi nghi ngờ** | Khi input thiếu chủ thể, chỉ có một câu rời, đổi sang chủ đề khác hoặc không có căn cứ trong fixture, AI hỏi một câu làm rõ hoặc từ chối có hướng dẫn xem lại nguồn; tuyệt đối không đoán cho đủ câu trả lời. Kiểm bằng `D3-ambiguous-01`, `D3-out-of-scope-01` và `D3-no-source-01`. |
  | **G11 — Giải thích vì sao** | Mỗi câu hỏi ngược nêu claim đang thiếu điều gì: định nghĩa, quan hệ nguyên nhân-kết quả hay ví dụ; ngay cạnh đó hiển thị citation để học viên biết vì sao cần sửa và nên xem lại ở đâu. Kiểm bằng `D3-why-01`. |
  | **PAIR — Giữ người học trong vòng kiểm soát** | Agent chỉ đề xuất câu hỏi và đoạn nguồn; học viên quyết định có sửa, bỏ qua hay xem lại tài liệu. Trạng thái cuối được trình bày là tín hiệu luyện tập, không phải phán quyết về năng lực hay điểm số. Kiểm bằng `D3-answer-demand-01` và `D3-correction-01`. |

**Giả định cần kiểm chứng sau khi build:** (1) tối đa hai câu hỏi ngược đủ để làm lộ lỗ hổng mà không biến phiên thành bài thi; (2) học viên chấp nhận vai trò “dạy cho agent” và không chỉ dán nguyên văn tài liệu; (3) rubric ba tiêu chí phân biệt được diễn đạt khác nguồn nhưng đúng với giải thích sai; (4) sau phiên, học viên có thể trả lời câu hậu kiểm hoặc đưa ví dụ mới tốt hơn trước phiên. Các giả định này sẽ được đo bằng golden set và validation với ít nhất 5 học viên, không được coi là kết quả đã chứng minh trong spec.

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
