# Web app demo

> **Research Use Only. Chưa kiểm định lâm sàng, không dùng để chẩn đoán.**

Demo cho người review nghiên cứu thấy hành vi của mô hình phân loại bảy lớp tổn thương gan trên MRI 3D tám thì: xác suất từng lớp, mức bất định, và cờ `defer` khi mô hình từ chối quyết.

## Trạng thái

| Phần | Trạng thái |
|---|---|
| Contract API, nhận diện thì, đọc NIfTI, render lát | **chạy được** |
| Ảnh MRI hiển thị | **thật**, đọc trực tiếp từ file gốc |
| Kết quả ca demo | **prediction out-of-fold thật**, chỉ hiển thị cho ca demo có dữ liệu OOF |
| ZIP người dùng tải | chỉ kiểm tra manifest đủ 8 thì; không giải nén bền vững, không chạy model, không trả prediction |
| Grad-CAM | chưa có, hiển thị bằng vùng gạch chéo "chưa khảo sát" |

Khi có pipeline ROI tương đương lúc train ở giai đoạn sau, có thể bổ sung suy luận `live` như một contract riêng. V1 không suy luận từ dữ liệu tải lên.

## Chạy

```powershell
pip install -r webapp/backend/requirements.txt
python -m uvicorn webapp.backend.main:app --reload      # cổng 8000

cd webapp/frontend
npm install
npm run dev                                             # mở http://localhost:5173
```

Frontend proxy `/api` sang cổng 8000, nên ảnh bệnh nhân đi qua cùng origin.

> Dùng **`localhost:5173`**, không phải `127.0.0.1:5173`. Trên Windows, Vite bind vào `::1` (IPv6) chứ không bind IPv4, nên địa chỉ số sẽ bị từ chối kết nối.

## Dữ liệu

App đọc ảnh lúc chạy từ `LLDMMRI_SAMPLE_DIR`, mặc định `data/sample`.

**`data/` nằm ngoài git và phải giữ nguyên như vậy** — đó là volume MRI của bệnh nhân thật. Hệ quả:

- Máy khác clone repo về sẽ **không có** dữ liệu. App xuống thang tử tế: danh sách ca báo `available: false`, không crash.
- **Đem demo lên host công khai thì dữ liệu này không đi kèm.** Phải chuẩn bị bộ ca demo riêng, đã được duyệt về mặt quyền sử dụng dữ liệu.

## Biến môi trường

| Biến | Mặc định | Việc |
|---|---|---|
| `LLDMMRI_SAMPLE_DIR` | `data/sample` | Thư mục chứa 8 file `.nii` của ca demo |
| `LLDMMRI_CHECKPOINT` | *(chưa đặt)* | Đường dẫn checkpoint. Đặt vào khi nhánh suy luận thật đã viết |
| `LLDMMRI_DEFER_THRESHOLD` | `0.55` | Ngưỡng confidence dưới đó thì `defer`. Giá trị thật sẽ khoá trên validation từ đường risk-coverage, không chọn tay |

## Upload ZIP V1

Chỉ nhận **một ZIP**. ZIP có thể chứa thư mục con bất kỳ, nhưng phải có đúng một file `.nii` hoặc `.nii.gz` nhận diện được cho từng thì: C-pre, C+A, C+V, C+Delay, T2WI, DWI, In Phase và Out Phase. API `POST /api/validate-upload` chỉ đọc tên file trong ZIP và trả bảng kiểm 8 thì.

Không dùng folder picker: hành vi khác nhau giữa các trình duyệt. DICOM-folder là mở rộng riêng khi app có contract DICOM, không trộn với NIfTI ZIP V1.

## Thiết kế

Thế giới thị giác ở [`DESIGN.md`](DESIGN.md) trong thư mục này — **"bàn đọc tối"**, riêng cho web app. `DESIGN.md` ở gốc repo là hệ khác ("bản khắc atlas") và thuộc về `slides/` với `reports/`. Hai hệ cố ý khác nhau; cái phải khớp giữa chúng là con số, thuật ngữ và giọng.

Bốn luật dễ phá nhất khi sửa tiếp:

1. **Sàn màu chữ là `slate-400` `#94A3B8`.** `slate-500` và `slate-600` trượt WCAG AA trên nền này (3,82:1 và 2,40:1) nên chúng **không có mặt trong bảng token** như màu chữ. Bản bolt gốc dùng đúng hai màu đó cho chữ nhỏ; đây là chỗ duy nhất bản dựng này cố ý lệch khỏi nó.
2. **Nguồn prediction phải đọc được ngay.** Ca demo luôn mang badge `prediction out-of-fold`; dữ liệu ZIP V1 không bao giờ tạo số mô phỏng.
3. **Không `text-transform: uppercase` cho chữ tiếng Việt.** Dấu thanh chồng dấu phụ vỡ trên chữ hoa ở cỡ nhỏ (Ế, Ữ, Ậ, Ổ). Class `.label` cố ý bỏ `uppercase` so với bản bolt.
4. **Không hiển thị chỉ số pipeline không tính.** Không có epistemic/aleatoric tách đôi — chỉ có `entropy` và `ensemble_std`. Và không viết câu chỉ định lâm sàng ("cần sinh thiết"): ràng buộc RUO, không phải lựa chọn giọng.

## Test

```powershell
python -m pytest tests/test_webapp_phases.py tests/test_webapp_api.py tests/test_webapp_volumes.py -q
```

`test_webapp_volumes.py` skip sạch khi không có `data/sample`. Hai file kia chạy được ở mọi máy.
