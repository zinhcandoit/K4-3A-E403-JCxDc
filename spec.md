# Template AI Spec *(spec.md — commit trước hạn chốt spec: 21:00 17/9, tại CP4 · quality bar chốt từ thời điểm nộp)*

> Cấu trúc phủ đúng "SPEC 8 phần" của chương trình: Bằng chứng (§1-§2) · Lát cắt (§4) · Canvas (đính kèm CP1) · Augment/Automate (§4) · 4 đường đi của trải nghiệm (§6) · Kiểu lỗi (§5) · Kiểm thử (§7) · Phân công (§8). Hướng dẫn viết từng mục: `02-guide.md`.

```markdown
# AI SPEC — [Tên lát cắt] · Nhóm [XX] · Zone [X]
Hướng: [ ] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [ ] Tối ưu tính năng có sẵn  [ ] Tính năng mới

## §1. User & Job
- Job executor + workflow (đính kèm worksheet JTBD / ảnh sơ đồ):
- Core JTBD (không tên sản phẩm/AI trong câu):
- Problem statement (KHÔNG chữ AI):
- Evidence (chuẩn A và/hoặc B — log đầy đủ trong repo):
  - Số liệu mining / kết quả khảo sát (n = ?, % xác nhận):
  - ≥5 quote/ví dụ nguyên văn + nguồn:

## §2. Impact & quyết định chọn
- Bảng impact ≥3 ứng viên (bao nhiêu người · tần suất · tốn gì mỗi lần · khả thi):
- Ứng viên ĐÃ LOẠI + vì sao:
- Ứng viên CHỌN + vì sao (bằng số):

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
  1. Học viên chọn fixture “vì sao LLM bịa” và thấy thông báo đây là phiên luyện dạy, không phải bài thi.
  2. Học viên tự viết hoặc nói lời giải thích ban đầu trong ô nhập liệu.
  3. AI trích các claim chính, đối chiếu với đoạn nguồn đã nạp, rồi chọn một trong ba hành động: hỏi ngược vì thiếu/sai, yêu cầu làm rõ vì input mơ hồ, hoặc xác nhận tạm thời khi đủ căn cứ.
  4. Học viên sửa phần giải thích của mình và gửi lại; AI không viết thay toàn bộ.
  5. Sau tối đa hai vòng hỏi ngược, hệ thống hiển thị các claim đã đủ căn cứ, claim cần xem lại, trích dẫn nguồn liên quan và trạng thái `needs_revision` hoặc `teachable`.
  6. Học viên trả lời một câu hậu kiểm ngắn hoặc nêu một ví dụ mới để kiểm tra kết quả học, sau đó có thể xem lại transcript/slide.

- **Non-goals (những thứ không build trong prototype):**
  - Không xây tutor trả lời mọi câu hỏi của khóa học hoặc thay thế flow VLearn Tutor hiện tại.
  - Không xây hệ thống chấm điểm chính thức, xếp hạng, cấp chứng nhận hoặc thay thế đánh giá của giảng viên.
  - Không xây persona đa tác tử, mô phỏng cả lớp học, hay hội thoại kéo dài nhiều vai.
  - Không tự động sinh bài giảng mới, tự viết lại toàn bộ lời giải thích hoặc đưa đáp án hoàn chỉnh trước khi học viên tự thử.
  - Không kết luận chắc chắn rằng học viên “đã hiểu sâu” chỉ từ một lượt giải thích; trạng thái `teachable` chỉ có nghĩa là đạt rubric của fixture thử nghiệm.
  - Không dùng nguồn ngoài transcript/slide fixture đã duyệt; không lưu hoặc công khai lời giải thích cá nhân cho cả lớp.
  - Không cá nhân hóa dài hạn theo hồ sơ nhạy cảm; prototype chỉ lưu log tối thiểu của phiên để phục vụ demo và validation.

- **Mức prototype nhắm tới:** [ ] Sketch [ ] Mock [x] Working
  - **Phần thật:** giao diện Streamlit cho một phiên dạy; ít nhất một lời gọi `google-genai` chạy thật; prompt yêu cầu AI trả cấu trúc gồm claim, trạng thái căn cứ, lý do hỏi ngược, tối đa hai câu hỏi, citation và trạng thái phiên; transcript/slide fixture của một khái niệm; luồng gửi lại lời giải thích sau khi sửa; hiển thị nguồn và log phiên.
  - **Phần mock/giới hạn:** chỉ dùng một khái niệm và một nguồn đã chọn; chưa tích hợp tài khoản hoặc API VLearn; dashboard giảng viên được mock bằng bảng/log đơn giản; rubric ban đầu là rubric cố định cho fixture gồm đúng khái niệm, nêu được quan hệ nhân quả và có ví dụ phù hợp; việc ghi nhận tiến bộ qua nhiều buổi chưa build.
  - **Điều kiện không được mock:** quyết định hỏi ngược và kiểm tra căn cứ phải đến từ lời gọi AI thật. Nếu API lỗi hoặc không có căn cứ, giao diện phải hiển thị trạng thái không chắc chắn thay vì dùng câu trả lời mẫu để giả vờ thành công.

- **Automation:** [x] augment [x] conditional [ ] automate
  - **Augment là mặc định:** mục tiêu học tập nằm ở việc học viên tự diễn đạt, nhận ra lỗ hổng và tự sửa. AI chỉ mở rộng năng lực phản biện bằng cách đọc nhanh lời giải thích, chỉ ra claim cần xem lại và hỏi đúng chỗ; AI không làm thay công việc nhận thức cốt lõi.
  - **Conditional là các guard bắt buộc:** nếu lời giải thích quá ngắn hoặc mơ hồ, AI hỏi làm rõ; nếu không tìm thấy căn cứ trong fixture, AI nói “chưa đủ căn cứ”; nếu lời giải thích khác câu chữ tài liệu nhưng đúng nghĩa, AI không đánh dấu sai chỉ vì không trùng wording; nếu học viên đòi đáp án ngay, AI nhắc mục tiêu luyện dạy và đưa một câu hỏi gợi ý thay thế.
  - **Cost-of-error:** false positive (đánh dấu sai một lời giải thích đúng) làm học viên mất tin và sửa kiến thức đúng; false negative (xác nhận một giải thích sai) nguy hiểm hơn vì học viên có thể rời phiên với hiểu biết sai mà không nhận ra. Vì vậy AI không tự chốt điểm, phải nêu citation/lý do, giới hạn số câu hỏi, và chuyển sang `needs_revision` khi không đủ căn cứ. Giảng viên vẫn là người duyệt rubric cuối cùng.

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
