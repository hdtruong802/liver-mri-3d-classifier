# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Người dùng chính: hội đồng / người review nghiên cứu.** Họ xem demo và tài liệu để đánh giá công trình — cần thấy nhanh model làm được gì, phương pháp có chặt không, và kết quả có trung thực không. Họ không phải bác sĩ đang đọc ca bệnh; họ đang chấm một nghiên cứu.

**Đối tượng lâm sàng mà công cụ hướng tới (không phải người dùng của demo): bác sĩ chẩn đoán hình ảnh.** Mọi quyết định sản phẩm phải hợp lý với luồng làm việc của họ, nhưng demo hiện tại không được thiết kế để họ dùng trong thực hành.

**Người xây dựng: một người, làm một mình**, luân phiên nhiều công cụ AI coding trên cùng repo. Điều này giới hạn phạm vi những gì có thể xây và bảo trì.

## Product Purpose

Chứng minh rằng một mô hình phân loại đa lớp u gan trên MRI 3D đa pha có thể đưa ra **xác suất đáng tin cậy** và **biết từ chối khi không chắc**, thay vì chỉ đưa ra một nhãn.

Ba deliverable phục vụ cùng một mục đích đó:
- **Web app demo** — cho người review thấy hành vi của model trên ca thật: xác suất theo lớp, mức bất định, cờ chuyển bác sĩ, và vùng ảnh model đang nhìn.
- **Slide + report** — trình bày phương pháp và kết quả kèm khoảng tin cậy và giới hạn.
- **Reproducibility pack** — để người khác chạy lại được.

**Thành công nghĩa là:** người review tin con số, và tin cả những chỗ nghiên cứu tự nhận là chưa làm được. Thành công **không** phải là đạt một mức accuracy nào đó.

## Positioning

Các công trình SOTA trên LLD-MMRI báo accuracy / F1 / AUC rồi dừng lại. Chúng không trả lời được câu hỏi vận hành: *khi model nói 80%, có đáng tin không, và khi nào nó nên im lặng nhường bác sĩ?*

Đóng góp ở đây là **trustworthiness được đo lường**: calibration (ECE, Brier, reliability diagram, temperature scaling), selective prediction (risk–coverage, AURC, accuracy@coverage), kiểm định thống kê ghép cặp, external validation + OOD, và reproducibility đầy đủ. Một công trình chỉ tối ưu accuracy không thể sao chép định vị này mà không làm lại toàn bộ phần đánh giá.

Hệ quả trực tiếp lên sản phẩm: **mức bất định là nội dung hạng nhất trên mọi bề mặt**, không phải chú thích.

## Operating Context

- **Ràng buộc dự án:** 1 người, 6 tuần, 3 sprint. Web app thuộc Sprint 3 — sau khi đã có model và kết quả.
- **Huấn luyện:** Kaggle Notebook, session ≤ 12h, VRAM ~16GB, có thể bị ngắt bất kỳ lúc nào. Kaggle không phải server, không host API ở đó.
- **Luồng dùng demo:** người review mở web app → chọn một ca demo dựng sẵn hoặc upload NIfTI / DICOM series (zip) cho các pha → chờ vài giây → đọc kết quả.
- **Ca demo dựng sẵn (3–5 ca) là đường đi chính**, không phải phương án dự phòng: buổi trình bày có thể mạng chậm hoặc host lạnh, và người review thường không mang dữ liệu MRI theo.
- **Latency:** nút thắt là registration/tiền xử lý, không phải forward pass. Demo chạy trên lesion-crop, rigid-only, bỏ N4 → vài giây trên CPU.
- **Triển khai:** local + ngrok, hoặc Docker trên Hugging Face Spaces / Render free tier. **Chưa chốt.**
- **Slide và report dùng chung một bộ nội dung**, dựng theo chuẩn hội nghị rồi rút gọn cho nội bộ. Slide phải đọc được từ xa trong phòng họp; report đọc trên màn hình trong thời gian dài.

## Capabilities and Constraints

**Model làm gì:** phân loại 7 lớp tổn thương gan (HCC, ICC, di căn, nang, u máu, FNH, áp-xe — 3 ác, 4 lành) ở mức ROI, trên volume 3D đa pha 8 thì MRI.

**Web app trả về:** lớp dự đoán · xác suất từng lớp · xác suất ác tính · mức bất định (entropy, ensemble std) · cờ `defer` · heatmap Grad-CAM 3D trên vài lát chính.

**Ràng buộc kỹ thuật đã khoá:**
- Backend FastAPI, frontend tự code. **Không Streamlit, không Gradio, không framework demo dựng sẵn.**
- Không làm segmentation.
- Ngưỡng và temperature khoá trên validation, áp mù lên test. Tập test 104 ca chạm **đúng một lần**.
- Mọi con số báo kèm 95% CI.

**Thuật ngữ phải dùng nhất quán trên cả ba bề mặt** (giữ nguyên tiếng Anh, kể cả trong bản tiếng Việt): `defer`, `coverage`, `calibration`, `ECE`, `Brier`, `macro-F1`, `AUROC`, `AURC`, `OOD`, `HCC`, `ICC`, `FNH`, `LI-RADS`. Không dịch, không viết tắt riêng.

**Chưa quyết định (không được tự bịa ra):**
- Quyền truy cập LLD-MMRI đang chờ duyệt qua form. Nếu hết Tuần 1 chưa có → chuyển sang CT. **Chưa xác nhận.**
- Nơi triển khai demo cuối cùng.
- Model nào sẽ thắng (chưa train).

## Brand Commitments

Không có thương hiệu, logo, hay identity có sẵn. Ba cam kết bắt buộc:

1. **Cảnh báo Research Use Only phải xuất hiện trên mọi bề mặt có kết quả**, ở vị trí không thể bỏ sót. Không màn hình nào được ngụ ý công cụ đã kiểm định lâm sàng.
2. **Ngôn ngữ hiển thị là tiếng Việt** cho cả web app, slide và report. Thuật ngữ y khoa và thống kê giữ nguyên tiếng Anh (xem mục trên).
3. **Quy ước hội nghị là lựa chọn thường trực, không phải mặc định vì lười.** Người dùng đã chọn quy ước academic — cụ thể là chuẩn talk MICCAI/MIDL — thay vì một thế giới thị giác riêng (2026-07-24). Vì vậy quy ước trở thành cam kết và được thực thi ở mức thủ công cao nhất: chữ là chính, lưới chặt, kẻ hairline, phẳng hoàn toàn, không cài cắm phong cách riêng và không mỉa mai. Hệ thống thị giác cụ thể ở [`DESIGN.md`](DESIGN.md).

## Evidence on Hand

**Đã có:**
- [`MRI_Classification_Spec_Sheet.md`](MRI_Classification_Spec_Sheet.md) — chốt kỹ thuật: dataset, model, toàn bộ định nghĩa metric, chiến lược ngưỡng.
- [`liver_mri_3d_classification_plan.md`](liver_mri_3d_classification_plan.md) — kế hoạch 6 tuần, kill-switch, schema JSON của `/predict` (§8.1), outline báo cáo.

**Chưa có, và tuyệt đối không được bịa:**
- **Chưa có dữ liệu** — quyền truy cập LLD-MMRI đang chờ.
- **Chưa có model, chưa có checkpoint, chưa có một con số kết quả nào.**
- Không có người dùng thật, không có testimonial, không có case study, không có so sánh benchmark nào của riêng dự án này.

Mọi số hiển thị trong UI, slide hay report trước khi có kết quả thật **phải được đánh dấu rõ là dữ liệu giả lập**. Số placeholder trông giống số thật là rủi ro nghiêm trọng nhất của dự án này — người review sẽ tưởng đó là kết quả.

## Product Principles

1. **Mức bất định đi cùng mọi con số.** Không bao giờ hiển thị một nhãn hay một tỷ lệ đứng một mình. Đây là toàn bộ luận điểm của công trình; bề mặt nào vi phạm là bề mặt đó phản bác chính nghiên cứu.
2. **Từ chối là kết quả hợp lệ, không phải lỗi.** Khi model `defer`, đó là hành vi đúng và phải được trình bày như một kết quả có giá trị, không phải một thất bại cần giấu.
3. **Trung thực hơn ấn tượng.** Giới hạn, domain shift, lớp hiếm và ca sai được hiển thị chủ động. Người review tin một công trình dám tự chỉ ra chỗ yếu.
4. **Ba bề mặt, một sự thật.** Web app, slide và report phải khớp nhau về con số, thuật ngữ và giọng. Mâu thuẫn giữa chúng phá huỷ độ tin cậy nhanh hơn bất kỳ lỗi nào khác.
5. **Đọc đúng quan trọng hơn đọc đẹp.** Đây là công cụ y tế research, không phải sản phẩm tiêu dùng. Không hiệu ứng nào được cạnh tranh với số liệu.

## Accessibility & Inclusion

- **Thông tin không bao giờ chỉ mã hoá bằng màu.** Ác/lành, mức tin cậy và trạng thái `defer` phải luôn kèm nhãn chữ hoặc hình dạng. Mù màu đỏ-lục phổ biến ở nam giới, và bác sĩ chẩn đoán hình ảnh không phải ngoại lệ.
- **Tương phản tối thiểu WCAG AA**, tính cả trên overlay heatmap chồng lên ảnh MRI xám.
- **Slide phải đọc được từ cuối phòng họp**, trên máy chiếu có thể mất tương phản.
- Tôn trọng `prefers-reduced-motion`.
- Tiếng Việt có dấu — phải chọn được font hiển thị đúng toàn bộ dấu thanh và dấu phụ, kể cả ở cỡ chữ nhỏ trong bảng số liệu.
