---
name: Liver MRI Classifier — Web App
description: Hệ thị giác riêng cho web app demo, bàn đọc tối kiểu trạm chẩn đoán hình ảnh
scope: webapp/
colors:
  pacs-950: "#070A13"
  pacs-900: "#0B1020"
  pacs-850: "#0F1525"
  pacs-800: "#141B2E"
  pacs-700: "#1C2540"
  accent: "#22D3EE"
  accent-glow: "#67E8F9"
  text-primary: "#FFFFFF"
  text-secondary: "#CBD5E1"
  text-muted: "#94A3B8"
  state-ok: "#34D399"
  state-warn: "#FBBF24"
  state-danger: "#FB7185"
typography:
  headline:
    fontFamily: "Inter, system-ui, Segoe UI, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.2
  metric:
    fontFamily: "Inter, system-ui, Segoe UI, sans-serif"
    fontSize: "1.875rem"
    fontWeight: 700
    lineHeight: 1.1
    fontFeature: "tnum"
  title:
    fontFamily: "Inter, system-ui, Segoe UI, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: "Inter, system-ui, Segoe UI, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Inter, system-ui, Segoe UI, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0.05em"
  data:
    fontFamily: "JetBrains Mono, ui-monospace, Consolas, monospace"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.4
    fontFeature: "tnum"
rounded:
  chip: "9999px"
  control: "0.75rem"
  panel: "1rem"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  xxl: "40px"
components:
  panel:
    backgroundColor: "{colors.pacs-850}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.body}"
    rounded: "{rounded.panel}"
    padding: "20px"
  ruo-bar:
    backgroundColor: "{colors.pacs-900}"
    textColor: "{colors.text-muted}"
    typography: "{typography.label}"
    rounded: "0"
    padding: "8px 24px"
  chip:
    backgroundColor: "{colors.pacs-800}"
    textColor: "{colors.text-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.chip}"
    padding: "4px 10px"
  btn-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.pacs-950}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "10px 16px"
---

# Design System: Liver MRI Classifier — Web App

> **Phạm vi: chỉ `webapp/`.** `DESIGN.md` ở gốc repo ("bản khắc atlas") chi phối `slides/` và `reports/`, và `slides/overview_v2.html` đang dùng nó. Hai hệ cố ý khác nhau. Cái phải khớp giữa các bề mặt là **con số, thuật ngữ và giọng** (`PRODUCT.md` Product Principle 4), không phải lớp nhìn.
>
> **Lịch sử:** hệ này thay hướng "hải đồ đo sâu" nền sáng dựng ở WORKLOG S-076. Người dùng xem bản dựng rồi chọn quay về bố cục bản bolt.new gốc với theme tối (S-077). Hướng cũ không còn hiệu lực ở đâu cả; đừng khôi phục từng mảnh của nó.

## Overview

**Bàn đọc tối — trạm chẩn đoán hình ảnh.**

Nền mực xanh đen, panel nổi nhẹ, một sắc cyan làm accent. Đây là ngôn ngữ của phòng đọc phim: màn hình tối để mắt không loá khi nhìn ảnh xám, và **ảnh MRI là thứ sáng nhất trên màn hình**.

Tính cách: gọn, có nhịp, dày thông tin nhưng không chật. Panel bo góc, chiều sâu nhẹ. Chuyển động ít và chỉ để giải thích trạng thái.

**Điều hệ này phải làm được, ngoài chuyện trông ổn:** người review nhìn màn hình phải phân biệt ngay **cái gì là dữ liệu thật, cái gì là số minh hoạ**. Chưa có checkpoint, nên mọi con số suy luận hiện tại đều là giả lập. Hệ thị giác nào làm mờ ranh giới đó là đang phản bác chính nghiên cứu.

## Colors

### Nền

| Token | Hex | Việc |
|---|---|---|
| `pacs-950` | `#070A13` | nền trang |
| `pacs-900` | `#0B1020` | header, dải RUO, chân trang |
| `pacs-850` | `#0F1525` | panel |
| `pacs-800` | `#141B2E` | panel nổi, ô số liệu bên trong panel |
| `pacs-700` | `#1C2540` | viền, đường phân cách |

### Accent

**Cyan** `#22D3EE` — hành động chính, tiêu đề mục, chỉ báo đang hoạt động. `#67E8F9` cho hover.

### Chữ

| Token | Hex | Tương phản trên `pacs-850` | Việc |
|---|---|---|---|
| trắng | `#FFFFFF` | 17,4:1 | tiêu đề, số chính |
| `slate-300` | `#CBD5E1` | 12,3:1 | chữ chạy |
| `slate-400` | `#94A3B8` | 7,1:1 | **sàn — chữ nhỏ nhất được phép** |

### Trạng thái

`#34D399` đủ / xong · `#FBBF24` cần chú ý, `defer` · `#FB7185` nhóm ác

### Vùng chú giải trên ảnh

`#E879F9` mask tổn thương · `#F5D0FE` bản nhạt (chữ trên nền tối)

Cố ý nằm **ngoài** cả bảng bảy lớp lẫn bảng trạng thái. Mask không phải một lớp và không phải một trạng thái — nó là một vùng do **người chú giải** khoanh, có sẵn trong bộ dữ liệu LLD-MMRI. Dùng màu lớp cho nó (ví dụ `#38BDF8` của "nang") sẽ khiến người xem đọc vùng khoanh thành một chẩn đoán; dùng màu trạng thái sẽ đọc thành một cảnh báo.

Vẽ **viền đặc + ruột nhuộm 25%**, không tô kín: bác sĩ cần nhìn thấy pixel bên dưới để tự đánh giá, và một mảng màu kín che đúng chỗ đang cần đọc.

⚠️ Mọi chỗ hiển thị mask phải nói rõ đây **không phải đầu ra của model** — dự án không làm segmentation (`AGENTS.md` §3.9).

### Bản đồ chú ý của mô hình

`#F59E0B` Grad-CAM · `#FCD34D` bản nhạt

Phải khác hẳn màu vùng chú giải ở trên. Hai thứ trông giống nhau nhưng **ngược nhau về bản chất**: `annotation` là vùng **người** khoanh — ground truth; `attention` là chỗ **mô hình** nhạy — phỏng đoán, và với ca mô hình đoán sai thì nó *nên* trông sai. Lẫn hai thứ này là hiểu nhầm tệ nhất app có thể gây ra, nên chúng nằm ở hai phía đối diện của vòng màu và không bao giờ xuất hiện trong cùng một ảnh.

Phủ theo **alpha trên nền xám**, không thay màu nền: cường độ mô bên dưới phải còn đọc được, nếu không thì bản đồ che mất chính thứ nó đang chỉ vào. Dưới ngưỡng 0.15 thì không tô gì — một lớp mờ phủ khắp ảnh không thêm thông tin nào.

⚠️ Chỗ hiển thị bản đồ **bắt buộc** nói rõ hai điều: (1) đây là khối crop mô hình thực sự nhìn, không phải lát gốc; (2) độ phân giải **gốc** của bản đồ trước khi nội suy. Một bản đồ 7×7×2 phóng lên 112×112×32 trông mịn tới từng voxel nhưng không hề mịn.

### Bảy màu lớp

- **ác:** HCC `#EF4444` · di căn `#F97316` · ICC `#FB7185`
- **lành:** FNH `#22C55E` · u máu `#14B8A6` · nang `#38BDF8` · áp-xe `#A3E635`

Nhóm ác dùng dải ấm, nhóm lành dùng dải lạnh. Đây là tuyến mã hoá **thứ hai**, không phải tuyến duy nhất. Nang dùng `#38BDF8` chứ không phải `#06B6D4` để không đụng accent cyan.

### Named Rules

**The 4.5 Rule.** Chữ nhỏ nhất được phép là `slate-400` `#94A3B8`. `slate-500` (`#64748B`, **3,82:1**) và `slate-600` (`#475569`, **2,40:1**) trượt WCAG AA và **không được dùng cho chữ** — chỉ cho viền và nền. Bản bolt gốc dùng đúng hai màu đó cho chữ metadata và dòng disclaimer; đây là chỗ duy nhất hệ này cố ý lệch khỏi bản tham chiếu.

**The Never-Colour-Alone Rule.** Không thông tin nào chỉ mã hoá bằng màu. Lớp tổn thương luôn kèm nhãn chữ và nhãn nhóm "ác"/"lành"; `defer` luôn kèm nhãn chữ và icon; trạng thái thì luôn kèm chữ "đủ"/"thiếu". Bài kiểm: khử màu ảnh chụp màn hình — mất thông tin là thiết kế sai. (`PRODUCT.md` Accessibility & Inclusion; mục này **không** nằm trong phần ràng buộc đã được gỡ.)

**The Accent Budget.** Cyan là accent duy nhất. Bảy màu lớp chỉ sống trong biểu đồ xác suất và dải chú giải, không tràn ra chrome. Ba màu trạng thái chỉ mang nghĩa trạng thái.

## Typography

**`Inter`** cho toàn bộ giao diện. **`JetBrains Mono`** cho định danh và giá trị đo: `case_id`, tên file, entropy, spacing mm. Cả hai tự host qua `@fontsource`, không CDN.

**Cả hai phải phủ đủ dấu tiếng Việt** — ràng buộc cứng. Kiểm bằng cách xác nhận subset `vietnamese` có mặt trong `dist/` sau build, không phải bằng cách nhìn.

### Named Rules

**The No-Uppercase Rule.** `text-transform: uppercase` **không dùng cho chữ tiếng Việt**. Lý do là kỹ thuật, không phải khẩu vị: dấu thanh chồng dấu phụ vỡ trên chữ hoa ở cỡ nhỏ (Ế, Ữ, Ậ, Ổ). Bản bolt dùng `uppercase tracking-wider` cho mọi nhãn; ở đây bỏ `uppercase`, giữ `tracking-wider` cộng cỡ chữ và màu để tạo cảm giác nhãn. Viết tắt vốn đã là chữ hoa không dấu (`HCC`, `ICC`, `FNH`, `ECE`, `AURC`, `OOD`, `DWI`, `T2WI`) giữ nguyên — đó không phải `text-transform`.

**The Tabular Rule.** Mọi con số dùng `font-variant-numeric: tabular-nums`. Số nhảy cột khi cập nhật là lỗi đọc.

## Shapes & Depth

Panel bo `1rem`, control bo `0.75rem`, chip bo tròn hoàn toàn. Viền `1px` màu `pacs-700` hoặc `white/10`.

Chiều sâu đến từ hai cấp nền cộng viền mảnh. `shadow-glow` (`0 0 24px -4px rgba(34,211,238,.45)`) chỉ dùng cho **hành động chính lúc hover** và vùng thả file đang active — không rải lên panel tĩnh.

## Đánh dấu số minh hoạ

Backend khai nguồn gốc ở `provenance.source` của mọi phản hồi. Khi nó là `simulated`, UI bắt buộc dựng **hai tín hiệu độc lập**:

1. **Badge chữ** cạnh khối số: "minh hoạ, chưa có model".
2. **Chữ nghiêng** cho chính con số.

Màu **không** nằm trong hai tín hiệu này — chúng phải sống sót qua bản khử màu và qua screen reader.

Khi `source` thành `oof` hoặc `live`, cả hai tự tắt.

## Dải RUO

Full-width, ngay dưới header, **dính trên cùng, không bao giờ cuộn khuất**. Nội dung: "Research Use Only: chưa kiểm định lâm sàng".

Bản bolt gốc không có khối này. Nó bắt buộc (`AGENTS.md` §3.1, `PRODUCT.md` Brand Commitment 1) và không phải một lựa chọn thiết kế.

## Motion

Ngân sách nhỏ. **Được phép:** `fade-in` khi khối kết quả xuất hiện, `pulse-soft` cho chỉ báo đang chạy, đổi lát khi kéo. **Không:** hiệu ứng quét, số đếm lên, panel trượt vào, hover nảy.

`prefers-reduced-motion: reduce` → mọi chuyển động về 0.

## Do's and Don'ts

### Do
- **Do** cho mọi thứ mã hoá bằng màu một nhãn chữ hoặc icon đi kèm.
- **Do** dùng cả badge chữ lẫn chữ nghiêng cho số minh hoạ.
- **Do** giữ `slate-400` làm sàn cho chữ.
- **Do** để ảnh MRI là thứ sáng nhất màn hình.
- **Do** kiểm tương phản bằng số. Nền tối đánh lừa mắt rất giỏi.

### Don't
- **Don't** dùng `slate-500` hay `slate-600` cho chữ (The 4.5 Rule).
- **Don't** dùng `text-transform: uppercase` cho chữ tiếng Việt.
- **Don't** hiển thị chỉ số pipeline không tính: **không có** epistemic/aleatoric tách đôi, chỉ có `entropy` và `ensemble_std`.
- **Don't** viết câu chỉ định lâm sàng ("cần sinh thiết", "nên theo dõi sát"). Ràng buộc RUO, không phải lựa chọn giọng.
- **Don't** bịa định danh bệnh nhân, ngày khám, hay phiên bản model.
- **Don't** rải `shadow-glow` lên panel tĩnh.
- **Don't** sinh ảnh MRI giả. Chưa có dữ liệu thì hiện trạng thái rỗng có nhãn.
