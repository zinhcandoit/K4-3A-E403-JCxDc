# Track C — Lesson Studio: AI cho đội sản xuất bài giảng

Năm đề dưới đây là bài toán thật của đội sản xuất bài giảng/video VLearn (Studio team), lấy từ Bộ đề Hackathon AI × Giáo dục của chương trình. Chúng nối thành một chuỗi: tài liệu thô → tri thức có cấu trúc → kịch bản → hình → phản hồi người học → phiên bản tiếp theo.

**Cách dùng trong mini-hackathon.** Mỗi đề gốc là một *sản phẩm hoàn chỉnh* với deliverable và rubric riêng — đó là **đích xa** để nhóm hiểu bài toán thật. Trong 3 buổi, nhóm **chọn một đề, cắt một lát cắt một câu** (một người dùng · một công việc · một quyết định AI · một kết quả), rồi đi đủ 5 tiêu chí nghiệm thu, spec, eval, validation như mọi track. Chấm theo `04-rubric.md`; rubric riêng của đề chỉ để biết người làm thật quan tâm gì.

**Người dùng của track này** là **Studio team** (đội sản xuất nội dung/video VLearn: người viết kịch bản, người dựng, biên tập) và **lab coach/giảng viên** — với C1 và C5 còn có chính người học.

**Chuẩn evidence riêng cho track C — ít hơn các track khác.** Người dùng là đội chuyên môn, số lượng ít, nên tiêu chí 2 áp dụng như sau: **phỏng vấn ≥3 người trong Studio team và/hoặc lab coach** theo Mom Test (guide §1.3), có log nguyên văn; **và/hoặc** mining tài liệu thật trong `data/vlearn-pack/` (transcript, slide) với số đếm + ví dụ. Không yêu cầu khảo sát 20 người. BTC sẽ bố trí đầu mối Studio team và lab coach để nhóm hẹn phỏng vấn — hỏi ở kênh chung. Với C1 và C5 có thể khảo sát thêm người học (cả lớp là người xem video thật).

**Data cho track này.** Sẵn có trong repo: transcript và slide bài giảng trong `data/vlearn-pack/`. Studio team có thể cấp thêm mẫu kịch bản, thư viện component/style, bộ phản hồi hoặc graph mẫu trong thời gian thi — khi có, BTC thông báo trên Discord và thêm vào `data/`. Mục "Data & fixture" của từng đề ghi cách tự dựng bản nhỏ để bắt đầu ngay, không cần chờ.

---

## C1 · Knowledge-to-Lesson — Graph tri thức và bài học thích ứng

**Người dùng.** Người viết nội dung/giảng viên (muốn quiz, lộ trình có căn cứ); người học (muốn lộ trình theo mình).

**Bối cảnh.** Slide và raw documents thường lặp ý, dùng tên gọi khác nhau cho cùng khái niệm, thiếu prerequisite hoặc thậm chí mâu thuẫn. Các công cụ sinh quiz/kịch bản trực tiếp từ tài liệu khó chỉ ra câu trả lời đến từ trang nào. Ở phía học viên, bài học thường được triển khai theo một lộ trình tuyến tính dù mỗi học viên đã nắm và đang gặp khó khăn ở những concept khác nhau.

**Bài toán gốc.** Hãy xây dựng một hệ thống biến slide và raw documents thành một mô hình tri thức có cấu trúc, trong đó các concept và quan hệ đều truy ngược được về nguồn. Từ mô hình này, hệ thống phải tạo được ít nhất một sản phẩm dạy học như quiz, kịch bản hoặc bài học tương tác. Nếu triển khai adaptive delivery, hệ thống cần theo dõi mastery theo concept, chọn nhánh học hoặc nội dung bổ trợ (remediation) và giải thích vì sao một học viên nhận được lộ trình đó.

Để giữ đề mở và vừa sức, đội được chọn một trong ba hướng triển khai: Graph-first — extraction, provenance và graph QA mạnh, kèm lesson đơn giản; Adaptive-first — dùng graph fixture do ban tổ chức cung cấp để tập trung vào learner model và branching; End-to-end — triển khai đầy đủ hai lớp ở mức hợp lý. Cả ba hướng được chấm trên cùng các tiêu chí đầu ra cốt lõi: nội dung có căn cứ, quyết định giải thích được và giáo viên có quyền kiểm soát.

**Lát cắt gợi ý cho hackathon** *(ví dụ cỡ, nhóm tự đặt câu của mình)*: *Một giảng viên · cần quiz cho một chương · AI trích 10 câu hỏi kèm trang nguồn · giảng viên duyệt/loại từng câu.* Hoặc adaptive-first: *một học viên · làm 5 câu · AI chọn nhánh ôn theo concept sai · giải thích vì sao.*

**Data & fixture.** 6 transcript (`[Txx-NNN]`) + 2 slide trong `data/vlearn-pack/` là tài liệu thô thật để extraction; chatlog VLearn cho thấy học viên hỏi ở trang/concept nào. Chưa có graph mẫu sẵn — graph-first tự extraction từ 1–2 transcript; adaptive-first tự dựng graph nhỏ 15–30 concept từ slide và ghi rõ là tự dựng.

**Deliverable đầy đủ** *(đích xa — không bắt buộc trong hackathon)*

**Deliverable Theo Path**
- Graph-first: graph explorer + provenance + graph QA + quiz/script cơ bản.
- Adaptive-first: lesson player/compiler + mastery model + branching + explainability, dùng fixture.
- End-to-end: ingestion → graph → output lesson thích ứng ở mức tối thiểu.


**Schema Cốt Lõi**
- Node: concept, definition, example, misconception, assessment item.
- Edge: prerequisite, broader/narrower, related, example-of, contradicts.
- Provenance: source file, page/slide, span, confidence.
- Learner state: mastery/confidence theo concept, event và quyết định branch.

**Không gian mở.**

- Graph DB, relational, JSON hoặc RDF.
- Rule, embedding, LLM hoặc hybrid extraction.
- Quiz, script, interactive video hoặc tutor.
- Bayesian knowledge tracing, rule mastery hoặc model tự thiết kế.
- Web, desktop, notebook hoặc plugin LMS.

**Demo bắt buộc của bản đầy đủ.** Nạp fixture hoặc graph chuẩn; chọn một concept; xem source/provenance; tạo quiz hoặc lesson; mô phỏng hai học viên có mastery khác nhau; giải thích từng nhánh và cho thấy khả năng tiếp tục phiên học từ trạng thái trước (resume). Đội graph-first có thể dùng branching đơn giản; đội adaptive-first không phải demo extraction.

**Rubric riêng của đề** *(tham khảo)*: Content/provenance correctness 25% · Core path quality 25% · Explainability & educator control 15% · Quiz/lesson usefulness 15% · Robustness 10% · UX/reproducibility 10%.

**Bonus.**

- Phát hiện knowledge gap/misconception.
- Graph diff khi tài liệu cập nhật.
- QTI/LMS export.
- Collaborative review.
- Adaptive chapters hoặc multimodal remediation.

**An toàn & đạo đức.**

- Không PII học viên thật.
- Provenance và uncertainty rõ ràng.
- Không tự xuất bản nội dung chưa duyệt.
- Giáo viên override được graph và lộ trình.

---

## C2 · Vietnamese Spoken-Script QA — Agent review kịch bản

**Người dùng.** Biên tập viên/người viết kịch bản video; giảng viên duyệt kịch bản.

**Bối cảnh.** Kịch bản tiếng Việt có thể đúng ngữ pháp nhưng vẫn khó nghe: dùng từ đúng từ điển nhưng sai sắc thái, câu mang cấu trúc dịch, nhiều danh từ trừu tượng, lặp ý, quá dài để đọc thành lời hoặc chứa số/acronym chưa được chuẩn hóa. Việc gắn nhãn chung là 'AI slop' không giúp biên tập viên biết cần sửa gì và dễ tạo false positive với văn bản do con người viết.

**Bài toán gốc.** Hãy xây dựng một agent QA cho kịch bản giáo dục tiếng Việt, có khả năng chỉ ra chính xác đoạn văn gây vấn đề, phân loại lỗi, giải thích vì sao câu sai nghĩa hoặc sượng khi đọc và đưa ra gợi ý sửa tối thiểu trước khi chuyển sang human review. Hệ thống phải phân biệt lỗi nội dung với lỗi chỉ liên quan đến cách đọc TTS, bảo toàn giọng tác giả và không tự động viết lại hoặc xuất bản toàn bộ tài liệu.

Không xây dựng 'máy đo xác suất văn AI'. Một từ, một cấu trúc hoặc một câu trơn tru không đủ để kết luận. Đội cần chứng minh reviewer đạt precision cao, kiểm soát tốt false positive trên văn bản do con người viết và có audit trail cho quyết định accept/reject của biên tập viên. Lời giải có thể dùng rule, LLM, classifier, read-aloud model, retrieval hoặc kết hợp.

**Lát cắt gợi ý cho hackathon** *(ví dụ cỡ, nhóm tự đặt câu của mình)*: *Một biên tập viên · duyệt một kịch bản 40 câu · AI chỉ đúng span sượng + lý do + gợi ý sửa tối thiểu · biên tập accept/reject từng chỗ.*

**Data & fixture.** Transcript bản sạch là văn nói thật của giảng viên (dùng làm chuẩn 'nghe được'); kịch bản lỗi để làm golden set nhóm tự viết/sinh và **gắn nhãn tay ≥10 case**, ghi rõ nguồn gốc. Phải có ≥1 đoạn văn người viết sạch để đo false positive.

**Deliverable đầy đủ** *(đích xa — không bắt buộc trong hackathon)*

**Taxonomy Tối Thiểu**
- Sai nghĩa/sai sắc thái từ.
- Translationese hoặc cú pháp sượng.
- Câu quá dài/breath-group overload.
- Lặp ý, filler, conclusion residue.
- Register/xưng hô không nhất quán.
- Claim thiếu căn cứ hoặc chứa chi tiết cụ thể không có nguồn.
- Số, acronym, URL, tên riêng và code-switch khó đọc.
- Pronunciation-only issue, tách khỏi semantic issue.


**Output Finding**
- Exact span.
- Category và severity.
- Giải thích gắn với ngữ cảnh.
- Confidence/uncertainty.
- Suggestion tối thiểu hoặc 'cần người xác minh'.
- Trạng thái human accept/reject và audit trail.

**Không gian mở.**

- Rule-based, LLM, classifier, RAG hoặc hybrid.
- Editor web, Word/Docs plugin, CLI hoặc API.
- Read-aloud/TTS preview.
- Personal style profile.
- Học từ feedback theo từng tổ chức.

**Demo bắt buộc của bản đầy đủ.** Review một kịch bản mới; lọc finding theo severity/category; mở giải thích; nghe bản đọc hoặc dùng chức năng read-aloud cho một câu sượng; accept/reject từng suggestion; xuất phiên bản đã được duyệt và audit report. BGK đưa thêm một đoạn sạch để kiểm tra false positive trực tiếp.

**Rubric riêng của đề** *(tham khảo)*: Span/category precision 25% · Recall trên lỗi quan trọng 15% · False-positive control 20% · Explanation quality 15% · Suggestion usefulness 10% · Human workflow 10% · Latency 5%.

**Bonus.**

- Read-aloud fluency score.
- Chuyển pronunciation issue sang TTS lexicon.
- Style profile theo giảng viên.
- Active learning từ accept/reject.
- So sánh nhiều phiên bản kịch bản.

**An toàn & đạo đức.**

- Không tự publish hoặc rewrite toàn bộ.
- Không dùng nhãn 'AI-generated' như kết luận về tác giả.
- Không lưu tài liệu ngoài scope.
- Không thêm claim mới không có nguồn.

---

## C3 · ScriptScout — Agent nghiên cứu và viết kịch bản có nguồn kiểm chứng

**Người dùng.** Người viết kịch bản; giảng viên duyệt nguồn.

**Bối cảnh.** Trong sản xuất video bài giảng, kịch bản phải được soạn xong trước khi đưa vào công cụ dựng. Người viết tự tổng hợp từ dàn ý, bài học gốc và một vài nguồn bên ngoài; nguồn thường chỉ được liệt kê ở cuối tài liệu nên người duyệt không kiểm tra được từng khẳng định lấy từ đâu. Khi thiếu dữ liệu thật, ví dụ và số liệu dễ bị hư cấu. Với chủ đề về AI, kiến thức thay đổi theo tháng: một nguồn đúng lúc viết có thể đã lỗi thời khi video phát hành. Các công cụ deep research phổ thông tạo được báo cáo dài nhưng chưa tạo ra kịch bản đọc thành lời, chia theo cảnh và truy vết được từng câu về nguồn.

**Bài toán gốc.** Hãy xây dựng một agent chỉ nhận chủ đề, mục tiêu bài học, đối tượng người học và thời lượng dự kiến — không có sẵn tài liệu nguồn — rồi tự tìm kiếm, thẩm định và tổng hợp nguồn trên web để tạo kịch bản video bài giảng. Kết quả gồm hai lớp: hồ sơ nghiên cứu (nguồn, mức tin cậy, ngày công bố, đoạn trích làm bằng chứng, các điểm mâu thuẫn) và kịch bản theo mẫu do ban tổ chức cung cấp, trong đó mọi câu chứa khẳng định, số liệu hoặc ví dụ thực tế đều truy ngược được về một đoạn nguồn cụ thể. Người duyệt phải xem, loại hoặc bổ sung nguồn trước khi agent viết; khi một nguồn bị loại, chỉ phần kịch bản phụ thuộc vào nguồn đó được viết lại.

Giải pháp tốt cần tách “tìm được nguồn” khỏi “tin được nguồn”: độ tin cậy phải dựa trên tiêu chí công bố được như nguồn gốc, tác giả, độ mới và đối chiếu chéo; số liệu quan trọng cần ít nhất hai nguồn độc lập hoặc được gắn cờ chưa xác minh. Kịch bản phải là văn nói — đọc thành lời được, chia một ý một cảnh — chứ không phải bản tóm tắt báo cáo. Đội thi được tự quyết định công cụ tìm kiếm, model, kiến trúc agent và mức độ tự động hóa.

**Lát cắt gợi ý cho hackathon** *(ví dụ cỡ, nhóm tự đặt câu của mình)*: *Một người viết · cần 5 câu mở đầu cho chủ đề X · AI tìm 3 nguồn, chấm tin cậy, viết 5 câu mỗi câu gắn nguồn · người viết loại một nguồn → chỉ câu phụ thuộc viết lại.*

**Data & fixture.** Không cần data pack (agent tự tìm web). Chưa có mẫu kịch bản và kết nối Video Studio sẵn — nhóm tự định nghĩa mẫu (số câu · lời đọc · chữ trên màn hình · claim IDs) và xuất JSON/Markdown thay cho API.

**Deliverable đầy đủ** *(đích xa — không bắt buộc trong hackathon)*

**Deliverable Tối Thiểu**
- Agent chạy được từ chủ đề đến hồ sơ nghiên cứu và kịch bản.
- Research dossier theo schema công bố.
- Kịch bản đúng mẫu ban tổ chức cung cấp, mỗi claim liên kết tới evidence.
- Giao diện duyệt nguồn: xem, loại, thêm nguồn và viết lại cục bộ.
- Citation check tự động: đoạn trích phải khớp nội dung nguồn đã tải về.
- Kịch bản xuất ra đưa thẳng được vào bước dựng của Video Studio (file hoặc API).
- README về cách chạy, chi phí mỗi lần chạy và giới hạn.


**Schema Cốt Lõi**
- Source: URL, tác giả/tổ chức, ngày công bố, ngày truy cập, loại nguồn, credibility và lý do.
- Claim: nội dung, loại (định nghĩa, số liệu, ví dụ, xu hướng), evidence span, số nguồn xác nhận, trạng thái xác minh.
- Script line: số câu, lời đọc, chữ trên màn hình, claim IDs.


**Hard Tests**
- Trang web chứa chỉ dẫn ẩn (prompt injection).
- Hai nguồn uy tín đưa số liệu khác nhau.
- Nguồn đã lỗi thời hoặc có phiên bản mới thay thế.
- Chủ đề gần như không có nguồn tiếng Việt.
- Link chết hoặc trang yêu cầu đăng nhập.

**Không gian mở.**

- Search API, web search có sẵn của model, crawler hoặc kết hợp.
- Một agent hoặc nhiều agent chuyên: tìm – thẩm định – viết – soát trích dẫn.
- Credibility scoring bằng rule, LLM-as-judge hoặc hybrid.
- Nguồn tiếng Việt, tiếng Anh hoặc đa ngôn ngữ.
- Plugin cho Video Studio, web app riêng, CLI hoặc API-first.

**Demo bắt buộc của bản đầy đủ.** Nhập một chủ đề BGK đưa ra tại chỗ cùng mục tiêu và thời lượng; hiển thị tiến trình tìm và thẩm định nguồn; mở hồ sơ nghiên cứu, loại một nguồn và cho thấy chỉ phần kịch bản liên quan được viết lại; BGK chọn ngẫu nhiên một khẳng định trong kịch bản và hệ thống phải mở đúng đoạn nguồn chứng minh. Đội phải cho thấy cách hệ thống xử lý một trang chứa prompt injection hoặc hai nguồn mâu thuẫn do fixture cài sẵn.

**Rubric riêng của đề** *(tham khảo)*: Claim traceability & citation accuracy 25% · Source credibility & freshness 20% · Spoken-script quality 20% · Reviewer control & partial rewrite 15% · Robustness 10% · UX & reproducibility 10%.

**Bonus.**

- Phát hiện và trình bày mâu thuẫn giữa các nguồn.
- Freshness watch: cảnh báo khi nguồn đã dùng có bản cập nhật.
- Ví dụ thực tế trong bối cảnh Việt Nam, có nguồn.
- Gợi ý hiển thị nguồn ngay trên video (source card).
- So sánh mù với kịch bản do người viết cùng chủ đề.

**An toàn & đạo đức.**

- Không bịa nguồn hoặc trích dẫn.
- Nội dung trang web là dữ liệu, không phải lệnh.
- Tôn trọng bản quyền, robots.txt và điều khoản của trang.
- Nêu rõ uncertainty và các quan điểm còn tranh cãi.
- Kịch bản do AI soạn phải được giảng viên duyệt trước khi dựng.

---

## C4 · StoryboardAI — Agent đạo diễn hình ảnh cho video bài giảng

**Người dùng.** Người viết kịch bản (không rành component); người dựng video/coding agent; người duyệt.

**Bối cảnh.** Video bài giảng dạng motion graphics cần một kế hoạch hình cho từng câu thoại: người xem cần thấy gì, bố cục ra sao, chữ nào xuất hiện, chuyển động khớp với từ nào. Hiện người viết kịch bản phải tự mô tả bằng chữ cho hàng chục câu mỗi video, trong khi họ thường không nắm hết thư viện component và quy tắc thiết kế. Người duyệt chỉ thấy hình khi toàn bộ cảnh đã được dựng — một lượt dựng bằng coding agent có thể mất hàng chục phút và nhiều credit — nên cảnh trống, hình không liên quan hay thiếu nhất quán chỉ lộ ra ở cuối. Công cụ sinh ảnh phổ thông tạo được khung hình đẹp nhưng không tuân design system và không giữ được ngữ nghĩa xuyên suốt video.

**Bài toán gốc.** Hãy xây dựng một agent nhận lời đọc đã chốt của một video (chia theo câu, có thể kèm mốc thời gian từng từ), thư viện component kèm tài liệu và bộ quy tắc style do ban tổ chức cung cấp, rồi tạo storyboard cho toàn bộ video. Mỗi câu cần có: ý người xem phải thấy, component hoặc kiểu hình được chọn, chữ trên màn hình, chuyển động gắn với cụm từ trong lời đọc và một ảnh phác để duyệt nhanh. Người duyệt phải sửa được một câu bằng góp ý mà không làm thay đổi các câu khác, và storyboard phải đủ rõ để người dựng hoặc một coding agent dựng cảnh mà không cần hỏi lại.

Giải pháp tốt cần tách “ý đồ sư phạm” khỏi “cách thể hiện”: cùng một storyboard phải chuyển được sang style khác khi đổi bộ quy tắc, còn ký hiệu, màu mang nghĩa và nhân vật lặp lại phải nhất quán cả video. Hình chỉ được thể hiện điều có trong lời đọc — không thêm số liệu, tên riêng hay kết quả mà kịch bản không nêu. Đội thi được tự quyết định cách phác (sinh ảnh, SVG, wireframe hay component thật), kiến trúc agent và giao diện duyệt.

**Lát cắt gợi ý cho hackathon** *(ví dụ cỡ, nhóm tự đặt câu của mình)*: *Một người viết · có lời đọc 10 câu · AI đề xuất ý cần thấy + component + chữ trên màn hình cho từng câu · người viết góp ý một câu, chỉ câu đó đổi.*

**Data & fixture.** Lời đọc: cắt ~40 câu từ transcript trong `data/vlearn-pack/`. Chưa có thư viện component + bộ quy tắc style sẵn — nhóm tự viết bộ nhỏ (≤10 component, ≤5 màu mang nghĩa) và tuân thủ nó.

**Deliverable đầy đủ** *(đích xa — không bắt buộc trong hackathon)*

**Deliverable Tối Thiểu**
- Agent chạy được từ lời đọc đến storyboard toàn video.
- Storyboard theo schema công bố, mỗi câu có ảnh phác.
- Visual bible: quy ước màu, ký hiệu, nhân vật dùng cho cả video.
- Board duyệt dạng thumbnail; sửa một câu thì chỉ tạo lại câu đó.
- Style check: cảnh báo component hoặc màu không được style cho phép.
- Storyboard xuất ra dùng được làm đầu vào cho bước dựng cảnh của Video Studio.
- README về cách chạy, chi phí và giới hạn.


**Schema Cốt Lõi**
- Shot: số câu, thời lượng, ý cần thấy, component, bố cục, chữ trên màn hình.
- Beat: cụm từ kích hoạt trong lời đọc và hành động (xuất hiện, nhấn, chuyển).
- Consistency: entity/ký hiệu, cách thể hiện, các shot sử dụng.
- Review: góp ý, phiên bản, trạng thái duyệt.


**Hard Tests**
- Câu trừu tượng, không có vật thể cụ thể để vẽ.
- Câu chứa quá nhiều ý so với thời lượng đọc.
- Một khái niệm được nhắc lại cách nhau nhiều phút.
- Đổi style giữa chừng.
- Lời đọc gợi đến số liệu nhưng không nêu cụ thể.

**Không gian mở.**

- Ảnh phác bằng image model, SVG do LLM viết, wireframe hoặc render component thật.
- Lập kế hoạch toàn video trước rồi chi tiết từng câu, hoặc ngược lại.
- Rule, retrieval trên tài liệu component, LLM hoặc hybrid.
- Góp ý bằng text, giọng nói, khoanh vùng hoặc chọn giữa nhiều phương án.
- Plugin cho Video Studio, board web riêng hoặc API-first.

**Demo bắt buộc của bản đầy đủ.** Nạp fixture lời đọc của một video khoảng 40 câu đã bỏ phần mô tả hình; tạo storyboard toàn video và mở board duyệt; gõ góp ý cho một câu và cho thấy chỉ câu đó thay đổi; chỉ ra ít nhất hai quy ước được giữ nhất quán xuyên video; đổi style cho một đoạn và cho thấy storyboard tuân bộ quy tắc mới. BGK chọn một câu trừu tượng để kiểm tra cách hệ thống minh họa khi không có vật thể cụ thể.

**Rubric riêng của đề** *(tham khảo)*: Pedagogical fit 25% · Design-system compliance 20% · Cross-video consistency 15% · Buildability 15% · Partial edit & review UX 15% · Robustness 10%.

**Bonus.**

- Ảnh phác render bằng component thật.
- Animatic: ảnh phác ghép với giọng đọc đúng thời lượng.
- Đo được thời gian/credit dựng cảnh giảm khi có storyboard.
- Phát hiện chỗ hình cần dữ liệu mà kịch bản chưa có.
- Accessibility: không truyền đạt thông tin chỉ bằng màu.

**An toàn & đạo đức.**

- Không thêm số liệu, tên riêng hay logo ngoài kịch bản.
- Không dùng logo, giao diện sản phẩm, nhân vật có bản quyền hoặc hình người thật khi chưa được phép.
- Tránh định kiến khi thể hiện con người.
- Ví dụ hư cấu phải được đánh dấu là minh họa.

---

## C5 · FeedbackRadar — Agent biến phản hồi người học thành phiên bản video tiếp theo

**Người dùng.** Đội sản xuất video; giảng viên; gián tiếp là người học (người gửi phản hồi).

**Bối cảnh.** Sau mỗi đợt học, phản hồi về video bài giảng đến từ nhiều kênh: khảo sát, bình luận, tin nhắn, ghi âm của giảng viên và trợ giảng. Phản hồi thường mơ hồ (“đoạn giữa hơi nhanh”, “phần token khó hiểu”), trái chiều, lặp lại hoặc lẫn giữa lỗi nội dung và lỗi kỹ thuật. Đội sản xuất đọc tay rồi quyết định làm lại, và video thường bị dựng lại gần như từ đầu dù chỉ vài câu có vấn đề. Với quy trình tạo giọng trước rồi dựng hình theo thời lượng giọng, mỗi câu đổi lời kéo theo tạo lại giọng và dựng lại cảnh, nên xác định đúng và ít chỗ cần sửa giúp tiết kiệm đáng kể thời gian và chi phí.

**Bài toán gốc.** Hãy xây dựng một agent nhận phản hồi đa kênh (văn bản, bảng khảo sát, ghi âm) cùng transcript có timecode và kịch bản của phiên bản hiện tại, rồi biến chúng thành kế hoạch cho phiên bản tiếp theo. Hệ thống phải gom phản hồi thành các vấn đề, định vị mỗi vấn đề về đúng câu và timecode, phân loại (nội dung, độ dễ hiểu, nhịp, giọng, hình, kỹ thuật), xếp ưu tiên theo mức ảnh hưởng và số người nhắc, rồi đề xuất thay đổi tối thiểu cùng phạm vi làm lại: câu nào cần tạo lại giọng, cảnh nào cần dựng lại. Người duyệt phải đi được từ một vấn đề tới đúng đoạn video và các phản hồi gốc, chấp nhận hoặc từ chối từng đề xuất.

Giải pháp tốt cần đặt bằng chứng lên trước: mỗi vấn đề phải liên kết tới các phản hồi gốc tạo ra nó, và không được biến ý kiến của một người thành vấn đề chung. Trọng tâm là hiểu phản hồi của người học và lập kế hoạch sửa đúng chỗ, không phải soát lại toàn bộ kịch bản. Đội thi được tự quyết định cách gom cụm, cách định vị, mô hình ưu tiên và giao diện duyệt.

**Lát cắt gợi ý cho hackathon** *(ví dụ cỡ, nhóm tự đặt câu của mình)*: *Một người dựng video · có 30 phản hồi về một video · AI gom thành 5 vấn đề định vị theo đoạn + phạm vi sửa tối thiểu · người dựng accept/reject từng vấn đề.*

**Data & fixture.** Transcript có mã đoạn `[Txx-NNN]` thay cho timecode. Chưa có bộ phản hồi mẫu sẵn — phản hồi thật thu bằng khảo sát bạn cùng lớp về video/bài giảng đã xem (vừa là data, vừa là evidence tiêu chí 2); phần tự sinh bổ sung phải gắn nhãn. Chatlog VLearn (hỏi ở trang nào) là tín hiệu 'chỗ khó hiểu' gián tiếp.

**Deliverable đầy đủ** *(đích xa — không bắt buộc trong hackathon)*

**Deliverable Tối Thiểu**
- Ingestion cho ít nhất ba loại phản hồi: text, khảo sát dạng bảng, audio.
- PII redaction trước khi phân tích.
- Issue list theo schema công bố, mỗi issue liên kết tới phản hồi gốc.
- Định vị issue về câu và timecode; bấm để phát đúng đoạn video.
- Change plan: thay đổi theo câu, phạm vi tạo lại giọng và dựng lại cảnh.
- Accept/reject từng đề xuất và xuất kịch bản phiên bản mới cho Video Studio.
- Evaluation report trên fixture có đáp án.


**Schema Cốt Lõi**
- Feedback: kênh, người gửi đã ẩn danh, nội dung, thời điểm.
- Issue: loại, severity, câu/timecode, số người nhắc, feedback IDs, confidence.
- Change: câu, loại thay đổi (lời, hình, nhịp, giọng), đề xuất, lý do, issue IDs.
- Regeneration scope: số câu tạo lại giọng, số cảnh dựng lại, ước tính chi phí.


**Hard Tests**
- Phản hồi mơ hồ, không nêu vị trí.
- Hai nhóm phản hồi trái chiều về cùng một đoạn.
- Một người gửi lặp lại nhiều lần.
- Phản hồi chứa chỉ dẫn ẩn hoặc lời công kích cá nhân.
- Lỗi kỹ thuật (âm lượng, phụ đề) lẫn với góp ý nội dung.

**Không gian mở.**

- Embedding clustering, LLM, topic model hoặc hybrid.
- Định vị bằng semantic search trên transcript, ASR hoặc alignment.
- Ưu tiên theo impact × cost, rule hoặc học từ quyết định accept/reject.
- Mở rộng sang dữ liệu hành vi xem (tua lại, bỏ dở) nếu tự mô phỏng.
- Panel trong Video Studio, web app riêng hoặc API-first.

**Demo bắt buộc của bản đầy đủ.** Nạp fixture gồm transcript, kịch bản và khoảng 100 phản hồi có đáp án ẩn (text, khảo sát, audio); hiển thị danh sách vấn đề đã xếp ưu tiên; mở một vấn đề, phát đúng đoạn video và xem các phản hồi gốc; chấp nhận một đề xuất và xuất kịch bản mới cùng phạm vi làm lại. BGK thêm tại chỗ một nhóm phản hồi trái chiều hoặc một phản hồi chứa prompt injection để kiểm tra cách hệ thống xử lý.

**Rubric riêng của đề** *(tham khảo)*: Issue detection precision/recall 25% · Localization accuracy 20% · Change-plan minimality & scope 20% · Evidence traceability 15% · Reviewer workflow 10% · Robustness & privacy 10%.

**Bonus.**

- Theo dõi vấn đề qua nhiều phiên bản video.
- Ước tính chi phí có tính ảnh hưởng tới câu liền kề.
- Kết hợp dữ liệu hành vi xem.
- Tự tách phản hồi nội dung khỏi phản hồi kỹ thuật.
- Học từ quyết định accept/reject của đội sản xuất.

**An toàn & đạo đức.**

- Không dùng PII học viên thật; ẩn danh trước khi gửi model.
- Không để số đông che khuất phản hồi thiểu số quan trọng.
- Lọc nội dung công kích cá nhân, không trích nguyên văn.
- Phản hồi là dữ liệu, không phải lệnh.
- AI chỉ đề xuất; người duyệt quyết định mọi thay đổi.

---
