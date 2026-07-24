# slides/

| File | Thế giới | Trạng thái |
|---|---|---|
| [`overview.html`](overview.html) | Bản khắc atlas giải phẫu | ✅ Bản chính thức |

13 bản khắc, một file tự chứa, mở bằng double-click. Điều hướng: mũi tên trái/phải,
Space, Home/End. In ra PDF được (mỗi bản khắc một trang ngang, URL tự hiện trong ngoặc).

Hệ thống thị giác đầy đủ ở [`DESIGN.md`](../DESIGN.md). Prompt đã dùng để sinh file
này ở [`prompt/slides_overview.md`](../prompt/slides_overview.md).

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

- RUO trên **13/13** bản khắc, ở vị trí không thể bỏ sót
- **Không một con số nào của dự án này** — chưa có kết quả, và không được bịa
- Ác/lành phân biệt bằng **hình dạng cộng nhãn chữ**, không bao giờ chỉ bằng màu
- Nét đứt cộng nhãn chữ = "chưa có dữ liệu"
- Không `text-transform: uppercase` (dấu tiếng Việt trên chữ hoa bị chèn ép)
- Mọi số của người khác mang **chú số dẫn về chú giải có link tới paper gốc**
- Tự chứa: CSS và JS inline, không CDN, không webfont, mở được ngoại tuyến
  *(có 14 hyperlink tới nguồn — bấm thì cần mạng, nhưng file vẫn mở và hiển thị
  đầy đủ khi không có mạng)*

## Số liệu trên slide đến từ đâu

Mọi con số đều là **kết quả đã công bố của nhóm khác**, đã mở nguồn gốc đối chiếu:

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
