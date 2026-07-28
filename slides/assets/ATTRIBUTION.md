# Attribution cho asset trong `slides/overview.html`

## `cmir-8-107-f5.jpg`

- **Tác giả:** Nils Albiin
- **Mô tả:** MRI gan đa thì có thuốc tương phản, minh hoạ tổn thương FNH và adenoma.
- **Nguồn:** [Wikimedia Commons: CMIR-8-107 F5.jpg](https://commons.wikimedia.org/wiki/File:CMIR-8-107_F5.jpg)
- **Nguồn gốc:** [PMC3462338](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3462338/)
- **Giấy phép:** [CC BY 2.5](https://creativecommons.org/licenses/by/2.5/)
- **Thay đổi:** Thu nhỏ để nhúng vào slide; không thay đổi nội dung ảnh.

Asset này là minh hoạ công khai, không phải dữ liệu LLD-MMRI và không phải ca bệnh/kết quả của dự án.

## `synthetic-mri-8phase-contact-sheet.png`

- **Nguồn:** Ảnh tổng hợp do OpenAI Image Generation tạo.
- **Dùng ở:** `overview.html` slide 2 (minh hoạ MRI đa thì) và slide 10 (ảnh input 8 thì); `overview_v2.html` slide 1 (bìa, chú số 10).
- **Mô tả:** Contact sheet MRI bụng gồm tám lát tổng hợp của cùng một trường nhìn, dùng làm minh hoạ cho 8 thì MRI.
- **Không phải:** Dữ liệu bệnh nhân, ảnh LLD-MMRI, hay kết quả thực nghiệm của dự án.

## `ui-output-screen.png`

- **Nguồn:** Ảnh do Antigravity tạo.
- **Dùng ở:** Slide 9 và 10 (bản tạm).
- **Mô tả:** Ảnh minh hoạ bố cục màn hình UI output (viewer + heatmap, phân bố xác suất, mức bất định, cờ `defer`).
- **⚠️ Cảnh báo:** Ảnh chứa số phần trăm và biểu đồ **giả lập, chỉ minh hoạ bố cục** — không phải kết quả dự án. Slide 9/10 đã có figcaption ghi rõ. Nên thay bằng bản không có số khi có điều kiện.
- **Không phải:** Dữ liệu bệnh nhân hay kết quả thực nghiệm của dự án.
- **Ghi chú:** Bản `.jpg` trùng nội dung đã được xoá; `.png` là bản duy nhất còn dùng. `overview_v2.html` cố ý **không** dùng ảnh này vì nó chứa số phần trăm giả lập.

## `nii-volume-stack.*` (tuỳ chọn — chưa dùng)

- **Trạng thái:** Slide 10 input hiện đã dùng `synthetic-mri-8phase-contact-sheet.png`. Ảnh stack nhiều lát cắt này là cải tiến tuỳ chọn về sau, không bắt buộc.
- **Mô tả dự kiến:** Ảnh minh hoạ 8 file `.nii`, mỗi file là một khối gồm nhiều lát cắt (3D).
- **Nếu dùng:** Thay `<img>` trong `.phase-sheet` (slide 10) bằng `<img src="assets/nii-volume-stack.<ext>">`, giữ nhãn phase và figcaption.
- **Bắt buộc:** Ảnh minh hoạ khái niệm, không phải dữ liệu bệnh nhân hay ảnh LLD-MMRI.
