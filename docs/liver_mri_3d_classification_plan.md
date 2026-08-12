# Liver MRI 3D Multi-class Classification — Kế hoạch dự án

> Phân loại đa lớp u gan khu trú (focal liver lesion) trực tiếp trên MRI 3D đa pha.
> Solo · 6 tuần · Kaggle-only · MONAI/PyTorch · Web app tự code (không Streamlit/Gradio).
>
> **Trạng thái scope:** ĐÃ CHỐT hướng (xem §0). Tài liệu này là project doc chính; dùng checklist để theo tiến độ trực tiếp.

---

## Mục lục

- [0. Tóm tắt scope & các quyết định đã chốt](#0-tóm-tắt-scope--các-quyết-định-đã-chốt)
- [1. Research questions](#1-research-questions)
- [2. Định vị so với SOTA](#2-định-vị-so-với-sota)
- [3. Quyết định dataset](#3-quyết-định-dataset)
- [4. Bộ metric & chặt chẽ thống kê](#4-bộ-metric--chặt-chẽ-thống-kê)
- [5. Kế hoạch 6 tuần (theo tuần)](#5-kế-hoạch-6-tuần-theo-tuần)
- [6. Chi tiết kỹ thuật 3D MRI trên Kaggle](#6-chi-tiết-kỹ-thuật-3d-mri-trên-kaggle)
- [7. Rigor & reproducibility](#7-rigor--reproducibility)
- [8. Web app demo tự code](#8-web-app-demo-tự-code)
- [9. Outline báo cáo/paper & checklist "vượt kỳ vọng"](#9-outline-báopaper--checklist-vượt-kỳ-vọng)
- [Phụ lục A — Kill-switch & go/no-go](#phụ-lục-a--kill-switch--gono-go)
- [Nguồn tham khảo](#nguồn-tham-khảo)

---

## 0. Tóm tắt scope & các quyết định đã chốt

**Một câu định vị:**
> *Một bộ phân loại u gan khu trú 3D đa pha, **hiệu chỉnh xác suất tốt (well-calibrated)** và có **selective prediction** cho an toàn lâm sàng, kèm **phase-importance** nối model với động học ngấm thuốc (LI-RADS) và **external validation nhãn thô + OOD stress test**.*

| Quyết định | Chốt | Ghi chú |
|---|---|---|
| **Đóng góp headline** | **Trustworthiness (B):** calibration + selective prediction | Không đua accuracy leaderboard; đánh vào chỗ SOTA bỏ trống |
| **Model** | Fusion đa pha (A) làm backbone của model chính | 8 pha → multi-channel / per-phase attention |
| **Ablation lõi** | 3D vs 2.5D vs 2D; fusion variants; pretrained vs scratch; registered vs không; loss | Mỗi ablation chứng minh 1 lựa chọn |
| **External validation** | Nhãn thô (ác/lành hoặc HCC vs non-HCC) từ nguồn public thứ 2 **+** domain-shift/OOD trên Duke | Không giả vờ có external 7-class matched |
| **Scope** | **Full ambition:** 3D full-volume là arm hạng nhất; external pipeline dựng từ tuần 1 | Kèm kill-switch ở [Phụ lục A] để không dở dang |
| **Modality** | **MRI (LLD-MMRI)** | CT chỉ fallback nếu hết Tuần 1 không có quyền truy cập LLD-MMRI |
| **Dataset chính** | LLD-MMRI (498 BN, 7 lớp, 8 pha) | Dùng patch cắt sẵn + arm full-volume |
| **Metric headline** | Macro-F1 & Cohen's κ (khớp challenge) + calibration + risk–coverage | Mọi số có **CI bootstrap** |
| **Stack demo** | FastAPI + HTML/JS thuần (React tuỳ chọn) | Serve trên lesion-crop để đạt latency chấp nhận |

**Nguyên tắc xuyên suốt:** chặt chẽ > hào nhoáng. Baseline đơn giản + evaluation nghiêm túc + external + reproducible > kiến trúc phức tạp không tái lập.

> Chi tiết mục 1–4 giữ nguyên như phần thảo luận đã chốt; tóm tắt ngắn ở dưới để tài liệu tự đứng vững.

---

## 1. Research questions

Headline = **RQ-B**; RQ-A là model; RQ-C là ablation.

- **RQ-B (headline) — Trustworthiness.** Bộ phân loại 7 lớp u gan 3D "biết khi nào mình không biết" tới đâu? Selective prediction (từ chối → chuyển bác sĩ) cải thiện an toàn lâm sàng bao nhiêu, và calibration (temperature scaling, deep ensemble, MC-dropout) ảnh hưởng thế nào tới quyết định ở ranh giới ác/lành và lớp hiếm?
  - *Novelty:* cao về framing (calibration + risk–coverage trên MRI gan 3D đa lớp còn ít). *Khả thi:* cao. *Rủi ro:* cần base model đủ tốt trước → đặt risk–coverage làm kết quả chính, không phụ.
- **RQ-A (model) — Fusion đa pha gắn động học ngấm thuốc.** Pha nào mang tín hiệu phân biệt lớp, và cơ chế fusion nào (early concat vs per-phase encoder + phase-attention vs mô hình chuỗi pha động) khai thác tốt nhất arterial hyperenhancement / washout?
  - *Novelty:* trung bình–cao (đo phase-importance kiểu leave-one-phase-out). *Khả thi:* cao. *Rủi ro:* registration; nếu attention không thắng concat → vẫn là phân tích có giá trị.
- **RQ-C (ablation) — 3D full-volume vs 2.5D dưới khan hiếm dữ liệu.** Với n≈500 và crop nhỏ, 3D thắng 2.5D ở đâu; pretrained 3D backbone thu hẹp khoảng cách thế nào?
  - *Novelty:* trung bình (twist = data-efficiency curve). *Khả thi:* cao. *Rủi ro:* "đã biết" nếu thiếu định lượng.

## 2. Định vị so với SOTA

| Công trình | Input | Số liệu LLD-MMRI (test 104) |
|---|---|---|
| LLD-MMRI / MICCAI 2023 Challenge (metric = mean(F1, κ)) | 3D đa pha | nhóm mạnh ~**85.6% acc / 85.3% F1 / 97.1% macro-AUC** |
| SDR-Former (Neural Networks 2025) | 3D đa pha (CT 3-pha + MR 8-pha) | SOTA-tier ~85% |
| Spatio-temporal multi-stream Transformer (2024) | Đa chuỗi | cùng khoảng |
| Multidimensional Dual-Encoding Net (2025) | Đa pha | lesion-wise acc 0.859 / F1 0.840 |
| Explainable multiparametric MRI (Radiology:AI 2025) | Multiparam | acc tới 93–97% *(nhãn/data khác — không so trực tiếp)* |
| DL pipeline w/ uncertainty (arXiv 2110.08817) | Multi-phasic/seq | tiền lệ cho RQ-B (detection+diff) |

- **Đánh vào:** calibration + selective prediction bài bản; rigor thống kê (CI + DeLong/McNemar); reproducibility mở trên Kaggle; heatmap độ nhạy đa thì chỉ hỗ trợ failure analysis định tính.
- **KHÔNG đấu:** accuracy leaderboard test-104 (bão hòa, phương sai cao); transformer khổng lồ multi-GPU; segmentation.
- **Phân biệt với 2110.08817:** họ làm localization+differentiation; của ta = **calibration + selective prediction chuẩn hoá + external nhãn thô + OOD + pipeline mở tái lập trên chính LLD-MMRI.**

## 3. Quyết định dataset

**Chính — LLD-MMRI:** 498 BN (1 lesion/BN), 7 lớp (HCC, ICC, di căn, nang, u máu, FNH, áp-xe — 3 ác/4 lành), 8 pha (pre / arterial / venous / delay / T2WI / DWI / T1 in-phase / T1 out-phase), pre-split 316/78/104, cung cấp **full-volume + bbox + patch cắt sẵn**, truy cập qua form (research-use).

- **Mất cân bằng:** mạnh (áp-xe/FNH hiếm). Chiến lược: **5-fold stratified patient-level CV trên train+val**; test-104 = held-out khoá kín, báo cáo 1 lần. Lớp hiếm: class-balanced loss (effective number) / focal + balanced sampler + augmentation mạnh; **head phân cấp** (ác/lành → 7-class); báo cáo song song **taxonomy gộp** (3–4 super-class) để có số ổn định.
- **External (nhãn thô + OOD):** (1) dựng tập external ác/lành hoặc HCC-vs-nonHCC từ nguồn public thứ 2 (cohort HCC MRI / TCIA); (2) **Duke Liver Dataset** (2146 series/105 BN, có liver mask + series-label, **không** có nhãn loại tổn thương) làm **OOD/domain-shift probe** cho calibration/robustness + OOD detection.
- **Registration đa chuỗi:** pass đầu dùng patch cắt sẵn như kênh đã căn; pass rigor rigid/affine intra-patient về pha portal-venous **trong ROI gan** (SimpleITK/ANTs), resample DWI/T2 về grid tham chiếu; **ablation registered vs unregistered**.

## 4. Bộ metric & chặt chẽ thống kê

- **Chính:** macro-F1 & Cohen's κ (headline). **Phụ:** balanced accuracy, macro-AUC (OvR), macro **AUC-PR**, sensitivity/specificity per-class, confusion matrix chuẩn hoá.
- **Calibration:** ECE, adaptive-ECE, MCE, **Brier đa lớp**, NLL, reliability diagram; temperature scaling post-hoc.
- **Selective prediction:** **risk–coverage curve, AURC, accuracy@coverage, coverage@fixed-risk.**
- **An toàn lâm sàng:** sensitivity ác/lành (đừng-bỏ-sót-ung-thư) + cost-weighted error (bỏ sót HCC ≫ nhầm nang).
- **OOD/external:** AUROC OOD detection; ECE dưới shift.
- **Thống kê:** bootstrap **patient-level, stratified, ≥2000** → 95% CI cho **mọi** metric (`điểm ± CI`). So model: **DeLong** (AUC), **McNemar** (accuracy ghép cặp), bootstrap/permutation ghép cặp (macro-F1, κ), hiệu chỉnh **Holm**. Nhấn repeated stratified k-fold CV; test-104 báo 1 lần. **Pre-register** metric/split trước khi train model cuối.
- **Bẫy phải tránh:** rò rỉ cùng-BN giữa split; overlap crop; dùng test để chọn model; bbox rò rỉ size; thống kê chuẩn hoá tính trên test; báo best-of-many-seeds.

---

## 5. Kế hoạch 6 tuần (theo tuần)

3 sprint × 2 tuần. Cột **Buffer/Go-no-go** là mốc phòng train fail; kill-switch chi tiết ở [Phụ lục A]. Ngân sách Kaggle: ~30h GPU/tuần, session ≤12h → **checkpoint + resume mỗi epoch bắt buộc**.

### Sprint 1 (Tuần 1–2) — Dữ liệu / tiền xử lý / augmentation / baseline

| Tuần | Mục tiêu | Deliverable đo được | Ước lượng | Buffer / Go-no-go |
|---|---|---|---|---|
| **T1** | Có data + hiểu data + pipeline tiền xử lý chạy được; **khởi động external từ ngày 1 (full ambition)** | (a) LLD-MMRI tải xong + EDA (phân bố lớp, spacing, shape) notebook; (b) preprocessing v0 (resample + crop + z-score) → **cache thành Kaggle Dataset**; (c) file split 5-fold stratified patient-level; (d) baseline 2.5D chạy 1 fold ra số; (e) shortlist ≥2 nguồn external + Duke tải về | 6 ngày | **GNG-1 (hết T1):** nếu chưa có quyền LLD-MMRI → kích hoạt CT fallback. Nếu preprocessing chưa cache xong → cắt N4 khỏi pipeline v0 |
| **T2** | Baseline 3D + fusion v0 + số CV đầu tiên có CI; external harmonized | (a) 3D-patch baseline (MONAI DenseNet121-3D) chạy 5-fold; (b) fusion v0 (early concat 8 kênh); (c) **bảng CV macro-F1/κ ± CI bootstrap**; (d) registration pipeline (rigid) chạy được; (e) external nhãn thô harmonized (mapping về ác/lành) + Duke thành OOD set | 8 ngày | **GNG-2 (hết T2):** nếu 3D-patch không hội tụ / < 2.5D nhiều → 2.5D thành primary, 3D thành ablation. Nếu external harmonize không xong → OOD-only |

### Sprint 2 (Tuần 3–4) — Train / tối ưu / đánh giá

| Tuần | Mục tiêu | Deliverable | Ước lượng | Buffer / Go-no-go |
|---|---|---|---|---|
| **T3** | Model chính + arm full-volume + xử lý mất cân bằng | (a) fusion variants (per-phase encoder + phase-attention; group structural/dynamic); (b) pretrained backbones (MedicalNet ResNet-3D, Models Genesis); (c) **arm 3D full-volume** (ROI gan → sliding-window); (d) class-balanced/focal loss; (e) chọn model chính theo CV | 9 ngày | **GNG-3 (hết T3):** nếu full-volume không kịp/không thắng patch → full-volume xuống ablation, patch-3D là primary. Ensemble K=5→K=3 nếu quá giờ GPU |
| **T4** | Trustworthiness + ablation + so sánh thống kê + external | (a) calibration (temp scaling, deep ensemble K, MC-dropout) → **ECE/Brier/reliability**; (b) selective prediction → **risk–coverage/AURC**; (c) **bảng ablation lõi** khoá lại; (d) DeLong/McNemar + Holm; (e) external nhãn thô + OOD/Duke; (f) chạy test-104 **một lần** (khoá kín) | 9 ngày | **Buffer 1 ngày** cho re-train fail. Nếu deep ensemble hụt giờ → MC-dropout làm phương án uncertainty chính |

### Sprint 3 (Tuần 5–6) — Triển khai / web app / kiểm thử / tài liệu

| Tuần | Mục tiêu | Deliverable | Ước lượng | Buffer / Go-no-go |
|---|---|---|---|---|
| **T5** | Web app tự code serve model 3D + heatmap định tính | (a) FastAPI phục vụ ca demo OOF, endpoint `/api/validate-upload` nhận một ZIP NIfTI và chỉ kiểm tra 8 thì; (b) frontend React: chọn ca demo, ZIP checker, slice-viewer, prob bar, cờ `defer`; (c) heatmap `|input × gradient|` đa thì phủ trực tiếp lên crop E4; (d) freeze best model + card | 9 ngày | **GNG-5:** suy luận upload chỉ mở khi có pipeline ROI tương đương train; React vẫn là lựa chọn hợp lệ |
| **T6** | Failure analysis + đóng gói tái lập + viết báo cáo | (a) confusion matrix + case sai + kiểm tra heatmap định tính; (b) bảng/figure cuối **có CI**; (c) reproducibility pack (seed/config/notebook công khai, requirements pin, split file, checkpoints); (d) bản thảo paper/report; (e) README + hướng dẫn chạy | 8 ngày | **Buffer 2 ngày** cho train fail cuối / viết. Cắt được: deformable registration, arm full-volume nếu chưa xong |

**Critical path:** truy cập data → cache preprocessing → fusion baseline có CV+CI → calibration/selective → web app → báo cáo.
**Cắt được nếu trễ (theo thứ tự):** deformable registration → chỉ rigid; arm full-volume → chỉ patch-3D; deep ensemble K=5 → K=3; external nhãn thô → OOD-only; React → HTML/JS thuần.

---

## 6. Chi tiết kỹ thuật 3D MRI trên Kaggle

### 6.1 Preprocessing 3D MRI (làm 1 lần, cache lại)
- **N4 bias field correction** (SimpleITK) trên các chuỗi cấu trúc (T1/T2) — **chậm**, chạy offline 1 lần rồi cache; có thể bỏ ở pipeline demo.
- **Resampling** về spacing đồng nhất, ví dụ **1.5 × 1.5 × 3.0 mm** (điển hình MRI gan, slice dày). DWI/T2 thường khác geometry → resample về grid tham chiếu (portal-venous).
- **Registration** intra-patient: **rigid/affine** từng pha về portal-venous **trong bounding box gan** (SimpleITK Elastix / ANTs). Deformable (SyN/bspline) chỉ khi cần + kiểm chứng (rủi ro ảo giác căn chỉnh).
- **ROI-crop:** patch cố định quanh tâm lesion, ví dụ **96×96×48** (hoặc 64×64×32 nếu chật VRAM) với margin; arm full-volume: crop ROI gan → resample về **128×128×64**.
- **Intensity normalization:** MRI **không có đơn vị chuẩn như HU** → **per-sequence z-score trong ROI gan** hoặc robust percentile clip (0.5–99.5) rồi z-score. Tuỳ chọn **Nyul histogram matching** để harmonize cross-scanner (giúp external).

### 6.2 Vượt ràng buộc bộ nhớ/thời gian
- **MONAI** `PersistentDataset`/`SmartCacheDataset`; **cache patch tiền xử lý thành Kaggle Dataset** để không tiền xử lý lại mỗi session.
- **Patch-based** làm primary (8 pha × 96³ vẫn hợp VRAM ~16GB với batch nhỏ); **whole-volume** dùng **sliding-window inference** (`monai.inferers.sliding_window_inference`).
- **Mixed precision** (`torch.cuda.amp`), **gradient accumulation** (batch 2–4 → effective 16–32), **gradient checkpointing** trên backbone.
- **Checkpoint + resume mỗi epoch** ra Kaggle output (session ≤12h); log CSV.

### 6.3 Kiến trúc
- **Backbone 3D:** MONAI **DenseNet121-3D** (nhẹ, ổn định) và **MedicalNet ResNet-3D pretrained** (transfer từ 23 bộ y tế) — chọn theo CV. Swin-based chỉ nếu dư compute.
- **Nhận đa chuỗi thành multi-channel:**
  - *v0 early fusion:* 8 pha → 8 input channels.
  - *v1 mid fusion:* per-phase shared encoder → feature/pha → **phase-attention** (transformer/attention pooling) → head.
  - *v2 group:* tách "structural" (T1/T2/DWI) vs "dynamic" (pre/art/venous/delay); model pha động như chuỗi.
- **Fallback 2.5D:** stack 3 lát kề làm kênh (RGB-like) hoặc 3 lát trực giao (axial/coronal/sagittal) → backbone 2D ImageNet-pretrained. **Tiêu chí chuyển fallback:** 3D CV macro-F1 thua 2.5D quá margin **và** vượt ngân sách compute tại GNG-2/GNG-3.
- **Loss:** CE → focal → class-balanced (effective number), so bằng ablation.
- **Optimizer:** AdamW, lr ~1e-4, cosine + warmup, weight decay 1e-4–1e-2, early stopping theo macro-F1 CV.

### 6.4 Split patient-level & điểm rò rỉ (3D đa chuỗi)
- Split **patient-level** tuyệt đối; LLD-MMRI 1 lesion/BN nên OK nhưng vẫn giữ nguyên tắc.
- **Điểm dễ leak:** (1) các pha của cùng BN rơi vào 2 split; (2) thống kê normalization/registration tính trên cả test; (3) bbox rò rỉ kích thước lesion; (4) ensemble member "nhìn" fold test; (5) augmentation/oversample lặp cùng BN xuyên split; (6) chọn model/temperature trên test.

---

## 7. Rigor & reproducibility

### 7.1 Ablation chứng minh đóng góp
- [ ] **Fusion:** concat vs per-phase+attention vs group-dynamic → giá trị fusion.
- [ ] **Phase-importance:** leave-one-phase-out / phase-dropout → pha nào quan trọng (kỳ vọng arterial/venous) → nối LI-RADS.
- [ ] **Dimensionality:** 2D vs 2.5D vs 3D-patch vs 3D-full-volume → data-efficiency curve.
- [ ] **Transfer:** pretrained vs scratch.
- [ ] **Calibration:** raw vs temp-scaling vs ensemble vs MC-dropout → ECE/Brier/AURC.
- [ ] **Registration:** registered vs unregistered.
- [ ] **Loss:** CE vs focal vs class-balanced.

### 7.2 Reproducibility
- [ ] Seed cố định (torch/numpy/random) + cờ deterministic; ghi lại non-determinism còn lại.
- [ ] Config hoá (YAML) mọi hyperparam; log đầy đủ.
- [ ] **Lưu file split** (không sinh lại ngẫu nhiên mỗi lần).
- [ ] Version data cache (Kaggle Dataset có version).
- [ ] Notebook Kaggle công khai chạy end-to-end; requirements pin.
- [ ] Checkpoints + script eval tách khỏi train.

### 7.3 Failure analysis & cảnh báo kết quả giả
- [ ] Confusion matrix + liệt kê case sai theo lớp.
- [ ] Heatmap độ nhạy đa thì kiểm model không chỉ nhìn nền/gan lành; đây là kiểm tra định tính, không phải segmentation.
- [ ] Reliability diagram + worst OOD cases.
- [ ] **Cảnh báo:** leakage; test nhỏ cherry-pick; tuning trên test; báo best-of-many-seeds; báo điểm không CI.

---

## 8. Web app demo tự code

**Stack:** FastAPI (backend) + HTML/JS thuần (frontend), React tuỳ chọn. **Không Streamlit/Gradio.**

### 8.1 Backend (FastAPI)
- Phục vụ prediction OOF thật cho ca demo qua `POST /api/cases/{id}/predict`; không sinh số mô phỏng.
- `POST /api/validate-upload` nhận một ZIP NIfTI và chỉ trả `valid`, lỗi cùng bảng kiểm 8 phase. Không giải nén bền vững, không chạy model và không trả `PredictResult`.
- Suy luận từ upload chỉ được mở khi có pipeline ROI tương đương lúc train; đó là contract riêng, không giả lập bằng tên file.
- Heatmap độ nhạy của ca demo trả qua `/api/cases/{id}/model-view`, trực tiếp trên crop E4 và chỉ giải thích lớp dự đoán.
- `defer` của ca demo dùng quy tắc bất định đã khóa trước trên validation; phần so sánh tín hiệu thuộc report.

### 8.2 Frontend (HTML/JS)
- Một vùng tải ZIP hiển thị bảng kiểm đủ/thiếu/trùng theo 8 phase. Ca demo hiển thị hàng tóm tắt prediction, donut xác suất nhóm ác, trạng thái `defer`, cùng hai tab **Xác suất** và **Khám phá ảnh**.

### 8.3 Latency & serving trong ràng buộc
- Nút thắt là **registration/N4**, không phải forward pass. V1 không suy luận upload nên không giả định tiền xử lý đã tương đương; khi bổ sung inference phải có lesion-crop và registration tương thích recipe train.
- **Triển khai:** chạy local + `ngrok` để demo; hoặc **Docker FastAPI trên Hugging Face Spaces** (được phép — đây là Docker Space, không phải Gradio) / Render free tier. Kaggle không phải server → chỉ để train, không host API.
- Precompute sẵn 3–5 ca demo từ prediction OOF trên validation để trình diễn mượt khi mạng/host chậm; không dùng Test-104, không commit NIfTI, checkpoint hay artefact bệnh nhân.

---

## 9. Outline báo cáo/paper & checklist "vượt kỳ vọng"

### 9.1 Outline (mức nộp hội nghị được)
1. **Title / Abstract** — nhấn trustworthiness + reproducibility.
2. **Introduction** — động lực lâm sàng (đừng bỏ sót ung thư) + khoảng trống: SOTA báo accuracy nhưng thiếu calibration/selective/rigor.
3. **Related work** — LLD-MMRI benchmark, SDR-Former, multi-stream transformer, uncertainty pipeline (2110.08817).
4. **Data** — LLD-MMRI (split, class imbalance) + external nhãn thô + Duke OOD.
5. **Method** — fusion đa pha + phase-attention; calibration (temp/ensemble/MC-dropout); selective prediction.
6. **Experiments** — setup, metric, **giao thức thống kê (pre-registered, bootstrap CI, DeLong/McNemar/Holm)**.
7. **Results** — bảng chính có CI; calibration (ECE/reliability); **risk–coverage/AURC**; external nhãn thô + OOD; **bảng ablation**.
8. **Failure analysis định tính** — heatmap độ nhạy đa thì, với giới hạn diễn giải nêu rõ.
9. **Discussion & Limitations** — thẳng thắn: không có external 7-class matched; test nhỏ.
10. **Reproducibility statement** + **Conclusion**.

*Venue thực tế cho solo:* MICCAI workshop / ISBI / journal *Journal of Imaging Informatics in Medicine* (đã đăng dòng công trình LLD-MMRI).

### 9.2 Checklist "vượt kỳ vọng"
- [ ] **CI trên mọi số** + test ý nghĩa (DeLong/McNemar) có hiệu chỉnh đa so sánh.
- [ ] **Calibration + selective prediction là kết quả hạng nhất**, không phải phụ lục.
- [ ] **External nhãn thô + OOD/domain-shift** có phân tích, không chỉ 1 con số.
- [ ] **Phase-importance** khớp trực giác lâm sàng (arterial/venous nổi bật).
- [ ] **Pipeline Kaggle công khai chạy được** + config + seed + split file + checkpoints.
- [ ] **Web app tự code** (FastAPI, không Gradio) có uncertainty + heatmap + cờ defer.
- [ ] **Giao thức eval pre-registered** (khoá metric/split trước train cuối).
- [ ] **Ablation sạch** chứng minh từng lựa chọn thiết kế.
- [ ] **Limitations trung thực** — reviewer tin hơn là giấu.
- [ ] Data-efficiency curve (3D vs 2.5D) như bằng chứng định lượng cho RQ-C.

---

## Phụ lục A — Kill-switch & go/no-go

"Full ambition" chỉ an toàn nếu có điểm dừng. Mỗi mốc: nếu **fail** → hạ cấp theo cột phải, KHÔNG kéo dài.

| Mốc | Điều kiện fail | Hành động (fallback) |
|---|---|---|
| **GNG-1** (hết T1) | Chưa có quyền LLD-MMRI | Kích hoạt **CT fallback** (bộ CT gan đa pha public); chấp nhận mất T2/DWI + câu chuyện LI-RADS |
| **GNG-1** | Preprocessing chưa cache | Bỏ N4 khỏi v0; chỉ resample + crop + z-score |
| **GNG-2** (hết T2) | 3D-patch < 2.5D nhiều / không hội tụ | **2.5D làm primary**, 3D thành ablation |
| **GNG-2** | External harmonize không xong | **OOD-only** (Duke), hoãn external nhãn thô |
| **GNG-3** (hết T3) | Full-volume không kịp/không thắng patch | **Full-volume → ablation**, patch-3D là primary |
| **GNG-3** | Hụt giờ GPU | Ensemble **K=5 → K=3**; giảm epoch + early stop |
| **T4** | Deep ensemble hụt giờ | **MC-dropout** làm uncertainty chính |
| **GNG-5** (T5) | Latency web app quá cao | Serve trên lesion-crop + rigid-only + K=3; React → HTML/JS thuần |
| **T6** | Train cuối fail | Dùng buffer 2 ngày; cắt deformable registration + arm full-volume khỏi kết quả chính |

**Ưu tiên bảo vệ (không bao giờ cắt):** model fusion có CV+CI · calibration + selective prediction · rigor thống kê · web app tối thiểu chạy được · reproducibility pack.

---

## Nguồn tham khảo

- LLD-MMRI dataset & MICCAI 2023 Challenge — https://github.com/LMMMEng/LLD-MMRI2023 · https://github.com/LMMMEng/LLD-MMRI-Dataset
- SDR-Former (Neural Networks 2025) — https://arxiv.org/abs/2402.17246
- Spatio-temporal collaborative multiple-stream transformer — https://www.sciencedirect.com/science/article/abs/pii/S095219762402092X
- Multidimensional Dual Encoding Network (2025) — https://link.springer.com/article/10.1007/s10278-025-01698-x
- Explainable DL, multiparametric MRI (Radiology: AI 2025) — https://pubs.rsna.org/doi/10.1148/ryai.240531
- DL pipeline w/ localization + uncertainty (multi-phasic/seq MRI) — https://arxiv.org/pdf/2110.08817
- Duke Liver Dataset (MRI) — https://pubs.rsna.org/doi/full/10.1148/ryai.220275 · https://zenodo.org/records/7774566
- LLD-MMRI (HuggingFace, MedSAM2 variant) — https://huggingface.co/datasets/wanglab/LLD-MMRI-MedSAM2
