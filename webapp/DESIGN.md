---
name: Liver MRI Classifier — Workstation
description: Bàn đọc MRI 3 cột, kế thừa mật độ và hệ màu của C2-App-061
scope: webapp/
mode: operate
themes:
  dark:
    background: "oklch(0.18 0.02 240)"
    panel: "oklch(0.22 0.025 245)"
    panel-raised: "oklch(0.24 0.03 245)"
    foreground: "oklch(0.95 0.01 240)"
    muted: "oklch(0.65 0.02 240)"
    border: "oklch(0.32 0.03 245)"
    cyan: "oklch(0.78 0.14 220)"
  light:
    background: "oklch(0.96 0.015 240)"
    panel: "oklch(0.99 0.005 240)"
    secondary: "oklch(0.92 0.015 240)"
    foreground: "oklch(0.22 0.02 240)"
    muted: "oklch(0.50 0.02 240)"
    border: "oklch(0.86 0.015 240)"
    cyan: "oklch(0.53 0.16 220)"
colors:
  annotation: "#E879F9"
  attention: "#F59E0B"
  success: "semantic"
  warning: "semantic"
  danger: "semantic"
typography:
  ui: "Segoe UI Variable, Segoe UI, system-ui, sans-serif"
  data: "JetBrains Mono, ui-monospace, Consolas, monospace"
rounded:
  control: "6px"
  panel: "8px"
  viewer: "8px"
---

# Design System: Liver MRI Classifier — Web App

## Overview

**MRI workstation, không phải dashboard AI.** App dùng bố cục ba cột: dữ liệu đầu vào ở trái, ảnh MRI ở trung tâm, kết quả AI ở phải. Bố cục và mức phân lớp bề mặt tham khảo `C2-App-061`; chỉ giữ các affordance phục vụ MRI đa thì, không sao chép nghiệp vụ X-quang hoặc hồ sơ bệnh nhân.

Ảnh MRI luôn là vùng đọc chính và luôn dùng nền đen, kể cả khi giao diện đang ở light theme. Các panel khác chỉ tổ chức công việc: không cạnh tranh về thị giác với ảnh.

## Theme

App hỗ trợ `light` và `dark` với token semantic `background`, `foreground`, `panel`, `panel-raised`, `secondary`, `muted-foreground`, `border`, `cyan`, `success`, `warning` và `danger`.

- Lần đầu mở app theo `prefers-color-scheme`.
- Lựa chọn thủ công được lưu localStorage và thay thế lựa chọn hệ điều hành.
- Theme được gắn trên `html` trước khi React render để không chớp sai màu.
- Cyan trên light theme được tối hoá đủ tương phản AA; không dùng cyan sáng của dark theme cho chữ trên nền sáng.

Không hard-code màu nền/chữ trong component đang render. Component dùng token semantic để light/dark luôn đồng bộ.

## Layout

- Header 56 px, workspace chiếm phần chiều cao còn lại của `100dvh`. Dòng phụ dưới tên app mang RUO ngắn gọn để không chiếm thêm một dải ngang.
- Từ 1280 px: panel dữ liệu 272 px có thể thu gọn, viewer `minmax(0, 1fr)`, panel kết quả 384 px luôn hiện; mỗi sidebar cuộn độc lập.
- Dưới 1280 px: dùng ba tab Dữ liệu / Ảnh MRI / Kết quả. Ảnh MRI là tab mặc định. Tab không nhận phím mũi tên; chúng chỉ đổi bằng click/touch hoặc focus + Enter/Space.
- Mobile giữ tối thiểu vùng chạm 44 px. Phase strip cuộn ngang, không ép xuống hai hàng.

Panel dùng nền riêng, viền 1 px và bo 8 px. Không dùng shadow tĩnh, card lồng nhau, hero metric hay bo góc lớn. Chip pill chỉ dành cho provenance/trạng thái ngắn.

## MRI viewer

Viewer hiển thị **ảnh NIfTI nguồn** của ZIP vừa tải lên; crop UniFormer chỉ là input nội bộ, không phải ảnh đọc chính.

- Phase mặc định là `C-pre`.
- Dùng chung zoom, pan, slider, nút `←`/`→` và thanh lát cho mọi thì.
- Phím `←`/`→` chỉ đổi lát khi khung ảnh đang focus, không đổi tab hoặc panel.
- Toggle fuchsia biểu thị mask tổn thương do người tải lên cung cấp; phải gọi rõ là nhãn người chú giải, không phải segmentation của model.
- Upload trực tiếp không có heatmap. Không tạo màu giả để lấp khoảng trống.
- Viewer hết cache hiển thị hướng dẫn tải lại ZIP, không để ảnh lỗi trống.

## Ý nghĩa màu

- Cyan: hành động chính, trạng thái chọn và focus.
- Fuchsia `annotation`: mask tổn thương của người chú giải.
- Hổ phách `attention`: heatmap độ nhạy model khi có artefact hợp lệ; không dùng cho upload live.
- Bảy màu lớp chỉ nằm trong xác suất từng lớp; mọi màu luôn có nhãn chữ đi kèm.
- Success/warning/danger chỉ biểu thị trạng thái, không biểu thị chẩn đoán.

## Nội dung và an toàn

Dòng phụ của header luôn nêu rõ "Chỉ dùng cho nghiên cứu · Không dùng để chẩn đoán". Không bịa danh tính bệnh nhân, ngày khám, phiên bản model hoặc khuyến nghị lâm sàng.

Kết quả upload trực tiếp phải ghi rõ provenance. Không hiển thị `defer`, calibration OOF hoặc heatmap không tồn tại như thể chúng áp dụng cho suy luận live. Thay vào đó, dùng mô tả trung tính rằng kết quả cần người có chuyên môn đối chiếu.

## Accessibility

- Chữ nội dung và control phải đạt WCAG AA ở cả hai theme.
- Focus ring cyan luôn thấy rõ.
- Thông tin không chỉ được mã hoá bằng màu.
- Không dùng `text-transform: uppercase` với tiếng Việt.
- Tôn trọng `prefers-reduced-motion`.
