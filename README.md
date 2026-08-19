# Phân loại đa lớp tổn thương gan trên MRI 3D đa thì

> ### ⚠️ Research Use Only — chưa kiểm định lâm sàng
> Toàn bộ kết quả trong repo này đo trên dữ liệu hồi cứu của một dataset nghiên cứu.
> **Không dùng để chẩn đoán, điều trị, hay thay thế ý kiến của bác sĩ.**

Phân loại **7 loại tổn thương gan** ở mức ROI, trực tiếp trên khối MRI 3D **8 thì**, trên
dataset [LLD-MMRI](https://github.com/LMMMEng/LLD-MMRI2023) (MICCAI 2023, 498 bệnh nhân).

Đóng góp của đề tài **không phải điểm số leaderboard** mà là **độ tin cậy của câu trả lời**:
xác suất đã hiệu chỉnh, và một cơ chế để mô hình **từ chối ca nó không chắc** thay vì đoán bừa.

---

## Kết quả chốt

Đo trên **tập test 104 ca chính thức**, giữ kín trong suốt quá trình phát triển, đánh giá theo
protocol khoá trước. Bộ dự đoán là **ensemble 5 fold** của UniFormer-S 3D + trọng số Kinetics-400.

| | giá trị | ghi chú |
|---|---|---|
| **macro-F1** | **0,7682** [0,6902; 0,8422] | κ = 0,7333 · accuracy 0,7788 |
| **ECE** (chưa hiệu chỉnh) | **0,0833** | tự tin thái quá chỉ +0,042 |
| **macro-F1 @ coverage 80%** | **0,8421** | hiệu +0,0739 [+0,0126; +0,1360], **P = 0,027** |
| **Coverage ở mức sai ≤ 10%** | **76,9%** | phần ca hệ thống tự quyết được |
| so với cấu hình đối chứng | **+0,1520** [+0,0647; +0,2421] | **P = 0,001**, bootstrap ghép cặp |

**Định vị cho đúng — hai câu, đọc cả hai:**

- ✅ **Vượt baseline chính thức của challenge (0,6083) một cách có ý nghĩa thống kê** —
  khoảng tin cậy [0,690; 0,842] không chứa con số đó.
- ⛔ **Chưa phân biệt được với nhóm 0,71–0,83** (các phương pháp công bố tốt nhất đạt
  0,79–0,83). Ở n = 104 khoảng tin cậy rộng ±0,09, nên không được viết "ngang SOTA".

Chi tiết đầy đủ: **[`reports/FINAL_REPORT.docx`](reports/FINAL_REPORT.docx)**.

---

## Bài toán

Cho trước một bộ MRI gan đa thì và **vị trí tổn thương đã khoanh sẵn**, xác định tổn thương
thuộc loại nào trong bảy loại:

| ác tính | lành tính |
|---|---|
| HCC · ICC · di căn | nang · u máu · FNH · áp-xe |

**Không phải** bài toán phát hiện (vị trí cho trước), **không phải** phân vùng (đầu ra là một
nhãn, không phải mặt nạ).

**Đầu vào:** 8 thì — C-pre, C+A, C+V, C+Delay, T2WI, DWI, In Phase, Out Phase. Tám thì này
*không* nằm trên cùng một lưới voxel, nên phải đưa về một lưới chung rồi xếp thành 8 kênh.

**Đầu ra:** 7 xác suất · một mức bất định · một cờ từ chối.

---

## Cấu hình chính

| | |
|---|---|
| Kiến trúc | **UniFormer-S 3D**, khởi tạo từ trọng số **Kinetics-400** |
| Đầu vào mô hình | 8 kênh × **112 × 112 trong mặt phẳng × 14 lát** |
| Lưới cache | 128 × 128 × 16 (train cắt ngẫu nhiên, suy luận cắt giữa) |
| Loss | Focal γ=2 (softmax) + trọng số số mẫu hiệu dụng + label smoothing 0,1 |
| Bộ dự đoán | ensemble 5 fold, trung bình softmax |
| Config | [`configs/uniformer_s.yaml`](configs/uniformer_s.yaml) |

Đây là bản **tái lập recipe của đội hạng hai** trong challenge, có ghi rõ bốn chỗ cố ý lệch
(xem báo cáo §3.5). Đáng chú ý: baseline chính thức dùng **đúng kiến trúc này** nhưng huấn
luyện từ đầu và chỉ đạt 0,6083 — nên đây gần như là một phép so sánh có kiểm soát sẵn có.

---

## Cấu trúc repo

| Thư mục | Nội dung |
|---|---|
| `src/` | `data/` `preprocess/` `models/` `train/` `eval/` `utils/` — code chạy trên Kaggle |
| `configs/` | YAML siêu tham số; mọi run đúng một file |
| `splits/` | Split chính thức 316/78/104 — **đã khoá, bất biến** |
| `notebooks/` | Lớp mỏng gọi vào `src/`, chạy trên Kaggle |
| `webapp/` | Demo full-stack: FastAPI + React/Vite/TS |
| `reports/` | `FINAL_REPORT.docx` + 4 báo cáo tuần + hình |
| `slides/` | Slide HTML |
| `scripts/` | Quality gate, sinh báo cáo, tiện ích |
| `tests/` | 537 test, gồm test chống rò rỉ dữ liệu |
| `docs/` | Spec sheet, pre-registration, kho lưu thí nghiệm |

---

## Cài đặt

Hai môi trường **tách hẳn nhau** — backend serve không kéo theo cả stack huấn luyện:

```bash
pip install -r requirements.txt                  # huấn luyện / tiền xử lý (torch, MONAI)
pip install -r webapp/backend/requirements.txt   # chỉ để chạy web app
```

---

## Tái lập kết quả

```bash
# 0. Kiểm split chính thức còn nguyên vẹn
python -c "from src.data.splits import Splits; Splits('splits').validate()"

# 1. Dựng cache tiền xử lý — CHẠY MỘT LẦN, trên CPU, ~20 phút
python -m src.preprocess.build_cache --config configs/preprocess_cghnet.yaml

# 2. Huấn luyện 5 fold  (~6,5 giờ mỗi fold trên Tesla T4 => ~32,5 giờ)
for f in 1 2 3 4 5; do
  python -m src.train.run --config configs/uniformer_s.yaml --fold $f
done

# 3. Đánh giá — chỉ cần CPU, đọc xác suất đã lưu
python -m src.eval.run     --run-dir runs/Uniformer3D      # macro-F1, kappa, CI bootstrap
python -m src.eval.trust   --run-dir runs/Uniformer3D      # calibration + selective
python -m src.eval.compare --baseline runs/E4_cv_results --candidate runs/Uniformer3D
```

Huấn luyện **checkpoint và resume mỗi epoch** — chạy lại đúng lệnh trên sẽ tiếp tục từ chỗ
dừng, vì một phiên Kaggle có thể chết bất cứ lúc nào.

### Chạm tập test

⚠️ Tập test 104 ca **đã được chạm hai lần hợp lệ**. Lượt thứ ba cần đủ ba thứ, không bỏ bước
nào: xin phép, một pre-registration **commit trước khi chạy**, và một entry WORKLOG.
Protocol ở [`docs/TEST104_PREREGISTRATION.md`](docs/TEST104_PREREGISTRATION.md).

Đọc lại số của lượt đã chạy thì **không** tính là một lượt chạm mới:

```bash
python -m src.eval.test_report --run-dir runs/Uniformer3D/test --oof-dir runs/Uniformer3D
```

---

## Chạy web app demo

```bash
python -m uvicorn webapp.backend.main:app --reload    # cổng 8000
cd webapp/frontend && npm install && npm run dev
```

Mở **`http://localhost:5173`** — trên Windows, Vite bind vào `::1` nên `127.0.0.1:5173`
**không** vào được.

Luồng làm việc một chiều: thả một tệp ZIP chứa 8 chuỗi MRI trong `images/` và 8 nhãn tổn
thương tương ứng trong `masks/` → hệ thống kiểm contract → chạy ensemble 5 mô hình ngay trên
máy chủ → hiện xác suất từng lớp, mức bất định và trạng thái kết quả.

Nhãn tổn thương là **dữ liệu người dùng cung cấp**, không phải đầu ra phân vùng của mô hình —
dự án này không làm phân vùng.

---

## Thứ KHÔNG nằm trong repo

Ba nhóm sau bị `.gitignore` và **không đi kèm** khi clone:

| | Vì sao | Cách trỏ lại |
|---|---|---|
| `data/` — ảnh MRI bệnh nhân | Dữ liệu người thật; giấy phép **CC BY-NC-ND** cấm phát tán bản phái sinh | tự xin quyền truy cập LLD-MMRI |
| `artifacts/` — cache tiền xử lý | Vài GB, dựng lại được | chạy bước 1 ở trên, hoặc `LLDMMRI_CACHE_DIR` |
| `runs/` — checkpoint + xác suất đã lưu | Hàng trăm MB mỗi fold | `LLDMMRI_LIVE_WEIGHTS_DIR` cho web app |

Web app báo `model_loaded: false` ở `/api/health` cho tới khi tìm thấy trọng số 5 fold — đó là
trạng thái **đúng** của một máy vừa clone repo, không phải lỗi.

---

## Giới hạn

Đọc kèm mọi con số ở trên:

1. **RUO.** Chưa qua bất kỳ kiểm định lâm sàng nào.
2. **n = 104** ở tập test ⇒ khoảng tin cậy rộng ±0,09; ở mức từng lớp chỉ 10–16 ca mỗi lớp
   nên các con số đó chỉ mang tính mô tả.
3. **Số out-of-fold mang thiên lệch chọn checkpoint +0,0797** — đã đo và báo, nên nó *không*
   phải ước lượng không thiên lệch của khả năng khái quát hoá.
4. **Tập test đã chạm hai lần.** Mỗi lần đều có protocol khoá trước, nhưng càng nhiều lượt
   thì tính "chưa từng nhìn thấy" càng yếu đi.
5. **Phép căn các thì chỉ khử tịnh tiến** — không khử xoay, không khử biến dạng.
6. **Chưa có external validation, chưa có OOD probe.** Toàn bộ kết quả nằm trong một dataset
   duy nhất, nên chưa nói được gì về khả năng chuyển sang máy chụp hay quần thể khác.
7. **Lớp di căn là nút thắt còn lại**: F1 0,576 out-of-fold. Nếu sáu lớp kia đều đạt 0,95 mà
   lớp này giữ nguyên thì macro-F1 cũng chỉ tới 0,896 — nó một mình chặn mốc 0,9.

---

## Tài liệu

| File | Nội dung |
|---|---|
| [`reports/FINAL_REPORT.docx`](reports/FINAL_REPORT.docx) | **Báo cáo kết thúc dự án** — đầy đủ |
| `reports/W1–W4_REPORT.md` | Báo cáo tiến độ từng tuần |
| [`AGENTS.md`](AGENTS.md) | Nguồn sự thật ngữ cảnh dự án cho mọi công cụ AI |
| [`docs/MRI_Classification_Spec_Sheet.md`](docs/MRI_Classification_Spec_Sheet.md) | Chốt kỹ thuật: dataset, metric, ngưỡng |
| [`docs/TEST104_PREREGISTRATION.md`](docs/TEST104_PREREGISTRATION.md) | Protocol khoá trước mỗi lần chạm test |
| [`docs/EXPERIMENT_ARCHIVE.md`](docs/EXPERIMENT_ARCHIVE.md) | Hồ sơ thí nghiệm đã bị thay thế |
| [`WORKLOG.md`](WORKLOG.md) | Nhật ký bàn giao, append-only |

---

## Kiểm tra chất lượng

```bash
python -m pytest                                  # 537 test
python -m ruff check src tests scripts webapp
powershell -File scripts/quality-gate.ps1         # Windows
sh scripts/quality-gate.sh                        # Bash
```

---

## Giấy phép và trích dẫn dữ liệu

Dataset **LLD-MMRI** phát hành theo **CC BY-NC-ND**: không thương mại, **không phát tán bản
phái sinh**. Cache tiền xử lý và mọi khối ảnh sinh ra từ nó vì thế không được công bố.

Nguồn được tái lập trong dự án: [LLD-MMRI2023](https://github.com/LMMMEng/LLD-MMRI2023)
(baseline + bảng xếp hạng) và [ZHEGG/miccai2023](https://github.com/ZHEGG/miccai2023)
(recipe đội hạng hai). Danh mục tham khảo đầy đủ ở mục 7 của báo cáo cuối.
