# Web app demo

> **Research Use Only. Chưa kiểm định lâm sàng, không dùng để chẩn đoán.**

Demo cho người review nghiên cứu thấy hành vi của mô hình phân loại bảy lớp tổn thương gan trên MRI 3D tám thì: xác suất từng lớp, mức bất định, và cờ `defer` khi mô hình từ chối quyết.

## Trạng thái

| Phần | Trạng thái |
|---|---|
| Contract API, nhận diện thì, đọc NIfTI, render lát | **chạy được** |
| Ảnh MRI hiển thị | **thật**, đọc trực tiếp từ file gốc |
| Kết quả ca demo | **prediction out-of-fold thật**, chỉ hiển thị cho ca demo có dữ liệu OOF |
| ZIP người dùng tải | kiểm tra 8 MRI trong `images/` và 8 mask trong `masks/`; khi đủ contract, chạy ensemble UniFormer-S trực tiếp trong thư mục tạm |
| Heatmap đa thì | artefact offline E4; thiếu hoặc sai shape thì viewer chỉ hiện MRI nguồn, không dựng heatmap thay thế |

Suy luận `live` chỉ mở khi ZIP có mask tổn thương cùng lưới vật lý với từng MRI. Đó là dữ liệu cần thiết để tái tạo crop ROI của UniFormer, không phải output segmentation do app tạo ra.

## Chạy

```powershell
.\.venv\Scripts\python.exe -m pip install -r webapp/backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn webapp.backend.main:app --reload      # cổng 8000

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
| `LLDMMRI_MODEL_HEATMAP_DIR` | `runs/E4_per_phase_results/model_heatmaps` | Thư mục artefact heatmap đa thì E4 đã xuất offline |
| `LLDMMRI_CHECKPOINT` | *(chưa đặt)* | Đường dẫn checkpoint. Đặt vào khi nhánh suy luận thật đã viết |
| `LLDMMRI_LIVE_WEIGHTS_DIR` | `runs/Uniformer3D` | Thư mục các checkpoint `uniformer3D_best_<fold>.pt` hoàn tất |
| `LLDMMRI_LIVE_PREPROCESS_CONFIG` | `configs/preprocess_cghnet.yaml` | Crop ROI `128×128×16` rồi cắt giữa thành `112×112×14` cho UniFormer |
| `LLDMMRI_UPLOAD_VIEW_TTL_SECONDS` | `1800` | Số giây giữ MRI gốc của upload mới nhất trong thư mục tạm để xem ảnh |
| `LLDMMRI_DEFER_THRESHOLD` | `0.55` | Ngưỡng confidence dưới đó thì `defer`. Giá trị thật sẽ khoá trên validation từ đường risk-coverage, không chọn tay |

## Upload ZIP và suy luận trực tiếp

Chỉ nhận **một ZIP**. ZIP cần có hai thư mục: `images/` chứa 8 MRI và `masks/` chứa 8 mask tổn thương tương ứng. Mỗi phần phải có đúng một `.nii` hoặc `.nii.gz` nhận diện được cho từng thì: C-pre, C+A, C+V, C+Delay, T2WI, DWI, In Phase và Out Phase. Mask phải cùng shape, spacing, origin và direction với ảnh của chính thì đó.

`POST /api/validate-upload` chỉ đọc manifest. `POST /api/predict-upload` chỉ giải nén tạm đúng 16 NIfTI đã được nhận diện, tái tạo crop UniFormer và chạy các checkpoint fold đã hoàn tất. Xác suất là trung bình softmax thô. Cơ chế tự nhận/từ chối dùng max-prob với ngưỡng 80% coverage được khóa từ 394 dự đoán OOF UniFormer; backend không đọc hay fit lại trên Test-104. Kết quả không dùng để chẩn đoán.

Sau một lần suy luận thành công, app cho xem đủ 8 thì của **ảnh MRI gốc, chưa crop** và bật/tắt nhãn tổn thương do người dùng cung cấp. Để đọc lát, app chỉ giữ tạm NIfTI của bộ tải lên mới nhất trong thư mục tạm tối đa 30 phút (mặc định); hết hạn, khởi động lại server hoặc tải bộ mới thì chúng bị xoá. Crop ROI `112×112×14` vẫn chỉ dùng nội bộ cho UniFormer. Upload không có heatmap vì app không tạo heatmap mô phỏng.

Không dùng folder picker: hành vi khác nhau giữa các trình duyệt. DICOM-folder là mở rộng riêng khi app có contract DICOM, không trộn với NIfTI ZIP V1.

## Heatmap đa thì E4

Xuất artefact offline bằng [`notebooks/11_model_heatmaps.ipynb`](../notebooks/11_model_heatmaps.ipynb). Mỗi `<case>.npz` phải có `phase_tokens`, `crop_refs`, `heatmaps_pred`, `annotation_masks`, `pred_index` và `heatmap_scale`; ba mảng cùng shape `[8, X, Y, Z]`. `heatmaps_pred` là `|input × gradient|` của **lớp model đã dự đoán**, chuẩn hoá bằng một thang chung trên cả tám thì.

Backend chỉ chấp nhận đúng thứ tự phase E4 và shape khớp nhau. Nó render duy nhất theo thứ tự MRI → heatmap hổ phách → nhãn người chú giải fuchsia, nên nhãn không bị che hoặc bị hiểu nhầm là model segmentation.

## Thiết kế

Thế giới thị giác ở [`DESIGN.md`](DESIGN.md) trong thư mục này — **"bàn đọc tối"**, riêng cho web app. `DESIGN.md` ở gốc repo là hệ khác ("bản khắc atlas") và thuộc về `slides/` với `reports/`. Hai hệ cố ý khác nhau; cái phải khớp giữa chúng là con số, thuật ngữ và giọng.

Bốn luật dễ phá nhất khi sửa tiếp:

1. **Sàn màu chữ là `slate-400` `#94A3B8`.** `slate-500` và `slate-600` trượt WCAG AA trên nền này (3,82:1 và 2,40:1) nên chúng **không có mặt trong bảng token** như màu chữ. Bản bolt gốc dùng đúng hai màu đó cho chữ nhỏ; đây là chỗ duy nhất bản dựng này cố ý lệch khỏi nó.
2. **Nguồn prediction phải đọc được ngay.** Ca demo mang badge đánh giá độc lập; ZIP đủ MRI + mask mang badge suy luận trực tiếp. Không có số mô phỏng.
3. **Không `text-transform: uppercase` cho chữ tiếng Việt.** Dấu thanh chồng dấu phụ vỡ trên chữ hoa ở cỡ nhỏ (Ế, Ữ, Ậ, Ổ). Class `.label` cố ý bỏ `uppercase` so với bản bolt.
4. **Không hiển thị chỉ số pipeline không tính.** Không có epistemic/aleatoric tách đôi — chỉ có `entropy` và `ensemble_std`. Và không viết câu chỉ định lâm sàng ("cần sinh thiết"): ràng buộc RUO, không phải lựa chọn giọng.

## Test

```powershell
python -m pytest tests/test_webapp_phases.py tests/test_webapp_api.py tests/test_webapp_volumes.py tests/test_webapp_model_heatmaps.py -q
```

`test_webapp_volumes.py` skip sạch khi không có `data/sample`. Hai file kia chạy được ở mọi máy.
