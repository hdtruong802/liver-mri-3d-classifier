# Web app demo

> **Research Use Only. Chưa kiểm định lâm sàng, không dùng để chẩn đoán.**

Demo cho người review nghiên cứu thấy hành vi của mô hình phân loại bảy lớp tổn thương gan trên MRI 3D tám thì: xác suất từng lớp, mức bất định, và cờ `defer` khi mô hình từ chối quyết.

## Trạng thái

| Phần | Trạng thái |
|---|---|
| Contract API, nhận diện thì, đọc NIfTI, render lát | **chạy được** |
| Ảnh MRI hiển thị | **thật**, đọc trực tiếp từ file gốc |
| Kết quả suy luận | **giả lập**, chưa có checkpoint. Mọi con số mang `provenance.source = "simulated"` |
| Grad-CAM | chưa có, hiển thị bằng vùng gạch chéo "chưa khảo sát" |

Khi có checkpoint ở giai đoạn sau: thay nhánh trong `backend/inference.py`, đổi `source` sang `live`. Không phần nào khác phải sửa.

## Chạy

```powershell
pip install -r webapp/backend/requirements.txt
python -m uvicorn webapp.backend.main:app --reload      # cổng 8000

cd webapp/frontend
npm install
npm run dev                                             # cổng 5173, mở http://127.0.0.1:5173
```

Frontend proxy `/api` sang cổng 8000, nên ảnh bệnh nhân đi qua cùng origin.

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

## Thiết kế

Thế giới thị giác ở [`DESIGN.md`](DESIGN.md) trong thư mục này — **"hải đồ đo sâu"**, riêng cho web app. `DESIGN.md` ở gốc repo là hệ khác ("bản khắc atlas") và thuộc về `slides/` với `reports/`. Hai hệ cố ý khác nhau; cái phải khớp giữa chúng là con số, thuật ngữ và giọng.

Ba luật dễ phá nhất khi sửa tiếp:

1. **Magenta chỉ dành cho `defer`.** Không dùng nó cho nhãn, tiêu đề, hover, hay bất cứ thứ gì khác.
2. **Chữ nghiêng nghĩa là số giả lập**, gạch chéo nghĩa là chưa có dữ liệu. Cả hai đã có nghĩa, không được dùng để trang trí hay nhấn mạnh.
3. **Bo góc 0, không đổ bóng.** Điều này được ép ở `frontend/tailwind.config.js` chứ không chỉ ghi trong tài liệu: viết `rounded-2xl` hay `shadow-xl` sẽ không sinh ra class nào.

## Test

```powershell
python -m pytest tests/test_webapp_phases.py tests/test_webapp_api.py tests/test_webapp_volumes.py -q
```

`test_webapp_volumes.py` skip sạch khi không có `data/sample`. Hai file kia chạy được ở mọi máy.
