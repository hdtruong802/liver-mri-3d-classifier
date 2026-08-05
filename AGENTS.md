# AGENTS.md — Nguồn sự thật duy nhất của dự án

> **File này là single source of truth cho MỌI công cụ AI coding dùng trên repo này.**
> `CLAUDE.md` và `.cursor/rules/*` chỉ *trỏ về đây*, không chứa nội dung riêng.
> Sửa ngữ cảnh dự án = sửa file này. Sửa chỗ khác = tạo drift, bị coi là lỗi.

**Tool đang dùng luân phiên:** Claude Code · Google Antigravity · OpenAI Codex · Cursor
**Người dùng:** 1 người, làm một mình, luân phiên tool trên cùng một repo.

---

## 0. Đọc gì trước khi làm bất cứ việc gì

Mọi phiên, bất kể tool nào, theo đúng thứ tự:

1. Đọc file này (AGENTS.md) — ngữ cảnh nền.
2. Đọc **entry cuối cùng** của `WORKLOG.md` — biết phiên trước dừng ở đâu.
   ```bash
   tail -n 80 WORKLOG.md          # bash / git-bash
   ```
   ```powershell
   Get-Content WORKLOG.md -Tail 80   # PowerShell
   ```
3. `git status` phải sạch. Nếu bẩn → **dừng, hỏi người dùng**, không tự commit đè việc của tool khác.

Khi kết thúc phiên: chạy quality gate phù hợp với shell (`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-gate.ps1` trên Windows; `sh scripts/quality-gate.sh` trên Bash thật), **bắt buộc** append một entry vào `WORKLOG.md` (quy tắc ở đầu file đó), rồi commit + push.

Giao thức đầy đủ (checklist vào/ra phiên, ai sửa file config của tool nào, các điểm dễ xung đột): **[`docs/MULTI_TOOL_WORKFLOW.md`](docs/MULTI_TOOL_WORKFLOW.md)**.

---

## 1. Dự án là gì

Dự án **research** (Research Use Only, chưa kiểm định lâm sàng): mô hình AI **phân loại đa lớp u gan trên MRI 3D đa pha**.

- **Bài toán:** 7 lớp tổn thương gan (HCC, ICC, di căn, nang, u máu, FNH, áp-xe) ở mức ROI, trên **volume 3D đa pha** (8 thì MRI), dataset chính **LLD-MMRI** (498 bn).
- **Đóng góp headline:** **Trustworthiness** — xác suất *được hiệu chỉnh* (calibration) + **selective prediction** (biết từ chối ca không chắc để chuyển bác sĩ). **Không đua accuracy leaderboard.**
- **Quy mô:** 1 người, 6 tuần, compute là **Kaggle** (session ≤ 12h).
- **Ba loại deliverable:**
  1. Code tiền xử lý / huấn luyện / đánh giá (chạy trên Kaggle).
  2. **Web app demo tự code full-stack** — FastAPI backend + frontend React. **KHÔNG Streamlit, KHÔNG Gradio.**
  3. **HTML slide + report** trình bày kết quả.

Chi tiết đầy đủ, không lặp lại ở đây:
- [`docs/MRI_Classification_Spec_Sheet.md`](docs/MRI_Classification_Spec_Sheet.md) — chốt kỹ thuật (dataset, model, metric, ngưỡng).
- [`docs/liver_mri_3d_classification_plan.md`](docs/liver_mri_3d_classification_plan.md) — kế hoạch 6 tuần, kill-switch, outline báo cáo.

> **Agent phải đọc 2 file trên trước khi đề xuất thay đổi về model / metric / split.** Không tự ý đổi quyết định đã chốt trong đó; muốn đổi thì nêu ra và ghi vào WORKLOG dưới mục "Quyết định".

---

## 2. Bản đồ tài liệu (ai đọc gì)

| File | Vai trò | Ai được sửa |
|---|---|---|
| `AGENTS.md` | **Nguồn sự thật** ngữ cảnh dự án | Bất kỳ tool nào, nhưng phải ghi WORKLOG |
| `CLAUDE.md` | Cầu nối → import AGENTS.md | Chỉ khi thêm quy tắc *riêng Claude Code* |
| `.cursor/rules/00-project-context.mdc` | Cầu nối → AGENTS.md | Chỉ khi thêm quy tắc *riêng Cursor* |
| `WORKLOG.md` | Nhật ký bàn giao giữa các tool, **append-only** | Mọi tool, chỉ được **thêm** |
| `docs/MRI_Classification_Spec_Sheet.md` | Chốt kỹ thuật (khoa học) | Người dùng duyệt; agent đề xuất diff |
| `docs/liver_mri_3d_classification_plan.md` | Kế hoạch & lộ trình | Người dùng duyệt; agent đề xuất diff |
| `docs/plan.md` | Kế hoạch chi tiết W2–W6 (triển khai Plan thành task/tuần) | Mọi tool, ghi WORKLOG |
| `docs/W2_plan.md` | Plan làm việc chi tiết Tuần 2 (task theo ngày) | Mọi tool, ghi WORKLOG |
| `docs/MULTI_TOOL_WORKFLOW.md` | Giao thức chống xung đột giữa 4 tool, tích hợp Impeccable | Mọi tool |
| `PRODUCT.md` | Sự thật sản phẩm: người dùng, mục đích, ràng buộc, nguyên tắc, a11y | Mọi tool |
| `DESIGN.md` | Thế giới thị giác **của slide và report** ("bản khắc atlas"). `slides/overview_v2.html` đang dùng | Mọi tool, ghi WORKLOG |
| `webapp/DESIGN.md` | Thế giới thị giác **riêng của web app** ("bàn đọc tối"). Cố ý khác `DESIGN.md` gốc — xem WORKLOG S-076, S-077 | Mọi tool, ghi WORKLOG |
| `scripts/quality-gate.sh` / `scripts/quality-gate.ps1` | Quality gate chung cho Bash thật / Windows PowerShell | Mọi tool |

**Quy tắc chống trùng lặp:** nếu một thông tin đã có trong Spec Sheet hoặc Plan, AGENTS.md chỉ **link tới**, không chép lại. Nếu bạn (agent) thấy nội dung bị chép ra nhiều chỗ → xoá bản chép, giữ link, ghi vào WORKLOG.

---

## 3. Nguyên tắc bất di bất dịch

Vi phạm những điều này = làm hỏng tính hợp lệ khoa học của cả dự án. Không có ngoại lệ vì "cho nhanh".

1. **RUO.** Mọi UI, slide, report, docstring phải nói rõ *Research Use Only, không dùng chẩn đoán lâm sàng*. Không bao giờ viết chữ nào ngụ ý đã được kiểm định.
2. **Split ở mức bệnh nhân, tuyệt đối.** Không để hai pha của cùng một bệnh nhân rơi vào hai split. Có unit test kiểm giao tập bệnh nhân = rỗng.
3. **Không leakage.** Thống kê normalization/registration chỉ tính trên train. Không chọn model, không chọn threshold, không fit temperature trên test.
4. **Test-104 là held-out khoá kín, chạm đúng 1 lần.** Ai định chạy test phải ghi WORKLOG trước, nêu rõ lý do.
5. **Mọi con số báo kèm 95% CI** (bootstrap mức bệnh nhân, ≥2000 lần). Không bao giờ báo best-of-many-seeds, không báo điểm trần.
6. **File split được lưu và commit**, không sinh lại ngẫu nhiên mỗi lần chạy.
7. **Seed cố định + config YAML** cho mọi hyperparam. Không hardcode số trong code train.
8. **Web app phải tự code full-stack.** Ai đề xuất Streamlit/Gradio/bất kỳ framework demo dựng sẵn nào → từ chối; "web app demo tự code" là một trong ba deliverable của dự án (§1), không phải một lựa chọn kỹ thuật. **Thư viện frontend thì được tự do** (React, Vite, Tailwind, v.v.) — ràng buộc "HTML/CSS/JS thuần" đã được gỡ ngày 2026-07-31, xem WORKLOG S-076.
9. **Không làm segmentation.** Bài toán là classification.
10. **Không commit dữ liệu bệnh nhân, checkpoint, hay file NIfTI/DICOM.** Xem `.gitignore`.

> ⚠️ **Hệ quả của luật 2 và 3 mà rất dễ vi phạm: KHÔNG gộp 5 checkpoint của 5 fold thành một ensemble rồi báo số out-of-fold.** Mỗi ca ở val của fold `f` nằm trong tập train của **cả 4 model kia** — đã kiểm trực tiếp trên `splits/` (WORKLOG S-080). Gộp lại là để 4/5 thành viên chấm bài họ đã học thuộc. Ensemble 5 fold **chỉ** hợp lệ trên dữ liệu chưa ai thấy: test-104 (một lần, phải xin phép) hoặc dữ liệu ngoài. Muốn có bất định epistemic *trên out-of-fold* thì dùng MC-dropout (`src/eval/mc_dropout.py`) hoặc train nhiều seed **trên cùng một split**.

---

## 4. Cấu trúc thư mục

> Thư mục nào chưa tồn tại thì là **đích đến đã chốt** — tool nào tạo nó đầu tiên thì theo đúng cây này, không tự đặt tên khác.

```
liver-mri-3d-classifier/
├── AGENTS.md                    # ← nguồn sự thật (file này)
├── CLAUDE.md                    # cầu nối cho Claude Code (@AGENTS.md)
├── WORKLOG.md                   # nhật ký bàn giao, append-only
├── README.md                    # mô tả public + RUO disclaimer          [chưa có]
├── PRODUCT.md                   # sự thật sản phẩm (Impeccable init sinh ra)
├── DESIGN.md                    # thị giác của SLIDE + REPORT ("bản khắc atlas")
├── .gitignore
├── .githooks/pre-commit         # quality gate; bật: git config core.hooksPath .githooks
├── .cursor/rules/               # cầu nối cho Cursor
├── .impeccable/                 # config.json, design.json, critique/*.md → COMMIT
│                                #   phần còn lại ephemeral → gitignore
├── docs/
│   ├── MULTI_TOOL_WORKFLOW.md   # giao thức đa tool + tích hợp Impeccable
│   ├── MRI_Classification_Spec_Sheet.md      # chốt kỹ thuật (khoa học)
│   ├── liver_mri_3d_classification_plan.md   # kế hoạch & lộ trình 6 tuần
│   ├── plan.md                  # kế hoạch chi tiết W2–W6 (triển khai)
│   └── W2_plan.md               # plan làm việc chi tiết Tuần 2
├── configs/                     # YAML hyperparam (mọi run 1 file)
├── splits/                      # file fold đã khoá — COMMIT, bất biến
├── src/
│   ├── data/                    # dataset, transform MONAI, loader
│   ├── preprocess/              # N4, resample, registration, ROI-crop
│   ├── models/                  # backbone 3D + các biến thể fusion
│   ├── train/                   # vòng train, checkpoint/resume
│   ├── eval/                    # metric, calibration, selective, thống kê
│   ├── xai/                     # Grad-CAM 3D, attention rollout
│   └── utils/                   # seed.py, io, logging
├── tests/                       # trong đó có test chống leakage
├── notebooks/                   # notebook Kaggle (đã strip output)
├── webapp/
│   ├── README.md                # cách chạy, biến môi trường, ràng buộc dữ liệu
│   ├── DESIGN.md                # thị giác của WEB APP ("bàn đọc tối")
│   ├── backend/                 # FastAPI — requirements.txt RIÊNG, không có torch
│   └── frontend/                # React + Vite + Tailwind + TS (node_modules/, dist/ gitignore)
├── slides/                      # HTML slide
├── reports/                     # HTML/MD report
├── scripts/
│   ├── quality-gate.sh          # gate cho Bash thật
│   └── quality-gate.ps1         # gate cho Windows PowerShell, không cần WSL
├── artifacts/                   # checkpoint, log, hình — GITIGNORE
├── data/                        # dữ liệu bệnh nhân — GITIGNORE
└── prompt/                      # prompt gốc dùng dựng dự án
```

**Nguyên tắc đặt file:** code chạy trên Kaggle nằm trong `src/`, notebook chỉ là lớp mỏng gọi vào `src/` (import, không copy-paste logic). Notebook phồng lên chứa logic = nợ kỹ thuật, phải refactor ngược về `src/`.

---

## 5. Tech stack

| Lớp | Chọn | Ghi chú |
|---|---|---|
| DL framework | PyTorch + **MONAI** | MONAI cho transform 3D, DenseNet121-3D, sliding-window inference |
| Backbone | DenseNet121-3D (baseline) · MedicalNet ResNet-3D / Models Genesis (pretrained) | xem ghi chú bên dưới về transformer |
| Xử lý ảnh y tế | SimpleITK (+ Elastix), tuỳ chọn ANTs | N4, resample, rigid registration |
| Thống kê | numpy / scipy / scikit-learn | bootstrap, DeLong, McNemar, Holm |
| Backend | **FastAPI** + uvicorn | load model 1 lần lúc startup |
| Frontend | **React + Vite + Tailwind + TypeScript** | Thư viện tự do. Slice-viewer đọc PNG do backend render từ NIfTI |
| Slide / Report | HTML tĩnh | không phụ thuộc build tool nặng |
| Compute | **Kaggle Notebook** (train) · local (web app, slide) | Kaggle KHÔNG dùng để host API |

> **Hàm mất mát** (`src/train/losses.py`, W4): `cross_entropy` · `focal` · trọng số lớp `none|balanced|effective_number`. Chọn qua khối `loss:` trong YAML, không sửa code. `baseline_3dpatch.yaml` bị khoá bởi `tests/test_protocol_conformance.py` nên **mọi thí nghiệm về loss phải sang config riêng**.

Pin version trong `requirements.txt` (train) và `webapp/backend/requirements.txt` (serve) — **hai file tách nhau**, backend không kéo theo cả MONAI training stack nếu không cần.

> **Sửa giả định "n≈500 → tránh transformer lớn" (WORKLOG S-043).** Câu này từng nằm ở cột ghi chú của Backbone và **không đúng như một luật**. Baseline chính thức của MICCAI 2023 LLD-MMRI là **UniFormer-S 3D** — một kiến trúc lai conv + self-attention — train **from scratch, không pretrained**, trên đúng 316 ca của dataset này, và đạt **macro-F1 0.6083** trên test-104. Dữ liệu ít không tự động loại transformer ở bài toán này. Vẫn giữ DenseNet121-3D làm baseline vì lý do khác: nó đã chạy được, đúng Spec Sheet, và MONAI hỗ trợ sẵn — không phải vì transformer bị cấm. UniFormer-S 3D là một mục hợp lệ trong bảng so sánh kiến trúc ở W4.

### Mốc đối chiếu ngoài (quan trọng)

**Bảng xếp hạng challenge**, macro-F1 trên test-104:

| | macro-F1 | Ghi chú |
|---|---|---|
| Đội nhất challenge | 0.8322 | |
| **Baseline official** | **0.6083** | UniFormer-S 3D, from scratch, 300 epoch |
| Hạng 20–24 | 0.5047 – 0.6076 | đủ loại kiến trúc |

Metric của họ là `sklearn.f1_score(average='macro')` và `cohen_kappa_score` — **khớp với `src/eval/metrics.py`**, đã có test đối chiếu trực tiếp. Recipe train của họ được ghi lại trong `configs/baseline_3dpatch.yaml` và khoá bằng `tests/test_protocol_conformance.py`. Nguồn: [`LMMMEng/LLD-MMRI2023`](https://github.com/LMMMEng/LLD-MMRI2023).

**Bảng so sánh có kiểm soát** — CGHNet Bảng 1 ([doi:10.1016/j.compmedimag.2026.102780](https://doi.org/10.1016/j.compmedimag.2026.102780), Comput Med Imaging Graph 132, 2026). Đây là bảng **hữu ích hơn** bảng trên khi debug, vì mọi hàng dùng **cùng một protocol** (tiền xử lý 16×128×128 → crop 14×112×112, Focal loss, AdamW lr 1e-4, 300 epoch, batch 4), 5 model từ 5 fold, và đều báo trên **đúng test-104 official**:

| Phương pháp | F1 | Kappa |
|---|---|---|
| ViT3D | 0.645 ± 0.038 | 0.557 |
| ResNet2D | 0.684 ± 0.024 | 0.624 |
| ConvNeXt2D | 0.696 ± 0.027 | 0.653 |
| **ResNet3D** | **0.709 ± 0.021** | 0.662 |
| Swin3D · 3D UX-Net | 0.709 | 0.651 · 0.668 |
| Uniformer | 0.719 ± 0.022 | 0.673 |
| SDR-Former | 0.791 ± 0.017 | 0.747 |
| STM-Former | 0.793 ± 0.016 | 0.752 |
| RadioFormer | 0.806 ± 0.013 | 0.745 |
| **CGHNet** | **0.818 ± 0.012** | 0.782 |

Ba điều rút ra, đều đã được dùng để định hướng thí nghiệm (WORKLOG S-064, S-065):

1. **Một `ResNet3D` trần đạt 0.709**, vượt xa baseline official 0.6083, chỉ nhờ hình học đầu vào đó. Hình học quan trọng hơn kiến trúc.
2. **3D thắng 2D ở so sánh cùng họ** (ResNet3D 0.709 so với ResNet2D 0.684). Đừng dùng bảng ablation nội bộ của CGHNet (nhánh 2D 74.2 so với nhánh 3D 72.4) để kết luận ngược lại — hai nhánh đó khác kiến trúc, không phải phép thử 2D-vs-3D sạch.
3. Ablation huấn luyện của họ (Bảng 4): **Focal Loss 81.8 so với CE 79.9**; **bỏ random-crop mất 8.8 điểm** (73.0), là biến augmentation nặng nhất; lr 1e-4 tốt hơn cả 1e-3 lẫn 1e-5.

**Bất kỳ ai định debug chất lượng model đều phải đối chiếu với bảng này trước.** Ba phiên (S-036, S-039, S-040) đã đốt ba run GPU để đoán nguyên nhân mà không hề biết điểm số nào là đạt được — cả ba chẩn đoán đều sai.

### Kết quả nội bộ đã đo (đọc trước khi đề xuất thí nghiệm mới)

Bốn run, **cùng fold 1 · cùng 82 ca val · cùng seed · cùng recipe train**. Chỉ dữ liệu đầu vào đổi:

| | Cửa sổ cắt | Kích thước | Căn pha | macro-F1 | Epoch tốt nhất |
|---|---|---|---|---|---|
| E0 | 144mm cố định | 96×96×48 | tham chiếu | 0.4244 | 162 / 300 |
| E1 | bám tổn thương | 96×96×48 | tham chiếu | 0.5740 | 200 / 300 |
| E3 | bám tổn thương | 112×112×32 | tham chiếu | 0.5566 | **145 / 300 — DỪNG SỚM** |
| **E4** | bám tổn thương | 112×112×32 | **từng pha** | **0.7001** | 231 / 300 |

So cặp (bootstrap trên hiệu, phân tầng, 2000 lần): **E4 − E1 = +0.126, CI95 [+0.033, +0.230], P = 0.009**.

⚠️ **E3 bị chủ động dừng ở epoch 145, không chạy hết 300.** Nó **không dùng làm đối chứng được**: cả ba run chạy hết đều đạt đỉnh *sau* epoch 145 (162, 200, 231), nên 0.5566 là cận dưới chứ không phải trần của cấu hình đó. Đính chính ở WORKLOG S-074; phiên trước đã đọc nhầm nó thành kết quả âm đầy đủ.

Ba điều rút ra từ bộ số này:

1. **Căn pha ăn tiền, nhưng chưa tách được khỏi hình học.** E4 − E1 = +0.126 là chắc chắn. Việc quy mức tăng đó cho `align_phases` thay vì cho hình học 112×112×32 thì **chưa chứng minh được**, vì phép so một biến (E4 − E3) dựa trên một run bị cắt ngắn. Giả thuyết "tỉ lệ trục là nút thắt" **chưa bị bác**, chỉ là chưa được ủng hộ. **Việc chạy lại E3 để tách hai biến đã bị loại khỏi kế hoạch** (quyết định của người dùng, S-076): nó chỉ ảnh hưởng tới phần quy kết nguyên nhân, không ảnh hưởng tới con số báo cáo được. Từ nay mức tăng +0.126 được quy cho **cả cụm** hình học cộng phép căn, không tách riêng.
2. **Vấn đề overfitting kinh niên là triệu chứng của lệch pha, không phải của recipe train.** `val_loss` chạm đáy ở **epoch 9** (E1) so với **epoch 100** (E4); khoảng cách train/val cuối +2.55 so với +1.50. Đừng đi chỉnh dropout/weight-decay/augmentation để chữa nó.
3. **0.7001 không phải một đỉnh may mắn.** 29/50 epoch cuối của E4 đạt ≥ 0.60 (E1: 0/50); trung bình 50 epoch cuối 0.607 so với 0.512.

⚠️ **Con số của ta đo trên val fold 1 (82 ca), bảng văn liệu đo trên test-104.** Hai tập khác nhau — **không được** viết "ta ngang ResNet3D 0.709". So sánh nội bộ E0/E1/E4 với nhau thì hợp lệ vì cùng tập và cùng số epoch; **E3 thì không**, xem cảnh báo ở trên.

### CV 5-fold của E4 — con số báo cáo được (2026-08-04, WORKLOG S-078)

Đủ 5 fold, mỗi fold 300 epoch, **cùng seed 1337 · config giống hệt nhau trừ đúng khoá `fold`**. Năm tập val phân hoạch sạch 394 ca trainval (kiểm chứng: giao mọi cặp = rỗng, hợp = đúng 394).

| fold | n val | macro-F1 | κ | epoch tốt nhất |
|---|---|---|---|---|
| 1 | 82 | 0.7001 | 0.6465 | 231 |
| 2 | 80 | 0.6771 | 0.6273 | 297 |
| 3 | 78 | 0.7304 | 0.6772 | 104 |
| 4 | 77 | 0.6680 | 0.6548 | 135 |
| 5 | 77 | 0.6618 | 0.6031 | 144 |
| **gộp out-of-fold** | **394** | **0.6851 [0.6394, 0.7308]** | **0.6419 [0.5907, 0.6940]** | — |

Trung bình 5 fold 0.6875 ± 0.0281 (SD mẫu), khoảng 0.662–0.730. **Con số dùng để báo cáo là bản gộp out-of-fold, không phải trung bình này** — trung bình các fold không có CI đúng nghĩa vì mỗi fold là một tập nhỏ khác nhau.

⚠️ **Thiên lệch do chọn epoch: +0.079.** Checkpoint `best` được chọn theo macro-F1 trên *chính tập val đang báo*. Đo trên cùng 312 ca (fold 2–5, vì fold 1 không có `val_probs_last`): `best` 0.6824 so với `last` (epoch 300) 0.6038. Con số 0.6851 vì thế **lệch lạc quan**; generalization thật nằm đâu đó giữa hai cột, và chỉ test-104 mới chốt được. Mọi báo cáo phải nói rõ điều này, không được im lặng đưa 0.6851 ra như một ước lượng không thiên lệch.

**Hai lớp yếu, nhất quán ở cả 5 fold** (F1 out-of-fold): **di căn 0.488** (n=40) và **ICC 0.519** (n=46). Ba hướng nhầm lớn nhất trong ma trận gộp: HCC → di căn (15 ca), ICC → áp-xe (10), HCC → ICC (9). Các lớp còn lại 0.66–0.83. Đây là chỗ đáng cải thiện, không phải nhiễu một fold.

⚠️ Vẫn là **val out-of-fold, không phải test-104**. Không so trực tiếp 0.6851 với bảng văn liệu ở trên.

### E6 augmentation mạnh hơn — null trên trung bình, nhưng hai fold đi NGƯỢC nhau (2026-08-05, WORKLOG S-102)

Cùng 162 ca (fold 1+2). Khác baseline **chỉ trong `data.augment`**: xoay 10°→15° (áp 80% ảnh), tịnh tiến 8→12 voxel trong mặt phẳng, và **bật nhiễu cường độ** (baseline tắt).

| fold | n | E4 | E6 | hiệu | epoch tốt nhất |
|---|---|---|---|---|---|
| 1 | 82 | 0.7001 | **0.7580** | **+0.058** | 231 → 267 |
| 2 | 80 | 0.6771 | **0.5922** | **−0.085** | 297 → 110 |
| gộp | 162 | 0.6879 | 0.6739 | −0.014 | — |

Bootstrap ghép cặp 2000 lần: macro-F1 **−0.014** [−0.078, +0.052] P=0.68 · accuracy −0.007 P=0.75 · ECE +0.005 P=0.91. **Không có ý nghĩa thống kê.**

**Nhưng đừng đọc đây là "augmentation vô ích" — có hai hiệu ứng ngược chiều triệt tiêu nhau.**

**Bằng chứng 1 — fold 1 là con số tốt nhất dự án từng có, và nó ổn định.** Trung bình macro-F1 **50 epoch cuối**: E6 **0.701** so với E4 0.607. Không phải một đỉnh may mắn. Khoảng cách train/val cũng hẹp lại (+1.257 so với +1.495).

**Bằng chứng 2 — fold 2 không phải "epoch xấu", cả run sập.** `val_loss` chạm đáy ở **epoch 5** (E4 fold 2: epoch 79). Trung bình 50 epoch cuối 0.535 so với 0.572.

**Bằng chứng 3 — bảng từng lớp có cấu trúc rõ, không phải nhiễu:**

| lớp | n | E4 | E6 | hiệu |
|---|---|---|---|---|
| nang | 18 | 0.727 | 0.857 | **+0.130** |
| FNH | 15 | 0.759 | 0.778 | +0.019 |
| u máu | 26 | 0.833 | 0.840 | +0.007 |
| HCC | 50 | 0.783 | 0.761 | −0.022 |
| áp-xe | 18 | 0.778 | 0.743 | −0.035 |
| **ICC** | 19 | 0.449 | 0.364 | **−0.085** |
| **di căn** | 16 | 0.486 | 0.375 | **−0.111** |

⚠️ **Hai lớp yếu nhất — đúng hai lớp đang kéo macro-F1 xuống — TỆ ĐI nhiều nhất.**

**Giả thuyết (chưa chứng minh):** `RandomIntensity` áp scale/shift **độc lập cho từng pha** (`src/data/transforms.py`, `per_channel`). Chẩn đoán u gan trên MRI đa pha dựa vào cường độ **tương đối giữa các pha** — ngấm rồi thải (HCC), ngấm tiến triển (ICC), viền ngấm (di căn). Xáo mỗi pha ±10% độc lập là đổ nhiễu thẳng lên tín hiệu phân biệt. Khớp bảng trên: hai lớp phụ thuộc động học nhất tụt mạnh nhất, còn **nang** — nhận ra bằng tín hiệu tuyệt đối chứ không bằng động học — tăng nhiều nhất.

`configs/e6b_geom_only.yaml` tách đúng một biến (`intensity_prob: 0`) để trả lời.

⚠️ Giả thuyết cạnh tranh chưa loại được: augmentation mạnh làm **tối ưu hoá bất ổn** ở fold 2 (`val_loss` đáy ở epoch 5). Hai cách giải thích này không loại trừ nhau.

### E5 focal loss — 2/5 fold, chưa kết luận được (2026-08-05, WORKLOG S-094)

Cùng 162 ca (fold 1+2), cùng split, cùng seed. Config khác baseline **đúng 3 khoá**: `loss.name`, `loss.gamma`, `output_dir`.

| | macro-F1 | ECE thô | MCE | Brier | tự tin (lệch) |
|---|---|---|---|---|---|
| E4 (CE) | 0.6879 | 0.2212 | 0.3837 | 0.5585 | 0.903 (+0.206) |
| E5 (focal γ=2) | 0.6601 | **0.1542** | 0.4990 | **0.5033** | 0.833 (+0.136) |

Bootstrap ghép cặp 2000 lần trên cùng bệnh nhân: macro-F1 **−0.029** [−0.105, +0.048] P=0.47 · ECE **−0.050** [−0.123, +0.024] P=0.17. **Không cái nào có ý nghĩa thống kê.**

⚠️ **Phát hiện quan trọng hơn cả hai giả thuyết: sau khi hiệu chỉnh đúng cách, hai bên bằng nhau.**

| | T tối ưu ECE | ECE sau |
|---|---|---|
| E4 (CE) | 2.00 | 0.1281 |
| E5 (focal) | 1.50 | 0.1255 |

Focal *có* làm model bớt tự tin quá mức từ đầu (T cần nhỏ hơn: 1.50 so với 2.00), nhưng **"CE + temperature fit theo ECE" đã đạt 0.128 rồi**. Lợi thế ECE thô 0.154 của focal biến mất sau bước hiệu chỉnh mà dự án vốn đã làm. Đây là lý do kỹ thuật để **không** đổi loss chỉ vì mục tiêu calibration.

⚠️ Dùng `T` fit theo **NLL** cho focal thì ECE *xấu đi* (0.154 → 0.176) — bắn quá sang thiếu tự tin (0.596 so với accuracy 0.698). Với focal bắt buộc dùng `fit_temperature_min_ece`.

⚠️ MCE xấu đi (0.384 → 0.499) và AURC xấu đi nhẹ (0.181 → 0.196). Fold 2 tụt rõ (0.677 → 0.609) còn fold 1 hoà (0.700 → 0.697).

### Grad-CAM 4 ca demo — kết quả thật (2026-08-05, WORKLOG S-098)

`notebooks/10_gradcam.ipynb`, tầng `denseblock3`, **HiResCAM** (không phải Grad-CAM gốc — xem `src/xai/gradcam.py`). Mỗi ca dùng model của fold chứa nó ở val.

| ca | thật | đoán | bản đồ lớp thật | đỉnh (x,y,z) | lệch tâm |
|---|---|---|---|---|---|
| MR113627 | ICC | ICC | không cần | (55, 55, 24) | 8.5 |
| MR170828 | u máu | u máu | không cần | (54, 55, 24) | 8.6 |
| MR207769 | di căn | áp-xe | có | (40, 55, 24) | 17.7 |
| **MR127280** | **di căn** | **u máu** | **SUY BIẾN** | **(55, 87, 0)** | **35.1** |

Crop cắt **bám tổn thương** nên tổn thương nằm giữa khối (tâm 55, 55, 15).

**Hai ca đoán đúng có đỉnh đúng tâm trong mặt phẳng** (55,55) — bằng chứng model nhìn vào tổn thương chứ không vào rìa.

**`MR127280` là ca thất bại toàn diện, và bản đồ nói ra điều đó:** đỉnh ở (55, **87**, **0**) — lệch 32 voxel theo y và nằm ở **lát biên**. Cộng với việc bản đồ cho lớp thật **suy biến** (không voxel nào ủng hộ lớp đúng). Nghĩa là model không chỉ đoán sai — nó nhìn nhầm chỗ và không thấy bằng chứng nào cho đáp án đúng. Đây là ca đáng đưa vào phần failure analysis của báo cáo.

**Độ nhạy theo thì** (tổng = 1; mức đều = 0.125):

| ca | C-pre | C+A | C+V | C+Delay | T2WI | DWI | InPhase | OutPhase |
|---|---|---|---|---|---|---|---|---|
| MR113627 | 0.120 | 0.105 | 0.129 | **0.161** | 0.151 | 0.150 | 0.091 | 0.092 |
| MR127280 | **0.214** | 0.139 | 0.166 | 0.183 | 0.083 | 0.105 | 0.053 | 0.057 |
| MR170828 | 0.125 | 0.124 | 0.194 | **0.201** | 0.186 | 0.072 | 0.046 | 0.053 |
| MR207769 | 0.094 | 0.158 | 0.152 | **0.178** | 0.129 | 0.158 | 0.043 | 0.087 |

**In Phase và Out Phase thấp nhất ở cả 4 ca** (0.043–0.092, đều dưới mức đều). Hợp lý về lâm sàng: hai thì chemical-shift chủ yếu để phát hiện mỡ, ít phân biệt được giữa 7 lớp này; còn các thì có thuốc mang đúng kiểu ngấm thuốc — thứ dẫn dắt chẩn đoán u gan.

⚠️ **Bốn cảnh báo bắt buộc kèm bộ số này:**

1. **Bản đồ gốc chỉ 7×7×2.** Theo Z chỉ có **2 mức** rồi nội suy lên 32 lát — vị trí `z` của đỉnh chỉ nói được "nửa trên hay nửa dưới", không hơn. Trong mặt phẳng mỗi ô gốc phủ 16 voxel, nên lệch đỉnh **dưới ~8 voxel là trong cùng một ô**, đừng diễn giải.
2. **n = 4 ca.** "In/Out Phase luôn thấp nhất" là quan sát trên 4 ca, không phải kết luận thống kê.
3. **Là saliency, không phải ablation.** Không nói bỏ hẳn một thì đi thì mất bao nhiêu điểm.
4. **Mức phân biệt giữa các thì là vừa phải** — thì cao nhất chỉ gấp 1.3–1.7 lần mức đều. Model trải độ nhạy khá rộng, không dựa hẳn vào một thì.

### Trustworthiness — calibration & selective (2026-08-04, WORKLOG S-079)

Chạy bằng `python -m src.eval.trust --run-dir runs/E4_cv_results`. Temperature fit **leave-one-fold-out**: `T` áp lên fold `f` học từ 4 fold còn lại, nên không ca nào được hiệu chỉnh bởi một `T` đã nhìn thấy nó.

| | ECE | MCE | Brier | NLL | tự tin TB | macro-F1 |
|---|---|---|---|---|---|---|
| chưa hiệu chỉnh | 0.2030 | 0.6775 | 0.5488 | 2.0308 | 0.889 (+0.186) | 0.6851 |
| temp-scaled, fit **NLL** | 0.1756 | 0.8026 | 0.5228 | **1.1687** | 0.606 (−0.097) | 0.6851 |
| temp-scaled, fit **ECE** | **0.1534** | **0.3510** | **0.5162** | 1.2812 | 0.745 (+0.042) | 0.6851 |

*(accuracy thật 0.7030; cột "tự tin TB" kèm độ lệch so với accuracy)*

Bốn điều rút ra:

1. **Model tự tin quá mức nghiêm trọng.** Tự tin trung bình 0.889 trong khi đúng 70,3%; trung vị 0.987 và phân vị 75 là **1.000**. Đây là hệ quả trực tiếp của 300 epoch CE trần không label smoothing, đúng như `src/eval/calibration.py` mô tả.
2. **`T` tối ưu NLL ≠ `T` tối ưu ECE, và chênh nhau nhiều.** NLL nhỏ nhất ở `T≈3.26`, ECE nhỏ nhất ở `T≈2.05`. Lấy `T` của NLL thì model **bắn quá sang thiếu tự tin** (0.606 so với accuracy 0.703) và MCE *xấu đi* (0.678 → 0.803). Fit theo ECE tốt hơn ở mọi metric calibration, chỉ thua NLL. Có `fit_temperature_min_ece` cho việc này.
3. **Một scalar là không đủ.** Ngay cả `T` tốt nhất cũng chỉ hạ ECE xuống 0.153 — vẫn lớn. Bước tiếp theo hợp lý là vector/matrix scaling hoặc ensemble, không phải chỉnh thêm `T`.
4. **Selective prediction có tác dụng nhưng yếu.** AURC 0.206 so với điểm ngẫu nhiên 0.296 [0.258, 0.335] và oracle 0.049 — tốt hơn ngẫu nhiên rõ rệt, còn xa hoàn hảo. macro-F1@80% = 0.6813 [0.6286, 0.7327], **gần như không hơn** 0.6851 ở coverage 100%. Ở mức sai số ≤10% chỉ tự quyết được **12,9%** số ca.

⚠️ **Hiệu chỉnh xác suất làm selective hơi TỆ đi** (AURC 0.206 → 0.214). Không mâu thuẫn: temperature không thêm thông tin nào, chỉ đổi thang. Kết luận kỹ thuật cho web app: **xếp hạng/defer theo max-prob thô, hiển thị theo xác suất đã hiệu chỉnh.**

⚠️ Giả thuyết "gộp 5 model khác nhau làm hỏng thứ hạng tin cậy" **đã kiểm và bác bỏ**: AURC trung bình trong từng fold 0.2038, gộp 394 ca 0.2059 — như nhau.


### MC-dropout & phép lai — selective prediction cuối cùng cũng có tác dụng (2026-08-04, WORKLOG S-087)

`notebooks/08_mc_dropout.ipynb`, K=20 lượt/ca trên chính model của từng fold (nên mọi thành viên đều mù với val của nó). Đọc bằng `python -m src.eval.trust --run-dir runs/E4_per_phase_results --members`.

**MC-dropout hạ macro-F1 0.6851 → 0.5852 (−0.100).** Không dùng làm bộ dự đoán được. Nhưng ECE của nó là **0.1216** — tốt hơn cả temperature scaling tốt nhất (0.1534) mà không cần fit gì.

**Phép lai là thứ đáng giá:** dự đoán lấy từ model tất định, **chỉ điểm xếp hạng defer** lấy từ epistemic của MC-dropout.

| điểm xếp hạng defer | AURC | F1@100% | F1@90% | F1@80% | F1@70% | F1@50% |
|---|---|---|---|---|---|---|
| tất định · max-prob | 0.2059 | 0.6851 | 0.6909 | 0.6799 | 0.7043 | 0.7388 |
| **LAI · tất định + −epistemic** | **0.1689** | 0.6851 | 0.6923 | **0.7222** | 0.7367 | 0.7484 |

Bootstrap **ghép cặp** trên hiệu (2000 lần, phân tầng, mức bệnh nhân):

| | hiệu | CI95 | P |
|---|---|---|---|
| F1@80%(epistemic) − F1@100% | **+0.0350** | [+0.0039, +0.0647] | **0.030** |
| AURC(epistemic) − AURC(max-prob) | **−0.0346** | [−0.0648, −0.0080] | **0.013** |
| *đối chứng:* F1@80%(max-prob) − F1@100% | −0.0027 | [−0.0340, +0.0263] | 0.88 |

**Kết luận cho báo cáo:** selective prediction có tác dụng, nhưng **chỉ khi tín hiệu bất định đến từ mức bất đồng giữa các lượt dự đoán, không phải từ softmax của một lượt tất định.** Dòng đối chứng là thứ mang cả lập luận: cùng model, cùng dự đoán, chỉ đổi cách xếp hạng — max-prob cho +0.000, epistemic cho +0.035.

⚠️ F1@50% (+0.060) **không có ý nghĩa thống kê** (P=0.061), và ở coverage thấp lớp hiếm bắt đầu biến mất. Đừng báo con số 0.7484 như một mức đạt được.

⚠️ Đã xem 5 điểm xếp hạng rồi báo cái tốt nhất. `−epistemic` là lựa chọn có lý do từ trước (nó *là* đại lượng headline), và dòng đối chứng mới là thứ chống đỡ kết luận — nhưng phải ghi rõ điều này trong báo cáo.

⚠️ Đây vẫn là **MC-dropout, không phải deep ensemble thật**. Ensemble nhiều seed (mọi thành viên đều mạnh) nhiều khả năng cho cả nền cao lẫn thứ hạng tốt; MC-dropout phải đánh đổi.

---

## 6. Lệnh chạy

> Repo chưa có code → bảng này **chưa đầy đủ**. Tool nào tạo entrypoint đầu tiên **bắt buộc cập nhật đúng dòng tương ứng ở đây** trong cùng commit đó, và ghi vào WORKLOG.

| Việc | Lệnh | Trạng thái |
|---|---|---|
| **Bật quality gate** (một lần / máy) | `git config core.hooksPath .githooks` | sẵn sàng |
| **Quality gate** (trước khi rời tool) | Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-gate.ps1`; Bash thật: `sh scripts/quality-gate.sh` | sẵn sàng |
| Cài Impeccable (một lần / máy) | `npx impeccable install --providers=claude,codex,cursor --scope=project` | ✅ đã chạy 2026-07-24 |
| Quét UI thủ công (mọi tool, kể cả Antigravity) | `npx impeccable detect --json <dir>` | sẵn sàng |
| Cài môi trường train | `pip install -r requirements.txt` | sẵn sàng (W2 ngày 1) |
| Validate split official (đã khoá, không sinh) | `python -c "from src.data.splits import Splits; Splits('splits').validate()"` | sẵn sàng (W2 ngày 1) |
| Sinh manifest bệnh nhân | `python -m src.data.build_manifest --config configs/data.yaml` | sẵn sàng (W2 ngày 1), cần `LLDMMRI_DATA_ROOT` trỏ tới data thật |
| Báo cáo geometry + **phán quyết thứ tự trục** | `python scripts/kaggle_geometry_report.py --limit 0` | sẵn sàng (W2 ngày 2) |
| Tiền xử lý (chạy 1 lần, cache) | `python -m src.preprocess.build_cache --config configs/preprocess.yaml` | sẵn sàng; **cần điền `axis_order` trước**. `crop_mode` chọn `fixed_mm` (cache v0) hay `lesion_tight` (cắt bám tổn thương, dùng mask ở `lld/labels`) — đổi giá trị này là **đổi dữ liệu**, phải build sang thư mục cache khác |
| Train baseline 3D-patch (1 fold) | `python -m src.train.run --config configs/baseline_3dpatch.yaml --fold 1` | sẵn sàng (W2 ngày 5); resume tự động từ `last.pt`; cần `LLDMMRI_CACHE_DIR` trỏ tới cache |
| **Train một fold, config bất kỳ** | `python -m src.train.run --config configs/e5_focal.yaml --fold 1` | sẵn sàng (W4); `configs/e5_focal.yaml` = baseline + focal loss, khác đúng khối `loss:` |
| **Sàng thí nghiệm (rẻ)** | `notebooks/09_cv_runner.ipynb` với `FOLDS = [1, 2]` | 7.4h = 1 session. Sàng trên 2 fold rồi mới xác nhận cái thắng trên 5 fold — **đừng chạy 5 fold cho một ý tưởng chưa đo** |
| **TTA** (GPU, vài phút) | `src/eval/tta.py::tta_predict` — dùng lại checkpoint đã có, **không train lại**. Chỉ lật; `rot90` không hợp lệ về giải phẫu |
| **EMA** | `configs/e7_ema.yaml` (`train.ema_decay: 0.999`) | mặc định TẮT ở baseline. Khi bật, **mọi số trong `train_log.csv`/`metrics_best.json`/`val_probs_*.npz` là của model EMA** |
| **Backbone pretrained** | `configs/e8_pretrained.yaml` | cần upload MedicalNet `resnet_18_23dataset.pth` thành Kaggle Dataset trước; `load_medicalnet_weights` nổ nếu khớp <50% khoá |
| **Chạy CV trên Kaggle** | mở `notebooks/09_cv_runner.ipynb`, đặt `CONFIG_NAME` + `FOLDS` | sẵn sàng (W4); **thay cho notebook 07** (07 khoá cứng vào baseline và còn logic dò đường dẫn cũ đã sai) |
| Đánh giá (CPU, không cần GPU) | `python -m src.eval.run --run-dir artifacts/runs/baseline_3dpatch` | sẵn sàng (W3); đọc `val_probs_*.npz` đã lưu → bảng metric ± CI bootstrap + gộp out-of-fold |
| **Bảng trustworthiness** (CPU) | `python -m src.eval.trust --run-dir runs/E4_cv_results` | sẵn sàng (W3); calibration + selective từ cùng các `.npz`. Temperature fit **leave-one-fold-out**, không fit gộp — xem docstring module |
| Bảng trên + bất định epistemic | `python -m src.eval.trust --run-dir runs/E4_cv_results --members` | sẵn sàng (W3); cần `fold*/mc_dropout.npz` sinh từ `notebooks/08_mc_dropout.ipynb` |
| **MC-dropout** (GPU, ~8 phút) | chạy `notebooks/08_mc_dropout.ipynb` trên Kaggle | sẵn sàng (W3); inference thuần, **không train**. Cần mount **hai** dataset: cache E4, và checkpoint (`best-weights`: `best_fold_1..5.pt` phẳng, hoặc `fold_N/best.pt`) |
| Test (chạm 1 lần!) | `python -m src.eval.run --ckpt <path> --split test --i-know-this-is-final` | chưa có |
| Cài backend web app (một lần / máy) | `pip install -r webapp/backend/requirements.txt` | sẵn sàng; **tách hẳn** khỏi `requirements.txt` train, không kéo torch/monai |
| Cài frontend web app (một lần / máy) | `cd webapp/frontend && npm install` | sẵn sàng |
| **Chạy web app** — backend | `python -m uvicorn webapp.backend.main:app --reload` | sẵn sàng; cổng 8000. Ảnh thật từ `LLDMMRI_SAMPLE_DIR`; **số thật** từ `LLDMMRI_PREDICTIONS_DIR` (mặc định `runs/E4_per_phase_results`) — 394 ca out-of-fold, `provenance.source = oof`. Ca ngoài 394 đó rơi về `simulated` |
| **Grad-CAM + độ nhạy theo thì** (GPU, vài phút) | chạy `notebooks/10_gradcam.ipynb` trên Kaggle | sẵn sàng (W4); inference + backward, **không train**. Cổng B đo hình dạng tầng trước khi chạy — tầng cuối của DenseNet có thể còn Z=1, khi đó bản đồ là hằng số theo lát |
| **Trích ca demo** (chạy trên Kaggle) | `python scripts/export_demo_cases.py --out /kaggle/working/demo_cases` | sẵn sàng (W4); 4 ca out-of-fold chọn theo hành vi thật của model, xem docstring |
| **Chạy web app** — frontend | `cd webapp/frontend && npm run dev` | sẵn sàng; proxy `/api` sang 8000. Mở **`http://localhost:5173`** — trên Windows Vite bind vào `::1`, nên `127.0.0.1:5173` **không** vào được |
| Build frontend | `cd webapp/frontend && npm run build` · `npm run typecheck` | sẵn sàng |
| Test | `pytest -q` | sẵn sàng (113 test; 8 test cần torch/monai sẽ tự skip nếu chưa cài) |
| Lint | `ruff check src tests` · `ruff format src tests` | sẵn sàng (W2 ngày 1) |
| **Kết xuất báo cáo ra PDF** | `python scripts/md2pdf.py reports/W2_REPORT.md` | sẵn sàng; Markdown → HTML → Chrome/Edge headless. Không cần pandoc hay LaTeX. `--keep-html` để soi bản trung gian |

---

## 7. Ràng buộc Kaggle (quan trọng khi sinh code)

Code train phải được viết với các ràng buộc này ngay từ đầu, không "sửa sau":

- **Session ≤ 12h, có thể bị ngắt bất cứ lúc nào** → checkpoint + resume **mỗi epoch**, log ra CSV ghi liên tục (không buffer đến cuối).
- **VRAM ~16GB** → AMP (`torch.cuda.amp`), batch 2–4 + gradient accumulation, gradient checkpointing trên backbone. **Batch hiệu dụng chọn theo kích thước dataset, không phải theo VRAM**: 312 mẫu train mà hiệu dụng 16 chỉ cho ~20 bước cập nhật mỗi epoch — đủ ít để model gần như đứng yên (WORKLOG S-040). VRAM chỉ quyết định `batch_size`; `accum_steps` là lựa chọn tối ưu hoá, và tăng nó **không** làm epoch nhanh hơn.
- **Không tiền xử lý lại mỗi session** → chạy preprocessing offline 1 lần, đẩy lên làm **Kaggle Dataset có version**, notebook chỉ mount vào.
- **Ổ đĩa ghi được duy nhất là output dir** → mọi đường dẫn ghi phải qua biến config, không hardcode `/kaggle/working` rải rác trong code.
- **Không có internet trong một số chế độ** → pin sẵn dependency, model pretrained nạp từ Kaggle Dataset, không tải runtime.
- **Kaggle không phải server** → không bao giờ chạy FastAPI ở đó.

---

## 8. Quy ước code

- **Python 3.11**, format bằng **ruff** (`ruff format` + `ruff check --fix`). 100 ký tự/dòng.
- **Type hint** cho mọi hàm public. Không `Any` trừ khi có lý do ghi trong comment.
- **Không hardcode hyperparam** — tất cả qua YAML trong `configs/`. Trong code chỉ đọc config.
- **Không có magic number ở đường dẫn** — dùng `pathlib.Path`, gốc lấy từ config/env.
- **Randomness đi qua một chỗ duy nhất**: `src/utils/seed.py::set_seed()`. Không rải `random.seed` khắp nơi.
- **Hàm eval phải thuần** (input → metric), tách hẳn khỏi vòng train, để chạy lại được trên checkpoint cũ.
- **Docstring** cho hàm khoa học phải ghi rõ *metric này là gì và tại sao dùng* — báo cáo sẽ trích lại.
- **Frontend:** React + Vite + Tailwind + TypeScript, thư viện tự do. Token thị giác được ép ở `webapp/frontend/tailwind.config.js` chứ không chỉ ghi trong tài liệu — `borderRadius` chỉ có `0`, `boxShadow` chỉ có `none`, bảng màu mặc định của Tailwind bị loại hẳn. Viết `rounded-2xl` sẽ không sinh ra class nào. Chi tiết thẩm mỹ do `webapp/DESIGN.md` quy định.
- **Comment bằng tiếng Việt là chấp nhận được** (dự án cá nhân), nhưng **tên biến/hàm bằng tiếng Anh**.

---

## 9. Quy ước Git

- Branch chính: `main`. Nhánh việc: `feat/<scope>`, `fix/<scope>`, `exp/<tên-thí-nghiệm>`, `docs/<scope>`.
- Commit message: `<type>(<scope>): <mô tả ngắn>` — type ∈ `feat|fix|exp|docs|chore|refactor`.
  Ví dụ: `exp(fusion): thêm phase-attention v1`, `feat(webapp): endpoint /predict trả uncertainty`.
- **Một phiên tool = ít nhất một commit sạch trước khi đổi tool.** Không để việc dang dở ngoài git khi rời tool.
- Không `git push --force` lên `main`.
- **Không commit:** dữ liệu bệnh nhân, `.nii/.nii.gz/.dcm`, checkpoint `.pt/.pth`, thư mục `artifacts/`, secret/token Kaggle.

> Giao thức đầy đủ về đổi tool, ai được sửa file config của tool nào, và checklist vào/ra phiên → [`docs/MULTI_TOOL_WORKFLOW.md`](docs/MULTI_TOOL_WORKFLOW.md).

---

## 10. Ranh giới — tuyệt đối không tự làm

Agent phải **hỏi người dùng trước**, không tự quyết:

- Thay đổi quyết định đã chốt trong Spec Sheet (dataset, taxonomy 7 lớp, metric chính, chiến lược split/threshold).
- Chạy đánh giá trên **test-104**.
- Kích hoạt bất kỳ **kill-switch** nào trong plan (chuyển 2.5D, đổi sang CT, giảm K ensemble).
- Sửa `.gitignore` theo hướng *bỏ ignore* một thư mục dữ liệu.
- Thêm dependency nặng mới, hoặc đổi framework.
- Xoá / viết đè entry cũ trong `WORKLOG.md`.
- Đẩy dữ liệu, checkpoint hay kết quả lên dịch vụ bên ngoài (Hugging Face, ngrok, v.v.).

---

## 11. Ghi chú riêng theo tool

Ba mục dưới đây tồn tại vì mỗi tool có cơ chế riêng. **Nội dung dự án không được để ở đây** — chỉ ghi cách tool đó tiếp cận file này.

- **Claude Code** — đọc `CLAUDE.md`, file đó `@AGENTS.md` để nhúng nguyên bản này. Không chép nội dung vào CLAUDE.md.
- **OpenAI Codex** — đọc thẳng `AGENTS.md`. Không cần file cầu nối.
- **Cursor** — đọc `AGENTS.md` (bản mới) và `.cursor/rules/00-project-context.mdc` (`alwaysApply: true`) trỏ về đây. Rule file giữ mỏng, không chép nội dung.
- **Google Antigravity** — đọc `AGENTS.md`. ⚠️ Antigravity còn có **hệ memory riêng** có thể lưu ngữ cảnh cũ và **drift khỏi file này**. Nguyên tắc: khi memory của Antigravity mâu thuẫn với AGENTS.md thì **AGENTS.md thắng**; xoá/ghi đè memory đó rồi ghi vào WORKLOG. Đây là điểm ma sát không loại bỏ được hoàn toàn, chỉ giảm thiểu bằng kỷ luật. Antigravity cũng **không có `/impeccable`** — xem `docs/MULTI_TOOL_WORKFLOW.md` §9.

---

## 12. Ràng buộc thiết kế — áp cho MỌI deliverable có giao diện

Ba thứ có mặt người dùng — **web app** (`webapp/`), **HTML slide** (`slides/`), **HTML report** (`reports/`) — phải khớp nhau về **con số, thuật ngữ và giọng** (`PRODUCT.md` Product Principle 4).

> **Đổi ngày 2026-07-31 (WORKLOG S-076, cập nhật S-077):** ba bề mặt **không còn buộc phải nhìn như một hệ thống**. Web app có thế giới thị giác riêng ở [`webapp/DESIGN.md`](webapp/DESIGN.md) — **"bàn đọc tối"**, nền `#070A13` accent cyan, dựng theo bố cục bản bolt.new gốc. `DESIGN.md` ở gốc ("bản khắc atlas") nay chỉ chi phối `slides/` và `reports/`, và `slides/overview_v2.html` đang dùng nó. Cái phải khớp là **con số, thuật ngữ và giọng**, không phải lớp nhìn.
>
> Hướng "hải đồ đo sâu" nền sáng dựng ở S-076 **đã bị loại** ở S-077 sau khi người dùng xem bản dựng. Đừng khôi phục từng mảnh của nó.

**Bắt buộc, với mọi tool, kể cả tool không có `/impeccable`:**

1. **Đọc [`PRODUCT.md`](PRODUCT.md) trước khi viết dòng UI đầu tiên** — đặc biệt mục *Product Principles*, *Brand Commitments*, *Evidence on Hand*, *Accessibility & Inclusion*. Đây là ràng buộc, không phải gợi ý. Rồi đọc file design đúng phạm vi: [`webapp/DESIGN.md`](webapp/DESIGN.md) khi làm web app, [`DESIGN.md`](DESIGN.md) khi làm slide hoặc report.
2. **Giọng: công cụ y tế nghiêm túc.** Không gradient rực rỡ, không hiệu ứng khoe kỹ thuật, không micro-interaction vui vẻ. Người dùng là bác sĩ chẩn đoán hình ảnh và người review nghiên cứu.
3. **Số liệu là nhân vật chính.** Xác suất, mức bất định và cờ `defer` phải nổi bật nhất trên màn hình. Không hiệu ứng nào được cạnh tranh với chúng.
4. **Màu chỉ mang thông tin, không trang trí.** Thông tin **không bao giờ** chỉ mã hoá bằng màu — luôn kèm nhãn chữ hoặc hình dạng (yêu cầu a11y, và bác sĩ mù màu là chuyện có thật).
5. **RUO hiển thị trên mọi màn hình có kết quả**, ở vị trí không thể bỏ sót.
6. **Không trình bày kết quả như chẩn đoán chắc chắn.** Mức bất định là nội dung hạng nhất, không phải chú thích nhỏ.
7. **Motion chỉ để giải thích chuyển trạng thái.** Tôn trọng `prefers-reduced-motion`.
8. **Trước khi chốt bất kỳ deliverable UI nào:** chạy quality gate phù hợp với shell (Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-gate.ps1`; Bash thật: `sh scripts/quality-gate.sh`) để dùng detector Impeccable cho cả 4 tool.

**Việc dựng UI mới nên giao cho Claude Code / Codex / Cursor** (có `/impeccable shape` và `critique`). Antigravity nên nhận backend, xử lý dữ liệu, sửa lỗi logic — lý do ở `docs/MULTI_TOOL_WORKFLOW.md` §9.3.

---

*Cập nhật lần cuối: 2026-08-04 · Mọi thay đổi file này phải kèm một entry trong `WORKLOG.md`.*
