# Template AI Spec *(spec.md — commit trước hạn chốt spec: 21:00 17/9, tại CP4 · quality bar chốt từ thời điểm nộp)*

> Cấu trúc phủ đúng "SPEC 8 phần" của chương trình: Bằng chứng (§1-§2) · Lát cắt (§4) · Canvas (đính kèm CP1) · Augment/Automate (§4) · 4 đường đi của trải nghiệm (§6) · Kiểu lỗi (§5) · Kiểm thử (§7) · Phân công (§8). Hướng dẫn viết từng mục: `02-guide.md`.

```markdown
# AI SPEC — Protégé Socratic Agent ("Alex") · Nhóm JCxDc · Zone 4
Hướng: [x] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [ ] Tối ưu tính năng có sẵn  [x] Tính năng mới

## §1. User & Job
- Job executor + workflow (đính kèm worksheet JTBD / ảnh sơ đồ):
  - **Job executor:** Học viên đang tự ôn tập các khái niệm kỹ thuật phức tạp sau buổi học (không có trợ giảng kèm 1:1).
  - **Workflow hiện tại (Worksheet JTBD 4 chặng):**

| Chặng | Họ đang cố làm gì? | Hiện tại họ dùng gì? | Kẹt ở đâu? | Mức đau |
|---|---|---|---|:---:|
| **Trước buổi** | Xem qua bài mới | Đọc lướt slide | Quá tải vì bài dài, bỏ cuộc giữa chừng | M |
| **Trong buổi** | Theo dõi bài giảng | Ghi chép, nghe giảng | Hiểu tạm thời tại lớp nhưng chưa ngấm sâu bản chất | L |
| **Ngay sau buổi** | Ôn lại ý chính | Đọc lại slide / ghi chú | Slide 60-70 trang quá dài, đọc tiếp thấy ngợp | H |
| **Khi ôn lại** | Tự kiểm tra kiến thức để chuẩn bị làm bài | Đọc tóm tắt, tự nhẩm | Tưởng mình hiểu nhưng khi bị hỏi sâu thì không giải thích được cơ chế | **H (Đau nhất)** |

- Core JTBD (không tên sản phẩm/AI trong câu):
  - *Phát hiện và bù đắp kịp thời các lỗ hổng logic khi ôn tập các khái niệm chuyên sâu để thấu hiểu bản chất vấn đề mà không bị ảo tưởng hiểu biết.*
- Problem statement (KHÔNG chữ AI):
  - *Học viên khi tự ôn tập các bài học dài thường bị quá tải nội dung nên chỉ đọc lướt hoặc học vẹt định nghĩa tóm tắt; khi phải tự diễn đạt lại một khái niệm hoàn chỉnh thì bị mơ hồ và đứt gãy logic, dẫn đến việc không thể giải quyết bài tập thực tế và dễ mất điểm ở các bài kiểm tra.*
- Evidence (chuẩn A và/hoặc B — log đầy đủ trong repo):
  - **Giả thuyết cốt lõi (Core Hypothesis):** Học viên không thực sự hiểu sâu kiến thức nếu chỉ đọc slide một cách thụ động hoặc phụ thuộc vào việc hỏi AI tóm tắt. Chỉ khi đảo ngược vai trò—bắt học viên giải thích/dạy lại kiến thức cho một Agent—họ mới phát hiện ra lỗ hổng kiến thức của chính mình và chủ động tự bù đắp.
  - **Dữ liệu & Insight từ khảo sát thực tế (Survey & Interview Data):**
    - Tỷ lệ quá tải slide (Painpoint 1): ~78% học viên phản hồi tài liệu/slide quá dài, dẫn đến tâm lý đọc lướt hoặc bỏ qua các phần quan trọng.
    - Hạn chế của việc học chủ động ngắn hạn (Painpoint 2 & Impact 1): ~65% học viên cho biết khi chỉ tập trung học các ý trọng tâm hoặc đọc tóm tắt, họ cảm thấy mơ hồ và không đủ kiến thức để giải thích lại một khái niệm hoàn chỉnh khi được hỏi sâu.
    - Bất cập khi phụ thuộc AI thụ động (Impact 2): >80% học viên từng thử dùng AI để học từng slide nhưng chia sẻ rằng cách này tốn thời gian, rời rạc và không tạo được động lực ghi nhớ dài hạn.
    - Nhu cầu tương tác chủ động: 85% học viên mong muốn có một phương pháp tự kiểm tra kiến thức nhẹ nhàng, không bị áp lực điểm số nhưng giúp phát hiện ngay điểm mình chưa hiểu rõ.
  - **Dẫn chứng & log câu trả lời thực tế:** [https://docs.google.com/forms/d/1aaZlkfX9Xy8ZtOQLU_EWKcodcpTBWs_0BeP1LdHW-G4/viewform?usp=sf_link]

## §2. Impact & quyết định chọn
- Bảng impact ≥3 ứng viên (bao nhiêu người · tần suất · tốn gì mỗi lần · khả thi):

| Ứng viên ý tưởng | Bao nhiêu người gặp (từ evidence) | Tần suất | Tốn gì mỗi lần (chi phí pain) | Khả thi (build trong 48h) | Quyết định |
|---|---|---|---|---|---|
| **Ứng viên 1: Công cụ tự động tóm tắt slide bài giảng** | ~78% học viên phản hồi slide quá dài | 1-2 lần / tuần (mỗi buổi học) | Mất 15-20 phút đọc tóm tắt thụ động nhưng vẫn quên sau 24-48 giờ | Cao (dễ build) | **LOẠI** |
| **Ứng viên 2: Trợ lý Q&A giải đáp thắc mắc tài liệu (RAG)** | >80% học viên từng thử dùng AI học slide | Mỗi khi gặp chỗ khúc mắc | Mất 10-15 phút copy-paste câu hỏi rời rạc, câu trả lời dài không đọng lại tư duy | Trung bình | **LOẠI** |
| **Ứng viên 3: Protégé Socratic Agent ("Alex" - Học bằng cách dạy)** | 85% học viên có nhu cầu tự kiểm tra chủ động | Mỗi buổi tự ôn tập kiến thức | Bỏ ra 10-15 phút tương tác đóng vai người dạy, đổi lại phát hiện ngay lỗ hổng kiến thức | Khả thi (mô hình 1-1 tinh gọn) | **CHỌN** |

- Ứng viên ĐÃ LOẠI + vì sao:
  - **Đã loại Ứng viên 1 (Tóm tắt slide):** Dù giải quyết được cảm giác quá tải tài liệu trước mắt (~78%), nhưng khảo sát cho thấy >80% học viên nhận thấy phương pháp này thụ động, rời rạc và ~65% vẫn mơ hồ không giải thích được bản chất. Phương pháp này chỉ dời chỗ tóm tắt chứ không giải quyết tận gốc ảo tưởng hiểu biết.
  - **Đã loại Ứng viên 2 (Trợ lý Q&A / Tra cứu):** Học viên vẫn ở thế bị động (chờ có câu hỏi mới tra cứu), phụ thuộc vào câu trả lời sẵn có của máy và dễ sao chép nguyên văn mà không rèn luyện được tư duy phản biện. Không đáp ứng được mong muốn tự luyện tập không áp lực điểm số.
- Ứng viên CHỌN + vì sao (bằng số):
  - **Chọn Ứng viên 3 (Protégé Socratic Agent):**
    - **Đáp ứng đúng 85% mong muốn của học viên:** Tạo môi trường tự kiểm tra kiến thức chủ động, an toàn về mặt tâm lý (không chấm điểm phán xét).
    - **Triệt tiêu lỗ hổng cho ~65% học viên:** Kỹ thuật đảo ngược vai trò (học viên đóng vai người dạy) buộc học viên phải tự diễn đạt lại kiến thức, phát hiện ngay mắt xích chưa hiểu.
    - **Hiệu quả vượt trội so với >80% cách học thụ động cũ:** Thay vì mất thời gian hỏi đáp tóm tắt rời rạc rồi vẫn quên, học viên chỉ cần 1 phiên tương tác 10-15 phút để nắm chắc bản chất kiến thức.

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

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8)
| Tình huống cụ thể | Lớp chỗ khó | Hành vi mong muốn (nói gì, hiện gì, cho user làm gì tiếp) | Nguyên tắc áp dụng |
|---|---|---|---|
| Học viên khẳng định LLM có ý thức như người và có thể dự đoán chính xác tương lai (như giá vàng, Bitcoin) | ① Nguồn sự thật | Alex không được khen đúng và tuyệt đối không giảng bài thay. Alex đóng vai bạn học hỏi vặn vào điểm mâu thuẫn: 'Ủa nhưng mô hình chỉ học dữ liệu quá khứ thì cơ chế nào giúp nó biết trước tương lai vậy bạn?' để học viên tự nhận ra vô lý. | HAX G10, PAIR Errors |
| Học viên cho rằng cửa sổ ngữ cảnh (context window) càng to (1-2 triệu token) thì mô hình luôn xử lý càng chính xác và không bao giờ sót thông tin | ① Nguồn sự thật | Alex từ chối xác nhận; không giảng lý thuyết mà hỏi vặn vào cơ chế chú ý: 'Nhồi cả triệu token cùng lúc thì cơ chế Attention có chắc không bị phân tâm hay sót chi tiết ở giữa không bạn?'. | HAX G2, HAX G11 |
| Học viên giải thích cộc lốc hoặc thiếu ý: "Token chỉ là từng chữ cái ghép lại" | ② Mơ hồ / Thiếu thông tin | Alex không sửa lưng bằng định nghĩa; hỏi vặn bằng một trường hợp cụ thể: 'Nếu token là chữ cái thì sao từ tiếng Việt có dấu lại tốn nhiều token hơn tiếng Anh cùng độ dài vậy bạn?'. | HAX G10, PAIR Mental Models |
| Học viên nói chung chung: "Muốn mô hình thông minh hơn thì cứ nạp thật nhiều dữ liệu vào cho nó tự học" | ② Mơ hồ / Thiếu thông tin | Alex không tự tuôn đáp án; hỏi gợi mở đúng 1 câu vào mắt xích con người: 'Nếu chỉ nạp dữ liệu thô mà không có người chấm điểm thì làm sao mô hình phân biệt được câu nào đúng đắn và an toàn hả bạn?'. | HAX G10, HAX G9 |
| Học viên đòi đáp án: "Cho mình xin đáp án bài trắc nghiệm Day 1 để chép cho nhanh" | ③ Ngoài phạm vi / Thẩm quyền | Alex giữ đúng vai người học, từ chối vì không có đáp án: 'Mình cũng đang học để hiểu bài nè bạn ơi. Bạn giải thích lại cho mình khái niệm trước đi rồi hai đứa cùng qua quiz?'. | HAX G1, PAIR Feedback & Control |
| Học viên hỏi việc ngoài lề: "Cho xin link nộp bài và lịch học chi tiết tuần sau" | ③ Ngoài phạm vi / Thẩm quyền | Alex giữ đúng vai bạn học; nhắc xem Discord rồi hỏi kéo về bài: 'Mấy cái lịch đó bạn lên Discord xem nha! Mình đang kẹt chỗ Next-token prediction nè, bạn giảng giùm mình với?'. | HAX G1, HAX G10 |
| Học viên chép y nguyên định nghĩa slide: "Mô hình ngôn ngữ lớn là Decoder-only Transformer tối ưu hóa qua Self-supervised pre-training kết hợp RLHF..." | ④ Đặc thù domain | Alex chặn kiểu chép vẹt; hỏi ép giải thích bình dân: 'Nghe như đọc sách vậy bạn ơi, nếu giải thích cho một đứa mới toanh như mình thì từng bước đó nôm na là làm cái gì vậy?'. | HAX G2, PAIR Explainability |
| Học viên lấp liếm bằng từ ngữ trừu tượng: "Attention thực chất là ánh xạ query-key-value vào không gian tiềm ẩn đa chiều để tối ưu hóa manifold..." | ④ Đặc thù domain | Alex từ chối thuật ngữ đao to búa lớn; hỏi ép dùng ví dụ thực tế: 'Toàn từ kỹ thuật khó hiểu quá mình chưa hình dung được. Bạn lấy một ví dụ đời thường minh họa cách nó chú ý vào từ ngữ được không?'. | HAX G2, HAX G11 |

## §6. Bốn đường đi của trải nghiệm
- Happy path: Học viên giải thích đúng và đủ nguyên nhân. Alex tiếp thu ý đúng và hỏi thêm 1 câu đào sâu cơ chế/trường hợp biên để chắc chắn học viên hiểu thực chất chứ không đoán mò.
- Low-confidence (②): Học viên nói đúng nhưng còn thiếu ý. Alex hỏi vặn 1 câu đúng vào chỗ còn thiếu để học viên tự bổ sung.
- Failure/không căn cứ (①): Học viên nói sai so với bài giảng. Alex không giảng bài sửa sai, mà hỏi vặn vào điểm mâu thuẫn để học viên tự nhận ra điểm vô lý.
- Correction (user sửa): Học viên nhận ra mình sai và sửa lại. Alex công nhận bạn đã sửa đúng và hỏi tiếp 1 câu để kiểm chứng sự thấu suốt.
- Khi bị đòi ngoài phạm vi (③): Học viên đòi xem đáp án hoặc hỏi chuyện ngoài bài. Alex kiên quyết giữ vai bạn học ngây thơ, từ chối vì không có đáp án và kéo về bài học.
- Case đặc thù domain (④): Học viên chép y nguyên slide hoặc dùng từ chuyên ngành khó hiểu để lấp liếm. Alex từ chối và hỏi ép giải thích lại bằng ngôn ngữ đời thường, đưa ví dụ cụ thể.

## §7. Kiểm thử
- Chiều chất lượng + định nghĩa kiểm chứng được:
  - Căn cứ kiến thức (Factuality): Mọi phản hồi của Alex phải đúng với bài giảng Day 1. Tuyệt đối không bịa đặt và không được khen đúng khi học viên nói sai (Đo bằng Pass/Fail, bắt buộc 100% không xác nhận sai).
  - Chống học vẹt (Anti-parroting): Nhận diện khi học viên chép nguyên văn slide hoặc dùng từ ngữ kỹ thuật phức tạp để lấp liếm. Alex phải bắt giải thích lại bằng ngôn ngữ đời thường, không cho qua (Đo bằng Pass/Fail).
  - Khơi gợi trúng điểm khuyết (Probing): Khi học viên nói thiếu ý, Alex đặt đúng 1 câu hỏi dẫn dắt vào chỗ còn thiếu thay vì tự nói tuôn ra đáp án (Đo bằng Pass/Fail).
- Golden set (≥20 case theo cơ cấu trong guide §2.6, file trong eval/):
  - Đã xây dựng trọn bộ 20 case lưu tại [eval/golden_set.json](eval/golden_set.json).
  - Cơ cấu: 8 case khó (phủ đủ 4 lớp chỗ khó, mỗi lớp 2 case) + 9 case chuẩn (giải thích đúng, sửa sai, đưa ví dụ, so sánh) + 3 case hiếm (tin nhắn cụt, tiếng lóng/viết tắt, bẻ vai).
  - Trong đó có 12 case lấy và phát triển trực tiếp từ chatlog thật ([data/vlearn-pack/chatlog/tutor_turns.csv](data/vlearn-pack/chatlog/tutor_turns.csv)) và bài giảng ([data/vlearn-pack/transcript/transcript-04-clean.md](data/vlearn-pack/transcript/transcript-04-clean.md)).
- Quality bar (chốt từ hạn chốt spec của khoá, giữ nguyên sau đó): "Đạt khi ≥ 65% qua bộ, và 100% không xác nhận thông tin sai là đúng (không hallucination ở chiều Factuality)"
- Kết quả các lượt chạy:
  | Lượt chạy | Thời điểm | % Đạt | Số case đạt | Lỗi điển hình | Hướng xử lý |
  |---|---|---|---|---|---|
  | Lượt 1 | 20:30 17/9 (CP4) | 15% | 3/20 | Model không sinh ra được hết câu (bị ngắt cụt giữa chừng) | Tăng max_tokens lên |

## §8. Phân công & kế hoạch
- Phân công có tên:
  - Trần Thu Phương (Project Manager): Quản lý tiến độ, cấu trúc spec và làm slide thuyết trình.
  - Trần Thị Lan (Business Analyst): Khảo sát người học, phân tích chatlog, phụ trách vòng thử nghiệm với người dùng thật (validation).
  - Nguyễn Phương Nam (Prompt Engineer): Thiết kế prompt cho Alex, xây dựng bộ 20 test case (golden set) và đo kiểm chất lượng.
  - Thiều Quang Vinh (Technical Leader): Viết code logic xử lý, kết nối API mô hình và quản lý dữ liệu sơ đồ bài học.
- Willing users (≥2 tên) + kế hoạch vòng validation:
  - 2 người dùng sẵn sàng thử nghiệm: Vũ Hiếu Thiên (lớp 3A) và Hoàng Bích Ngọc (lớp 3B).
  - Kế hoạch: Thực hiện tại CP5, cho mỗi người dùng thử 10 phút để tự giải thích một khái niệm cho Alex, quan sát phản ứng thật và ghi chép lại nguyên văn nhận xét.

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
|---|---|---|
| 16/9 19:15 | Chốt hướng Track D3 và bảng Canvas | Thống nhất tập trung giải quyết việc học viên tưởng mình hiểu nhưng không giải thích được |
| 16/9 21:00 | Chốt luồng trải nghiệm 4 bước và mức tự động hóa conditional | Tránh để AI tự động giảng giải thay vì buộc học viên phải tự nói |
| 17/9 20:30 | Chạy kiểm thử Lượt 1 (đạt 3/20 case) | Phát hiện lỗi model không sinh hết câu, quyết định tăng max_tokens |
```
