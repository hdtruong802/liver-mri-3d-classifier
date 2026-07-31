---
name: Liver MRI Classifier — Web App
description: Hệ thị giác riêng cho bề mặt web app demo, dựng trên ngữ pháp hải đồ đo sâu
scope: webapp/
colors:
  paper: "#F5F6F4"
  land: "#E4D8B8"
  shoal-1: "#DCE9F0"
  shoal-2: "#B8D4E4"
  shoal-3: "#8FBBD4"
  ink: "#16202A"
  ink-secondary: "#4A5A66"
  ink-tertiary: "#525C66"
  hairline: "#C3CBD1"
  rule: "#8C99A2"
  caution: "#C0247E"
  drying: "#7C9455"
typography:
  chart-title:
    fontFamily: "Archivo Narrow, Arial Narrow, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 2.6vw, 2.2rem)"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "0.01em"
  headline:
    fontFamily: "Archivo Narrow, Arial Narrow, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(1.25rem, 1.9vw, 1.5rem)"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "normal"
  sounding:
    fontFamily: "Archivo, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(1.3rem, 2.1vw, 1.65rem)"
    fontWeight: 500
    lineHeight: 1.1
    letterSpacing: "normal"
    fontFeature: "tnum"
  body:
    fontFamily: "Archivo, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(0.94rem, 1.3vw, 1.05rem)"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "normal"
  legend:
    fontFamily: "Archivo Narrow, Arial Narrow, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(0.8rem, 1.05vw, 0.88rem)"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0.015em"
  marginalia:
    fontFamily: "Archivo Narrow, Arial Narrow, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(0.72rem, 0.95vw, 0.8rem)"
    fontWeight: 400
    lineHeight: 1.35
    letterSpacing: "0.02em"
rounded:
  none: "0"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "28px"
  xl: "44px"
  xxl: "72px"
components:
  chart-panel:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "28px"
  marginalia-block:
    backgroundColor: "{colors.land}"
    textColor: "{colors.ink-secondary}"
    typography: "{typography.marginalia}"
    rounded: "{rounded.none}"
    padding: "12px 16px"
  caution-overprint:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.caution}"
    typography: "{typography.legend}"
    rounded: "{rounded.none}"
    padding: "16px 20px"
  sounding-cell:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.sounding}"
    rounded: "{rounded.none}"
    padding: "8px 12px"
---

# Design System: Liver MRI Classifier — Web App

> **Phạm vi: chỉ `webapp/`.** `DESIGN.md` ở gốc repo ("bản khắc atlas") vẫn chi phối `slides/` và `reports/`, và `slides/overview_v2.html` đang dùng nó. Hai hệ thống cố ý khác nhau. Cái phải khớp giữa ba bề mặt là **con số, thuật ngữ và giọng** (`PRODUCT.md` Product Principle 4), không phải lớp nhìn.

## Overview

**Creative North Star: "The Sounding Chart"**

Thế giới thị giác là **hải đồ đo sâu**.

Lý do chọn không phải liên tưởng hàng hải. Hải đồ là hệ thông tin duy nhất đã có sẵn, thành quy ước xuất bản, đúng thứ dự án này cần: một tấm bản đồ **tự khai báo chỗ nào của chính nó đáng tin tới đâu**. Người đi biển đọc sơ đồ *Zone of Confidence* để biết vùng nào được khảo sát kỹ, vùng nào chỉ đo thưa, vùng nào chưa ai đo. Vùng chưa khảo sát **được vẽ ra bằng gạch chéo**, không bị làm mượt cho đẹp bản đồ.

Đó chính là calibration cộng selective prediction, đã tồn tại hàng trăm năm dưới dạng một quy ước in ấn. Hệ trích nguồn và hệ báo bất định không bị dán vào từ ngoài — chúng **mọc ra từ ngữ pháp của thế giới này**.

Bốn thiết bị mượn nguyên vẹn, mỗi thứ mang một nghĩa dữ liệu:

| Thiết bị hải đồ | Nghĩa gốc | Nghĩa trong app |
|---|---|---|
| **Sounding** | số đo độ sâu tại một điểm thật | xác suất từng lớp, in ra như số đo chứ không làm mượt thành bề mặt |
| **Zone of Confidence** | vùng này được khảo sát kỹ tới đâu | mức tin cậy của ca, ngưỡng `defer`, `coverage` |
| **Gạch chéo "chưa khảo sát"** | chưa ai đo vùng này | chưa có dữ liệu thật: Grad-CAM chưa có, số giả lập |
| **Overprint magenta** | thông tin mang tính cảnh báo | cờ `defer` và mọi cảnh báo, không dùng vào việc gì khác |

Tính cách: khô, dày đặc, chính xác, không cảm tính. Đây là tài liệu vận hành, không phải sản phẩm tiêu dùng. Phẳng tuyệt đối — hải đồ là giấy in.

**Rủi ro đã biết, ghi lại để không quên.** Hải đồ là hệ dày. Dựng non tay thì nó thành trang trí hàng hải dán lên một dashboard — tệ hơn cả bản bolt đã bỏ. **Ranh giới tự đặt: mọi ký hiệu mượn từ hải đồ phải mang một nghĩa của dữ liệu. Ký hiệu nào chỉ để trông giống hải đồ thì bỏ.** Không có neo, không có bánh lái, không có la bàn hoa gió, không có giấy ố vàng làm giả.

## Colors

Bảng màu là **bảng màu hải đồ thật**, không phải bảng lấy cảm hứng. Trên hải đồ, nước càng **nông** thì càng **xanh đậm** — xanh nghĩa là cẩn thận, không phải nghĩa yên tâm. Luật đó được giữ nguyên.

### Ground
- **Giấy Hải Đồ** (`#F5F6F4`): nền chính, ứng với vùng nước sâu. Trắng ngả xám rất nhẹ, **không phải kem, không phải giấy cũ**.
- **Đất Liền** (`#E4D8B8`): buff, cấp nền thứ hai. Dùng cho khối marginalia và các vùng "đã biết chắc, không phải chỗ để đo".

### Confidence bands
- **Nông 1 / 2 / 3** (`#DCE9F0` · `#B8D4E4` · `#8FBBD4`): ba dải lam. Chỉ dùng để mã hoá **mức tin cậy**, đậm dần theo mức cảnh giác. Không dùng làm nền trang trí.

### Ink
- **Mực Sounding** (`#16202A`): mọi con số và chữ chính. Đen ngả lam như mực in hải đồ.
- **Mực Phụ** (`#4A5A66`) · **Mực Mờ** (`#525C66`): chú giải, siêu dữ liệu. Cả hai đạt WCAG AA trên **cả** Giấy Hải Đồ lẫn Đất Liền — Mực Mờ được ép xuống từ `#75838F` vì giá trị đó chỉ cho 2,74:1 trên nền buff, trượt AA ở đúng cỡ chữ nhỏ nhất của hệ thống.
- **Hairline** (`#C3CBD1`) · **Kẻ** (`#8C99A2`): đường đẳng sâu và kẻ khung.

### Overprint
- **Magenta Cảnh Báo** (`#C0247E`): lớp overprint. Trên hải đồ magenta luôn có đúng một nghĩa — *thông tin cần chú ý*. Ở đây nó thuộc về **`defer` và chỉ `defer`**, cộng các cảnh báo cùng hạng.
- **Xanh Ngập Triều** (`#7C9455`): vùng lúc nổi lúc chìm, tức **trạng thái có điều kiện**. Chỉ dùng trong sơ đồ Zone of Confidence cho dải giáp ngưỡng.

### Named Rules

**The Magenta Rule.** Magenta chỉ có một nghĩa: cần chú ý, ở đây là `defer`. Không dùng magenta cho nhãn, cho tiêu đề, cho hover, cho bất cứ thứ gì khác. Sức mạnh của nó nằm ở chỗ thấy magenta là biết ngay model đang từ chối quyết.

**The Blue-Means-Caution Rule.** Lam đậm hơn = tin cậy thấp hơn = cẩn thận hơn. Đây là luật ngược với trực giác dashboard thông thường (nơi xanh = tốt). Giữ đúng luật hải đồ và **luôn kèm nhãn chữ**, vì trực giác ngược là chính xác lý do không được để màu làm việc một mình.

**The Never-Colour-Alone Rule.** Không thông tin nào chỉ mã hoá bằng màu. Ác/lành, mức tin cậy, `defer`, thật/giả lập — mỗi thứ luôn kèm **nhãn chữ, hoặc kiểu chữ đứng-nghiêng, hoặc hình dạng ký hiệu**. Hải đồ vốn đã làm đúng thế: đá ngầm, xác tàu, đáy xấu mỗi thứ một hình riêng, phân biệt được cả trên bản in đen trắng. Bài kiểm: in đen trắng, mất thông tin là thiết kế sai.

**The Restraint Rule.** Bảy lớp tổn thương **không được mỗi lớp một màu**. Phân biệt bằng vị trí, nhãn chữ, và độ đậm nét. Bản bolt cho mỗi lớp một hex — đó là chỗ nó hỏng nặng nhất về mặt hệ thống.

## Typography

**Chữ hải đồ (condensed):** `Archivo Narrow → Arial Narrow → Segoe UI → system-ui → sans-serif`
Dùng cho tiêu đề, nhãn, chú giải, marginalia. Hải đồ dùng lettering hẹp vì phải nhồi nhiều nhãn vào ít chỗ; đặc điểm đó được giữ.

**Chữ số liệu (regular):** `Archivo → Segoe UI → system-ui → sans-serif`
Dùng cho chữ chạy và **mọi con số**.

Một superfamily ở hai độ rộng, đúng kỷ luật của hải đồ thật. Cả hai đều **phủ đủ dấu tiếng Việt** — đây là ràng buộc quyết định, không phải sở thích (`PRODUCT.md` Accessibility & Inclusion).

### Named Rules

**The Upright-Italic Rule — thiết bị chữ ký của hệ thống.**
Trên hải đồ, **chữ đứng** nghĩa là đối tượng *luôn nổi trên mặt nước*; **chữ nghiêng** nghĩa là đối tượng *chìm hoặc ngập nước*, tức chỉ đôi khi mới thấy. Luật đó được mang sang nguyên nghĩa:

- **Chữ đứng = số đo thật.** Ảnh MRI thật, kích thước volume thật, tên bệnh nhân thật.
- **Chữ nghiêng = số giả lập hoặc chưa xác lập.** Mọi output suy luận khi `provenance.source == "simulated"`.

Đây là tuyến phòng thủ **thứ hai** sau nhãn chữ, và nó hoạt động cả trên bản in đen trắng. Không bao giờ dùng nghiêng để nhấn mạnh — nghĩa đó đã bị chiếm.

**The Tabular Rule.** Mọi con số dùng `font-variant-numeric: tabular-nums`, canh theo dấu thập phân. Sounding trên hải đồ xếp thẳng cột được là vì thế.

**The No-Uppercase Rule.** `text-transform: uppercase` không dùng cho **chữ tiếng Việt**. Lý do là kỹ thuật: dấu thanh chồng dấu phụ vỡ trên chữ hoa cỡ nhỏ (Ế, Ữ, Ậ, Ổ). Viết tắt sẵn dạng hoa và không dấu (`HCC`, `ICC`, `FNH`, `ECE`, `AURC`, `OOD`) thì giữ nguyên, đó không phải `text-transform`.

**The Data-Outranks-Prose Rule.** Bậc `sounding` lớn hơn `body` một tỉ lệ đầy đủ. Số liệu là nhân vật chính nên nó phải *nhìn* ra như vậy.

## Layout

Bố cục theo **khung hải đồ**: một khung kẻ đôi bao quanh toàn mặt, marginalia nằm trong dải trên, chú giải nằm dải dưới. Không bao giờ có nội dung sát mép.

- **Dải trên (marginalia):** RUO · định danh ca · provenance · phiên bản model · ngày. Đây là chỗ khối title-block của hải đồ vốn nằm. **Dính trên cùng, không bao giờ cuộn khuất.**
- **Thân trái:** ảnh MRI thật cùng bộ chuyển lát.
- **Thân phải:** trường sounding (phân phối 7 lớp) và sơ đồ Zone of Confidence.
- **Dải dưới:** chú giải ký hiệu, đúng như chân hải đồ.

Nhịp khoảng cách theo thang `xs/sm/md/lg/xl/xxl`. **Luôn nhiều khoảng trống phía trên một tiêu đề hơn phía dưới nó.**

Dưới 900px: khung kẻ đôi bỏ, nội dung chảy dọc theo thứ tự marginalia → kết quả → ảnh → chú giải. Dải RUO vẫn dính trên.

`@media print`: đúng một tờ ngang, nền trắng, magenta chuyển sang đen cộng gạch chéo (bản in đen trắng vẫn phải đọc được `defer`).

## Elevation & Depth

**Hoàn toàn phẳng. Không `box-shadow` ở bất kỳ đâu.** Hải đồ là giấy in.

Chiều sâu đến từ ba thứ: độ đậm của nét, hairline, và hai cấp nền (Đất Liền nổi trên Giấy Hải Đồ).

## Shapes

- **Bo góc bằng 0** cho mọi khung, panel, nút, ô nhập. Khung hải đồ là khung kẻ.
- **Hình dữ liệu thì không bị luật đó ràng buộc**: đường đẳng sâu, vùng ZOC, đường viền tổn thương là hình hữu cơ — chúng là *dữ liệu*, không phải *khung*.
- Kẻ 1px. Độ dày chỉ tăng khi nó mang thông tin.
- **Gạch chéo (hatching) là ngôn ngữ dành riêng cho "chưa có dữ liệu"** — chưa khảo sát. Không dùng gạch chéo để trang trí, vì sẽ phá tín hiệu duy nhất phân biệt có dữ liệu với không.
- Đầu mục danh sách là **một đoạn kẻ ngang 12px**, không phải chấm tròn.

## Components

### Trường sounding (thiết bị chính, thay chỗ bar chart)
- Bảy lớp, mỗi lớp một con số xác suất in ra **như một sounding**: chữ số bảng, canh thập phân.
- **Lớp dẫn đầu nhấn bằng độ đậm nét**, không bằng màu.
- Mỗi hàng kèm một dải lam ngang dài theo xác suất — dải là phụ, **con số là chính**.
- Nhóm ác và nhóm lành phân biệt bằng **ký hiệu hình dạng cộng nhãn chữ**, không bằng màu.
- Xác suất dưới ngưỡng hiển thị vẫn phải in ra. Hải đồ không giấu sounding nông.

### Sơ đồ Zone of Confidence (panel `defer`)
- Các dải tin cậy xếp chồng, dải hiện tại của ca được đánh dấu.
- Ngưỡng `defer` là **một đường đẳng sâu kẻ ngang có nhãn số**.
- Khi `defer` bật: toàn panel nhận **overprint magenta** cộng nhãn chữ rõ ràng cộng ký hiệu cảnh báo. Ba tín hiệu, không phải một.
- Đây là panel được phép **to nhất** trên màn hình kết quả. Từ chối là kết quả hợp lệ, không phải lỗi cần giấu (`PRODUCT.md` Product Principle 2).

### Khối marginalia
- Nền Đất Liền, chữ marginalia.
- Bắt buộc chứa: dải RUO · định danh ca · `provenance` · phiên bản model · ngày.
- **Dải RUO**: chữ marginalia kèm một ô vuông rỗng 8px. Nội dung: "Research Use Only: chưa kiểm định lâm sàng". Có mặt trên **mọi** bề mặt có kết quả, không bao giờ cuộn khuất.

### Dấu "chưa khảo sát"
- Nền gạch chéo 45° màu Mực Mờ, cộng **nhãn chữ bắt buộc**: "Minh hoạ: chưa có dữ liệu thật", "Chưa xây dựng".
- Gắn liền với khối số hoặc hình mà nó mô tả, không đứng rời ở góc.
- Đi kèm luật chữ nghiêng ở trên. Hai tín hiệu độc lập cho cùng một sự thật là cố ý.

### Bộ chuyển lát (staging: wound medium)
- Cuộn qua khối 3D được dựng như **quay một băng từ giữa hai cuộn**: hai chỉ báo cho biết còn bao nhiêu lát phía trên và phía dưới lát hiện tại, cộng một bộ đếm số.
- Kéo trực tiếp làm đổi vị trí thật, không phải animation trang trí.
- Bàn phím có tương đương đầy đủ: mũi tên đi từng lát, `Home`/`End` về hai đầu.
- Đây là **chỗ duy nhất trong app được phép có chuyển động liên tục**.

### Link và focus
- Link gạch chân 1px màu Kẻ, chữ giữ màu Mực. Hover chuyển gạch chân sang Mực.
- `:focus-visible` outline 2px **Mực** (không phải magenta — magenta đã bị `defer` chiếm), offset 2px. Bắt buộc ở mọi phần tử tương tác.

## Motion

Ngân sách chuyển động gần bằng không. Hải đồ là giấy.

- **Được phép:** bộ chuyển lát (chuyển động là dữ liệu thật), và chuyển trạng thái tải.
- **Không được:** hover nảy, panel trượt vào, số đếm lên, nhấp nháy, hiệu ứng khoe kỹ thuật.
- `prefers-reduced-motion: reduce` → mọi chuyển động về 0, bộ chuyển lát nhảy thẳng tới lát đích.

## Do's and Don'ts

### Do
- **Do** in con số ra, ở cỡ đọc được. Sounding là nhân vật chính.
- **Do** cho mọi thứ mã hoá bằng màu một nhãn chữ hoặc một hình dạng đi kèm.
- **Do** dùng chữ nghiêng cho mọi số giả lập, và gạch chéo cho mọi vùng chưa có dữ liệu.
- **Do** giữ magenta cho riêng `defer` (The Magenta Rule).
- **Do** kiểm bằng cách in đen trắng.
- **Do** ghi rõ mỗi con số đo trên tập nào, kể cả khi làm bảng dài thêm.

### Don't
- **Don't** trình bày số giả lập mà không có cả hai tín hiệu: chữ nghiêng và nhãn chữ.
- **Don't** cho mỗi lớp trong bảy lớp một màu riêng (The Restraint Rule).
- **Don't** dùng `box-shadow`, gradient, glass, blur.
- **Don't** dùng bán kính bo góc khác 0 cho khung và điều khiển.
- **Don't** dùng `text-transform: uppercase` cho chữ tiếng Việt.
- **Don't** thêm ký hiệu hàng hải không mang nghĩa dữ liệu: neo, bánh lái, hoa gió, giấy ố vàng giả cổ.
- **Don't** dùng gạch chéo hay chữ nghiêng để trang trí — hai thứ đó đã có nghĩa.
- **Don't** viết câu mang tính chỉ định lâm sàng. Đây là ràng buộc RUO, không phải lựa chọn giọng.
