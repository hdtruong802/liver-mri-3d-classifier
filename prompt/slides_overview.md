# Prompt: dựng HTML slide tổng quan dự án

Prompt đã dùng để sinh ra [`slides/overview.html`](../slides/overview.html) (commit `54513ac`).
Giữ lại để chạy lại, sửa, hoặc dùng làm khuôn cho slide/report sau này.

**Cách dùng:** dán toàn bộ khối dưới đây vào Claude Code, Codex, hoặc Cursor.
Antigravity không có `/impeccable` — xem [`docs/MULTI_TOOL_WORKFLOW.md`](../docs/MULTI_TOOL_WORKFLOW.md) §9.

---

```text
/impeccable craft

Dựng một file HTML slide trình bày ở `slides/overview.html` — bản tổng quan dự án
phân loại u gan trên MRI 3D. Đây là bề mặt UI đầu tiên của dự án, nên thế giới thị
giác lập ra ở đây sẽ dùng lại cho web app và report sau này.

## Nguồn nội dung
Nền: `MRI_Classification_Spec_Sheet.md`. Đọc `PRODUCT.md` trước khi thiết kế —
mục Product Principles, Brand Commitments, Evidence on Hand, Accessibility.
Đọc `AGENTS.md` §12.

**Được phép và được khuyến khích tìm kiếm thêm trên web** để làm dày phần SOTA
và bối cảnh dataset. Ưu tiên theo thứ tự: paper gốc (arXiv/PubMed/DOI) → trang
challenge/benchmark chính thức → repo GitHub chính chủ. Không dùng blog, không
dùng bài tổng hợp thứ cấp, không dùng nội dung do AI khác sinh ra.

## Người xem
Hội đồng / người review nghiên cứu. Họ có nền kỹ thuật nhưng KHÔNG chuyên sâu
ảnh y tế. Xem trên máy chiếu trong phòng họp, người trình bày nói kèm.
Slide là chỗ dựa cho lời nói, không phải văn bản để đọc.

## Bốn phần, mỗi phần 2–3 slide, tổng 10–14 slide

1. **Bài toán**
   Phân loại 7 lớp tổn thương gan (3 ác: HCC, ICC, di căn — 4 lành: nang, u máu,
   FNH, áp-xe) ở mức ROI, trực tiếp trên volume 3D đa pha 8 thì MRI. Không
   segmentation. Nêu rõ câu hỏi nghiên cứu headline: **trustworthiness** — model
   đưa xác suất đáng tin và biết từ chối khi không chắc để chuyển bác sĩ.
   Động lực lâm sàng: đừng bỏ sót ung thư.

2. **Dataset — và độ phủ của nó trong lĩnh vực y tế**
   LLD-MMRI: 498 bệnh nhân, 1 tổn thương/bn, 8 thì MRI, 7 lớp, có bbox + patch
   cắt sẵn + full-volume, truy cập qua form research-use.
   Phần quan trọng nhất của mục này là **độ phủ**, hãy nói thẳng:
   - Đây là một trong số rất ít bộ MRI gan đa pha public có taxonomy 7 lớp.
     Kiểm chứng lại nhận định này qua tìm kiếm; nếu tìm được bộ khác tương đương,
     sửa lại nhận định cho đúng thay vì giữ nguyên.
   - Không tồn tại bộ public thứ hai cùng taxonomy → external validation buộc
     phải hạ về nhãn thô (ác/lành). Đây là giới hạn thật của cả lĩnh vực.
   - Duke Liver Dataset (2146 series / 105 bn) chỉ dùng làm probe OOD, không có
     nhãn loại tổn thương.
   - n≈500 là nhỏ; test 104 ca là rất nhỏ → phương sai cao. Lớp áp-xe và FNH hiếm.
   Nêu ngắn: split ở mức bệnh nhân, 5-fold CV, test khoá kín chạm đúng một lần.
   Mọi con số về dataset (số bệnh nhân, số series, số lớp) phải trích nguồn công
   bố chính thức của dataset đó.

3. **SOTA và khoảng trống**
   Spec Sheet ghi SOTA trên LLD-MMRI bão hoà quanh 85% accuracy / 85% macro-F1 /
   97% macro-AUC trên test 104 ca. **Xác minh lại ba con số này từ nguồn gốc** và
   sửa nếu sai; nêu rõ chúng đến từ công trình nào.
   Tìm thêm 3–5 công trình tiêu biểu trên LLD-MMRI hoặc phân loại tổn thương gan
   trên MRI đa pha. Với mỗi công trình nêu: tên/phương pháp, năm, metric chính
   kèm con số, và trên tập test nào — vì so số giữa các tập test khác nhau là
   so sai, phải nói rõ.
   ⚠️ Toàn bộ số ở mục này là **kết quả đã công bố của người khác**, không phải
   kết quả của dự án này. Slide phải ghi rõ điều đó ngay cạnh số — không được để
   người xem hiểu nhầm dù chỉ một giây.
   Khoảng trống cần làm nổi bật: các công trình đó báo accuracy/F1/AUC rồi dừng.
   Không ai báo calibration hay selective prediction. Vì test nhỏ và phương sai
   cao, đua thêm vài phần trăm accuracy là vô nghĩa thống kê — nên dự án này
   không đua leaderboard, mà thắng bằng rigor thống kê + calibration + selective
   prediction + external + reproducibility.
   Nhận định "không ai báo calibration/selective prediction" cũng phải được kiểm
   chứng bằng tìm kiếm. Nếu có công trình đã làm, nêu ra và điều chỉnh cách định
   vị cho trung thực — đừng bảo vệ một khoảng trống không còn trống.

4. **Output dự kiến và tính ứng dụng**
   Sản phẩm: web app tự code (FastAPI + frontend thuần) nhận NIfTI/DICOM, trả về
   lớp dự đoán, xác suất từng lớp, xác suất ác tính, mức bất định, cờ `defer`, và
   heatmap Grad-CAM 3D. Latency vài giây trên lesion-crop.
   Trả lời rõ hai câu:
   - **Phục vụ ai:** hướng tới bác sĩ chẩn đoán hình ảnh như một second reader.
     Ở giai đoạn hiện tại, người dùng thực tế là hội đồng review nghiên cứu.
   - **Phục vụ thế nào:** model tự quyết các ca nó chắc chắn, và **chủ động từ
     chối** các ca khó để chuyển bác sĩ. Đường risk–coverage định lượng được
     chính xác lợi ích đó — "model tự xử được bao nhiêu phần trăm ca trong khi
     giữ sai số dưới ngưỡng cho phép". Đây là điều một model chỉ báo accuracy
     không trả lời được.
   Kết bằng: đây là Research Use Only, chưa kiểm định lâm sàng.

## Quy tắc số liệu và trích nguồn — phần dễ sai nhất, đọc kỹ

Có đúng hai loại số trên bộ slide này, xử lý khác hẳn nhau:

**Loại A — số của người khác (đã công bố).** Được dùng, và bắt buộc trích nguồn.
- Mỗi con số phải kèm nguồn ở chân slide chứa nó, dạng ngắn: `[Tên/Tác giả, Năm]`.
- Slide "Tài liệu tham khảo" ở cuối liệt kê đầy đủ: tác giả, tiêu đề, venue/năm,
  và link DOI hoặc arXiv. Mỗi mục phải khớp với một chỉ số đã dùng trong bài.
- **Chỉ trích nguồn mà bạn thực sự đã mở và đọc được.** Không trích theo trí nhớ.
  Không suy ra tên paper từ tên phương pháp. Không bịa số DOI, số arXiv, hay năm.
- Nếu không xác minh được một con số: **bỏ nó đi**, hoặc ghi rõ
  "chưa xác minh được nguồn" ngay tại chỗ. Không đoán, không làm tròn cho đẹp.
- Nếu nguồn tìm được mâu thuẫn với Spec Sheet: **tin nguồn gốc**, sửa lại, và
  báo cho tôi biết chỗ nào lệch để tôi cập nhật Spec Sheet.
- Ghi rõ mỗi số đo trên tập test nào. So số giữa các tập test khác nhau mà không
  nói rõ là trình bày sai lệch.

**Loại B — số của dự án này.** Chưa tồn tại. Cấm tuyệt đối.
- Dự án chưa có dữ liệu, chưa có model, chưa train, chưa có một kết quả nào.
- Không bịa số, không vẽ biểu đồ kết quả giả, không đặt placeholder trông giống
  số thật.
- Cần minh hoạ khái niệm (ví dụ đường risk–coverage) thì vẽ dạng sơ đồ khái niệm
  không có trục số, dán nhãn rõ "minh hoạ khái niệm".
- Trên slide, số loại A và số loại B phải phân biệt được bằng mắt ngay lập tức —
  đây là rủi ro trình bày lớn nhất của cả bộ slide.

## Ràng buộc cứng

- **Tiếng Việt.** Thuật ngữ giữ nguyên tiếng Anh, không dịch: defer, coverage,
  calibration, ECE, macro-F1, AUROC, AURC, OOD, HCC, ICC, FNH, LI-RADS.
- **RUO — Research Use Only, chưa kiểm định lâm sàng** phải hiển thị ở vị trí
  không thể bỏ sót, không chỉ ở slide cuối.
- **Không mã hoá thông tin chỉ bằng màu.** Ác/lành, mức tin cậy, trạng thái defer
  luôn kèm nhãn chữ hoặc hình dạng.
- **Giọng: công cụ y tế nghiêm túc.** Không gradient rực rỡ, không hiệu ứng khoe
  kỹ thuật, không micro-interaction vui vẻ.
- Không trình bày kết quả model như chẩn đoán chắc chắn. Mức bất định là nội dung
  hạng nhất.

## Ràng buộc kỹ thuật

- **Một file HTML tự chứa duy nhất.** CSS và JS inline. Không CDN, không build
  tool, không framework. Phải mở được bằng double-click khi không có mạng.
- Điều hướng bàn phím: mũi tên trái/phải, Space, Home/End. Hiện số slide.
- Chữ đủ lớn để đọc từ cuối phòng họp; tương phản còn giữ được trên máy chiếu
  bị nhạt màu.
- Font phải hiển thị đúng toàn bộ dấu tiếng Việt, kể cả ở cỡ nhỏ.
- Có `@media print` để in ra PDF được, mỗi slide một trang.
- Tôn trọng `prefers-reduced-motion`.

## Bàn giao
Sau khi dựng xong, báo lại cho tôi:
1. Danh sách nguồn đã dùng, kèm nguồn nào xác minh được và nguồn nào không.
2. Chỗ nào Spec Sheet lệch so với nguồn gốc.
3. Nhận định nào trong Spec Sheet bị tìm kiếm bác bỏ.

Rồi chạy tiếp: /impeccable typeset → /impeccable layout → /impeccable critique →
/impeccable audit → /impeccable polish
```

---

## Ghi chú sau lần chạy đầu (2026-07-24)

Ba chỗ prompt này đã chứng minh là **đáng giá nhất**, đừng bỏ khi sửa:

1. **"Chỉ trích nguồn mà bạn thực sự đã mở và đọc được."** Một kết quả tìm kiếm
   trả về "accuracy 80,8% → 95,5% với 34,2% abstention". Mở paper gốc thì đó là
   công trình về **u sọ hầu**, không phải gan. Không có dòng này thì slide đã
   mang một con số sai hoàn toàn.
2. **"Nếu nguồn mâu thuẫn với Spec Sheet thì tin nguồn gốc."** Ba con số SOTA
   trong Spec Sheet đều cao hơn thực tế (chi tiết ở WORKLOG S-005).
3. **"Đừng bảo vệ một khoảng trống không còn trống."** Tìm kiếm bác bỏ một phần
   nhận định "không ai báo calibration/selective prediction".

Điều prompt **thiếu** và nên thêm nếu chạy lại: một dòng cấm
`text-transform: uppercase`. Bản dựng đầu có 31 chuỗi in hoa dài tới 108 ký tự,
và dấu thanh tiếng Việt trên chữ hoa bị chèn ép ở cỡ nhỏ. Nay đã thành luật
trong [`DESIGN.md`](../DESIGN.md) (`The No-Uppercase Rule`) nên lần sau tự động
được áp — nhưng chỉ với tool có đọc DESIGN.md.
