# slides/

| File | Thế giới | Bản khắc | Dùng cho | Trạng thái |
|---|---|---|---|---|
| [`overview.html`](overview.html) | Bản khắc atlas giải phẫu | 12 | Giới thiệu dự án nói chung | ✅ Bản chính thức |
| [`overview_v2.html`](overview_v2.html) | Bản khắc atlas giải phẫu | 7 + phụ lục nguồn | Báo cáo nội bộ VSF 28/07/2026 | ✅ Dựng xong, chưa soát trên máy chiếu |
| [`sprint_1.html`](sprint_1.html) | Bản khắc atlas giải phẫu | 7 | Báo cáo tiến độ 07/08/2026, **deck đầu tiên mang số đo được** | ✅ Dựng xong, in đúng 7 trang |

> `sprint_1.html` trước đây tên là `overview_v3.html`, đổi tên 2026-08-10 (nội dung không
> đổi một byte nào). Các entry WORKLOG từ S-112 trở về trước gọi nó bằng tên cũ.

Ba deck **song song**, không thay thế nhau. Cùng một thế giới thị giác, khác mạch kể:

- **v1 (12 bản khắc)** đi từ *bài toán → dataset → SOTA → ứng dụng → nguồn*. Có slide
  output UI và slide input/output chi tiết.
- **v2 (7 bản khắc)** đi từ *nỗi đau ngành → thị trường → khoảng trống nghiên cứu →
  kỹ thuật → metric → lộ trình*. Ngắn hơn, nặng về **trích dẫn ngoài**: mọi luận điểm
  ở slide 2–4 đều neo vào một công bố có DOI. Nguồn dồn vào một **slide phụ lục** đặt
  sau slide 7 (không đánh số vào 7, và không có dải mốc phần).
- **`sprint_1` (7 bản khắc)** đi từ *bài toán → dữ liệu → mốc đối chiếu → mô hình → kết quả →
  hướng đi tiếp*. Đây là deck **đầu tiên mang số đo được của dự án**, gồm cả kết quả
  test-104. Vì vậy nó là deck đầu tiên chịu ràng buộc Loại B của
  [`DESIGN.md`](../DESIGN.md): mỗi con số phải kèm **CI** và **tên tập đo được**.
  Có 5 mốc phần thay vì 4 như v2.

Mỗi file tự chứa, mở bằng double-click. In ra PDF được (mỗi bản khắc một trang ngang,
URL tự hiện trong ngoặc). Điều hướng: mũi tên trái/phải, Space, PageUp/PageDown,
Home/End. **v1 có thêm nút Trước/Sau ở đáy màn hình; v2 và `sprint_1` cố ý bỏ nút này** — deck
chỉ điều khiển bằng bàn phím, không có phần tử nào nổi lên trên nội dung khi trình chiếu.

> ⚠️ **v1 và v2 in ra thừa trang** (v2: 15 trang cho 8 bản khắc). Nguyên nhân là các mức
> sàn `rem` trong thang chữ: khi in, `1rem` = 4,23mm trong khi `--u` chỉ còn ~2,6mm, nên
> sàn thắng và chữ to lên tương đối chừng 23% so với bản màn hình, đủ để bề mặt đặc tràn
> sang trang sau. **`sprint_1` đã sửa** bằng cách cho thang chữ suy thẳng từ `--u` trong
> `@media print` (xem chú thích trong file). Nếu sửa v1/v2 thì chép cùng khối đó, và
> đừng ghim `--u` thành một giá trị mm cố định: Chrome headless mặc định in khổ Letter
> 279×216mm chứ không phải A4, hardcode bề rộng sẽ tràn ngang.

Hệ thống thị giác đầy đủ ở [`DESIGN.md`](../DESIGN.md). Prompt đã dùng để sinh từng file:
[`prompt/slides_overview.md`](../prompt/slides_overview.md) cho v1,
[`prompt/slides_overview_v2.md`](../prompt/slides_overview_v2.md) cho v2.

---

## Đã chốt thế giới thị giác (2026-07-24)

Dự án dựng **hai bản chạy được** rồi so trực tiếp:

- **Canon talk MICCAI/MIDL** — nền giấy sáng, một họ sans, trích dẫn `[Tác giả, Năm]`
  viết thẳng tại chỗ. **Đã bị loại.** Còn trong git ở commit `54513ac`.
- **Bản khắc atlas giải phẫu** — nền mực sâu, nét khắc sáng, chữ chân phương cho
  tiêu đề, khung kẻ đôi, và **chú số cộng chú giải** làm hệ trích nguồn. **Đã chọn.**

Lý do quyết định không phải thẩm mỹ: bản khắc atlas có sẵn thiết bị *chú số và
đường dóng*, và dự án này cần đúng thứ đó — mọi con số phải truy được về nguồn
công bố. Hệ trích nguồn mọc ra từ ngữ pháp của thế giới, không bị dán vào.

Đánh đổi đã chấp nhận: nền tối cần phòng chiếu **có giảm sáng**. Nếu buổi báo cáo
diễn ra trong phòng bật đèn đầy đủ thì nền sáng sẽ an toàn hơn. Ghi lại trong
`DESIGN.md` để không ai phát hiện lại rồi tưởng là lỗi.

## Ràng buộc cứng, không được đánh đổi

- RUO trên **mọi** bản khắc của cả hai deck (12/12 ở v1, 8/8 kể cả phụ lục ở v2)
- **Không một con số nào của dự án này** — chưa có kết quả, và không được bịa
- Ác/lành phân biệt bằng **hình dạng cộng nhãn chữ**, không bao giờ chỉ bằng màu
- Nét đứt cộng nhãn chữ = "chưa có dữ liệu"
- Không `text-transform: uppercase` (dấu tiếng Việt trên chữ hoa bị chèn ép)
- Mọi số của người khác mang **chú số dẫn về chú giải có link tới paper gốc**
- Tự chứa: CSS và JS inline, không CDN, không webfont, mở được ngoại tuyến
  *(có 14 hyperlink tới nguồn — bấm thì cần mạng, nhưng file vẫn mở và hiển thị
  đầy đủ khi không có mạng)*

## Số liệu trên slide đến từ đâu

Mọi con số đều là **kết quả đã công bố của nhóm khác**, đã mở nguồn gốc đối chiếu.

### `overview.html` (v1)

| Chú số | Nguồn |
|---|---|
| 1 | [LLD-MMRI Dataset](https://github.com/LMMMEng/LLD-MMRI-Dataset) · [LLD-MMRI2023 Challenge](https://github.com/LMMMEng/LLD-MMRI2023) |
| 2 | [Macdonald et al., *Radiol Artif Intell* 2023](https://doi.org/10.1148/ryai.220275) — Duke Liver Dataset |
| 3 | [LLD-MMRI2023 test leaderboard](https://github.com/LMMMEng/LLD-MMRI2023/blob/main/assets/test_leaderboard.md) |
| 4 | [Lou et al., *Neural Networks* 185 (2025)](https://arxiv.org/abs/2402.17246) — SDR-Former |
| 5 | [Wang et al., arXiv:2110.08817 (2021)](https://arxiv.org/abs/2110.08817) |

⚠️ **Spec Sheet đang lệch so với các nguồn này** ở ba con số SOTA và một nhận định
về khoảng trống nghiên cứu. Slide dùng số đã xác minh; Spec Sheet chưa được sửa.
Chi tiết ở [`WORKLOG.md`](../WORKLOG.md) entry S-005.

### `overview_v2.html` (v2)

Bộ chú số riêng, không dùng chung đánh số với v1. Toàn bộ fetch trực tiếp bản gốc
trong phiên S-055 (2026-07-28).

| Chú số | Nguồn | Dùng ở |
|---|---|---|
| 1 | [Vu et al., *Korean J Radiol* 2023;24(11)](https://doi.org/10.3348/kjr.2023.0829) — thiếu hụt bác sĩ CĐHA tại Việt Nam | Slide 2 |
| 2 | [Zamani et al., *JACR* 2026](https://doi.org/10.1016/j.jacr.2025.12.026) — 46,4 triệu lượt chụp, phân bố khối lượng đọc | Slide 2 |
| 3 | [Brady, *Insights Imaging* 2017;8(1)](https://doi.org/10.1007/s13244-016-0534-1) — tỷ lệ sai sót 3–5% và ~30% | Slide 2 |
| 4 | [Vosshenrich et al., *Radiology* 2021;298(3)](https://doi.org/10.1148/radiol.2021203486) — chất lượng báo cáo giảm trong ca | Slide 2 (biểu đồ) |
| 5 | [Sivakumar et al., *JAMA Netw Open* 2025;8(11)](https://doi.org/10.1001/jamanetworkopen.2025.42338) — 723 thiết bị, 97% qua 510(k) | Slide 3 |
| 6 | [LLD-MMRI2023 test leaderboard](https://github.com/LMMMEng/LLD-MMRI2023/blob/main/assets/test_leaderboard.md) | Slide 4, 6 |
| 7 | [LLD-MMRI Dataset](https://github.com/LMMMEng/LLD-MMRI-Dataset) · [Challenge](https://github.com/LMMMEng/LLD-MMRI2023) | Slide 5 |
| 8 | [Kompa, Snoek & Beam, *npj Digit Med* 2021;4:4](https://doi.org/10.1038/s41746-020-00367-3) — trích dẫn về abstention và calibration | Slide 4 |
| 9 | Bản đồ sản phẩm, tổng hợp ở [`docs/industry_landscape.md`](../docs/industry_landscape.md) (19 nguồn, kiểm 7/2026) | Slide 3 |
| 10 | Ảnh tám thì tổng hợp — xem [`assets/ATTRIBUTION.md`](assets/ATTRIBUTION.md) | Slide 1 |

Phụ lục của v2 **chỉ dẫn link ngoài**. Không trỏ vào file `.md` nào trong repo
(`docs/industry_landscape.md`, `assets/ATTRIBUTION.md`) — bảng trên là chỗ ghi lại
đường truy vết nội bộ đó, còn slide thì đứng độc lập khi gửi ra ngoài.

> ⚠️ **Mục tiêu macro-F1 của v2 là 0,85–0,90, cao hơn đội nhất challenge (0,8322).**
> Người dùng chốt mức này (2026-07-28, WORKLOG S-055). Nó **mâu thuẫn** với định vị
> "không đua accuracy leaderboard" đang ghi ở `AGENTS.md` §5 và `PRODUCT.md`. Hai chỗ
> đó chưa được sửa. Ai đọc thấy lệch thì đây là lý do, không phải nhầm lẫn.

**Đã loại có chủ ý khi dựng v2** (ghi lại để không ai đi tìm lại):

- *Biểu đồ "thời gian chẩn đoán thủ công"* — không có nguồn đo thật. Thay bằng biểu đồ
  chú số 4, là số thật có `n=`.
- *"30,8% nghiên cứu báo cáo calibration"* — bản gốc MDPI chặn truy cập, không verify
  được. Luận điểm khoảng trống dùng trích dẫn chú số 8 thay thế.
- *Hu et al. 2025 (F1 0,84)* — Springer paywall. Nhắc tên công trình, không trích số.
- *Median iBiopsy sensitivity 92%* — chỉ có nguồn thông cáo báo chí. Thông cáo báo chí
  chỉ được dùng để xác nhận **trạng thái sản phẩm**, không dùng cho số hiệu năng.
