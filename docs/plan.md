# Kế hoạch chi tiết 5 tuần còn lại (W2 → W6)

> **Research Use Only (RUO)** — chưa kiểm định lâm sàng, không dùng chẩn đoán.
> Dự án: phân loại đa lớp u gan trên **MRI 3D đa pha** (LLD-MMRI, 7 lớp, 8 thì). Solo · Kaggle-only · MONAI/PyTorch.
> **Đóng góp headline:** trustworthiness (calibration + selective prediction), **không** đua accuracy.
>
> Tài liệu này chi tiết hoá lộ trình **từ Tuần 2 đến Tuần 6**. Tuần 1 đã xong (xem [`reports/W1_REPORT.md`](../reports/W1_REPORT.md)).
> Nó **không thay thế** [`liver_mri_3d_classification_plan.md`](liver_mri_3d_classification_plan.md) (project doc gốc) hay [`MRI_Classification_Spec_Sheet.md`](MRI_Classification_Spec_Sheet.md) (chốt kỹ thuật) — chỉ triển khai chúng thành task theo tuần.

---

## 0. Bối cảnh & tái-định-mốc (đọc trước)

Kế hoạch gốc dự trù **6 tuần cho riêng phần MRI** (Sprint 1 = T1–T2 dựng data/baseline). Nhưng thực tế:

- **Tuần 1** đã tiêu cho: pha CT (LiTS/HCC-TACE-Assist), feedback mentor, **đổi scope sang MRI 3D đa lớp**, và đặc tả (Spec Sheet + Plan + slide + W1 report). Xem W1_REPORT §3–§6.
- Phần MRI hiện **mới ở mức thiết kế**: chưa tải LLD-MMRI, chưa có `src/`, chưa có preprocessing/split/baseline. W1_REPORT §4 ghi rõ hàng loạt mục "Chưa bắt đầu".

**Hệ quả:** 5 tuần còn lại phải **nén lộ trình MRI 6 tuần vào W2–W6**. Đây là ràng buộc chi phối toàn bộ plan này. Nguyên tắc nén:

1. **Không cắt "ưu tiên bảo vệ"** (Spec Sheet §5, Plan Phụ lục A): model fusion có CV+CI · calibration + selective prediction · rigor thống kê · web app tối thiểu chạy được · reproducibility pack.
2. **Cắt sâu vào tham vọng phụ** khi trễ: deformable registration, arm full-volume, deep ensemble K lớn, external nhãn thô, phase attention v2 (thứ tự cắt ở §6).
3. **Backend web app khởi động sớm** (song song W5) để W6 không vỡ.
4. **Kích hoạt kill-switch dứt khoát tại mỗi go/no-go, không kéo dài** (§6).

**Mốc thời gian dự kiến** (điều chỉnh theo lịch thật; Tuần 1 chạy ~16–24/07/2026):

| Tuần | Khoảng ngày (dự kiến) | Sprint |
|---|---|---|
| **W2** | 25/07 – 31/07/2026 | **Sprint 1 → kết thúc** (data/preprocess/split/baseline) |
| **W3** | 01/08 – 07/08/2026 | Sprint 2 (CV+CI, fusion v0, registration, external) |
| **W4** | 08/08 – 14/08/2026 | **Sprint 2 → kết thúc** (model chính, full-volume, imbalance) |
| **W5** | 15/08 – 21/08/2026 | Sprint 3 (trustworthiness, ablation, stats, **khoá + test-104**) |
| **W6** | 22/08 – 28/08/2026 | **Sprint 3 → kết thúc** (web app, XAI, failure analysis, repro pack, report) |

> **Ranh giới sprint (đã chốt):** Sprint 1 = **W2** · Sprint 2 = **W3–W4** · Sprint 3 = **W5–W6**. Kết thúc mỗi sprint là một mốc review: cuối W2, cuối W4, cuối W6.

---

## 1. Bảng tổng quan 5 tuần

| Tuần | Mục tiêu một câu | Deliverable chính | Cổng kiểm / CI gate |
|---|---|---|---|
| **W2** | Có data + pipeline tiền xử lý cache + **split khoá** + baseline chạy ra số đầu tiên | Kaggle Dataset preprocessed (versioned); `splits/` 5-fold patient-level; baseline 2.5D + 3D-patch 1 fold | `pytest` leakage test **pass** (giao tập BN = ∅); quality gate; số baseline có trên val |
| **W3** | Baseline có **CV 5-fold + CI bootstrap**; fusion v0; registration; external harmonized | Bảng CV macro-F1/κ ± CI; fusion v0 (early concat 8 kênh); rigid registration pipeline; external ác/lành + Duke OOD set | CI bootstrap ≥2000 mức BN trên mọi số; không leakage; quality gate |
| **W4** | Chọn **model chính**: fusion variants + pretrained + full-volume + xử lý lớp hiếm | Fusion v1 (phase-attention); pretrained backbones; arm full-volume; class-balanced/focal; model chính chốt theo CV | So sánh CV có CI; model chính reproduce được từ config+seed; quality gate |
| **W5** | **Trustworthiness + ablation + thống kê + KHOÁ protocol + chạm test-104 (1 lần)** | Calibration (ECE/Brier/reliability); risk–coverage/AURC; bảng ablation lõi; DeLong/McNemar/Holm; external + OOD; **kết quả test-104 khoá kín** | **Pre-register** trước train cuối; threshold/temperature khoá trên val; **WORKLOG ghi trước khi chạm test** |
| **W6** | Web app tự code + XAI + failure analysis + repro pack + **báo cáo cuối** | FastAPI + frontend thuần (probs+uncertainty+defer+heatmap); Grad-CAM 3D + phase-importance; reproducibility pack; report W6 có CI + limitations | Quality gate + Impeccable detector trên UI; README chạy được; mọi số trong report có CI |

**Critical path:** truy cập data → cache preprocessing → baseline có CV+CI → model chính → calibration/selective → **khoá + test-104** → web app → report.

---

## 2. Chi tiết theo tuần

Mỗi tuần gồm: **(1) Mục tiêu + Definition of Done · (2) Task theo thứ tự phụ thuộc · (3) Deliverable · (4) Rủi ro + kill-switch · (5) Ràng buộc Kaggle.**
Task ánh xạ tới backlog **W1_REPORT §5** và cây thư mục **AGENTS.md §4**.

---

### W2 — Nền dữ liệu: data · preprocessing · split khoá · baseline đầu tiên

*(Ứng W1_REPORT §5 mục 1–2; **Sprint 1 — kết thúc cuối W2**)*

**1. Mục tiêu & Definition of Done**
Mục tiêu: đưa LLD-MMRI vào một pipeline tái lập được, có **file split khoá mức bệnh nhân** và **con số baseline đầu tiên** để làm mốc.
DoD (đo được):
- [ ] LLD-MMRI tải xong + notebook EDA (phân bố 7 lớp, spacing, shape, thiếu pha) trong `notebooks/`.
- [ ] Preprocessing v0 (resample → ROI-crop → per-sequence z-score) chạy được và **cache thành Kaggle Dataset có version**.
- [ ] `splits/` chứa file 5-fold **stratified patient-level** đã commit (bất biến).
- [ ] `pytest tests/` chạy **leakage test pass**: giao tập bệnh nhân giữa mọi cặp fold = ∅.
- [ ] Baseline 2.5D **và** 3D-patch (MONAI DenseNet121-3D) chạy **1 fold**, ra macro-F1 trên val.

**2. Task (thứ tự phụ thuộc)**
1. **[GATE cứng] Xác nhận quyền truy cập LLD-MMRI.** Nếu chưa có form được duyệt → xem GNG-1 (CT fallback) ngay đầu tuần, đừng chờ. *(→ hỏi người dùng, §5)*
2. Dựng khung `src/`: `src/utils/seed.py::set_seed()` (randomness một chỗ), `src/utils/io.py`, `src/utils/logging.py`.
3. `src/data/` — dataset LLD-MMRI (đọc 8 thì + bbox + nhãn 7 lớp), MONAI transforms.
4. `notebooks/` — EDA (strip output trước khi commit).
5. `src/preprocess/build_cache.py` + `configs/preprocess.yaml` — resample ~1.5×1.5×3.0 mm, ROI-crop 96×96×48, per-sequence z-score. **N4 tuỳ chọn** (chậm; có thể hoãn — xem kill-switch). Đường dẫn ghi **qua config**, không hardcode `/kaggle/working`.
6. `src/data/make_splits.py` → sinh `splits/` 5-fold stratified patient-level; **commit file split**.
7. `tests/test_no_leakage.py` — kiểm giao tập BN = ∅ giữa các fold.
8. `src/models/densenet3d.py` (baseline) + `src/models/backbone2p5d.py` (fallback arm) + `src/train/run.py` tối thiểu (checkpoint/resume mỗi epoch, log CSV).
9. Chạy 1 fold cho cả 2 baseline → ghi số val.
10. **Cập nhật bảng lệnh AGENTS.md §6** (build_cache, make_splits, train, pytest) trong cùng commit tạo entrypoint.

**3. Deliverable**
Kaggle Dataset preprocessed (versioned) · `splits/*.json|csv` · `configs/preprocess.yaml` · EDA notebook · leakage test pass · 2 số baseline val (2.5D, 3D-patch).

**4. Rủi ro & kill-switch**
- **Chưa có quyền data (rủi ro #1, nay khẩn cấp vì W1 đã tiêu):** → **GNG-1 → CT fallback đa pha public**, chấp nhận mất T2/DWI + câu chuyện LI-RADS. *Kích hoạt = hỏi người dùng.*
- **Preprocessing (N4) không cache kịp:** → bỏ N4 khỏi v0, chỉ resample + crop + z-score.
- **VRAM tràn với 96³×8 pha:** → hạ crop 64×64×32.

**5. Ràng buộc Kaggle**
Preprocessing chạy **offline 1 lần** → Kaggle Dataset versioned (không tiền xử lý lại mỗi session). Train: AMP + checkpoint/resume mỗi epoch + log CSV ghi liên tục. Mọi path ghi qua config.

---

### W3 — Baseline có CV+CI · fusion v0 · registration · external harmonized

*(Ứng W1_REPORT §5 mục 2 & 5; **Sprint 2 — bắt đầu**)*

**1. Mục tiêu & Definition of Done**
Mục tiêu: biến baseline 1-fold thành **bảng CV 5-fold có CI bootstrap**, có fusion v0, và dựng xong hạ tầng external/OOD.
DoD:
- [ ] Baseline 3D-patch chạy **đủ 5-fold**; có **bảng macro-F1/κ ± 95% CI** (bootstrap patient-level ≥2000).
- [ ] Fusion v0 (early concat 8 kênh) chạy 5-fold, so với baseline.
- [ ] Rigid registration pipeline (intra-patient về portal-venous trong ROI gan) chạy được.
- [ ] External nhãn thô harmonized (mapping về ác/lành hoặc HCC-vs-nonHCC) **+** Duke thành OOD set (không nhãn loại tổn thương).
- [ ] `src/eval/` thuần (input → metric), tách khỏi train, chạy lại được trên checkpoint cũ.

**2. Task (thứ tự phụ thuộc)**
1. `src/eval/metrics.py` — macro-F1, κ, balanced acc, macro-AUC/AUC-PR, sensitivity/specificity per-class, confusion matrix.
2. `src/eval/bootstrap.py` — CI bootstrap **mức bệnh nhân, stratified, ≥2000 lần** → mọi số dạng `điểm ± CI`.
3. Chạy baseline 3D-patch đủ 5-fold → **bảng CV có CI đầu tiên** (mốc so sánh chính).
4. `src/models/fusion.py` v0 (early concat 8 kênh) → chạy 5-fold, so baseline.
5. `src/preprocess/registration.py` — rigid/affine SimpleITK (Elastix) trong bbox gan; **ablation registered vs unregistered chuẩn bị** (chưa cần chạy đủ).
6. External: audit metadata nguồn public thứ 2 (cohort HCC MRI/TCIA) + harmonize nhãn về ác/lành. Duke: dựng OOD probe. **Chưa chạm test/external accuracy** — chỉ dựng tập.
7. Cập nhật AGENTS.md §6 (eval command).

**3. Deliverable**
Bảng CV macro-F1/κ ± CI (baseline vs fusion v0) · registration pipeline · external ác/lành set + Duke OOD set · `src/eval/` tách khỏi train.

**4. Rủi ro & kill-switch**
- **3D-patch không hội tụ / thua 2.5D nhiều (rủi ro registration + data nhỏ):** → **GNG-2 → 2.5D làm primary, 3D thành ablation.** *(→ hỏi người dùng vì đây là kill-switch, §5)*
- **External harmonize không xong / mapping mù mờ:** → **OOD-only (Duke)**, hoãn external nhãn thô. (Không được báo external accuracy trên nhãn không audit.)
- **Registration tạo "ảo giác căn chỉnh":** → giữ patch cắt sẵn như kênh đã căn, registration thành nhánh ablation.

**5. Ràng buộc Kaggle**
Thống kê normalization/registration **chỉ tính trên train** (chống leakage). Bootstrap chạy ở eval (CPU) không tốn GPU quota. Registration chạy offline, cache vào Kaggle Dataset.

---

### W4 — Model chính: fusion variants · pretrained · full-volume · lớp hiếm

*(Ứng W1_REPORT §5 mục 3; **Sprint 2 — kết thúc cuối W4**)*

**1. Mục tiêu & Definition of Done**
Mục tiêu: từ fusion v0 tiến tới **model chính** và chốt nó bằng CV; xử lý mất cân bằng lớp hiếm (áp-xe/FNH).
DoD:
- [ ] Fusion v1 (per-phase encoder + **phase-attention**) chạy 5-fold, so v0.
- [ ] ≥1 pretrained backbone (MedicalNet ResNet-3D hoặc Models Genesis) transfer, so scratch.
- [ ] Arm 3D full-volume (ROI gan → sliding-window inference) chạy được.
- [ ] Xử lý lớp hiếm: class-balanced (effective number) / focal + balanced sampler; báo song song **taxonomy gộp** (3–4 super-class) để có số ổn định.
- [ ] **Model chính chốt theo CV** (macro-F1/κ ± CI), reproduce được từ config+seed.

**2. Task (thứ tự phụ thuộc)**
1. `src/models/fusion.py` v1 — per-phase shared encoder → phase-attention → head.
2. `src/models/backbones.py` — nạp MedicalNet ResNet-3D / Models Genesis **từ Kaggle Dataset** (không tải runtime).
3. `src/train/` — arm full-volume: crop ROI gan → resample 128×128×64 → `monai.inferers.sliding_window_inference`.
4. `src/train/losses.py` — CE / focal / class-balanced; `src/data/` — WeightedSampler; head phân cấp ác/lành → 7-class (tuỳ chọn).
5. **Comparison protocol Phase 1** (Spec Sheet §3): mỗi biến thể train 1 seed/1 fold → xếp hạng macro-F1 val. Chọn 1–2 top.
6. Chốt **model chính** + config YAML khoá.

**3. Deliverable**
Fusion v1 (phase-attention) · pretrained backbone results · arm full-volume · bảng loss ablation sơ bộ · **model chính đã chốt** + config.

**4. Rủi ro & kill-switch**
- **Full-volume không kịp / không thắng patch:** → **GNG-3 → full-volume xuống ablation, patch-3D là primary.**
- **Hụt giờ GPU (~30h/tuần):** → giảm epoch + early stop; ensemble **K=5 → K=3**. *(giảm K = kill-switch → hỏi người dùng, §5)*
- **Phase-attention không thắng concat:** → vẫn là **phân tích phase-importance có giá trị** (RQ-A), không coi là thất bại; giữ v0 làm model chính.

**5. Ràng buộc Kaggle**
VRAM ~16GB → AMP + gradient accumulation (batch 2–4, effective 16–32) + gradient checkpointing. Full-volume dễ tràn → sliding-window. Pretrained weights nạp từ Kaggle Dataset (một số chế độ không có internet).

---

### W5 — Trustworthiness · ablation · thống kê · **KHOÁ + chạm test-104**

*(Ứng W1_REPORT §5 mục 4 & 6; **Sprint 3 — bắt đầu**; headline của cả dự án)*

**1. Mục tiêu & Definition of Done**
Mục tiêu: hoàn thành **đóng góp hạng nhất** (calibration + selective prediction), khoá protocol, rồi **chạm test-104 đúng một lần**.
DoD:
- [ ] Calibration: temperature scaling + (deep ensemble K / MC-dropout) → **ECE, adaptive-ECE, MCE, Brier, NLL, reliability diagram**.
- [ ] Selective prediction: **risk–coverage curve, AURC, accuracy@coverage, coverage@fixed-risk**.
- [ ] Bảng **ablation lõi** khoá (fusion, phase-importance leave-one-phase-out, 2D/2.5D/3D, pretrained/scratch, registered/unregistered, loss).
- [ ] So sánh thống kê: **DeLong / McNemar / bootstrap ghép cặp + Holm correction**.
- [ ] External nhãn thô + OOD/Duke (Δ domain shift, AUROC OOD, ECE dưới shift).
- [ ] **Pre-register** metric/split; threshold/temperature khoá trên **validation**.
- [ ] **Chạm test-104 đúng 1 lần** — kết quả khoá kín có CI.

**2. Task (thứ tự phụ thuộc — thứ tự này BẮT BUỘC không đảo)**
1. `src/eval/calibration.py` — temperature scaling (fit trên **val**), ensemble/MC-dropout; ECE/Brier/NLL/reliability.
2. `src/eval/selective.py` — risk–coverage, AURC, accuracy@coverage, coverage@fixed-risk.
3. `src/eval/stats.py` — DeLong, McNemar, bootstrap/permutation ghép cặp, Holm.
4. Chạy đủ **ablation lõi** trên model chính (Phase 2 Spec Sheet §3: 1–2 model top × 5-fold × nhiều seed).
5. External nhãn thô (task coarse) + OOD/Duke — **chạm 1 lần** mỗi tập.
6. **PRE-REGISTER**: viết ra file khoá metric/split/threshold/temperature **trước khi** chạm test. Ghi WORKLOG mục "Quyết định".
7. **[GATE] Chạm test-104:** *ghi WORKLOG trước, nêu lý do* → chạy `python -m src.eval.run --ckpt <path> --split test --i-know-this-is-final` **đúng 1 lần**. *(→ hỏi người dùng trước, §5)*

**3. Deliverable**
Calibration report (ECE/Brier/reliability) · risk–coverage/AURC · bảng ablation lõi · bảng so sánh thống kê có Holm · external + OOD · **kết quả test-104 khoá kín có CI** · file pre-registration.

**4. Rủi ro & kill-switch**
- **Deep ensemble hụt giờ:** → **MC-dropout làm nguồn uncertainty chính.**
- **Cám dỗ tinh chỉnh trên test:** cấm tuyệt đối — threshold/temperature khoá trên val, áp mù lên test (Spec Sheet §4.8). Vi phạm = hỏng tính hợp lệ khoa học.
- **Ablation không kịp đủ:** ưu tiên fusion + calibration + phase-importance; cắt registered/unregistered nếu phải.

**5. Ràng buộc Kaggle**
Calibration/selective/stats chạy ở eval (CPU) — không tốn GPU. Chỉ train lại nếu cần seed bổ sung cho CI. Buffer 1 ngày cho re-train fail.

> ⚠️ **test-104 là held-out khoá kín, chạm đúng 1 lần** (AGENTS.md §3.4). Sau bước 7, **không train/chọn model/đổi threshold** dựa trên số test nữa. Nếu số test xấu → báo cáo trung thực, không "sửa lại cho đẹp".

---

### W6 — Web app tự code · XAI · failure analysis · repro pack · **report cuối**

*(Ứng W1_REPORT §5 mục 7; **Sprint 3 — kết thúc cuối W6**; nén T5+T6 gốc — tuần nặng nhất)*

**1. Mục tiêu & Definition of Done**
Mục tiêu: nối **model đã khoá** vào web app tự code, đóng gói tái lập, và viết báo cáo cuối trung thực.
DoD:
- [ ] FastAPI backend load model **1 lần** lúc startup; `POST /predict` (NIfTI/DICOM → class + probs + uncertainty + malignant_prob + defer + heatmap).
- [ ] Frontend HTML/JS thuần: upload, slice-viewer `<canvas>`, prob bar, uncertainty gauge, cờ **defer**, **RUO hiển thị mọi màn hình có kết quả**.
- [ ] Grad-CAM 3D + phase-importance trả overlay; sanity check (nhìn đúng vùng u).
- [ ] Failure analysis: confusion matrix + case sai theo lớp.
- [ ] Reproducibility pack: seed/config/notebook công khai (strip output)/requirements pin/split file/checkpoints.
- [ ] Report cuối (W6): mọi số **có CI** + limitations trung thực; README chạy được.

**2. Task (thứ tự phụ thuộc)**
1. *(Khởi động sớm — làm song song cuối W5)* `webapp/backend/` skeleton: FastAPI `main.py`, `requirements.txt` **tách khỏi** train stack, wiring preprocessing rút gọn (rigid-only + crop, **bỏ N4**).
2. `src/xai/gradcam3d.py` + `src/xai/phase_importance.py` → overlay base64 PNG vài lát chính.
3. `POST /predict` trả JSON đầy đủ (probs/uncertainty/malignant_prob/defer/heatmap); `defer=true` khi confidence < ngưỡng coverage đã hiệu chỉnh.
4. `webapp/frontend/` — HTML/CSS/JS thuần (§12 AGENTS.md + PRODUCT.md): số liệu là nhân vật chính, màu không phải kênh thông tin duy nhất, RUO nổi bật, tôn trọng `prefers-reduced-motion`.
5. Precompute 3–5 ca demo (mượt khi host chậm).
6. Failure analysis + `reports/W6_REPORT.md` (hoặc report cuối) có CI + limitations; README + hướng dẫn chạy.
7. **Quality gate + Impeccable detector** trên UI trước khi chốt (§12).

**3. Deliverable**
Web app chạy được (FastAPI + frontend thuần) có uncertainty + heatmap + defer · Grad-CAM 3D + phase-importance · failure analysis · reproducibility pack · **report cuối có CI + limitations** · README.

**4. Rủi ro & kill-switch**
- **W6 quá tải (webapp + report trong 1 tuần):** giảm tải bằng cách **khởi động backend skeleton từ cuối W5**; nếu vẫn trễ → frontend tối thiểu (upload + probs + uncertainty + defer + RUO), hoãn slice-viewer đẹp.
- **Latency web app cao:** → **GNG-5 → lesion-crop (64³–96³) + rigid-only + K=3**; chấp nhận upload đã căn sẵn.
- **React hụt giờ:** → HTML/JS thuần (vốn là default; §8 AGENTS.md cấm Streamlit/Gradio).
- **Train cuối fail:** dùng buffer; cắt deformable registration + arm full-volume khỏi kết quả chính.

**5. Ràng buộc Kaggle**
**Kaggle không phải server** — web app chạy **local** (uvicorn), demo qua ngrok hoặc Docker (HF Space Docker được phép, **không** Gradio). Không host API trên Kaggle. Không đẩy checkpoint/dữ liệu lên dịch vụ ngoài mà chưa hỏi (§5).

---

## 3. Ánh xạ backlog W1_REPORT §5 → tuần

| Backlog W1 §5 | Tuần thực hiện |
|---|---|
| 1. EDA, tiền xử lý LLD-MMRI + frozen split mức BN | **W2** |
| 2. Baseline 3D (hoặc 2.5D) đa pha với CV + CI | **W2 → W3** |
| 3. Fusion/phase-importance + xử lý mất cân bằng lớp hiếm | **W4** |
| 4. Calibration, selective, reliability, risk–coverage/AURC | **W5** |
| 5. Audit OpenSwissHCC external + tách Duke OOD | **W3** (dựng) → **W5** (chạm 1 lần) |
| 6. Khoá protocol/model/threshold trước test 1 lần | **W5** |
| 7. Nối model thật vào FastAPI + failure analysis + repro + report | **W6** |

## 4. Ánh xạ tuần → thư mục `src/` (AGENTS.md §4)

| Tuần | Thư mục/entrypoint chạm tới |
|---|---|
| W2 | `src/utils/{seed,io,logging}` · `src/data/{dataset,make_splits}` · `src/preprocess/build_cache` · `src/models/{densenet3d,backbone2p5d}` · `src/train/run` · `tests/` · `configs/preprocess.yaml` · `splits/` · `notebooks/` |
| W3 | `src/eval/{metrics,bootstrap}` · `src/models/fusion` (v0) · `src/preprocess/registration` |
| W4 | `src/models/{fusion(v1),backbones}` · `src/train/{losses,full_volume}` · `src/data/` (sampler) |
| W5 | `src/eval/{calibration,selective,stats}` · `src/eval/run --split test` |
| W6 | `webapp/backend/` · `webapp/frontend/` · `src/xai/{gradcam3d,phase_importance}` · `reports/` · `README.md` |

> Mỗi khi tạo entrypoint đầu tiên: **cập nhật bảng lệnh AGENTS.md §6 trong cùng commit** và ghi WORKLOG.

---

## 5. Điểm ra quyết định — PHẢI hỏi người dùng trước (AGENTS.md §10)

Không tự quyết những việc sau; nêu ra, ghi WORKLOG mục "Quyết định", chờ duyệt:

- **Kích hoạt bất kỳ kill-switch nào:** chuyển sang CT (GNG-1), 2.5D làm primary (GNG-2), full-volume xuống ablation (GNG-3), giảm ensemble K=5→K=3, MC-dropout thay deep ensemble.
- **Chạm test-104** (W5) — ghi WORKLOG **trước**, nêu lý do, chạy đúng 1 lần.
- **Đổi quyết định đã chốt trong Spec Sheet:** dataset, taxonomy 7 lớp, metric chính, chiến lược split/threshold.
- **Sửa `.gitignore` để bỏ ignore** thư mục dữ liệu.
- **Thêm dependency nặng mới / đổi framework** (ví dụ nếu muốn dùng ANTs thay SimpleITK, hoặc thêm lib demo).
- **Đẩy dữ liệu/checkpoint/kết quả lên dịch vụ ngoài** (HF, ngrok, TCIA re-upload…).

---

## 6. Rủi ro & kill-switch (gom chung) — thứ tự cắt khi trễ

Bảng kill-switch đầy đủ ở [Plan Phụ lục A](liver_mri_3d_classification_plan.md#phụ-lục-a--kill-switch--gono-go). Tóm tắt trigger:

| Mốc | Điều kiện fail | Hành động |
|---|---|---|
| **GNG-1** (đầu W2) | Chưa có quyền LLD-MMRI | CT fallback đa pha (hỏi người dùng) |
| **GNG-1** (W2) | Preprocessing/N4 không cache kịp | Bỏ N4; resample + crop + z-score |
| **GNG-2** (cuối W3) | 3D-patch < 2.5D nhiều / không hội tụ | 2.5D primary, 3D → ablation (hỏi người dùng) |
| **GNG-2** (W3) | External harmonize không xong | OOD-only (Duke) |
| **GNG-3** (cuối W4) | Full-volume không kịp/không thắng patch | Full-volume → ablation |
| **GNG-3** (W4) | Hụt giờ GPU | K=5→K=3; giảm epoch + early stop (hỏi người dùng) |
| **W5** | Deep ensemble hụt giờ | MC-dropout làm uncertainty chính |
| **GNG-5** (W6) | Latency web app cao | lesion-crop + rigid-only + K=3; React→HTML/JS |
| **W6** | Train cuối fail | Buffer; cắt deformable + full-volume khỏi kết quả chính |

**Thứ tự cắt khi trễ (từ cắt trước tới cắt sau):**
deformable registration → arm full-volume → deep ensemble K=5→K=3 → external nhãn thô (giữ OOD-only) → phase-attention v2 (giữ v0 concat) → React (giữ HTML/JS thuần).

**Ưu tiên KHÔNG BAO GIỜ cắt:** model fusion có CV+CI · calibration + selective prediction · rigor thống kê · web app tối thiểu chạy được · reproducibility pack.

## 7. Buffer / contingency

- **Buffer nội tuần:** W5 giữ 1 ngày cho re-train fail; W6 giữ 2 ngày cho train cuối/viết.
- **Task cắt được (không ảnh hưởng headline):** đánh dấu ⚑ — deformable registration, arm full-volume, phase-attention v2, external nhãn thô (thay bằng OOD-only), React frontend, N4 trong pipeline demo.
- **Nếu trễ 1 tuần trọn vẹn:** dồn W3 vào W2 bằng cách chỉ chạy 3-fold thay vì 5-fold cho baseline (vẫn có CI, độ ổn định thấp hơn — ghi rõ trong report), và bắt đầu backend skeleton ngay W5.
- **Đệm sớm cho W6:** backend FastAPI skeleton + Grad-CAM integration nên dựng **song song cuối W5** (dùng checkpoint sơ bộ, thay bằng checkpoint khoá sau).

---

## 8. Câu hỏi cần chốt (Spec/Plan chưa rõ hoặc cần xác nhận)

1. **Quyền truy cập LLD-MMRI** đã được duyệt chưa? Đây là gate cứng đầu W2 — nếu chưa, cần kích hoạt CT fallback ngay, không chờ.
2. **Nguồn external nhãn thô cụ thể:** W1_REPORT §4 ghi OpenSwissHCC "mới ở mức đề xuất, cần audit metadata". Có xác nhận nguồn này (hay cohort HCC MRI/TCIA khác) làm external ác/lành không? Nếu không audit kịp → OOD-only.
3. **Ngân sách Kaggle GPU thực tế/tuần** (~30h giả định): nếu ít hơn, nên hạ K ensemble và số seed ngay từ W4.
4. **Mốc thời gian tuần** ở §0 là dự kiến — xác nhận ngày bắt đầu W2 để chốt lịch test-104 (W5).
5. **W6 nén T5+T6:** chấp nhận web app tối thiểu (không slice-viewer đẹp) nếu phải đánh đổi để report có CI đầy đủ?

---

*Tài liệu triển khai [`liver_mri_3d_classification_plan.md`](liver_mri_3d_classification_plan.md) + [`MRI_Classification_Spec_Sheet.md`](MRI_Classification_Spec_Sheet.md) thành task theo tuần. Mọi thay đổi quyết định đã chốt phải kèm một entry trong `WORKLOG.md`.*
