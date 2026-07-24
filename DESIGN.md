---
name: Liver MRI 3D Classifier
description: Hệ thống thị giác cho slide, report và web app của một dự án research phân loại u gan trên MRI đa pha
colors:
  ink: "#12161A"
  ink-secondary: "#5A646E"
  ink-tertiary: "#7A848E"
  paper: "#F6F7F8"
  paper-panel: "#FFFFFF"
  rule: "#C8CDD2"
  rule-strong: "#9AA4AE"
  data-primary: "#14507A"
  data-secondary: "#A8500A"
  unverified: "#656E7A"
typography:
  display:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Arial, sans-serif"
    fontSize: "clamp(1.9rem, 3.9vw, 3.1rem)"
    fontWeight: 600
    lineHeight: 1.12
    letterSpacing: "-0.018em"
  headline:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Arial, sans-serif"
    fontSize: "clamp(1.35rem, 2.5vw, 2rem)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.012em"
  title:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Arial, sans-serif"
    fontSize: "clamp(1.05rem, 1.7vw, 1.4rem)"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.005em"
  body:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Arial, sans-serif"
    fontSize: "clamp(0.95rem, 1.5vw, 1.25rem)"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Arial, sans-serif"
    fontSize: "clamp(0.7rem, 1vw, 0.85rem)"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0.02em"
  data:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Arial, sans-serif"
    fontSize: "clamp(1rem, 1.6vw, 1.3rem)"
    fontWeight: 500
    lineHeight: 1.25
    letterSpacing: "normal"
    fontFeature: "tnum"
rounded:
  none: "0"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "28px"
  xl: "48px"
  xxl: "80px"
components:
  metric-cell:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.data}"
    rounded: "{rounded.none}"
    padding: "8px 16px"
  citation-tag:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-secondary}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "2px 0"
  unverified-chip:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.unverified}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "4px 10px"
---

# Design System: Liver MRI 3D Classifier

## Overview

**Creative North Star: "The Conference Proceedings"**

Đây là hệ thống thị giác của một bài talk hội nghị ảnh y tế (MICCAI/MIDL), chơi thẳng, không mỉa mai, không cài cắm phong cách riêng. Người dùng chọn quy ước thay vì một thế giới thị giác riêng, nên quy ước trở thành cam kết — và cam kết đó được thực thi ở mức thủ công cao nhất, chứ không phải ở mức "slide tử tế".

Tính cách: khô, chặt, tự tin về mặt số liệu. Mật độ trung bình — mỗi slide mang đúng một luận điểm và đủ chỗ thở để một con số đứng riêng được. Nền sáng vì đây là bài chiếu trong phòng họp còn bật đèn để người nghe ghi chú, và vì máy chiếu hội trường xử lý nền sáng ổn định hơn nền tối bị nhạt màu. Phẳng tuyệt đối: không đổ bóng, không bo góc, không hiệu ứng vật liệu. Chiều sâu đến từ kẻ hairline và khoảng trắng, đúng như một trang proceedings.

Hệ thống này tồn tại để phục vụ một luận điểm khoa học: **một con số không bao giờ đứng một mình**. Vì vậy phần khó nhất của nó không phải màu hay chữ, mà là một quy tắc: phân biệt được ngay lập tức giữa số đã xác minh từ công bố của người khác và thứ chưa hề tồn tại.

**Key Characteristics:**
- Nền sáng, mực gần đen, một họ chữ duy nhất
- Phẳng hoàn toàn — không bóng đổ, bán kính bo góc bằng 0
- Kẻ hairline 1px là công cụ tạo cấu trúc chính
- Số dùng chữ số bảng (tabular figures), canh theo cột
- Màu chỉ phân biệt dữ liệu, không bao giờ trang trí, không bao giờ là kênh thông tin duy nhất

## Colors

Bảng màu tối giản có chủ đích: hai sắc dữ liệu trên nền trung tính. Cặp xanh–cam được chọn vì đây là cặp phân biệt được với mù màu đỏ-lục, dạng thiếu hụt thị giác màu phổ biến nhất.

### Primary
- **Xanh Lâm Sàng** (#14507A): sắc dữ liệu thứ nhất. Dùng cho chuỗi số liệu chính, đường kẻ nhấn dưới tiêu đề slide, và trạng thái đang hoạt động của chỉ báo tiến trình. Tỷ lệ tương phản 7.9:1 trên nền giấy.

### Secondary
- **Cam Đất Nung** (#A8500A): sắc dữ liệu thứ hai, chỉ xuất hiện khi cần **đối lập** với Xanh Lâm Sàng trong cùng một hình. Không bao giờ dùng một mình để nhấn mạnh. Tương phản 5.1:1 trên nền giấy.

### Neutral
- **Mực** (#12161A): toàn bộ chữ chính và số liệu. Gần đen nhưng ngả lạnh, dịu hơn đen tuyệt đối khi chiếu.
- **Mực Phụ** (#5A646E): chú thích, nhãn nguồn, chữ hỗ trợ. Tương phản 5.3:1 — vẫn đạt AA cho chữ thường.
- **Mực Mờ** (#7A848E): chỉ dùng cho số slide và siêu dữ liệu không mang nội dung.
- **Giấy** (#F6F7F8): nền. Cố ý không phải trắng tuyệt đối — trắng #FFF trên máy chiếu gây loá và làm chữ mảnh bị mất nét.
- **Giấy Panel** (#FFFFFF): nền của ô dữ liệu cần tách khỏi nền chính.
- **Kẻ** (#C8CDD2): hairline mặc định. **Kẻ Đậm** (#9AA4AE): kẻ phân tách cấp cao hơn, ví dụ đầu bảng.
- **Chưa Xác Minh** (#656E7A): duy nhất cho nội dung được đánh dấu là chưa có dữ liệu. Tương phản 4.8:1 — giá trị đầu tiên thử là #6B7480 chỉ đạt 4.4:1 và đã bị detector bắt; đừng làm nhạt lại.

### Named Rules

**The Two-Number Rule.** Bộ slide này chỉ có hai loại số. **Loại A** là số đã công bố của người khác: hiển thị bằng Mực, chữ số bảng, và **bắt buộc** kèm nhãn nguồn `[Tác giả, Năm]` cùng cỡ mẫu `n=` ở chân slide chứa nó. **Loại B** là số của dự án này: **chưa tồn tại, và không bao giờ được vẽ ra**. Nơi cần minh hoạ một khái niệm, dùng sơ đồ không có trục số kèm nhãn "Minh hoạ khái niệm: chưa có dữ liệu". Vi phạm quy tắc này là lỗi nghiêm trọng nhất hệ thống có thể mắc.

**The Never-Colour-Alone Rule.** Không thông tin nào được mã hoá chỉ bằng màu. Ác/lành, mức tin cậy, trạng thái `defer`, xác minh/chưa xác minh — mỗi thứ luôn đi kèm nhãn chữ, hoặc kiểu nét (liền so với đứt), hoặc cả hai. Bài kiểm tra: in slide ra máy in đen trắng; nếu mất thông tin thì thiết kế sai.

**The Restraint Rule.** Hai sắc dữ liệu là toàn bộ ngân sách màu. Không có sắc thứ ba. Muốn phân biệt thêm hạng mục thì dùng vị trí, kiểu nét, hoặc nhãn — không phải hue mới.

## Typography

**Một họ chữ duy nhất** cho toàn hệ thống, là stack font hệ thống:
`Segoe UI → system-ui → -apple-system → Noto Sans → Liberation Sans → Arial → sans-serif`

**Character:** Đây là lựa chọn có chủ ý chứ không phải sự lười. Canon hội nghị dùng một workhorse sans và để trọng lượng cùng cỡ chữ gánh phân cấp. Ràng buộc quyết định là **tiếng Việt có dấu phải hiển thị đúng khi ngoại tuyến**, không CDN và không webfont, nên chỉ font hệ thống mới bảo đảm đủ dấu thanh và dấu phụ ở mọi cỡ. Segoe UI đứng đầu vì môi trường phát triển là Windows; Noto Sans và Liberation Sans là hai fallback Linux có bộ dấu tiếng Việt đầy đủ; Arial là chốt chặn cuối, không phải lựa chọn thẩm mỹ.

Detector sẽ cảnh báo `single-font` và `overused-font=arial`. Cả hai đã được đăng ký ngoại lệ kèm lý do trong `.impeccable/config.json`. **Đừng thêm font thứ hai chỉ để tắt cảnh báo** — nó sẽ phá cam kết ngoại tuyến.

### Hierarchy
- **Display** (600, clamp 1.9–3.1rem, lh 1.12): tiêu đề slide. Là **một câu khẳng định**, không phải nhãn danh từ.
- **Headline** (600, clamp 1.35–2rem, lh 1.2): tiêu đề mục trong slide, và con số đơn lẻ khi nó là nội dung chính.
- **Title** (600, clamp 1.05–1.4rem, lh 1.3): đầu cột bảng, nhãn nhóm.
- **Body** (400, clamp 0.95–1.25rem, lh 1.5): chữ chạy. Giới hạn 62ch cho slide — ngắn hơn chuẩn đọc 65–75ch vì đây là chữ nhìn từ xa, không phải chữ đọc gần.
- **Label** (600, clamp 0.7–0.85rem, tracking 0.02em, **chữ thường**): nhãn nguồn, cỡ mẫu, nhãn trạng thái, đầu cột bảng, tên phần. Vai trò "nhãn" do cỡ nhỏ, trọng lượng 600 và màu Mực Phụ gánh — không do chữ hoa.
- **Data** (500, clamp 1–1.3rem, `tnum`): mọi con số trong bảng và hình.

### Named Rules

**The Assertion Rule.** Tiêu đề slide phải là một mệnh đề có thể đúng hoặc sai — "SOTA trên LLD-MMRI đã bão hoà", không phải "Kết quả SOTA". Người xem đọc tiêu đề trước; nếu tiêu đề chỉ là nhãn thì slide đã lãng phí dòng quan trọng nhất của nó.

**The Tabular Rule.** Mọi con số dùng `font-variant-numeric: tabular-nums`. Số trong bảng canh theo dấu thập phân. Số nhảy cột khi so sánh là lỗi đọc, không phải lỗi thẩm mỹ.

**The No-Uppercase Rule.** `text-transform: uppercase` **không được dùng ở đâu trong hệ thống này**. Lý do là tiếng Việt, không phải sở thích: dấu thanh và dấu phụ chồng lên nhau khi đặt trên chữ hoa (Ế, Ữ, Ậ, Ổ), chúng bị chèn ép ở cỡ nhỏ và mất hẳn khi chiếu trên máy chiếu nhạt màu. Bản dựng đầu tiên của bộ slide này có 31 chuỗi in hoa, dài tới 108 ký tự, và detector đã bắt đúng. Muốn tạo cảm giác "nhãn" thì dùng cỡ chữ, trọng lượng và màu.

## Layout

Khung slide tỷ lệ **16:9 cố định**, co giãn theo viewport bằng `clamp()` chứ không dùng transform scale — để chữ giữ nguyên chất lượng render và dấu tiếng Việt không bị mờ.

Lưới 12 cột với máng 28px. Lề trong slide bằng `xl` (48px) ở mọi phía, nới lên `xxl` (80px) ở slide tiêu đề. Vùng chân slide cao cố định, tách khỏi nội dung bằng một kẻ hairline, chứa nhãn nguồn bên trái và số slide bên phải.

Nhịp khoảng cách theo thang `xs/sm/md/lg/xl/xxl`. **Luôn nhiều khoảng trống phía trên một tiêu đề hơn phía dưới nó** — tiêu đề thuộc về nội dung bên dưới, không phải nội dung bên trên.

Dưới 900px chiều rộng, slide bỏ khung tỷ lệ cố định và chảy dọc để đọc được trên laptop nhỏ; đây là chế độ soát lại, không phải chế độ trình chiếu.

`@media print`: mỗi slide một trang ngang, `break-after: page`, bỏ mọi điều khiển điều hướng, giữ nguyên nhãn nguồn.

## Elevation & Depth

**Hệ thống này hoàn toàn phẳng. Không có bóng đổ, ở bất kỳ đâu.**

Chiều sâu được diễn đạt bằng ba thứ: kẻ hairline 1px, khoảng trắng, và một cấp nền duy nhất (Giấy Panel #FFFFFF nổi trên Giấy #F6F7F8). Đây là ngữ pháp của trang in khoa học, và nó cũng là lựa chọn kỹ thuật đúng — bóng đổ mảnh biến mất hoàn toàn trên máy chiếu bị nhạt màu, nên bóng đổ ở đây sẽ là chiều sâu chỉ tồn tại trên màn hình của người thiết kế.

### Named Rules

**The No-Shadow Rule.** `box-shadow` không xuất hiện trong hệ thống này. Cần tách một vùng khỏi nền thì dùng kẻ hairline hoặc đổi cấp nền. Không có ngoại lệ.

## Shapes

Bán kính bo góc bằng **0** ở mọi nơi. Không bo góc mềm, không viên thuốc, không hình tròn trừ khi hình tròn mang nghĩa dữ liệu.

Kẻ luôn là 1px. Kẻ dày hơn 1px chỉ được dùng khi nó mang thông tin — ví dụ đường nhấn dưới tiêu đề slide dày 3px màu Xanh Lâm Sàng, đóng vai trò mốc thị giác cho biết đang ở phần nào của bài.

Nét đứt (`dashed`) là **ngôn ngữ dành riêng cho "chưa có dữ liệu / minh hoạ khái niệm"**. Không dùng nét đứt cho mục đích trang trí, vì làm vậy sẽ phá vỡ tín hiệu duy nhất phân biệt hai loại số.

## Components

### Bảng số liệu
- **Hình dạng:** không viền ngoài. Chỉ có một kẻ Kẻ Đậm dưới hàng đầu cột và kẻ hairline giữa các hàng.
- **Số:** chữ số bảng, canh phải, canh theo dấu thập phân.
- **Cột "trên tập test nào":** bắt buộc có mặt trong mọi bảng so sánh giữa các công trình. Bảng không có cột này là bảng trình bày sai lệch.
- **Nhãn nguồn:** một nhãn `[Tác giả, Năm]` cho mỗi hàng, không gom chung ở cuối.

### Nhãn nguồn (citation-tag)
- **Kiểu:** chữ Label, màu Mực Phụ, đặt ở chân slide.
- **Nội dung:** `[Tên/Tác giả, Năm]` cộng `n=` khi con số gắn với một tập đánh giá cụ thể.
- **Quy tắc:** không có nhãn nguồn thì con số không được lên slide.

### Chip "chưa có dữ liệu" (unverified-chip)
- **Kiểu:** viền 1px **nét đứt** màu Chưa Xác Minh, nền Giấy, chữ Label.
- **Nội dung:** luôn có chữ, ví dụ "Minh hoạ khái niệm — chưa có dữ liệu" hoặc "Chưa xác minh được nguồn".
- **Hành vi:** chip này gắn liền với hình hoặc số mà nó mô tả, không đứng rời ở góc slide.

### Chỉ báo tiến trình
- **Kiểu:** một dải các đoạn hairline ở mép trên slide, mỗi phần của bài một đoạn; đoạn đang hoạt động chuyển sang Xanh Lâm Sàng và dày lên 3px.
- **Kèm chữ:** luôn có tên phần bằng chữ. Đoạn màu một mình không đủ.

### Dải RUO
- **Kiểu:** chữ Label màu Mực Phụ trên kẻ hairline, cố định ở đầu mỗi slide có nội dung kết quả.
- **Nội dung:** "RESEARCH USE ONLY — chưa kiểm định lâm sàng".
- **Quy tắc:** không bao giờ bị cuộn khuất, không bao giờ chỉ xuất hiện ở slide cuối.

## Do's and Don'ts

### Do:
- **Do** viết tiêu đề slide thành câu khẳng định có thể đúng hoặc sai (The Assertion Rule).
- **Do** gắn nhãn nguồn `[Tác giả, Năm]` và cỡ mẫu `n=` vào chân mọi slide có số của người khác.
- **Do** ghi rõ mỗi con số đo trên tập test nào, kể cả khi điều đó làm bảng dài thêm một cột.
- **Do** dùng `font-variant-numeric: tabular-nums` cho mọi số.
- **Do** dùng nét đứt cộng nhãn chữ cho mọi thứ chưa có dữ liệu.
- **Do** kiểm tra bằng cách in đen trắng: nếu mất thông tin thì màu đang làm việc một mình.

### Don't:
- **Don't** vẽ bất kỳ con số nào của dự án này — chưa có kết quả, và số giả trông giống số thật là rủi ro nghiêm trọng nhất ở đây.
- **Don't** dùng `box-shadow` (The No-Shadow Rule).
- **Don't** dùng bán kính bo góc khác 0.
- **Don't** thêm sắc màu thứ ba ngoài Xanh Lâm Sàng và Cam Đất Nung.
- **Don't** dùng nét đứt để trang trí — nó đã được đặt trước cho nghĩa "chưa có dữ liệu".
- **Don't** dùng gradient, glass, blur, hay icon trang trí.
- **Don't** dùng `text-transform: uppercase` (The No-Uppercase Rule) — tiếng Việt có dấu không chịu được.
- **Don't** rải em-dash trong chữ chạy. Dùng dấu phẩy, hai chấm, chấm, hoặc ngoặc đơn. Bản dựng đầu có 46 em-dash và bị bắt là nhịp văn máy.
- **Don't** đặt nền trắng tuyệt đối #FFFFFF làm nền slide (gây loá khi chiếu); #FFFFFF chỉ dành cho panel dữ liệu.
- **Don't** đặt hai bảng số của hai tập test khác nhau cạnh nhau mà không ghi rõ — đó là trình bày sai lệch, không phải tiết kiệm chỗ.
