---
name: Liver MRI 3D Classifier
description: Hệ thống thị giác cho slide, report và web app của một dự án research phân loại u gan trên MRI đa pha
colors:
  ground: "#10161B"
  plate: "#161E24"
  line: "#E8E4DA"
  line-secondary: "#A9B2B8"
  line-tertiary: "#8B949B"
  rule: "#2E3A42"
  rule-strong: "#44535D"
  key: "#D4A72C"
  counter: "#6FC2DC"
typography:
  display:
    fontFamily: "Cambria, Times New Roman, Liberation Serif, Noto Serif, Georgia, serif"
    fontSize: "clamp(1.75rem, 3.5vw, 2.85rem)"
    fontWeight: 400
    lineHeight: 1.16
    letterSpacing: "0.002em"
  headline:
    fontFamily: "Cambria, Times New Roman, Liberation Serif, Noto Serif, Georgia, serif"
    fontSize: "clamp(1.2rem, 2.2vw, 1.75rem)"
    fontWeight: 400
    lineHeight: 1.35
    letterSpacing: "normal"
  title:
    fontFamily: "Cambria, Times New Roman, Liberation Serif, Noto Serif, Georgia, serif"
    fontSize: "clamp(1rem, 1.6vw, 1.3rem)"
    fontWeight: 400
    lineHeight: 1.3
    letterSpacing: "normal"
  body:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Arial, sans-serif"
    fontSize: "clamp(0.92rem, 1.45vw, 1.2rem)"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "normal"
  data:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Arial, sans-serif"
    fontSize: "clamp(1rem, 1.6vw, 1.3rem)"
    fontWeight: 400
    lineHeight: 1.25
    letterSpacing: "normal"
    fontFeature: "tnum"
  label:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Arial, sans-serif"
    fontSize: "clamp(0.7rem, 1vw, 0.85rem)"
    fontWeight: 400
    lineHeight: 1.35
    letterSpacing: "0.02em"
  caption:
    fontFamily: "Cambria, Times New Roman, Liberation Serif, Noto Serif, Georgia, serif"
    fontSize: "clamp(0.7rem, 1vw, 0.85rem)"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "normal"
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
  plate-panel:
    backgroundColor: "{colors.plate}"
    textColor: "{colors.line}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "28px"
  plate-key:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.key}"
    typography: "{typography.caption}"
    rounded: "{rounded.none}"
    padding: "0"
  legend-entry:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.line-secondary}"
    typography: "{typography.caption}"
    rounded: "{rounded.none}"
    padding: "0"
  unverified-chip:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.line-tertiary}"
    typography: "{typography.caption}"
    rounded: "{rounded.none}"
    padding: "4px 10px"
---

# Design System: Liver MRI 3D Classifier

## Overview

**Creative North Star: "The Anatomical Plate"**

Thế giới thị giác là **bản khắc atlas giải phẫu**, dựng như một bản khắc âm bản: nét sáng ấm trên nền mực sâu. Đây là nghề in nền tảng của y học — atlas giải phẫu là hiện vật thị giác lâu đời nhất mà mọi bác sĩ đều đã đọc.

Lý do chọn nó không phải là hoài cổ. Bản khắc atlas có sẵn một thiết bị mà dự án này cần đúng: **chú số và đường dóng**. Mọi thứ trong một bản khắc giải phẫu đều mang một con số, và mọi con số đều truy được về chú giải ở chân bản. Dự án này có một yêu cầu gần như y hệt: mọi số liệu trên màn hình phải truy được về nguồn công bố. Nên hệ trích nguồn không bị dán vào từ ngoài, nó **mọc ra từ chính ngữ pháp của thế giới**.

Tính cách: trang trọng, chậm rãi, có nghi thức. Mật độ trung bình, mỗi bản khắc mang đúng một luận điểm. Phẳng tuyệt đối — chiều sâu đến từ độ đậm nhạt của nét khắc và hai cấp nền, không từ bóng đổ. Khung kẻ đôi bao quanh mỗi bản, đúng như trang atlas in.

Hệ thống này tồn tại để phục vụ một luận điểm khoa học: **một con số không bao giờ đứng một mình**. Phần khó nhất của nó không phải màu hay chữ, mà là phân biệt được ngay lập tức giữa số đã xác minh từ công bố của người khác và thứ chưa hề tồn tại.

**Key Characteristics:**
- Nền mực sâu, nét sáng ấm — bản khắc âm bản
- Khung kẻ đôi bao quanh mỗi bề mặt
- Chữ chân phương cho tiêu đề và chú giải, sans cho số liệu
- Chú số cộng chú giải là hệ trích nguồn, không phải trang trí
- Phẳng hoàn toàn, bán kính bo góc bằng 0

**Rủi ro đã biết, ghi lại để không quên:** nền tối cần phòng chiếu **có giảm sáng**. Nếu buổi báo cáo diễn ra trong phòng bật đèn đầy đủ, hoặc máy chiếu bị nhạt màu nặng, nền sáng sẽ an toàn hơn. Hệ thống này chấp nhận đánh đổi đó một cách có ý thức; đừng phát hiện lại nó rồi tưởng là lỗi thiết kế.

## Colors

Nền mực sâu với nét sáng ấm, hai sắc dữ liệu. Cặp hoàng thổ và lam ngọc được chọn vì phân biệt được với mù màu đỏ-lục, dạng thiếu hụt thị giác màu phổ biến nhất.

### Primary
- **Hoàng Thổ** (#D4A72C): sắc của **chú số và chú giải**. Đây là màu mang chức năng cốt lõi của hệ thống, nên nó không được dùng cho bất cứ việc gì khác. Cũng dùng cho đường nhấn dưới tiêu đề và mốc phần đang hoạt động. Tương phản 8.1:1 trên nền mực.

### Secondary
- **Lam Ngọc** (#6FC2DC): sắc đối lập, chỉ xuất hiện khi cần **tương phản** với Hoàng Thổ trong cùng một hình (ví dụ lành tính so với ác tính). Không bao giờ dùng một mình để nhấn mạnh. Tương phản 9.1:1.

### Neutral
- **Nét Khắc** (#E8E4DA): toàn bộ chữ chính và số liệu. Trắng ngả ấm như mực in trên bản khắc, không phải trắng lạnh.
- **Nét Phụ** (#A9B2B8): chú thích, chữ hỗ trợ. Tương phản 8.5:1.
- **Nét Mờ** (#8B949B): số bản khắc, siêu dữ liệu, và nội dung đánh dấu là chưa có dữ liệu. Tương phản 5.9:1 — vẫn đạt AA.
- **Nền Mực** (#10161B): nền chính.
- **Nền Bản** (#161E24): cấp nền thứ hai, cho ô dữ liệu cần tách khỏi nền chính.
- **Kẻ** (#2E3A42): hairline trong. **Kẻ Đậm** (#44535D): khung ngoài và kẻ phân tách cấp cao.

### Named Rules

**The Two-Number Rule.** Hệ thống này chỉ có hai loại số. **Loại A** là số đã công bố của người khác: hiển thị bằng Nét Khắc, chữ số bảng, và **bắt buộc** mang một chú số dẫn về chú giải ở chân bề mặt, kèm cỡ mẫu `n=`. **Loại B** là số của dự án này: **chưa tồn tại, và không bao giờ được vẽ ra**. Nơi cần minh hoạ một khái niệm, dùng sơ đồ không có trục số kèm nhãn "Minh hoạ khái niệm: chưa có dữ liệu". Vi phạm quy tắc này là lỗi nghiêm trọng nhất hệ thống có thể mắc.

**The Plate Key Rule.** Hoàng Thổ thuộc về chú số. Không dùng nó để làm đẹp một tiêu đề, một đường viền, hay một trạng thái hover không liên quan đến trích nguồn. Sức mạnh của thiết bị này nằm ở chỗ khi thấy màu hoàng thổ, người xem biết ngay đó là một con trỏ tới nguồn.

**The Never-Colour-Alone Rule.** Không thông tin nào được mã hoá chỉ bằng màu. Ác/lành, mức tin cậy, trạng thái `defer`, xác minh/chưa xác minh — mỗi thứ luôn đi kèm nhãn chữ, hoặc kiểu nét (liền so với đứt), hoặc hình dạng (đặc so với rỗng). Bài kiểm tra: in ra máy in đen trắng; nếu mất thông tin thì thiết kế sai.

**The Restraint Rule.** Hoàng Thổ và Lam Ngọc là toàn bộ ngân sách màu. Không có sắc thứ ba. Muốn phân biệt thêm hạng mục thì dùng vị trí, kiểu nét, hoặc nhãn.

## Typography

**Chân phương (serif):** `Cambria → Times New Roman → Liberation Serif → Noto Serif → Georgia → serif`
Dùng cho tiêu đề, chú giải, chú thích bảng, và số bản khắc. Đây là giọng của trang in.

**Sans:** `Segoe UI → system-ui → -apple-system → Noto Sans → Liberation Sans → Arial → sans-serif`
Dùng cho chữ chạy và **mọi con số**. Số liệu cần rõ ràng hơn cần trang trọng.

**Character:** Cặp chân phương và sans chia nhau theo chức năng chứ không theo cấp bậc: chân phương nói *về* dữ liệu (tiêu đề, chú giải, nhãn), sans *là* dữ liệu. Ràng buộc quyết định cho cả hai stack là **tiếng Việt có dấu phải hiển thị đúng khi ngoại tuyến** — không CDN, không webfont. Cambria có bộ dấu tiếng Việt tốt trên Windows; Times New Roman, Liberation Serif và Noto Serif phủ các nền tảng còn lại. Arial ở cuối stack sans là chốt chặn, không phải lựa chọn thẩm mỹ (đã đăng ký ngoại lệ `overused-font=arial` kèm lý do trong `.impeccable/config.json`).

### Hierarchy
- **Display** (chân phương, 400, clamp 1.75–2.85rem, lh 1.16): tiêu đề bề mặt. Là **một câu khẳng định**, không phải nhãn danh từ.
- **Headline** (chân phương, 400, clamp 1.2–1.75rem, lh 1.35): câu dẫn, và con số đơn lẻ khi nó là nội dung chính.
- **Title** (chân phương, 400, clamp 1–1.3rem, lh 1.3): tiêu đề mục trong bề mặt.
- **Body** (sans, 400, clamp 0.92–1.2rem, lh 1.55): chữ chạy. Giới hạn 62ch.
- **Data** (sans, 400, clamp 1–1.3rem, `tnum`): mọi con số trong bảng và hình.
- **Label** (sans, 400, clamp 0.7–0.85rem, tracking 0.02em): dải RUO, siêu dữ liệu đầu bề mặt.
- **Caption** (chân phương nghiêng, 400, clamp 0.7–0.85rem): chú giải nguồn, chú thích bảng, đầu cột, nhãn nhóm, chip.

### Named Rules

**The Assertion Rule.** Tiêu đề phải là một mệnh đề có thể đúng hoặc sai — "SOTA trên LLD-MMRI đã bão hoà", không phải "Kết quả SOTA". Người xem đọc tiêu đề trước; nếu tiêu đề chỉ là nhãn thì bề mặt đã lãng phí dòng quan trọng nhất của nó.

**The Tabular Rule.** Mọi con số dùng `font-variant-numeric: tabular-nums` và canh theo dấu thập phân. Số nhảy cột khi so sánh là lỗi đọc, không phải lỗi thẩm mỹ.

**The No-Uppercase Rule.** `text-transform: uppercase` **không được dùng ở đâu trong hệ thống này**. Lý do là tiếng Việt, không phải sở thích: dấu thanh và dấu phụ chồng lên nhau khi đặt trên chữ hoa (Ế, Ữ, Ậ, Ổ), bị chèn ép ở cỡ nhỏ và mất hẳn khi chiếu trên máy chiếu nhạt màu. Muốn tạo cảm giác "nhãn" thì dùng cỡ chữ, kiểu nghiêng chân phương, và màu.

## Layout

Bề mặt trình chiếu theo tỷ lệ **16:9 cố định**, co giãn bằng `clamp()` chứ không dùng transform scale, để chữ giữ chất lượng render và dấu tiếng Việt không bị mờ.

**Khung kẻ đôi** là đặc trưng cấu trúc: hai đường viền lồng nhau (`inset` khoảng 1.2vw và 1.7vw), viền ngoài dùng Kẻ Đậm, viền trong dùng Kẻ. Khung không bao giờ chứa nội dung sát mép — luôn còn lề trong.

Đầu bề mặt: dải RUO bên trái, số bản khắc bên phải, phân cách với thân bằng một hairline. Chân bề mặt: **chú giải nguồn bên trái**, số thứ tự bên phải, phân cách bằng hairline.

Nhịp khoảng cách theo thang `xs/sm/md/lg/xl/xxl`. **Luôn nhiều khoảng trống phía trên một tiêu đề hơn phía dưới nó.**

Dưới 900px chiều rộng: bỏ khung tỷ lệ cố định và khung kẻ đôi, nội dung chảy dọc. Đây là chế độ soát lại, không phải chế độ trình chiếu.

`@media print`: mỗi bề mặt một trang ngang. Link bỏ gạch chân và **tự in URL trong ngoặc** — trên giấy không ai bấm được.

## Elevation & Depth

**Hoàn toàn phẳng. Không có bóng đổ, ở bất kỳ đâu.**

Chiều sâu đến từ ba thứ: độ đậm nhạt của nét (Nét Khắc → Nét Phụ → Nét Mờ), hairline, và hai cấp nền (Nền Bản #161E24 nổi trên Nền Mực #10161B). Đây là ngữ pháp của bản khắc, và cũng là lựa chọn kỹ thuật đúng: bóng đổ mảnh biến mất hoàn toàn trên máy chiếu bị nhạt màu.

### Named Rules

**The No-Shadow Rule.** `box-shadow` không xuất hiện trong hệ thống này. Cần tách một vùng khỏi nền thì dùng hairline hoặc đổi cấp nền. Không có ngoại lệ.

## Shapes

Bán kính bo góc bằng **0** ở mọi nơi.

Kẻ là 1px, trừ mốc phần đang hoạt động (2px Hoàng Thổ) — độ dày chỉ được tăng khi nó mang thông tin.

Đầu mục danh sách là một **đoạn kẻ ngang 16px** (đường dóng thu nhỏ), không phải dấu chấm tròn. Đây là chi tiết bản khắc, dùng nhất quán.

**Nét đứt (`dashed`) là ngôn ngữ dành riêng cho "chưa có dữ liệu / minh hoạ khái niệm".** Không dùng nét đứt để trang trí, vì làm vậy sẽ phá tín hiệu duy nhất phân biệt hai loại số.

## Components

### Chú số và chú giải (thiết bị chữ ký của hệ thống)
- **Chú số:** `<sup>` chân phương, màu Hoàng Thổ, đặt ngay sau con số hoặc mệnh đề mà nó dẫn nguồn.
- **Chú giải:** ở chân bề mặt, mỗi mục mở đầu bằng số Hoàng Thổ có dấu chấm, cách chữ 7px.
- **Định dạng trích dẫn:** kiểu số thứ tự (Vancouver). `Tác giả, et al. Tiêu đề ngắn. Tạp chí Năm. doi/arXiv` — mã định danh là **link bấm được**.
- **Quy tắc:** không có chú số thì con số không được lên bề mặt.

### Khung bản khắc
- Hai đường viền lồng nhau qua `::before` và `::after`, `pointer-events:none`.
- Không bao giờ bo góc, không bao giờ đổ bóng.

### Bảng số liệu
- Không viền ngoài. Một Kẻ Đậm dưới hàng đầu cột, hairline giữa các hàng.
- Đầu cột: chân phương nghiêng, màu Nét Phụ. Số: sans, chữ số bảng, canh phải.
- **Cột hoặc chú thích cho biết "đo trên tập nào" là bắt buộc** trong mọi bảng so sánh giữa các công trình. Thiếu nó là trình bày sai lệch.
- Hàng dẫn đầu dùng Hoàng Thổ **và** một nhãn chữ; màu không bao giờ đứng một mình.

### Chip "chưa có dữ liệu"
- Viền 1px **nét đứt** màu Nét Mờ, chữ chân phương nghiêng.
- Luôn có chữ: "Minh hoạ khái niệm: chưa có dữ liệu", "Chưa xây dựng", v.v.
- Gắn liền với hình hoặc số mà nó mô tả, không đứng rời ở góc.

### Mốc phần
- Một dải các đoạn hairline ở đầu bề mặt, mỗi phần một đoạn kèm tên phần bằng chữ.
- Đoạn đang hoạt động: Hoàng Thổ, dày 2px, chữ chuyển từ nghiêng sang đứng.
- Đoạn màu một mình không đủ — tên phần luôn hiện.

### Link
- Gạch chân 1px màu Kẻ Đậm, chữ giữ màu Nét Khắc. Hover chuyển sang Hoàng Thổ.
- `:focus-visible` có outline 2px Hoàng Thổ — bắt buộc, đây là bề mặt điều hướng bằng bàn phím.
- Khi in: bỏ gạch chân, tự chèn URL trong ngoặc.

### Dải RUO
- Chữ Label màu Nét Phụ, kèm một ô vuông rỗng 8px, đặt ở đầu **mọi** bề mặt có nội dung kết quả.
- Nội dung: "Research Use Only: chưa kiểm định lâm sàng".
- Không bao giờ bị cuộn khuất, không bao giờ chỉ xuất hiện ở bề mặt cuối.

## Do's and Don'ts

### Do:
- **Do** viết tiêu đề thành câu khẳng định có thể đúng hoặc sai (The Assertion Rule).
- **Do** gắn chú số cho mọi con số của người khác, và chú giải đầy đủ ở chân bề mặt kèm link tới nguồn.
- **Do** ghi rõ mỗi con số đo trên tập nào, kể cả khi điều đó làm bảng dài thêm.
- **Do** dùng `font-variant-numeric: tabular-nums` cho mọi số.
- **Do** dùng nét đứt cộng nhãn chữ cho mọi thứ chưa có dữ liệu.
- **Do** kiểm tra bằng cách in đen trắng: nếu mất thông tin thì màu đang làm việc một mình.
- **Do** giữ Hoàng Thổ cho riêng chú số (The Plate Key Rule).

### Don't:
- **Don't** vẽ bất kỳ con số nào của dự án này — chưa có kết quả, và số giả trông giống số thật là rủi ro nghiêm trọng nhất ở đây.
- **Don't** dùng `box-shadow` (The No-Shadow Rule).
- **Don't** dùng bán kính bo góc khác 0.
- **Don't** dùng `text-transform: uppercase` (The No-Uppercase Rule) — tiếng Việt có dấu không chịu được.
- **Don't** thêm sắc màu thứ ba ngoài Hoàng Thổ và Lam Ngọc.
- **Don't** dùng nét đứt để trang trí — nó đã được đặt trước cho nghĩa "chưa có dữ liệu".
- **Don't** dùng gradient, glass, blur, hay icon trang trí.
- **Don't** rải em-dash trong chữ chạy. Dùng dấu phẩy, hai chấm, chấm, hoặc ngoặc đơn.
- **Don't** thêm font thứ ba. Hai stack đã phủ hết vai trò, và mọi bổ sung đều phải qua bài kiểm tra "hiển thị đủ dấu tiếng Việt khi ngoại tuyến".
- **Don't** đặt hai bảng số của hai tập test khác nhau cạnh nhau mà không ghi rõ.
