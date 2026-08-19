# Kế hoạch làm việc chi tiết — Tuần 2 (Sprint 1)

> 📅 **Tài liệu LỊCH SỬ — kế hoạch viết trước khi thực thi, giữ nguyên làm hồ sơ.**
> Nó mô tả ý định ở thời điểm lập kế hoạch, **không** mô tả repo hiện tại: một số
> module nêu ở đây (ví dụ `src/xai/`) đã được gỡ ở WORKLOG S-197, và một số hướng đã
> bị kết quả thực nghiệm loại. Trạng thái đang hiệu lực: [`../README.md`](../README.md)
> và [`../AGENTS.md`](../AGENTS.md) §5.

> **Research Use Only (RUO)** — chưa kiểm định lâm sàng, không dùng chẩn đoán.
> Bung mục tiêu W2 trong [`docs/plan.md`](plan.md) thành task theo ngày cho một người thực thi tuần tự.
> **Sprint 1 kết thúc cuối W2.** Phần MRI bắt đầu từ số 0 về code (chưa có `src/`, chưa tải data).

**Mục tiêu W2 (không đổi):** đưa LLD-MMRI vào một pipeline tái lập được, có **file split khoá mức bệnh nhân**, và **con số baseline đầu tiên** (2.5D + 3D-patch, 1 fold) làm mốc so sánh cho các tuần sau.

**Nguồn ràng buộc:** Spec Sheet §2 (preprocessing/split/leakage), §3 (DenseNet121-3D + fallback 2.5D), §4.7 (bootstrap CI) · AGENTS.md §3/§4/§6/§7/§8/§10 · W1_REPORT §5 mục 1–2.

---

## 0. Kết quả review dataset (2026-07-24) — ĐÃ XÁC MINH

Dataset `marcohoang/lldmmridataset` (Kaggle, private, ~83.7GB, v1) = **bản raw của `wanglab/LLD-MMRI-MedSAM2` (HuggingFace) dump nguyên si**, gồm cả cache `lld/.cache/huggingface/**`. Là **input thô cho `build_cache`**, không phải cache đã tiền xử lý.

**Đã sẵn (khớp hướng mới):**
- ✅ 498 bn · 8 thì đúng chuẩn (`C-pre, C+A, C+V, C+Delay, T2WI, DWI, InPhase, OutPhase`) · full-volume `.nii.gz` tại `lld/images/`.
- ✅ `lld/LLD_MMRI_Annotation.json` (18MB) giữ **annotation phân loại gốc**: `Category_info` = 7 lớp + `Benign[0,2,4,5]`/`Malignant[1,3,6]` (khớp Spec Sheet 100%); `Annotation_info` = per-phase `pixel_spacing/slice_spacing/origin` + `lesion.category` + `bbox.2D_box` (hộp 2D theo từng slice).

**Bổ sung từ PDF challenge (`docs/LiverLesion…pdf` p.9-13) + repo LMMMEng:**
- **Phân bố lớp (tổng 498):** HCC 157 · u máu 79 · ICC 58 · áp-xe 54 · nang 53 · di căn 51 · FNH 46 → **HCC áp đảo, imbalance vừa phải** (HCC:FNH ≈ 3.4:1), KHÔNG long-tail. Split official **stratified, sizes 316/78/104**; **patient_id không có trong PDF nhưng ĐÃ TÁI LẬP** (xem Quyết định §0 + `splits/`).
- **Geometry khác nhau giữa thì (p.9):** non-contrast chụp **coronal**; DWI matrix 132×116 (thô); T1 spacing 2mm, T2 spacing 1mm; đa máy 1.5T/3T (Kangda/GE/Philips) → **registration + resample về grid chung là BẮT BUỘC**, và có **domain shift nội bộ** (hợp lý hoá calibration/robustness).
- **Nhãn = pathology report** (gold standard), bbox vẽ per-phase. Metric ranking = **trung bình(macro-F1, Cohen's κ)** — khớp Spec Sheet.
- ⚠️ **License CC BY-NC-ND** → KHÔNG phát tán bản dữ liệu phái sinh (cache) công khai; repro pack chỉ chia **code + split IDs + config**; Kaggle Dataset để **private**.

**Thiếu / phải xử lý (đã phản ánh vào task bên dưới):**
- ✅ **Split official 316/78/104 — ĐÃ TÁI LẬP** (bản wanglab không kèm split, nhưng lấy `labels_trainval.txt` từ repo đội thi ZHEGG/miccai2023 → test-104 = 498 − 394; verify khớp PDF 100%). Lưu 12 file ở `splits/`. Xem "Quyết định" dưới + T4.1.
- 🟡 **Là bản đóng gói SEGMENTATION** — kèm `lld/labels/` = mask MedSAM2 (không dùng, chiếm phần lớn 83.7GB). Reader chỉ đọc `images/` + annotation, **bỏ `labels/` + `.cache/`**. Không drift sang segmentation (AGENTS.md §3.9).
- 🟡 **Không có patch cắt sẵn** — chỉ full-volume → v0 **crop từ full-volume bằng bbox** (đảo giả định "patch cắt sẵn" của Plan §3).
- 🟡 **bbox là 2D per-slice** → phải gộp `2D_box` theo `slice_idx` thành 1 ROI 3D cho crop.
- 🟡 **Chưa xác minh ảnh↔annotation** (bản MedSAM2 có thể đã resample/reorient ảnh trong khi bbox ở toạ độ gốc) → gate EDA (T2.1).

**Quyết định đã chốt (2026-07-24, WORKLOG S-021):** dùng **split official 316/78/104 — ĐÃ TÁI LẬP + verify**. `labels_trainval.txt` (394) lấy từ [ZHEGG/miccai2023](https://github.com/ZHEGG/miccai2023) → test-104 = 498 − 394; **phân bố lớp khớp PDF official 100%** (7/7 lớp). Lưu 12 file ở `splits/` (bất biến); 5-fold CV dùng official fold. **Khôi phục so benchmark trực tiếp với SOTA.** *(Đảo quyết định S-019 "tự chia"; Spec Sheet §2 cập nhật lại.)*

---

## GATE ngày 0 — Data readiness (ĐÃ THÔNG)

> Data access = ✅ + **split official 316/78/104 đã tái lập + verify** (§0). **Không còn blocker cho W2.**

- [x] LLD-MMRI 498 bn / 8 thì / annotation 7 lớp + bbox — **có** (§0).
- [x] Split official 316/78/104 — **đã tái lập + verify** (khớp PDF 100%), lưu `splits/` (12 file, bất biến).
- [ ] Chốt reader **bỏ `lld/labels/` (mask segmentation) + `lld/.cache/`**.

**Verify:** `splits/labels_trainval.txt` = 394 · `splits/test_official.txt` = 104 · union = 498; đọc được `lld/images/` + `LLD_MMRI_Annotation.json`.
**Ghi chú:** CT fallback (GNG-1) KHÔNG còn cần — đã có MRI.

---

## Lịch 6 ngày

Ước lượng ~6 ngày làm việc. Mỗi task ghi: **file tạo ra · phụ thuộc · DoD + cách verify · ràng buộc Kaggle · rủi ro**.

---

### Ngày 1 — Khung `src/` + ingestion + manifest

**T1.1 — Scaffold hạ tầng chung**
- *File:* `src/utils/seed.py` (`set_seed()`), `src/utils/io.py`, `src/utils/logging.py`, `src/__init__.py` các cấp.
- *Phụ thuộc:* —
- *DoD + verify:* `from src.utils.seed import set_seed; set_seed(42)` chạy không lỗi; set seed cho `torch/numpy/random` + cờ deterministic tại **một chỗ duy nhất**.
- *Kaggle:* — · *Rủi ro:* —

**T1.2 — Dataset reader LLD-MMRI**
- *File:* `src/data/dataset.py` (đọc 8 pha từ `lld/images/{MR-*}_{lesion}_{phase}_0000.nii.gz` + parse `LLD_MMRI_Annotation.json` cho `category` + `bbox.2D_box`), `src/data/__init__.py`.
- *Phụ thuộc:* GATE ngày 0, T1.1.
- *DoD + verify:* load 1 mẫu → trả dict `{phases: tensor[8,...], label: int, patient_id, bbox3d}`; **chỉ đọc `images/` + annotation**, bỏ qua `lld/labels/` (mask segmentation) và `lld/.cache/`; script in ra 5 mẫu đầu.
- *Kaggle:* đường dẫn gốc data **qua config/env**, không hardcode. · *Rủi ro:* (a) thiếu pha ở một số bệnh nhân → ghi chiến lược (impute/loại) ở EDA; (b) đừng vô tình nạp `labels/` mask → sai bài toán (segmentation).

**T1.3 — Manifest bệnh nhân**
- *File:* `src/data/build_manifest.py` → `data/manifest.csv` (gitignore) : patient_id, class (từ `Category_info`), có/thiếu từng pha, spacing/shape gốc, cột `split` (điền từ `splits/` official: train_fold/val_fold/test).
- *Phụ thuộc:* T1.2.
- *DoD + verify:* manifest có đúng 498 dòng; cột class ∈ 7 nhãn; đếm thiếu-pha ra số cụ thể.

---

### Ngày 2 — EDA

**T2.1 — Notebook EDA**
- *File:* `notebooks/01_eda.ipynb` (lớp mỏng, chỉ gọi vào `src/`, **strip output trước commit**).
- *Phụ thuộc:* T1.3.
- *DoD + verify:* notebook chạy end-to-end sinh: (a) phân bố 7 lớp (đối chiếu phân bố official ở §0: HCC áp đảo, FNH ít nhất — kiểm dữ liệu thật có khớp); (b) phân bố spacing & shape mỗi pha; (c) tỉ lệ thiếu pha; (d) thống kê kích thước bbox lesion; (e) khuyến nghị crop size (96³ hay 64³) dựa trên bbox thực; (f) **GATE geometry (bắt buộc — các thì khác geometry theo PDF: non-contrast coronal, DWI thô):** load 3–5 ca, đối chiếu `shape`/`spacing`/**orientation** ảnh thật với `pixel_spacing/slice_spacing/origin` trong annotation; overlay `bbox.2D_box` lên đúng slice → xác nhận hộp trùng vùng u. **Không đạt → dừng, không crop theo bbox.**
- *Kaggle:* — · *Rủi ro:* (a) bbox lớn hơn 96×96×48 nhiều ca → chỉnh crop size ở `configs/preprocess.yaml` trước khi cache; (b) geometry lệch → phải resample bbox theo ảnh hoặc dùng full-volume tọa độ nhất quán trước khi tin ROI-crop.

**T2.2 — Chốt tham số tiền xử lý từ EDA**
- *File:* ghi quyết định vào đầu `configs/preprocess.yaml` (comment) + WORKLOG.
- *Phụ thuộc:* T2.1.
- *DoD + verify:* chốt: spacing đích, crop size, có/không N4 ở v0, chiến lược thiếu pha. Mỗi lựa chọn có 1 dòng lý do bám số EDA.

---

### Ngày 3 — Preprocessing v0 + cache Kaggle Dataset

**T3.1 — Config tiền xử lý**
- *File:* `configs/preprocess.yaml`.
- *Phụ thuộc:* T2.2.
- *DoD + verify:* mọi hyperparam preprocessing (spacing, crop, clip percentile, z-score, N4 on/off, path in/out) **đều trong YAML**, code chỉ đọc. Không magic number trong code.

**T3.2 — Pipeline build_cache**
- *File:* `src/preprocess/build_cache.py`, `src/preprocess/transforms.py`, `src/preprocess/bbox3d.py` (gộp `bbox.2D_box` theo `slice_idx` → 1 ROI 3D). MONAI: resample ~1.5×1.5×3.0mm → **ROI-crop 96×96×48 từ full-volume quanh ROI 3D** → per-sequence z-score / percentile clip. **N4 tuỳ chọn** (chậm — mặc định off ở v0, bật qua config).
- *Phụ thuộc:* T3.1, gate geometry T2.1. **Không có patch cắt sẵn** trong bản wanglab → crop từ full-volume bằng bbox (khác giả định Plan §3).
- **Cập nhật khi triển khai (S-030):** 8 pha KHÔNG cùng lưới voxel nên không thể "resample rồi crop theo voxel". Cách làm thực tế: đổi tâm bbox sang **toạ độ mm**, dựng **một lưới đích chung** quanh tâm đó, rồi lấy mẫu cả 8 pha lên lưới ấy (`sitk.Resample` với Identity transform trong không gian thế giới). **Đây đồng thời là bước căn chỉnh** — rigid registration riêng vẫn hoãn sang W3 làm ablation bù nhịp thở.
- *DoD + verify:* `python -m src.preprocess.build_cache --config configs/preprocess.yaml` chạy hết 498 ca, sinh cache (một file/ca hoặc tensor gộp); log CSV tiến độ; kiểm 3 ca ngẫu nhiên: shape đồng nhất `[8, 96, 96, 48]`, z-score mean≈0/std≈1 per-pha **tính trên train**.
- *Kaggle:* chạy **offline 1 lần** → đẩy lên làm **Kaggle Dataset có version**; notebook chỉ mount. Path ghi qua config. · *Rủi ro:* N4 quá chậm → **kill-switch: bỏ N4 v0** (đã mặc định off); cache không kịp → giảm còn resample+crop+z-score.

**T3.3 — Đẩy cache thành Kaggle Dataset versioned**
- *Phụ thuộc:* T3.2.
- *DoD + verify:* Kaggle Dataset tồn tại (**để private** — license CC BY-NC-ND), có version tag, ghi lại slug + version vào `configs/preprocess.yaml` (comment) để tái lập.
- *Kaggle:* **không commit cache/NIfTI vào git** (AGENTS.md §10). *License:* **CC BY-NC-ND → không phát tán cache/bản phái sinh công khai**; repro pack (W6) chỉ chia code + split IDs + config.

---

### Ngày 4 — Split khoá mức bệnh nhân + leakage test

**T4.1 — Nạp + validate split official (đã lưu ở `splits/`)**
- *File:* `src/data/make_splits.py` (nạp `splits/*.txt`, map ID theo **chữ số** sang key annotation + đường dẫn ảnh; **KHÔNG sinh ngẫu nhiên** — split đã khoá).
- *Phụ thuộc:* T1.3 (manifest 498 bn + class).
- *DoD + verify:* `python -m src.data.make_splits --check` xác nhận: `labels_trainval.txt` 394 + `test_official.txt` 104 = 498; 5-fold (`train_fold{i}`/`val_fold{i}`) hợp = 394, mọi cặp fold train∩val = ∅; class trong file khớp `Category_info`. **Split đã commit (bất biến) — không regenerate.** Docstring ghi rõ: **official split tái lập, test-104 = held-out khoá kín (chạm 1 lần)**.
- *Rủi ro:* ID format lệch (16/498 có gạch nối) → **chuẩn hoá theo chữ số** khi map file↔annotation↔ảnh; lớp thiểu số FNH 46 (không long-tail).

**T4.2 — Leakage test (bắt buộc)**
- *File:* `tests/test_no_leakage.py`, `tests/__init__.py`.
- *Phụ thuộc:* T4.1.
- *DoD + verify:* `pytest -q` **pass**: (a) giao tập patient_id giữa **mọi cặp fold = ∅**; (b) test-104 **giao với mọi fold = ∅**; (c) hợp các fold = đúng tập train+val.
- *Rủi ro:* fail → dừng, sửa split, không đi tiếp (đây là nguyên tắc bất di bất dịch §3.2).

**T4.3 — Wire dataset đọc cache + split**
- *File:* cập nhật `src/data/dataset.py` (đọc từ cache Kaggle Dataset theo fold).
- *Phụ thuộc:* T3.3, T4.1.
- *DoD + verify:* dựng được `train_loader/val_loader` cho fold 0; batch ra shape đúng; thống kê normalization **chỉ từ train fold**.

---

### Ngày 5 — Baseline 3D-patch + vòng train

**T5.1 — Backbone baseline**
- *File:* `src/models/densenet3d.py` (MONAI DenseNet121-3D, 8 kênh vào → 7 lớp — early concat v0), `src/models/__init__.py`.
- *Phụ thuộc:* T4.3.
- *DoD + verify:* forward `[B,8,96,96,48]` → logits `[B,7]` không lỗi; param count log ra.

**T5.2 — Vòng train + checkpoint/resume**
- *File:* `src/train/run.py`, `configs/baseline_3dpatch.yaml`.
- *Phụ thuộc:* T5.1.
- *DoD + verify:* `python -m src.train.run --config configs/baseline_3dpatch.yaml` train fold 0; **checkpoint + resume mỗi epoch**; **log CSV ghi liên tục** (không buffer đến cuối); AMP + gradient accumulation bật; early stopping theo macro-F1 val. Kiểm resume: kill giữa chừng → chạy lại tiếp đúng epoch.
- *Kaggle:* session ≤12h → checkpoint/resume mỗi epoch **bắt buộc**; batch 2–4 + effective 16–32; path output qua config. · *Rủi ro:* không hội tụ → xem GNG-2 (cuối W3, không phải giờ); VRAM tràn → hạ crop 64³ (config).

**T5.3 — Chạy 1 fold ra số**
- *Phụ thuộc:* T5.2.
- *DoD + verify:* fold 0 chạy xong, có macro-F1 val (chưa cần CI — CI là việc W3). Ghi số + config + seed.

---

### Ngày 6 — Baseline 2.5D + số mốc + đóng tuần

**T6.1 — Fallback 2.5D**
- *File:* `src/models/backbone2p5d.py` (stack 3 lát kề / 3 lát trực giao làm kênh, backbone 2D ImageNet-pretrained), `configs/baseline_2p5d.yaml`.
- *Phụ thuộc:* T5.2 (tái dùng train loop).
- *DoD + verify:* train fold 0, ra macro-F1 val; so cạnh 3D-patch (mốc để GNG-2 quyết ở cuối W3).

**T6.2 — Metric tối thiểu để báo số**
- *File:* `src/eval/metrics.py` (macro-F1 tối thiểu; bộ đầy đủ + bootstrap CI để sang W3), `src/eval/__init__.py`.
- *Phụ thuộc:* T5.3, T6.1.
- *DoD + verify:* hàm eval **thuần** (input→metric), tách khỏi train, chạy lại được trên checkpoint đã lưu.

**T6.3 — Cập nhật bảng lệnh + đóng tuần**
- *File:* `AGENTS.md` §6 (điền build_cache / make_splits / train / eval / pytest — trạng thái "sẵn sàng"); `WORKLOG.md` (append entry W2).
- *Phụ thuộc:* tất cả.
- *DoD + verify:* bảng lệnh khớp entrypoint thật; quality gate pass:
  `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-gate.ps1`; commit sạch.

---

## Definition of Done cuối W2 (khớp docs/plan.md) — kèm cách kiểm chứng

| DoD | Cách verify |
|---|---|
| [ ] EDA notebook (phân bố 7 lớp, spacing, shape, thiếu pha) | mở `notebooks/01_eda.ipynb`, chạy end-to-end ra đủ 5 biểu đồ/bảng |
| [ ] Preprocessing v0 (resample→crop→z-score) cache thành Kaggle Dataset versioned | `build_cache` chạy hết 498 ca; Kaggle Dataset có version; 3 ca kiểm shape `[8,96,96,48]` |
| [ ] `splits/` official 316/78/104 (12 file) đã commit, bất biến, validate | `labels_trainval.txt`(394)+`test_official.txt`(104)+5 fold trong git; `make_splits --check` pass; test không giao fold |
| [ ] `pytest tests/` leakage test PASS (giao tập BN mọi cặp fold = ∅) | `pytest -q` xanh; test kiểm cả test-104 tách rời |
| [ ] Baseline 2.5D + 3D-patch chạy 1 fold, ra macro-F1 val | 2 số val + 2 config + seed ghi lại |
| [ ] Cập nhật bảng lệnh AGENTS.md §6 (cùng commit tạo entrypoint) | đối chiếu §6 với entrypoint thật |

**Không phải việc của W2 (để tránh scope creep):** CV đủ 5-fold + bootstrap CI (→ W3), registration (→ W3), fusion variants/phase-attention (→ W4), calibration/selective (→ W5). W2 chỉ cần **1 fold ra số mốc**.

---

## Điểm phải hỏi người dùng (AGENTS.md §10)

- ✅ **Chiến lược split — đã chốt (2026-07-24, S-021):** **official 316/78/104 tái lập + verify** (khớp PDF 100%), lưu `splits/`. *(Đảo S-019; Spec Sheet §2 cập nhật. Data access ✅.)*
- **Đổi tham số đã chốt trong Spec Sheet** (spacing, crop, taxonomy, chiến lược split) — nếu EDA gợi ý phải đổi, nêu ra, không tự quyết.
- **Thêm dependency nặng** (vd ANTs cho registration — nhưng registration là W3, đừng kéo vào W2).
- **Đẩy dữ liệu/cache lên dịch vụ ngoài** ngoài Kaggle Dataset research-use.

## Task cắt được nếu trễ (thứ tự cắt)

1. **N4 bias correction** → bỏ khỏi v0 (mặc định off), chỉ resample+crop+z-score.
2. **Baseline 2.5D** (T6.1) → hoãn sang đầu W3; W2 tối thiểu chỉ cần 3D-patch ra số.
3. **Head phân cấp / xử lý thiếu pha tinh vi** → dùng chiến lược đơn giản (zero-fill pha thiếu), ghi rõ, xử lý kỹ ở W4.

---

## Câu hỏi cần chốt (Spec/plan chưa rõ)

1. ✅ **Data + split — đã chốt.** Official split 316/78/104 **đã tái lập** từ ZHEGG/miccai2023 + verify (khớp PDF). `splits/` có 12 file. Không còn chờ gì ở khâu data.
2. ✅ **Chốt: v0 crop từ full-volume bằng bbox** (bản wanglab không có patch cắt sẵn). Registration vẫn hoãn W3.
3. **Chạy N4 ở v0 không?** Mặc định đề xuất **off** (chậm, hoãn được). Đồng ý?
4. ✅ **Định dạng split:** txt chuẩn LLD-MMRI `<patient_id> <class>` (tương thích baseline) — đã lưu `splits/`.
5. **Chiến lược ca thiếu pha:** loại khỏi train hay zero-fill + mask? (EDA T2.1 sẽ cho số để quyết)
6. **Batch/crop mặc định:** bắt đầu 96³ batch 2 + grad-accum, hạ 64³ nếu tràn — chấp nhận?

---

*Bung mục tiêu W2 trong [`docs/plan.md`](plan.md) thành task. Mọi thay đổi quyết định đã chốt phải kèm một entry trong `WORKLOG.md`.*
