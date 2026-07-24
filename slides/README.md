# slides/ — hai bản để so sánh

Cùng nội dung, cùng số liệu đã xác minh, khác thế giới thị giác. Mở cả hai bằng
double-click, bấm mũi tên trái/phải để duyệt.

| File | Thế giới | Trạng thái |
|---|---|---|
| [`overview.html`](overview.html) | **Canon talk MICCAI/MIDL** | ✅ Đã chốt. Tuân theo [`DESIGN.md`](../DESIGN.md). |
| [`overview-alt-atlas.html`](overview-alt-atlas.html) | **Bản khắc atlas giải phẫu** | 🔍 Đối chiếu. Cố tình đi ra ngoài DESIGN.md. |

---

## Khác nhau ở đâu

| | `overview.html` (canon) | `overview-alt-atlas.html` |
|---|---|---|
| Nền | Giấy sáng `#F6F7F8` | Mực sâu `#10161B` |
| Chữ | Một họ sans hệ thống | Cambria chân phương cho tiêu đề, sans cho số liệu |
| Khung | Không khung, chỉ kẻ hairline phân vùng | Khung kẻ đôi bao quanh mỗi bản khắc |
| Trích nguồn | `[Tác giả, Năm]` viết thẳng ở chân slide | **Chú số¹ + chú giải ở chân bản khắc** |
| Sắc dữ liệu | Xanh lâm sàng và cam đất nung | Hoàng thổ và lam ngọc |
| Đánh số | "7 / 13" | "Bản khắc VII" + "7 / 13" |
| Nhịp | Thẳng, khô, đọc nhanh | Chậm hơn, có nghi thức |

Chỗ khác biệt đáng cân nhắc nhất là **hệ trích nguồn**. Bản atlas dùng chú số và
chú giải, vốn là thiết bị gốc của bản khắc giải phẫu, nên nội dung slide sạch hơn
và ít bị chú thích chen ngang. Bù lại, người xem phải liếc xuống chân slide mới
biết con số đến từ đâu — với hội đồng đang soi số liệu thì đó là một bước thừa.

Bản canon đặt `[Tác giả, Năm]` ngay tại chỗ, xấu hơn nhưng không bắt ai phải tra.

## Cả hai đều giữ nguyên các ràng buộc cứng

Đây không phải chỗ để đánh đổi. Cả hai file đều có:

- RUO trên **13/13** slide, ở vị trí không thể bỏ sót
- **Không một con số nào của dự án này** — chưa có kết quả, và không được bịa
- Ác/lành phân biệt bằng **hình dạng cộng nhãn chữ**, không bao giờ chỉ bằng màu
- Nét đứt cộng nhãn chữ = "chưa có dữ liệu"
- Không `text-transform: uppercase` (dấu tiếng Việt trên chữ hoa bị chèn ép)
- Một file tự chứa, **0 tham chiếu ngoài**, mở được ngoại tuyến
- Điều hướng bàn phím, `@media print`, tôn trọng `prefers-reduced-motion`

## Nếu bạn chọn bản atlas

Đừng chỉ đổi file. Phải làm ba việc, theo thứ tự:

1. **Viết lại [`DESIGN.md`](../DESIGN.md)** theo thế giới mới. File đó chi phối cả
   web app và report sau này, nên để nguyên bản canon trong khi slide dùng atlas
   là tạo drift ngay từ deliverable đầu tiên.
2. **Gỡ dòng ignore** `slides/overview-alt-*.html` trong `.impeccable/config.json`.
   Nó tồn tại vì file này *đang* là artifact đối chiếu; khi nó thành bản chính thì
   phải chịu detector soi như mọi bề mặt khác.
3. Đổi tên file thành `overview.html` và ghi một entry vào [`WORKLOG.md`](../WORKLOG.md).

Giữ nguyên ignore rồi coi bản atlas là chính thức là cách tự tắt đèn báo — đúng
thứ [`docs/MULTI_TOOL_WORKFLOW.md`](../docs/MULTI_TOOL_WORKFLOW.md) cảnh báo.
