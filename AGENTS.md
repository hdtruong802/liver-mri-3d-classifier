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
│   ├── xai/                     # heatmap độ nhạy offline, attention rollout
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

| | macro-F1 | κ | Ghi chú |
|---|---|---|---|
| Hạng 1 · WorkingisAllyouneed | 0.8322 | 0.7801 | |
| Hạng 2 · NPUBXY | 0.8078 | 0.7660 | |
| Hạng 3 · LinGroup | 0.7860 | 0.7435 | |
| **Baseline official** | **0.6083** | 0.5414 | UniFormer-S 3D, from scratch, 300 epoch |
| Hạng 20–24 | 0.5047 – 0.6076 | — | đủ loại kiến trúc |

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

#### ⭐ Bảng thứ ba, và là bảng DUY NHẤT đo một biến về FUSION (SDR-Former, đọc bài 2026-08-17)

Nguồn: Lou và cs., arXiv:2402.17246, Bảng 1 phần "MR (8-phase)". **Nhóm này chính là nhóm phát hành LLD-MMRI.** Họ bọc **cùng một backbone** vào khung Siamese của SDR-Former và đo lại — §5.1 nói thẳng các hàng `SNN-*` là những backbone đó *"integrated into the SDR-Former's weight-sharing network framework"*, nên đây **là** phép so một biến:

| backbone | image-level (8 pha = 8 kênh) | Siamese (encoder dùng chung) | hiệu |
|---|---|---|---|
| ResNet-50 | 0.6898 | 0.7168 | +0.027 |
| DenseNet-121 | 0.7171 | 0.7394 | +0.022 |
| MCSCNN | 0.7089 | 0.7409 | +0.032 |
| BoTNet-50 | 0.7139 | 0.7572 | +0.043 |
| **UniFormer-S** | 0.7123 | **0.7639** | **+0.052** |
| H2Former | 0.7342 | 0.7745 | +0.040 |
| **SDR-Former** (đủ bộ: DR-Former + BCIM + APSM) | — | **0.7910** | +0.027 nữa |

**6/6 đều dương**, trung bình **+0.036**, và transformer hưởng lợi hơn CNN (+0.045 so +0.027).

Vì sao bảng này đáng giá **ngay bây giờ**: hai trục đã cạn về mặt thực nghiệm — UniFormer-**Base** (dung lượng lớn hơn) và UniFormerV2-B/16 (nguồn pretrain khác) đều **không** vượt `uniformer_s`. Trục "8 pha được **kết hợp** thế nào" là trục thứ ba, và dự án **chưa từng thử** (mọi thí nghiệm từ E0 tới nay đều đưa 8 pha vào làm 8 kênh). `configs/sdrformer.yaml` + `notebooks/25_sdrformer.ipynb` là bản tái lập.

⚠️⚠️ **Nhưng SDR-Former train FROM SCRATCH.** Ta đang cân nhắc bỏ pretrained — can thiệp *duy nhất* từng thắng có ý nghĩa thống kê (+0.130, P<0.001). Đặt kỳ vọng cho đúng: 0.7910 của họ chỉ hơn **0.7682** của ta trên test-104 đúng **+0.023**, nằm gọn trong CI ±0.09. **Không phải một cấu hình chắc chắn tốt hơn.** Và nếu nó thua thì **không kết luận được** "Siamese fusion vô ích" — phép so gộp hai biến (fusion *và* pretrained).

⚠️ **ĐÍNH CHÍNH hai câu sai trong `src/models/siamese_fusion.py`** (đã sửa tại chỗ 2026-08-17):
1. Docstring cũ viết *"+0.074 chỉ do đổi sang SNN"*, lấy hiệu giữa `ResNet-50` (0.6898) và `SNN-UniFormer-S` (0.7639) — hai hàng khác nhau **cả backbone lẫn fusion**. Hiệu một biến thật là **+0.022…+0.052**. Đừng trích con số cũ.
2. Docstring cũ viết *"hạng 2 của challenge dùng ResNet18"* — sai, hạng 2 (`NPUBXY`) dùng UniFormer-S + Kinetics.

---

### 🔒🔒 TEST-104 OFFICIAL — LẦN CHẠM 2, UNIFORMER (2026-08-14, WORKLOG S-173)

> ⚠️ **Tập test đã bị nhìn MỘT LẦN trước đó** (2026-08-07, E4, 0.6162). Mọi câu trong báo
> cáo dùng số dưới đây **phải nói rõ đây là lần chạm thứ hai**. Lần thứ ba cần xin phép và
> một pre-registration §C mới.
>
> Protocol khoá ở [`docs/TEST104_PREREGISTRATION.md`](docs/TEST104_PREREGISTRATION.md) **§B**,
> commit `24b8464` — và `test_run_meta.json` ghi lại đúng sha commit đó, nên quan hệ
> "protocol có trước kết quả" là **kiểm được**, không phải lời hứa.

Cấu hình: `configs/uniformer_s.yaml` không sửa · cache `128×128×16` · **ensemble 5 fold**,
trung bình softmax · không TTA · không EMA · không mixup.

| | macro-F1 | κ | balanced acc | accuracy |
|---|---|---|---|---|
| **ensemble 5 fold (số chính)** | **0.7682 [0.6902, 0.8422]** | 0.7333 | 0.7822 | 0.7788 |
| trung bình 5 model đơn | 0.7302 ± 0.0278 | — | — | — |

#### So với lần chạm 1 — bootstrap ghép cặp trên ĐÚNG 104 ca

| | macro-F1 | hiệu | CI95 | P |
|---|---|---|---|---|
| E4 (lần chạm 1) | 0.6162 | — | — | — |
| **UniFormer (lần 2)** | **0.7682** | **+0.1520** | **[+0.0647, +0.2421]** | **0.001** |

Phép so hợp lệ: cấu hình UniFormer được chọn **hoàn toàn trên out-of-fold**, không dùng
thông tin nào của test. Đọc lại `test_probs.npz` đã lưu của lần 1 **không phải** một lần
chạm mới.

#### ✅ Ước lượng chốt trước đã trúng, và mức hụt NHỎ HƠN dự đoán

§B7 ghi trước khi chạy: **≈ 0.746, khoảng hợp lý 0.72–0.79**. Kết quả 0.7682 nằm giữa khoảng đó.

| | out-of-fold | test-104 | hụt |
|---|---|---|---|
| E4 | 0.6851 | 0.6162 | **−0.069** |
| **UniFormer** | 0.8147 | 0.7682 | **−0.047** |

Ước lượng dùng mức hụt của E4 (−0.069); thực tế chỉ **−0.047**, tức UniFormer khái quát hoá
*tốt hơn* E4 chứ không chỉ điểm cao hơn. Thiên lệch chọn epoch của hai bên gần bằng nhau
(+0.079 và +0.080), nên phần chênh này **không** giải thích được bằng nó.

#### ⭐ Ensemble lần này ĂN THẬT — ngược hẳn lần chạm 1

| | macro-F1 |
|---|---|
| ensemble 5 fold | **0.7682** |
| trung bình 5 thành viên | 0.7302 ± 0.0278 |
| **hiệu** | **+0.0380 [+0.0007, +0.0771] P=0.048** |
| model đơn tốt nhất | 0.7569 ⚠️ **thấp hơn ensemble** |

Lần chạm 1: hiệu chỉ +0.016 **P=0.43**, và model đơn tốt nhất (0.6308) **cao hơn** ensemble
(0.6162). Lần này ensemble vượt **cả 5** thành viên, và mức tăng có ý nghĩa thống kê.

⚠️ Vẫn **cấm** báo model đơn tốt nhất — chọn nó sau khi nhìn test là chọn trên test.

#### 🎯 Calibration — §B3 chốt bản CHƯA hiệu chỉnh, và đó là lựa chọn đúng

| | ECE | MCE | Brier | NLL | tự tin (lệch so acc) |
|---|---|---|---|---|---|
| **ensemble, chưa hiệu chỉnh** | **0.0833** | 0.3716 | 0.3075 | 0.6804 | 0.820 (**+0.042**) |
| ensemble, T=1.35 từ OOF | 0.0985 | **0.2384** | 0.3025 | 0.6656 | 0.749 (−0.030) |

**ECE 0.0833 mà không hiệu chỉnh gì** — so với 0.1303 của ensemble E4 ở lần chạm 1. Hiệu
chỉnh làm **ECE xấu đi** (đúng như §B3 dự đoán từ out-of-fold) nhưng làm MCE tốt lên. Đây là
đánh đổi, không phải cải thiện, và §B3 đã chốt trước bản chưa hiệu chỉnh là số chính.

Tự tin thái quá chỉ **+0.042** (E4 lần 1: +0.115; E4 out-of-fold: +0.186). **Đây là con số
mạnh nhất của phần trustworthiness trong báo cáo.**

#### ⚠️ SELECTIVE — dự đoán chốt trước của tôi ĐÃ SAI

§B4 ghi trước khi chạy: *"Dự đoán: trên test-104 selective cũng KHÔNG đạt ý nghĩa thống kê ở
mức 80%. Nếu nó đạt, dự đoán này sai và phải ghi rõ là sai."*

**Nó đạt, ở cả ba mức.** Bootstrap ghép cặp so với coverage 100%:

| | hiệu | CI95 | P |
|---|---|---|---|
| max-prob @90% | **+0.0340** | [+0.0015, +0.0688] | **0.044** |
| max-prob @80% | **+0.0739** | [+0.0126, +0.1360] | **0.027** |
| max-prob @70% | **+0.1229** | [+0.0087, +0.2043] | **0.033** |

Căn cứ của dự đoán sai: trên out-of-fold không mức nào đạt (@80% P=0.29) và **0/64 lỗi có
biên < 0.10**. Bài học: **"lỗi tự tin sai" trên out-of-fold KHÔNG dự báo được hành vi
selective trên test.** Đừng lặp lại lối suy luận đó.

| xếp hạng | AURC | F1@100% | F1@90% | F1@80% | F1@70% | cov@risk≤10% |
|---|---|---|---|---|---|---|
| **max-prob** | **0.0494** | 0.7682 | 0.8022 | **0.8421** | 0.8911 | **76.9%** |
| −epistemic | 0.0562 | 0.7682 | 0.8082 | 0.8194 | 0.8685 | 70.2% |

§B4 chốt `max-prob` làm chính (đảo vai so với lần 1) — **đúng**: nó thắng `−epistemic` ở AURC
(+0.0069 nghiêng về max-prob, P=0.053) và ở F1@80% (+0.0235, P=0.38). Củng cố kết luận đã rút
ở lần chạm 1: với 5 model độc lập thật, softmax của trung bình đã là tín hiệu bất định tốt,
không cần đại lượng bất đồng.

**Phát biểu dùng được cho báo cáo và web app:** *từ chối 20% ca khó nâng macro-F1 từ 0.768 lên
0.842 (P=0.027), và ở mức sai số ≤10% hệ thống tự quyết được 76,9% số ca.*

#### Latency — đo trong chính lượt chạm

| | ms/ca |
|---|---|
| 1 model | **81.7** |
| **ensemble 5 model** | **408.5** |

T4, batch 4, AMP bật, 104 ca. ⚠️ **Đây là latency theo LÔ.** Web app phục vụ từng ca nên sẽ
chậm hơn, và con số này **không** gồm đọc + tiền xử lý NIfTI. Đừng trình bày nó như thời gian
đáp ứng của hệ thống thật.

#### Từng lớp — di căn vẫn là nút thắt, đúng như out-of-fold

| lớp | n | F1 |
|---|---|---|
| nang | 11 | 0.957 |
| u máu | 16 | 0.938 |
| FNH | 10 | 0.909 |
| HCC | 32 | 0.787 |
| áp-xe | 12 | 0.667 |
| ICC | 12 | 0.621 |
| **di căn** | 11 | **0.500** |

Ba hướng nhầm lớn nhất: **di căn → ICC 3** · HCC → ICC 3 · áp-xe → ICC/di căn 2+2. ICC là
lớp hút nhầm chính, giống hệt bức tranh out-of-fold.

⚠️ n mỗi lớp chỉ 10–16 ca — đừng diễn giải sâu từng con số.

#### Vị trí so với văn liệu — đọc kỹ trước khi viết

| | macro-F1 test-104 | so với 0.7682 |
|---|---|---|
| baseline official (UniFormer-S from scratch) | 0.6083 | **ta cao hơn, CI loại được** (cận dưới 0.690) |
| ResNet3D (bảng CGHNet) | 0.709 | ta cao hơn, **CI không loại được** |
| Uniformer (bảng CGHNet) | 0.719 | ta cao hơn, **CI không loại được** |
| SDR-Former · STM-Former | 0.791 · 0.793 | ta thấp hơn, không phân biệt được |
| đội hạng 2 (recipe đang tái lập) | 0.8078 | ta thấp hơn, không phân biệt được |
| CGHNet · đội hạng 1 | 0.818 · 0.8322 | ta thấp hơn, không phân biệt được |

✅ **Câu được phép viết:** *vượt baseline official 0.6083 một cách có ý nghĩa thống kê*
(CI95 [0.690, 0.842] không chứa 0.6083). Đây là điều lần chạm 1 **không** nói được — hồi đó
0.6162 với CI chứa 0.6083 rất thoải mái.

⛔ **Câu KHÔNG được viết:** "ngang đội hạng 2", "ngang CGHNet", "tiệm cận SOTA". CI rộng ±0.09
nên không loại được mốc nào từ 0.709 trở lên. Định vị đúng: **trên baseline official và trên
nhóm hạng 20–24, dưới SOTA công bố, và với n=104 thì chưa phân biệt được với nhóm 0.71–0.83.**

⚠️ Và phải ghi: đây là **tái lập một phần** recipe của đội hạng 2 (0.8078) — ta dùng `small`
thay `base`, focal softmax thay sigmoid, và **chưa có** intra-class mixup. Chênh 0.039 so với
họ nằm trong khoảng đó cộng nhiễu cỡ mẫu.

---

### 🔒 TEST-104 OFFICIAL — lần chạm 1 (2026-08-07, WORKLOG S-110)

> **Test-104 ĐÃ BỊ CHẠM MỘT LẦN.** Mục này là kết quả của lần đó, cấu hình E4.
>
> ✅ **Lần chạm 2 ĐÃ CHẠY** (2026-08-14, WORKLOG S-173) — UniFormer ensemble 5 fold, **0.7682**. Xem mục ngay trên. Mục này giữ nguyên làm hồ sơ lần 1.
>
> Lần chạm **thứ ba** lại cần xin phép và một pre-registration §C mới (AGENTS.md §3.4, §10). Protocol lần 1 khoá ở cùng file, mục §A, commit `56baa41`.

Cấu hình: E4 (`baseline_3dpatch.yaml` + cache lesion-tight · 112×112×32 · per-phase) · **ensemble 5 fold**, trung bình softmax · không TTA · không EMA/pretrained.

| | macro-F1 | κ | accuracy |
|---|---|---|---|
| **ensemble 5 fold (số chính)** | **0.6162 [0.5246, 0.7032]** | 0.5647 | 0.6346 |
| trung bình 5 model đơn | 0.6001 ± 0.0204 | — | — |

⚠️ **Cao hơn baseline official (0.6083) đúng 0.0038, trong khi CI rộng ±0.09.** CI chứa 0.6083 rất thoải mái, nên **KHÔNG được viết "ta vượt baseline official"**. Câu đúng: *ngang baseline official, không phân biệt được về thống kê*. Định vị: trên phần lớn nhóm hạng 20–24, còn cách rõ ràng so với SOTA công bố (ResNet3D 0.709 · CGHNet 0.818).

⚠️ **Model đơn tốt nhất (fold 2, 0.6308) CAO HƠN ensemble.** Không được báo nó — chọn nó sau khi nhìn test là chọn trên test. Ensemble đã chốt trước là số chính. Ensemble − trung bình thành viên = +0.0162 [−0.0232, +0.0560] **P=0.43**, tức gộp 5 model gần như không giúp.

#### Thiên lệch chọn epoch đã được xác nhận về mặt định lượng

| | macro-F1 |
|---|---|
| out-of-fold (394 ca) | 0.6851 |
| **test-104 (104 ca)** | **0.6162** |
| hụt | **−0.069** |

Thiên lệch chọn epoch đo trước trên out-of-fold là **+0.079** (`best` 0.6824 so với `last` 0.6038, cùng 312 ca). Mức hụt thực tế 0.069 **gần trùng khít**. Nghĩa là 0.6851 lạc quan đúng bằng phần dự án đã tự chỉ ra và cảnh báo, không có nguồn thổi phồng nào khác lộ ra. Đây là điểm mạnh của phần phương pháp luận, nên đưa vào báo cáo.

#### Calibration: ensemble tự nó hiệu chỉnh tốt hơn temperature scaling

| | ECE | MCE | NLL | tự tin (lệch so acc) |
|---|---|---|---|---|
| ensemble, **chưa** hiệu chỉnh | **0.1303** | 0.4459 | 1.2050 | 0.750 (+0.115) |
| ensemble, T=2.10 fit từ OOF | 0.1902 | 0.3674 | 1.0441 | 0.581 (−0.054) |

**Pre-registration §3 dự đoán trước điều này và nó đã xảy ra:** `T` học từ phân bố *model đơn* mà áp lên *ensemble* vốn đã bớt tự tin, nên hiệu chỉnh quá tay — ECE xấu đi và bắn sang thiếu tự tin. Không được fit lại `T` trên test.

**Phát hiện đi kèm:** ensemble **chưa hiệu chỉnh** cho ECE 0.1303, tốt hơn cả model đơn *đã* temperature-scaling tốt nhất trên out-of-fold (0.1534). **Gộp 5 model là bộ hiệu chỉnh tốt hơn temperature scaling** ở bài toán này. Tự tin thái quá giảm từ +0.186 (OOF) xuống +0.115.

#### ⚠️ Selective: có tác dụng, nhưng luận điểm cũ của S-087 KHÔNG lặp lại

| xếp hạng | AURC | F1@100% | F1@90% | F1@80% | F1@70% |
|---|---|---|---|---|---|
| max-prob (đối chứng) | 0.1298 | 0.6162 | 0.6468 | 0.6844 | 0.7527 |
| −epistemic (bất đồng 5 model) | 0.1305 | 0.6162 | 0.6530 | 0.7239 | 0.7526 |

Hiệu giữa hai cách xếp hạng: AURC **+0.0009 P=0.90** · F1@80% +0.0286 **P=0.26**. **Không khác gì nhau.**

Nhưng cả hai đều có tác dụng thật so với không từ chối ca nào (bootstrap ghép cặp, 2000 lần):

| | hiệu so với F1@100% | CI95 | P |
|---|---|---|---|
| max-prob @80% | **+0.0696** | [+0.0154, +0.1245] | **0.016** |
| −epistemic @80% | **+0.0970** | [+0.0466, +0.1451] | **<0.001** |
| max-prob @70% | +0.1267 | [+0.0568, +0.1859] | 0.002 |

**ĐÍNH CHÍNH kết luận của S-087.** Trên out-of-fold, dòng đối chứng max-prob cho +0.000 (P=0.88), và dự án đã kết luận *"selective chỉ chạy được khi tín hiệu đến từ bất đồng, không phải từ softmax"*. **Trên test-104 điều đó sai:** max-prob cho +0.070 có ý nghĩa thống kê. Giải thích nhất quán: trên OOF "ensemble" chỉ là MC-dropout trên **một** model tự tin thái quá nên softmax của nó vô dụng; với **5 model độc lập thật**, softmax của trung bình đã là tín hiệu bất định tốt.

Phát biểu đúng để dùng trong báo cáo: **từ chối 20% ca khó nâng macro-F1 từ 0.616 lên 0.68–0.72, và không cần MC-dropout để làm việc đó.**

#### Từng lớp — hai lớp yếu tụt sâu hơn

| lớp | n | out-of-fold | test-104 | hiệu |
|---|---|---|---|---|
| u máu | 16 | 0.831 | **0.903** | +0.072 |
| nang | 11 | 0.762 | 0.762 | 0.000 |
| ICC | 12 | 0.519 | 0.519 | 0.000 |
| HCC | 32 | 0.776 | 0.679 | −0.097 |
| FNH | 10 | 0.761 | 0.640 | −0.121 |
| áp-xe | 12 | 0.660 | 0.538 | −0.122 |
| **di căn** | 11 | 0.488 | **0.273** | **−0.215** |

Hướng nhầm chính y hệt out-of-fold: **HCC → di căn 6/32 ca**, HCC → FNH 5/32, di căn → ICC 4/11.

Phép tính trần, **dùng đúng số của test-104** (di căn 0.273, ICC 0.519): kể cả 5 lớp còn lại đều đạt 0.90 thì macro-F1 cũng chỉ tới **0.756**. ⚠️ Đừng lẫn với con số **0.771** ở mục E6b bên dưới — cái đó tính từ F1 *out-of-fold* của E6b (0.455 và 0.444). Hai phép tính dùng hai tập khác nhau nên không thay thế nhau được.

⚠️ n mỗi lớp chỉ 10–16 ca, đừng diễn giải sâu từng con số.

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

### ⚠️ ENSEMBLE E4 ⊕ CGHNet — KẾT LUẬN ĐÃ BỊ BÁC BỞI 5 FOLD (2026-08-11, WORKLOG S-127)

> **Giữ lại làm hồ sơ, KHÔNG dùng làm căn cứ.** Mục này từng kết luận ensemble E4 ⊕ CGHNet là
> "hướng có kỳ vọng cao nhất hiện tại" dựa trên **1 fold**. Đủ 5 fold (394 ca) thì:
>
> | | hiệu | CI95 | P |
> |---|---|---|---|
> | **gộp 50/50 − E4** | **−0.0102** | [−0.0388, +0.0181] | **0.47** |
> | CGHNet − E4 | −0.0185 | [−0.0683, +0.0314] | 0.46 |
>
> Gộp out-of-fold: E4 **0.6851** · CGHNet **0.6673** · gộp 50/50 **0.6748**.
> **Fold 1 là fold duy nhất ensemble có tác dụng** (+0.065); bốn fold kia −0.054, −0.020,
> −0.018, −0.034. Quét trọng số cho cực đại ở w(E4)=0.9 → 0.6867, tức **gần đúng bằng E4 một
> mình**. **E4 vẫn là cấu hình gốc.**
>
> 🐛 Và mọi con số CGHNet ở đây là của **bản CÓ LỖI** (`pos_embed` không bao giờ được học,
> S-126). Đã sửa; muốn có mốc CGHNet đúng thì phải train lại 5 fold.
>
> **Đây là lần thứ BA dự án bị một phép sàng cỡ nhỏ lừa:** E6b +0.038 ở 2 fold → −0.002 ở 5
> fold (S-107); ensemble này +0.065 ở 1 fold → −0.010 ở 5 fold. Quy tắc rút ra không đổi:
> **một phép sàng nhỏ chỉ đủ để LOẠI, không đủ để CHỌN.**

#### Phần vẫn đúng và vẫn đáng giá: hai kiến trúc hỏng theo HAI CHIỀU NGƯỢC NHAU

Trên đủ 394 ca, `weak_classes` §1 cho hai bức tranh đối xứng:

| lớp | E4 đoán/thật | CGHNet đoán/thật |
|---|---|---|
| ICC | **1.26** (thừa) | **0.89** (thiếu) |
| áp-xe | **1.31** (thừa) | **0.76** (thiếu) |
| di căn | 1.05 | **0.80** (thiếu) |
| HCC | **0.86** (thiếu) | **1.13** (thừa) |

Ba hướng nhầm lớn nhất cũng đảo chiều: E4 là **HCC → di căn 15 · ICC → áp-xe 10 · HCC → ICC 9**
(lớp đa số rò VÀO lớp yếu); CGHNet là **ICC → HCC 14 · di căn → HCC 13 · áp-xe → HCC 11**
(lớp yếu sập VÀO lớp đa số).

Hệ quả đo được:

| | trùng lặp lỗi | oracle |
|---|---|---|
| E4 so E6b (chỉ khác augmentation) | 74% | 0.782 |
| **E4 so CGHNet** (khác kiến trúc *và* hình học) | **58%** (kỳ vọng 36 nếu độc lập) | **0.8123** |

**Có 12.7 điểm dư địa (0.812 so với 0.685 đạt được), và trung bình xác suất đơn thuần không
lấy được một điểm nào.** Giải thích nhất quán với bảng trên: E4 nói "di căn" đầy tự tin,
CGHNet nói "HCC" đầy tự tin; trung bình hai thiên lệch ngược chiều chỉ chọn bên nào tự tin
hơn, không sửa được bên nào. Muốn khai thác 12.7 điểm đó thì cần một bộ phối hợp **học được**
(stacking trên out-of-fold), không phải phép trung bình cố định.

⚠️ Thiên lệch chọn epoch của CGHNet là **+0.104** trung bình (0.6673 so 0.5692), lớn hơn hẳn
+0.079 của E4. Cả 5 fold đều chạm đáy `val_loss` ở epoch **15–40**, và `train_loss` về
**0.0000** từ khoảng epoch 180 — model thuộc lòng 312 ca train.

#### Hồ sơ: con số fold 1 từng làm cơ sở cho kết luận đã bị bác

⛔ **Mọi con số trong tiểu mục này đã bị 5 fold bác bỏ — xem bảng ở đầu mục. Đừng trích dẫn
nó như kết quả.** Giữ lại đúng một lý do: để thấy một phép sàng 1 fold trông thuyết phục đến
mức nào, kể cả khi kèm sẵn cảnh báo về cỡ mẫu.

*(Nguyên văn kết luận cũ, nay đã sai: "hướng có kỳ vọng cao nhất hiện tại, và nó gần như
miễn phí".)*

CGHNet fold 1: macro-F1 **0.6935** (epoch 112), so với E4 fold 1 0.7001. Ngang nhau
(−0.0066, CI95 [−0.119, +0.107], P=0.94). Nhưng **hai model sai ở những ca KHÁC nhau**:

| | trùng lặp lỗi | oracle |
|---|---|---|
| E4 so **E6b** (chỉ khác augmentation) | **74%** | 0.782 |
| E4 so **CGHNet** (khác kiến trúc *và* hình học) | **50%** | 0.854 |

Và gộp xác suất 50/50 trên 82 ca của fold 1:

| | macro-F1 | ICC | áp-xe | di căn |
|---|---|---|---|---|
| E4 | 0.7001 | 0.500 | 0.941 | 0.526 |
| CGHNet | 0.6935 | 0.588 | 0.588 | 0.444 |
| **gộp 50/50** | **0.7651** | **0.632** | 0.941 | **0.588** |

**+0.065 so với E4, và nó nâng đúng hai lớp yếu.** Quét trọng số cho w(E4)=0.50 là tối ưu,
tức 50/50 **không phải giá trị được chọn trên tập đánh giá** — nó là mặc định không thiên vị.

⚠️ **Phép gộp này HỢP LỆ**, khác hẳn cái bị cấm ở §3: cả hai model train trên **đúng 312 ca**
của fold 1 và đánh giá trên **đúng 82 ca val** mà không model nào thấy. Cái bị cấm là gộp 5
checkpoint của 5 fold rồi báo số out-of-fold.

⚠️ **1 fold, n=82, CI mỗi fold ~±0.19.** E6b sàng 2 fold cho +0.038 rồi 5 fold cho −0.002.
Cần CGHNet đủ 5 fold (1,6 h/fold ⇒ 8h) mới kết luận được. Nhưng khác E6b ở một điểm quan
trọng: đây **không phải cấu hình train mới**, và cơ chế (50% so với 74% trùng lặp) đo được
trực tiếp, không suy từ điểm số.

⚠️ CGHNet `val_loss` chạm đáy ở **epoch 16** (E4 fold 1: epoch 100). Theo ρ=0.770 của S-107
thì đó là dấu hiệu overfit rất sớm, vậy mà nó vẫn đạt 0.6935 — một ngoại lệ đáng ghi.

---

### 🏆🏆 UNIFORMER + KINETICS, ĐỦ 5 FOLD — CẤU HÌNH CHÍNH CỦA DỰ ÁN (2026-08-14, WORKLOG S-169)

**Đây là kết quả để báo cáo. Mọi mục UniFormer phía trên là hồ sơ 1 fold, đã bị mục này thay.**

5 fold, mỗi fold 300 epoch, **cùng seed 1337 · config giống hệt nhau trừ đúng khoá `fold`** —
đã kiểm trực tiếp `config_used.json` cả 5 (`stride [1,2,2]` trung thực, `variant small`,
`sampling sqrt`, `class_weights effective_number`, `smoothing 0.1`, không mixup).

| fold | n val | macro-F1 | κ | epoch tốt nhất | `val_loss` đáy |
|---|---|---|---|---|---|
| 1 | 82 | 0.8111 | 0.7664 | 259 | 48 |
| 2 | 80 | 0.8196 | 0.8304 | 270 | 93 |
| 3 | 78 | 0.8293 | 0.8238 | 103 | 96 |
| **4** | 77 | **0.7496** | 0.7474 | 194 | 91 |
| 5 | 77 | 0.8524 | 0.8397 | 176 | 48 |
| **gộp out-of-fold** | **394** | **0.8147 [0.7746, 0.8547]** | **0.8010 [0.7600, 0.8418]** | — | — |

Trung bình 5 fold 0.8124 ± 0.0383 (SD mẫu), trải 0.750–0.852. **Con số báo cáo là bản gộp
out-of-fold**, không phải trung bình này.

#### So với E4 — bootstrap GHÉP CẶP, 394 ca, 2000 lượt

| | hiệu | CI95 | P |
|---|---|---|---|
| **UniFormer − E4** | **+0.1296** | **[+0.0778, +0.1809]** | **< 0.001** |

**Cả 5 fold dương** (+0.082 → +0.191) và **cả 7 lớp dương**:

| lớp | n | E4 | UniFormer | hiệu |
|---|---|---|---|---|
| **ICC** | 46 | 0.519 | **0.731** | **+0.212** |
| áp-xe | 42 | 0.660 | 0.814 | +0.154 |
| nang | 42 | 0.762 | 0.897 | +0.135 |
| FNH | 36 | 0.761 | 0.895 | +0.134 |
| HCC | 125 | 0.776 | 0.878 | +0.103 |
| **di căn** | 40 | 0.488 | **0.576** | **+0.088** |
| u máu | 63 | 0.831 | 0.912 | +0.081 |

⭐ **Đây là can thiệp duy nhất của dự án vượt E4 có ý nghĩa thống kê, và là lần đầu một hiệu
ứng MẠNH LÊN khi tăng từ 1 fold lên 5** (fold 1 riêng +0.111, gộp +0.130). Ba lần trước đều
ngược: E6b +0.038 ở 2 fold → −0.002 ở 5; ensemble E4⊕CGHNet +0.065 ở 1 fold → −0.010 ở 5.

#### ⚠️ ĐÍNH CHÍNH ba khẳng định của mục fold-1

| khẳng định ở fold 1 | đủ 5 fold | |
|---|---|---|
| thiên lệch chọn epoch **+0.042**, "nhỏ nhất trong ba cấu hình" | **+0.0797** [+0.0419, +0.1213] | **SAI**, ngang hệt E4 (+0.079) |
| di căn top-2 = **1.000** (8/8), "biểu diễn đã mã hoá được lớp này" | **0.625** (n=40) | hướng đúng (E4: 0.500) nhưng **không phải 1.000** |
| `val_loss` đáy ở epoch 48 ⇒ động học lành mạnh | đáy 48/93/96/91/48 | ρ=0.770 của S-107 **không đúng trong nội bộ** cấu hình này: fold 5 đáy sớm nhất *và* điểm cao nhất |

**Bài học lặp lại lần thứ tư: n≈80 không kết luận được gì, kể cả khi có bằng chứng cơ chế đi
kèm.** Lần này kết luận cuối vẫn đúng, nhưng ba con số phụ trợ thì sai — và lúc viết chúng
trông thuyết phục y như con số chính.

#### 🎯 Trustworthiness — cải thiện lớn, đây là phần headline của dự án

| | ECE | MCE | Brier | NLL | tự tin TB (lệch) | `T` cần |
|---|---|---|---|---|---|---|
| E4 | 0.2030 | 0.6775 | 0.5488 | 2.0308 | 0.889 (**+0.186**) | 3.26 (NLL) · 2.05 (ECE) |
| **UniFormer** | **0.1073** | 0.4233 | **0.3033** | **0.7692** | 0.903 (**+0.065**) | **1.53** (NLL) · 1.45 (ECE) |

*(accuracy thật 0.8376; temperature fit **leave-one-fold-out**)*

**ECE giảm một nửa và Brier giảm 45% mà không phải hiệu chỉnh gì.** `T` chỉ 1.53 so với 3.26
— model gần calibrated sẵn. Sau temp-scaling theo ECE: **0.0943**, tốt hơn con số tốt nhất
E4 từng đạt (0.1534) một mức lớn.

⚠️ Nhưng temp-scaling **bắn quá sang thiếu tự tin** (0.8018 so với accuracy 0.8376) và làm
**MCE xấu đi** (0.4233 → 0.7376 khi fit theo ECE). Với model đã gần calibrated thì hiệu chỉnh
thêm là lợi bất cập hại — **khuyến nghị: báo cáo bản chưa hiệu chỉnh, nêu rõ ECE 0.107.**

#### ⚠️ Selective prediction — AURC tốt hơn nhiều, nhưng mức tăng KHÔNG có ý nghĩa thống kê

| | AURC | F1@100% | F1@90% | F1@80% | F1@70% |
|---|---|---|---|---|---|
| E4 · max-prob | 0.2059 | 0.6851 | 0.6909 | 0.6799 | 0.7043 |
| **UniFormer · max-prob** | **0.0972** | 0.8147 | 0.8158 | 0.8316 | 0.8404 |

*(mốc: ngẫu nhiên 0.1615 [0.1274, 0.1963] · oracle 0.0140)*

Bootstrap **ghép cặp** trên hiệu so với coverage 100%:

| | hiệu | CI95 | P |
|---|---|---|---|
| max-prob @90% | +0.0012 | [−0.0144, +0.0220] | 0.72 |
| max-prob @80% | +0.0170 | [−0.0141, +0.0444] | **0.29** |
| max-prob @70% | +0.0258 | [−0.0133, +0.0595] | 0.22 |

**Không mốc coverage nào đạt ý nghĩa thống kê.** Nhất quán với §3 của chẩn đoán: **0/64 lỗi
có biên < 0.10** — model sai một cách *tự tin*, nên xếp hạng theo softmax không tách được lỗi
ra. AURC 0.0972 vẫn tốt hơn ngẫu nhiên rõ rệt, tức thứ hạng *có* thông tin; chỉ là macro-F1 ở
coverage giảm không nhích đủ để phân biệt với nhiễu.

⚠️⚠️ **Và phép lai đã cứu selective trên E4 thì KHÔNG dùng được ở đây.** S-087 đạt +0.035
(P=0.030) nhờ xếp hạng bằng epistemic của MC-dropout. UniFormer có `head_dropout: 0.0` nên
**không có lớp Dropout nào** — MC-dropout sẽ trả K lượt giống hệt nhau. Muốn có tín hiệu bất
đồng thì phải train nhiều seed **trên cùng một split**, hoặc tạo một config riêng đặt
`head_dropout: 0.2` (và đó là cấu hình KHÁC, phải đo lại từ đầu).

Một con số vẫn dùng được cho web app: ở mức **sai số ≤ 20%, coverage đạt 100%** — tức tỉ lệ
lỗi ở toàn bộ 394 ca đã dưới 20% (16,2%). Trên E4 phải bỏ 71% số ca mới xuống được 10%.

#### Chẩn đoán lớp yếu — nút thắt ĐẢO CHIỀU so với E4

| lớp | thật | đoán | tỉ lệ | P | R |
|---|---|---|---|---|---|
| **di căn** | 40 | **26** | **0.65** | **0.731** | **0.475** |
| FNH | 36 | 40 | 1.11 | 0.850 | 0.944 |
| nang | 42 | 45 | 1.07 | 0.867 | 0.929 |
| áp-xe | 42 | 44 | 1.05 | 0.795 | 0.833 |
| HCC | 125 | 130 | 1.04 | 0.862 | 0.896 |
| ICC | 46 | 47 | 1.02 | 0.723 | 0.739 |
| u máu | 63 | 62 | 0.98 | 0.919 | 0.905 |

**Trên E4 vấn đề là precision** (ICC bị đoán thừa 1.26×, áp-xe 1.31×). **Trên UniFormer sáu
lớp đã cân, và di căn lật hẳn sang thiếu**: precision *tốt* (0.731) nhưng recall *tệ* (0.475)
— model giờ quá dè dặt khi gọi tên di căn.

⚠️ **Hệ quả trực tiếp, và nó NGƯỢC với hướng dẫn của mục chẩn đoán S-123:** ở E4, trọng số lớp
và logit adjustment bị loại vì *sai chiều*. Với UniFormer, **riêng cho di căn** chúng đúng
chiều. Nhưng §3 vẫn chặn: 0/64 lỗi sát sao, nên dịch ngưỡng cũng không lật được ca nào. Cách
duy nhất còn khớp là thứ tác động lúc **train**, không phải lúc suy luận —
`configs/uniformer_s_intra_mixup.yaml` là đúng loại đó.

Ba hướng nhầm lớn nhất: **di căn → HCC 8** · ICC → HCC 6 · HCC → ICC 4. Chữa hết 13 lỗi của
HCC chỉ đưa macro-F1 0.8147 → 0.8405 (+0.026) — nhỏ hơn nhiều so với +0.060 tương ứng trên
E4, tức **lớp đa số không còn là nút thắt**.

Trần nếu 6 lớp kia đều đạt 0.95 mà di căn giữ 0.576: macro-F1 chỉ tới **0.896**. **Di căn một
mình chặn mốc 0.9.**

#### ⚠️ Ensemble với E4 làm TỆ ĐI ở mọi trọng số — đừng gộp

| w(UniFormer) | macro-F1 |
|---|---|
| 0.5 | 0.7349 |
| 0.7 | 0.8055 |
| 0.9 | 0.8129 |
| **1.0 (một mình)** | **0.8147** |

Trùng lặp lỗi UniFormer so E4 là **61%** (kỳ vọng 30% nếu độc lập) và oracle 0.901 — tức vẫn
còn 8.6 điểm dư địa mà **trung bình xác suất không lấy được điểm nào**. Xác nhận ở quy mô đầy
đủ điều fold 1 đã gợi ý, và lặp lại bài học S-127: **trùng lặp lỗi thấp không bảo đảm ensemble
ăn.** Muốn khai thác thì cần bộ phối hợp **học được** (stacking trên out-of-fold).

#### Vị trí so với văn liệu — đọc kỹ trước khi viết báo cáo

⚠️ **0.8147 là val out-of-fold, KHÔNG phải test-104.** Không được đặt cạnh 0.8078 của đội hạng
2 hay 0.818 của CGHNet. Hai lý do cụ thể, đều đo được:

1. **Thiên lệch chọn epoch +0.0797** đã đo ngay trên chính bộ số này.
2. **Mức hụt OOF → test đo trên E4 là −0.069** (0.6851 → 0.6162), và nó gần trùng khít với
   thiên lệch chọn epoch của E4 (+0.079).

Nếu UniFormer hụt tương tự thì test-104 rơi vào khoảng **0.74–0.75** — vẫn là bước nhảy lớn so
với 0.6162 đã đo, nhưng dưới SOTA công bố. **Đây là ước lượng, không phải kết quả.**

#### Trạng thái: UniFormer là cấu hình chính, E4 lùi về mốc đối chứng

Từ S-169, `configs/uniformer_s.yaml` là cấu hình để báo cáo. E4 vẫn giữ nguyên giá trị làm
**đối chứng đã đo trên test-104** và làm nguồn cho web app/MC-dropout/TTA.

⚠️ **Chạm test-104 lần thứ hai bằng UniFormer cần đủ ba thứ, không được bỏ bước nào:** (1) xin
phép người dùng; (2) một pre-registration **mới** commit trước khi chạy; (3) cập nhật
`PINNED_SHA256` trong `src/eval/test_once.py` sang checkpoint UniFormer. Và phải báo cáo rõ
**đây là lần chạm thứ hai** (§3.4, §10).

---

### 📁 HỒ SƠ · UniFormer fold 1 = 0.8111 (2026-08-12, WORKLOG S-129) — ĐÃ BỊ BẢN 5 FOLD THAY

> **Giữ làm hồ sơ, KHÔNG trích làm kết quả.** Mục 5 fold ở trên là bản chính thức. Ba con
> số phụ trợ ở đây (thiên lệch +0.042 · di căn top-2 = 1.000 · động học từ `val_loss` đáy)
> **không sống sót** qua 394 ca — xem bảng đính chính ở mục trên.

**Con số cao nhất dự án từng có, và lần đầu một can thiệp vượt E4 có ý nghĩa thống kê.**
Cấu hình đúng `configs/uniformer_s.yaml` không sửa gì (`patch_embed1_stride [1,2,2]` trung
thực, `require_pretrained: true`).

| cùng 82 ca fold 1 | macro-F1 | accuracy |
|---|---|---|
| E4 (DenseNet) | 0.7001 | 0.7073 |
| CGHNet | 0.6935 | 0.7073 |
| **UniFormer + Kinetics** | **0.8111** | **0.8049** |

Bootstrap **ghép cặp** trên hiệu (phân tầng theo lớp, 2000 lượt):

| | hiệu | CI95 | P |
|---|---|---|---|
| UniFormer − E4 | **+0.1133** | [+0.0053, +0.2221] | **0.036** |
| UniFormer − CGHNet | **+0.1205** | [+0.0013, +0.2365] | **0.048** |

#### ⭐ Vì sao đây KHÁC ba lần bị fold 1 lừa trước đó

E6b (+0.066 ở fold 1) và ensemble E4⊕CGHNet (+0.065 ở fold 1) đều chỉ có **điểm số**. Lần này
**hai dấu hiệu cơ chế chốt trước ở plan S-125 đã được kiểm, và một cái bắn rất mạnh:**

| di căn (n=8, fold 1) | top-1 | top-2 |
|---|---|---|
| E4 | 0.625 | 0.625 ← **bằng nhau** |
| CGHNet | 0.500 | 0.625 |
| **UniFormer** | **0.875** | **1.000** |

§4 của chẩn đoán nói: *"trong 20 ca sai không một ca nào có di căn ở hạng hai — biểu diễn
không mã hoá được lớp này"*, và kết luận ràng buộc **là biểu diễn**. Pretrained là can thiệp
duy nhất đổi được biểu diễn, và **giờ mọi ca di căn đều nằm trong top-2**. Đây là dự đoán ra
trước, không phải giải thích sau.

⚠️ Dấu hiệu thứ hai **KHÔNG** đổi: vẫn **0/16 lỗi có biên < 0.10**. Tầng quyết định vẫn không
cứu được gì — §3 giữ nguyên. Số lỗi giảm 24 → 16, nhưng lỗi còn lại vẫn tự tin sai.

#### Từng lớp — lớp yếu tăng nhiều nhất

| lớp | n | E4 | UniFormer | hiệu |
|---|---|---|---|---|
| nang | 9 | 0.625 | 0.889 | **+0.264** |
| **di căn** | 8 | 0.526 | **0.737** | **+0.211** |
| FNH | 8 | 0.750 | 0.941 | +0.191 |
| **ICC** | 10 | 0.500 | **0.667** | **+0.167** |
| HCC | 25 | 0.776 | 0.826 | +0.051 |
| u máu | 13 | 0.783 | 0.818 | +0.036 |
| áp-xe | 9 | 0.941 | 0.800 | −0.141 |

áp-xe là lớp duy nhất giảm, và 0.941 của E4 ở fold 1 là ngoại lệ (E4 gộp 394 ca chỉ 0.660).

#### Động học lành mạnh hơn hẳn — bằng chứng chống "epoch may"

| | `val_loss` đáy | best @epoch | thiên lệch best−last | TB 50 epoch cuối |
|---|---|---|---|---|
| E4 | 100 | 231 | +0.071 | 0.607 |
| CGHNet | 16 | 112 | +0.069 | 0.627 |
| **UniFormer** | **48** | **259** | **+0.042** | **0.777** |

**Trung bình 50 epoch cuối của UniFormer (0.777) cao hơn epoch tốt nhất của E4 (0.700).**
Thiên lệch chọn epoch cũng nhỏ nhất trong ba. Không phải một đỉnh may mắn.

#### ⚠️ Gộp với E4/CGHNet làm TỆ ĐI — đừng ensemble

| | macro-F1 |
|---|---|
| UniFormer một mình | **0.8111** |
| gộp 50/50 với E4 | 0.7563 |
| gộp cả ba | 0.7820 |

Trùng lặp lỗi UniFormer so E4 chỉ **50%** và oracle 0.895, nhưng trung bình xác suất vẫn kéo
xuống — vì gộp một model mạnh với hai model yếu hơn 0.11 điểm thì phần yếu thắng. Cùng bài
học S-127: **trùng lặp lỗi thấp không bảo đảm ensemble ăn.**

#### ✅ ĐỦ 5 FOLD — bar đã vượt, xem mục ngay dưới

Bar chốt trước là **gộp 2 fold ≥ 0.78** ⇒ chạy đủ 5 fold và thành cấu hình chính. Đã đủ 5 fold
(S-169): gộp out-of-fold **0.8147**. Bar đã vượt.

⚠️ **Ba con số ở mục fold-1 phía trên KHÔNG sống sót qua 5 fold** — chúng là hiện vật cỡ mẫu
nhỏ, và mục dưới đây đính chính từng cái. Đừng trích mục fold-1 làm kết quả.

---

### ⭐ UNIFORMER + KINETICS — thiết kế và các chỗ lệch (2026-08-11, WORKLOG S-125)

Tái lập recipe của **đội hạng 2** LLD-MMRI 2023: [`ZHEGG/miccai2023`](https://github.com/ZHEGG/miccai2023).
Code: `src/models/uniformer3d.py` · `configs/uniformer_s.yaml` · `notebooks/20_uniformer.ipynb`.
**Chưa chạy fold nào.**

⚠️ **Là hạng 2 (`NPUBXY`, 0.8078), KHÔNG phải hạng 1** (`WorkingisAllyouneed`, 0.8322).
README của repo tự ghi *"second-place solution"*. Đừng viết nhầm trong báo cáo.

#### Vì sao hướng này khác bảy hướng đã bị loại

**Baseline official của challenge CHÍNH LÀ UniFormer-S 3D, from scratch → 0.6083.** Repo này
dùng **đúng kiến trúc đó** và `train.sh` của họ bật `--pretrained`, nạp
`uniformer_small_k400_16x8.pth` — trọng số học trên **video Kinetics-400**.

| | macro-F1 test-104 |
|---|---|
| UniFormer-S, **from scratch** (baseline official) | 0.6083 |
| UniFormer + **Kinetics** + cb_loss + sqrt sampling + smoothing 0.1 + drop-path 0.1 + 3 aug lọc | **0.8078** |

Cùng kiến trúc, chênh **~0.20**. Không mốc đối chiếu nào khác trong văn liệu của dataset này
tách được một cụm biến với biên độ như vậy.

**Chẩn đoán §5 không loại được nó.** Bảy hướng bị loại đều là chỉnh loss/ngưỡng/augment **trên
cùng một biểu diễn**; §4 nói thẳng ràng buộc *là* biểu diễn (di căn không vào nổi top-2).
Pretrained là can thiệp duy nhất đổi được biểu diễn. Dự án chưa từng thử đúng cách: E8 dùng
MedicalNet (pretrain segmentation, yếu hơn nhiều) và vướng lỗi `shortcut_type`; bản tái lập
CGHNet train ViT from scratch — đúng theo bài CGHNet, nhưng nghĩa là chưa có backbone pretrained mạnh.

⚠️ Chênh 0.20 **không phải phép thử một biến sạch** — nó gộp 6 thứ. Tái lập cả cụm thì chỉ quy
kết được cho **cả cụm**. Không được viết "pretrained cho +0.20".

#### Repo đã có gần hết — phần lớn là YAML

| của họ | ta có sẵn |
|---|---|
| `--img_size 16 128 128 --crop_size 14 112 112` | **`configs/preprocess_cghnet.yaml`** — khớp chính xác, **không build cache mới** |
| `--cb_loss` (Cui và cs., β=0.9999) | `losses.py::effective_number_weights`, cùng công thức `1−β^n` |
| `--smoothing 0.1` · flip · rotate · random_crop · mixup | đã có hết |

Mới: `uniformer3d` (đăng ký trong `_BUILDERS`), `RandomAppearance`, `data.sampling`.
**Không thêm dependency nào** — `timm` không cần (`DropPath` ~10 dòng, `trunc_normal_` có trong torch).

#### Ba con số phải biết trước khi chạy

1. **Ngân sách đi ngược trực giác.** `patch_embed1` stride `(1,2,2)` **không hạ mẫu trục lát**:

   | | bản pretrained 16×224×224 | của ta 14×112×112 |
   |---|---|---|
   | stage 3 (SABlock ×8, attention **toàn cục**) | 8×14×14 = **1568** token | 14×14×14 = **2744** token |

   1.75× token ⇒ ~3× chi phí stage 3, tức **đắt hơn** CGHNet (209 GFLOPs, 1.6 h/fold đo thật).

   **Cổng C ĐO THẬT trên T4 (2026-08-11): 0.869 s/batch · 78 s/epoch · 6.50 h/fold.**
   1 fold lọt một session 12h; **5 fold = 32.5h, vượt quota 30h/tuần** ⇒ phải trải qua hai
   tuần quota. ⚠️ **Người dùng đã chốt GIỮ NGUYÊN `[1,2,2]` của họ**, không đổi sang `[2,2,2]`
   dù rẻ hơn ~2–3×: tái lập trung thực recipe đạt 0.8078 quan trọng hơn tiết kiệm quota.
   32.5h là bài toán **kế hoạch**, không phải lý do đổi kiến trúc. Đừng "tối ưu" lại khoá đó.
   ⚠️ **Không suy giờ từ GFLOPs** — ước lượng kiểu đó cho CGHNet đã sai xa (S-123).

2. **Trọng số: bản `small` có ĐÚNG file, bản `base` thì không.**
   [`Sense-X/uniformer_video`](https://huggingface.co/Sense-X/uniformer_video) có
   `uniformer_small_k400_16x8.pth` (đúng của họ) nhưng chỉ có `uniformer_base_k600_**32x4**.pth`;
   bản `16x8` của base chỉ trên Google Drive. Đã chốt **chỉ làm small** — là 3/6 thành viên
   ensemble của họ. Không tham số nào có shape phụ thuộc số frame (đã kiểm), nên 32x4 vẫn nạp
   được nếu sau này cần base, và đó là một chỗ lệch phải ghi.

3. **⚠️ Recipe của họ bật HAI lớp cân bằng cùng lúc, đi ngược chẩn đoán §1.**
   `--cb_loss` (trọng số lớp trong loss) **và** `--sampling sqrt` (lấy mẫu lại). §1 đo ICC bị
   dự đoán **thừa** 1.26× và áp-xe 1.31× trên E4 — đẩy thêm là sai chiều. Không mâu thuẫn: §1
   đo trên **DenseNet from scratch**, biểu diễn khác có cán cân khác. **Tái lập trung thực
   trước, chẩn đoán sau** — cổng D + `weak_classes` sau fold 1; vượt 1.4× thì
   `data.sampling: instance` là ablation một khoá.

#### Bốn chỗ CỐ Ý lệch khỏi họ (đều phải vào báo cáo)

| chỗ | ta làm gì | vì sao |
|---|---|---|
| focal loss | **softmax** (`losses.py`) | của họ là **sigmoid** CB-focal. Chỗ lệch đáng kể nhất |
| `emboss`/`sharpen` | kernel + `scale` của PIL, **bỏ offset 128 và clip** | cache ta là **z-score**, của họ là [0,1] qua `uint8`. Đổi lại ta không mất mát lượng tử hoá |
| xoay | `rotate_mode: nearest` | họ xoay `mode='constant'` nên có dải 0 ở góc — đúng lỗi E12 đã đo (S-111). Đây là chỗ ta tốt hơn họ |
| `--mixup` | **CHƯA CÀI ĐƯỢC** (`mixup_alpha: 0`) | ⚠️ xem đính chính ngay dưới bảng |

⚠️ Và một chỗ **họ làm mà ta giữ nguyên dù nó đáng ngờ**: `blur`/`unsharp` của họ gọi
`ndimage.gaussian_filter` trên mảng **4 chiều** nên σ broadcast ra cả trục pha ⇒ **trộn 8 pha**.
Gần như chắc chắn ngoài ý định của họ. `filter_spatial_only: true` là ablation một khoá.

#### ⚠️ ĐÍNH CHÍNH S-128 — `--mixup` KHÔNG phải cờ chết, và nó là phép ta CHƯA CÓ

S-125 ghi *"cờ có trong `train.sh` nhưng `train.py` không nối nhánh mixup nào"* — **sai**, vì
tôi chỉ đọc `train.py`. Mixup của họ nằm trong **dataset**:
`mp_liver_dataset.py::__getitem__` gọi `self.mixup(image, label)` khi `args.mixup and label != 6`.

Và nó là một phép **khác hẳn** loại `data.mixup_alpha` của ta. Chú thích của chính họ là
`类内mixup` — **mixup TRONG CÙNG LỚP**:

```python
alpha = 1.0
index = random.choice([i for i, x in enumerate(self.lab_list) if int(x) == label])
lam = np.random.beta(alpha, alpha)              # Beta(1,1) = Uniform(0,1)
image = lam * image + (1 - lam) * load(self.img_list[index])
# NHÃN GIỮ NGUYÊN — không trộn nhãn
```

| | mixup của ta (`data.mixup_alpha`) | mixup của họ |
|---|---|---|
| trộn với | ca **bất kỳ** trong batch | ca **cùng lớp** trong toàn tập train |
| nhãn | trộn `λ·y + (1−λ)·y'` | **giữ nguyên** |
| λ | Beta(0.2, 0.2), lệch về hai đầu | Beta(1,1) = **đều** |
| phạm vi | mọi lớp | **loại HCC** (lớp 6) — chỉ 6 lớp thiểu số |
| xác suất | mỗi batch | **mọi mẫu** đủ điều kiện |

Bảng lớp của họ **trùng đúng thứ tự và đúng số ca** với `src/data/taxonomy.py`
(63/46/42/40/42/36/125 = 394), nên `label != 6` chắc chắn là loại HCC.

**Vì sao nó ăn khớp với `--sampling sqrt`:** lấy mẫu lại *có hoàn lại* sinh ra **bản sao y hệt**
của ca hiếm; mixup trong cùng lớp biến mỗi bản sao thành một nội suy mới. Không có nó thì
`sqrt` chỉ lặp lại đúng những ảnh cũ. Đây là mảnh thứ ba mà mục "hai lớp cân bằng" ở trên
bỏ sót — và nó là mảnh làm cho phép lấy mẫu lại **thêm thông tin** thay vì chỉ nhân bản.

**Vì sao nó khớp chẩn đoán §4 hơn mixup chuẩn:** di căn (n=40) không vào nổi top-2 ⇒ thiếu
biểu diễn. Nội suy trong cùng lớp sinh biến thiên mới **đúng cho các lớp hiếm**, mà không tạo
ra nhãn mềm chéo lớp — thứ mà §3 (0/117 lỗi sát sao) nói là không cứu được gì.

✅ **ĐÃ CÀI (2026-08-13, WORKLOG S-166).** `data.intra_class_mixup` ở tầng **dataset**
(`src/data/dataset.py::CachedLesionDataset`), không phải `run_epoch` — vì nó phải bốc một ca
cùng lớp từ **toàn tập train**, mà batch chỉ có 4 mẫu nên phần lớn batch không chứa hai ca
cùng một lớp hiếm. `data.mixup_alpha` là mixup chéo lớp có trộn nhãn, **không** thay thế được;
`tests/test_intra_class_mixup.py` chốt rằng hai khoá không được bật cùng lúc.

Chạy bằng `notebooks/21_intra_mixup.ipynb` + `configs/uniformer_s_intra_mixup.yaml` (khác
`uniformer_s.yaml` đúng hai khoá khoa học). **Chưa chạy fold nào.**

Ba tính chất của bản cài, cần biết khi đọc kết quả:

1. **Lớp bị loại được suy từ nhãn train của chính fold**, không ghi cứng số lớp. Trên cả 5
   fold của split này lớp đa số là HCC với đúng 100 ca train (lớp kế tiếp 50) nên phép suy là
   tất định — đã kiểm trực tiếp trên `splits/`.
2. **Ca đối tác có thể là chính nó** (pool gồm cả mẫu đang xét), khi đó phép trộn là đồng nhất
   bất kể λ. Xác suất `1/n_c`, tức 2–3% ở các lớp hiếm. Giữ như vậy để phân bố đúng nghĩa
   "bốc đều trong lớp".
3. **Đọc đĩa gấp đôi** cho mọi mẫu đủ điều kiện (6/7 số lớp). Cổng C của notebook đo `s/epoch`
   bằng chính loader của config nên con số nó in ra **đã bao gồm** chi phí này.

⚠️ **Phần cài đặt chưa xác nhận được trên máy local:** máy phát triển không có torch nên 8/13
test của phép này **skip**, gồm cả phép kiểm số học của tổ hợp lồi. Chỗ xác nhận thật là **cổng
F** trên Kaggle — nó giải ngược λ từ voxel và đọc file gốc bằng `np.load` độc lập với dataset.
Đừng bỏ cổng F vì thấy "đã có test".

⚠️ **Một chi tiết của họ ta không đọc được: thứ tự trộn so với augment.** Bản của ta trộn ảnh
**thô** rồi mới augment (một lần, cho ảnh đã trộn). Hai crop đều bám tổn thương nên nội suy
còn nghĩa giải phẫu, và cách này rẻ hơn. Nếu họ làm ngược thì chỗ lệch là một lượt augment
độc lập nữa — phải ghi vào báo cáo là chi tiết không xác định được.

#### Cây quyết định của ba augment lọc — 60% mẫu KHÔNG bị phép nào

Chúng **loại trừ nhau** (`elif`), nên gộp vào một lớp `RandomAppearance` là cách duy nhất giữ
đúng phân bố: edge 10% · emboss 10% · blur 8% · sharpen 8% · unsharp 4% · **không gì 60%**.
Nhẹ hơn nhiều so với "bật cả ba". Mọi phép áp **cùng tham số cho cả 8 pha** — đúng như họ, và
đúng bài học E6 (S-102).

#### Bar quyết định, chốt trước khi chạy (fold 1+2)

| gộp 2 fold | kết luận |
|---|---|
| **≥ 0.78** | pretrained là đòn bẩy thật ⇒ chạy đủ 5 fold, thành cấu hình chính |
| **0.73–0.78** | có tác dụng, chưa tới 0.8 ⇒ 5 fold, và ensemble với E4 ⊕ CGHNet |
| **0.69–0.72** | ngang E4 (0.6879 cùng 2 fold) ⇒ **dừng**, ghi thành kết quả âm: ba backbone pretrained độc lập đều không vượt from-scratch |
| **< 0.69** | nghi **lỗi triển khai** hơn kết luận khoa học (E13 cho <0.5 dù cổng A khớp 102/102) ⇒ đọc lại cổng A và B |

⚠️ **2 fold chỉ đủ để LOẠI, không đủ để CHỌN** (E6b: +0.038 ở 2 fold rồi −0.002 ở 5 fold, S-107).

**Ngoài phạm vi, có lý do:** `train_alldata.py` của họ train trên **toàn bộ** trainval nên
không đánh giá out-of-fold được bằng bất kỳ cách nào (chỉ dùng được trên test-104 — lần chạm
thứ hai, cần pre-registration mới); `json_refine.py` hợp nhất dự đoán trên test; ensemble 6
model của họ chọn fold nào lấy model nào **sau khi nhìn điểm val**, tức chọn trên tập đánh giá.

### ⭐ CHẨN ĐOÁN BA LỚP YẾU — bảy hướng chữa đã bị LOẠI (2026-08-10, WORKLOG S-123)

**Đọc mục này trước khi đề xuất bất cứ cách nào để nâng macro-F1.** Chạy lại bằng
`python -m src.eval.weak_classes --run-dir runs/E4_cv_results --compare runs/E6b`, không cần GPU.

Sáu phân tích trên 394 ca out-of-fold của E4:

**§1 — KHÔNG phải mất cân bằng lớp. Model đang *thừa* dự đoán hai lớp yếu.**

| lớp | thật | model đoán | tỉ lệ | P | R |
|---|---|---|---|---|---|
| **ICC** | 46 | **58** | **1.26** | 0.466 | 0.587 |
| **áp-xe** | 42 | **55** | **1.31** | 0.582 | 0.762 |
| di căn | 40 | 42 | 1.05 | 0.476 | 0.500 |
| HCC | 125 | **107** | **0.86** | 0.841 | 0.720 |

Vấn đề là **precision**, không phải recall.

**§2 — KHÔNG phải kích thước tổn thương.** di căn, u máu, nang đều có extent trung vị
**25mm** mà F1 là 0.488 / 0.831 / 0.762; áp-xe có tổn thương **lớn nhất** (60mm) và F1 0.660.

**§3 — KHÔNG phải tầng quyết định. Lỗi cực kỳ tự tin.** p(đoán) trung vị 0.75–0.99 so với
p(thật) 0.000–0.019, và **chỉ 1/117 lỗi có biên < 0.10**.

**§4 — ICC và di căn là HAI vấn đề khác nhau.**

| lớp | top-1 | top-2 | hạng trung vị |
|---|---|---|---|
| **ICC** | 0.587 | **0.848** | 1 |
| **di căn** | 0.500 | **0.500** | **2** |

ICC: thông tin *có*, xếp sai hạng. di căn: trong 20 ca sai **không một ca nào** có di căn ở
hạng hai — biểu diễn không mã hoá được lớp này.

**§5 — Lỗi CÓ CẤU TRÚC.** Trùng lặp lỗi E4 so với E6b: **86/117 = 74%**, kỳ vọng 35 nếu độc
lập; riêng di căn **18/20**. Và **gộp xác suất E4+E6b làm macro-F1 TỆ ĐI** (0.6688 so với
0.6851); oracle 0.782 so với 0.703, tức có 8 điểm dư địa mà ensemble kiểu này không lấy được.

**§6 — Nút thắt precision của hai lớp yếu phần lớn là lỗi của HCC.** Ba hướng nhầm lớn nhất:
HCC → di căn **15** · ICC → áp-xe **10** · HCC → ICC **9**. Chữa hết 35 lỗi của HCC thì
macro-F1 0.6851 → **0.7449 (+0.0598)**. Muốn nâng lớp yếu thì phải chữa lớp **mạnh**.

#### Bảy hướng bị loại, và bằng chứng nào loại

| hướng | bị loại bởi |
|---|---|
| `class_weights: balanced` / `effective_number` | §1 — hai lớp yếu đã bị **thừa** dự đoán |
| logit adjustment, prior correction | §1 + §3 — sai chiều, và gần như không lỗi nào sát sao |
| ngưỡng riêng từng lớp, vector scaling | §3 |
| focal loss mạnh hơn | §1 (và E5 đã đo: di căn −0.171 trên 2 fold, n=16 nên là nhiễu nhưng cùng chiều) |
| thêm augmentation | §5 — 74% lỗi trùng giữa hai cấu hình khác augmentation |
| gộp với một biến thể gần nó | §5 — đã đo, macro-F1 tệ đi |
| cắt sát tổn thương hơn / bỏ sàn 40mm | §2 |

Còn lại đúng một bộ bệnh lý: **tự tin sai + có cấu trúc + biểu diễn thiếu**, trên 312 ca
train. `configs/e14_mixup.yaml` và `configs/cghnet_mixup.yaml` là hai can thiệp khớp với nó.

⚠️ **Lớp yếu nhất của chính CGHNet ở 0.818 cũng là di căn** — bài viết *"the relatively lower
recall for HM indicates that metastatic lesions remain challenging, possibly due to the
limited HM samples and heterogeneous imaging appearances"*. Đây là giới hạn của bài toán,
không riêng của ta, và nó thuộc mục Giới hạn của báo cáo.

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

### E6b, bản sàng 2 fold — ⚠️ KẾT LUẬN ĐÃ BỊ BÁC BỞI 5 FOLD (2026-08-05, WORKLOG S-104)

> **Giữ lại làm hồ sơ, KHÔNG dùng làm căn cứ.** Mục này kết luận E6b là "cấu hình tốt nhất hiện có" dựa trên 2 fold. Đủ 5 fold thì E6b − E4 = **−0.002, P=0.92** — xem mục ngay dưới. Toàn bộ mức tăng ở đây đến từ fold 1, và fold 1 hoá ra là ngoại lệ.

E6b = E6 với `intensity_prob: 0`. Khác E6 **đúng một khoá**. Cùng 162 ca (fold 1+2).

| | fold 1 | fold 2 | gộp 162 | ECE |
|---|---|---|---|---|
| E4 | 0.7001 | 0.6771 | 0.6879 | 0.2212 |
| E6 | 0.7580 | 0.5922 | 0.6739 | 0.2262 |
| **E6b** | **0.7660** | 0.6611 | **0.7119** | 0.2349 |

Bootstrap ghép cặp: **E6b − E4 = +0.024** [−0.038, +0.083] P=0.44 · **E6b − E6 = +0.038** [−0.021, +0.095] P=0.18. **Không cái nào có ý nghĩa thống kê** — n=162, lực kiểm định thấp.

**Giả thuyết nhiễu cường độ được ỦNG HỘ.** Hai lớp phụ thuộc động học hồi phục đúng như dự đoán khi tắt nó: **ICC +0.091**, **di căn +0.069** (so với E6). Không chứng minh được, nhưng dự đoán ra trước và số liệu đi đúng hướng.

⚠️ **Kết quả KHÔNG khớp gọn dòng nào trong bảng đã chốt trước khi chạy — có HAI vấn đề tách bạch, không phải một:**

1. **Nhiễu cường độ độc-lập-theo-pha gây hại** → đã sửa bằng E6b.
2. **Augmentation hình học mạnh làm tối ưu hoá bất ổn** → **chưa sửa**. `val_loss` chạm đáy ở epoch **10** (E6: 5, E4: 79). Fold 2 của E6b vẫn 0.6611, **thấp hơn E4** 0.6771 — toàn bộ mức tăng của E6b đến từ fold 1.

Từng lớp so với E4: nang **+0.155** · FNH **+0.099** · u máu +0.042 · ICC +0.006 · HCC −0.035 · di căn −0.042 · áp-xe −0.056.

⚠️ **Hai lớp yếu vẫn yếu** (ICC 0.455, di căn 0.444). Mức tăng của E6b đến từ các lớp vốn đã dễ. Với mục tiêu macro-F1 thì đây là giới hạn: không thể tới 0.80 nếu hai lớp này còn ở mức 0.45.

⚠️ **ECE xấu đi** (0.2212 → 0.2349).

`configs/e9_e6b_ema.yaml` = E6b + EMA, nhắm đúng vấn đề 2. ⚠️ **Đã bỏ** — gốc của nó (E6b) không đứng vững trên 5 fold.

### E6b đủ 5 fold — NULL, và fold 1 là ngoại lệ. E4 được giữ làm cấu hình gốc (2026-08-06, WORKLOG S-107)

Đủ 394 ca, cùng bệnh nhân cùng thứ tự với E4. Bootstrap ghép cặp 2000 lần:

| | hiệu (E6b − E4) | CI95 | P |
|---|---|---|---|
| macro-F1 | **−0.0022** | [−0.0423, +0.0363] | **0.92** |
| accuracy | −0.0052 | [−0.0431, +0.0330] | 0.75 |
| ECE | +0.0248 | [−0.0199, +0.0705] | 0.29 |

Gộp out-of-fold: E4 **0.6851** · E6b **0.6828**. Theo luật đã chốt trước khi chạy (CI chứa 0 thì giữ E4), **E4 là cấu hình gốc mang sang test-104.**

| fold | E4 | E6b | hiệu |
|---|---|---|---|
| 1 | 0.7001 | **0.7660** | **+0.066** |
| 2 | 0.6771 | 0.6611 | −0.016 |
| 3 | 0.7304 | 0.7311 | +0.001 |
| 4 | 0.6680 | 0.6262 | −0.042 |
| 5 | 0.6618 | 0.6151 | −0.047 |

**Bài học về quy trình, quan trọng hơn kết quả:** sàng 2 fold cho +0.038 và trông rất hứa hẹn; 5 fold cho −0.002. **Hai fold chỉ đủ để LOẠI một ý tưởng, không đủ để CHỌN nó.** Con số 0.7660 từng là cao nhất dự án có được — nó là một fold may mắn.

#### Phát hiện đáng giá nhất của E6b không phải về E6b

Độ phân tán giữa các fold tăng hơn gấp đôi: SD mẫu 0.0280 → **0.0661**, trải 0.069 → 0.151. Ghép với chẩn đoán ổn định thì có một quy luật rất mạnh **trên cả 10 lần train** (5 fold × 2 cấu hình):

> **Epoch mà `val_loss` chạm đáy dự báo gần trọn vẹn macro-F1 cuối cùng của fold đó.** Spearman ρ = **+0.770**, P = **0.0092**.

```
 E4 f4  đáy@ep   3  F1 0.6680      E6b f3  đáy@ep  64  F1 0.7311
E6b f5  đáy@ep   6  F1 0.6151       E4 f2  đáy@ep  79  F1 0.6771
E6b f2  đáy@ep  10  F1 0.6611       E4 f1  đáy@ep 100  F1 0.7001
E6b f4  đáy@ep  12  F1 0.6262      E6b f1  đáy@ep 158  F1 0.7660
 E4 f5  đáy@ep  14  F1 0.6618       E4 f3  đáy@ep 227  F1 0.7304
```

Nút thắt là **thời điểm bắt đầu overfit**, và nó đúng với **cả E4** chứ không riêng E6b: E4 fold 4 và 5 chạm đáy ở epoch 3 và 14, và đúng là hai fold yếu nhất của E4. Augmentation mạnh chỉ làm tệ hơn — trung vị epoch chạm đáy 79 → 12, khoảng cách train/val cuối +1.91 → +2.45.

⚠️ Tương quan trên 10 run, và hai đại lượng cùng sinh từ một đường cong train nên **không tách được nhân quả**. Đây là chẩn đoán tốt, không phải bằng chứng rằng chặn overfit sẽ nâng điểm. Nhưng nó là cơ sở định lượng để ưu tiên **E7 = E4 + EMA**.

#### Giả thuyết nhiễu cường độ: đúng một nửa, không đổi được kết quả

So với E6 trên 162 ca thì cả ICC lẫn di căn đều hồi. Nhưng so với **E4** trên 394 ca thì hai lớp yếu đi ngược nhau và triệt tiêu:

| lớp | n | E4 | E6b | hiệu |
|---|---|---|---|---|
| di căn | 40 | 0.488 | 0.415 | **−0.073** |
| ICC | 46 | 0.519 | 0.547 | +0.028 |
| áp-xe | 42 | 0.660 | 0.689 | +0.029 |
| FNH | 36 | 0.761 | 0.753 | −0.007 |
| nang | 42 | 0.762 | 0.800 | +0.038 |
| HCC | 125 | 0.776 | 0.749 | −0.027 |
| u máu | 63 | 0.831 | 0.826 | −0.004 |

Precision hai lớp yếu: ICC 0.466 → 0.483 (đúng hướng, không đáng kể) · di căn 0.476 → **0.405** (sai hướng). Hướng nhầm chính không suy chuyển: HCC → ICC 9 → 12 ca, HCC → di căn 15 → 14 ca. **Nút thắt không nhúc nhích.**

⚠️ Calibration xấu đi nhất quán: ECE 0.2030 → 0.2344, NLL 2.03 → 2.35. Chưa có ý nghĩa thống kê (P=0.29) nhưng cùng chiều với kết quả trên 162 ca. Với dự án lấy calibration làm đóng góp headline, đây là thêm một lý do không chọn E6b.

Điểm sáng duy nhất, đo trên **cùng fold 2–5**: thiên lệch chọn epoch E4 +0.0787 so với E6b +0.0608. Không đủ để bù.

### TTA lật — ÂM, và nó đo được một thứ quan trọng hơn (2026-08-07, WORKLOG S-108)

TTA lật trên 5 checkpoint E4, 8 tổ hợp, 394 ca (notebook đã xoá ở S-176). Lượt 0 là ảnh gốc nên có đối chứng miễn phí — và nó dựng lại đúng macro-F1 lưu trong checkpoint tới 5 chữ số thập phân ở cả 5 fold, tức đường chạy đã được chứng minh đúng.

| | hiệu (TTA − gốc) | CI95 | P |
|---|---|---|---|
| macro-F1 | −0.0150 | [−0.0347, +0.0038] | 0.148 |
| accuracy | −0.0126 | [−0.0305, +0.0051] | 0.123 |
| **NLL** | **−0.2067** | [−0.2964, −0.1208] | **<0.0001** |

Gộp out-of-fold: gốc 0.6851 · TTA 0.6702. **4/5 fold âm.** Bản chỉ lật trong mặt phẳng (4 lượt, bỏ trục z) không cứu được: −0.0133 [−0.0280, −0.0003] **P=0.048**, tức âm *có ý nghĩa thống kê*.

#### Vì sao TTA thất bại: model không bất biến với chính augmentation của nó

| lượt | macro-F1 | so với gốc | đồng thuận với gốc |
|---|---|---|---|
| gốc | 0.6851 | — | 1.000 |
| lật y | 0.6618 | −0.023 | 0.944 |
| lật x | 0.6462 | −0.039 | 0.944 |
| lật z | 0.6456 | −0.040 | 0.878 |
| lật x+y+z | 0.6265 | −0.059 | 0.878 |

`RandomFlip` lật **từng trục độc lập với p=0.5** (`src/data/transforms.py`), nên trong lúc train cả 8 tổ hợp đều xuất hiện, mỗi cái xác suất 1/8 — phân bố train **đối xứng hoàn toàn** với phép lật. Model vẫn mất 0.02–0.06 khi bị lật.

> **Model học thuộc hướng của ảnh thay vì học đặc trưng bất biến với hướng, dù chính augmentation của nó dạy điều ngược lại.**

Đây là bằng chứng thứ ba, độc lập, cho cùng một câu chuyện overfit — và là cái **sạch nhất** trong ba, vì nó đo ở một checkpoint cố định, không dính gì tới chuyện chọn epoch:

1. epoch `val_loss` chạm đáy tương quan ρ=0.77 với macro-F1 cuối (S-107)
2. chênh `best` so với `last` +0.079 (S-078)
3. **không bất biến với phép lật** (mục này)

⚠️ **Phép kiểm nên chạy sau E7 (EMA), chốt trước:** nếu EMA thật sự chữa được overfit thì độ hụt khi lật (hiện 0.023–0.059) **phải co lại**. Đây là phép kiểm EMA độc lập với macro-F1, nói được EMA có tác dụng hay không kể cả khi điểm số đứng yên.

#### Chỗ TTA có ích, và vì sao vẫn không dùng

Sau hiệu chỉnh nhiệt độ leave-one-fold-out: ECE **0.1534 → 0.1131**, tự tin 0.745 → 0.738. Lợi thế này **sống sót** qua temperature scaling, khác với trường hợp focal loss ở E5.

Nhưng nó phải trả bằng macro-F1, mà macro-F1 mới là thứ so được với văn liệu; còn phần defer thì `−epistemic` của TTA (AURC 0.1901) vẫn thua MC-dropout (0.1689). Cộng thêm 8 lần chi phí suy luận. **Kết luận: không đưa TTA vào cấu hình khoá cho test-104.**

⚠️ Một cái bẫy đo được ở đây: điểm xếp hạng "tỉ lệ đồng thuận giữa 8 lượt" cho F1@80% = 0.7115 trông đẹp nhưng AURC 0.2606, **tệ hơn hẳn** max-prob (P=0.011). Tám lượt chỉ sinh 9 giá trị rời rạc nên rất nhiều ca đồng hạng. **Đừng chọn điểm xếp hạng bằng một con số coverage đơn lẻ.**

### ⚠️ Lỗi augmentation phát hiện 2026-08-07: ~100% mẫu train có dải đệm 0, val thì không (WORKLOG S-111)

Chưa chạy thí nghiệm nào để đo tác động, nhưng đây là **lỗi đúng nghĩa**, không phải lựa chọn thiết kế, và nó tồn tại suốt E0 → E6b.

Hai nguồn đệm 0, cả hai áp gần như mọi mẫu train:

| | hành vi | xác suất áp |
|---|---|---|
| `RandomTranslate3D` | dịch rồi **đệm 0** vào phần trống | ~100% (shift ngẫu nhiên trên 3 trục) |
| `RandomRotateSmall` | xoay rồi lấp góc bằng 0 (`cval=0.0`) | `rotate_prob` mặc định **1.0** |

Val không augment nên **không** có dải nào. Đây là lệch phân bố train/val có hệ thống ở **mọi bước huấn luyện**, và nó khớp với chẩn đoán overfit đã đo (ρ = +0.770 giữa epoch chạm đáy `val_loss` và macro-F1 cuối, S-107).

**Đối chiếu bên ngoài:** baseline official và CGHNet đều cache rộng hơn rồi **cắt ngẫu nhiên** (official resize 128² cắt 112²; CGHNet 16×128×128 → 14×112×112) nên không có đệm. Ablation CGHNet Bảng 4: **bỏ random-crop mất 8.8 điểm**, biến augmentation nặng nhất trong bảng của họ. Biên độ của ta cũng yếu hơn: ±8/112 = 7.1% trong mặt phẳng so với 12.5% của họ.

**E12 sửa nó:** cache lưới **136×136×40** (`configs/preprocess_e12.yaml`), train cắt ngẫu nhiên 112×112×32, val cắt giữa (`configs/e12_randomcrop.yaml`, khác baseline đúng 3 khoá khoa học).

Hai chi tiết đo được, cần cho ai định chỉnh lại tham số:

1. **Lề phải là 12, không phải 8.** Xoay 10° trên khối 136 làm hỏng góc tới ~12 voxel; với lề 8 thì cắt giữa vẫn dính 20 voxel bị lấp.
2. **Bắt buộc `rotate_mode: nearest`.** Với `constant`, cắt *giữa* thì sạch nhưng cắt *ngẫu nhiên* ở offset biên để lọt **517** voxel bị lấp 0; `nearest` cho **0** ở mọi offset. Lỗi này suýt lọt vì cắt giữa nhìn qua có vẻ ổn.

**Tính chất quan trọng để so sánh:** `spacing` vẫn suy từ `target_size` 112×112×32 chứ không từ lưới 136×136×40, nên độ phân giải vật lý y hệt E4 và **cắt giữa cache E12 cho ra đúng khối mà cache E4 tạo ra**. Val hai bên so trực tiếp được ⇒ E12 so E4 chỉ khác một biến là augmentation lúc train.

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

### Lưu trữ: Grad-CAM 4 ca demo — kết quả thật (2026-08-05, WORKLOG S-098)

Đây là kết quả lịch sử; module và notebook Grad-CAM đã được gỡ khỏi cây hoạt động ở S-132. Mỗi ca trong phép đo cũ dùng model của fold chứa nó ở val. Demo hiện dùng heatmap `|input × gradient|` đa thì trên crop E4.

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

MC-dropout K=20 lượt/ca trên chính model của từng fold (notebook đã xoá ở S-176) (nên mọi thành viên đều mù với val của nó). Đọc bằng `python -m src.eval.trust --run-dir runs/E4_per_phase_results --members`.

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
| Tiền xử lý (chạy 1 lần, cache) | `python -m src.preprocess.build_cache --config configs/preprocess.yaml` | sẵn sàng; **cần điền `axis_order` trước**. `crop_mode` chọn `fixed_mm` (cache v0) hay `lesion_tight` (cắt bám tổn thương, dùng mask ở `lld/labels`) — đổi giá trị này là **đổi dữ liệu**, phải build sang thư mục cache khác. `crop_margin_voxels` thêm lề dư quanh lưới (E12) |
| **⚠️ Build LẠI cache E4** (một lần, ~26 phút, **CPU**) | `python -m src.preprocess.build_cache --config configs/preprocess_e4.yaml` | Mọi notebook dùng cache E4 đã bị xoá (S-168 và S-176). Cache E4 giờ **chỉ còn web app** dùng, cho phần heatmap và cho dự đoán ca demo — mà cả hai đều đã được chốt gỡ. Nếu không khôi phục notebook nào từ git history thì lệnh này gần như không còn cần; giữ lại vì `runs/E4_per_phase_results` vẫn là mốc đối chứng đã đo trên test-104. Cách nhanh nhất trên Kaggle: sao `notebooks/18_build_cache_cghnet.ipynb` (wrapper mỏng, **Accelerator = None**) và đổi config sang `preprocess_e4.yaml` |
| Train baseline 3D-patch (1 fold) | `python -m src.train.run --config configs/baseline_3dpatch.yaml --fold 1` | sẵn sàng (W2 ngày 5); resume tự động từ `last.pt`; cần `LLDMMRI_CACHE_DIR` trỏ tới cache |
| **Train một fold, config bất kỳ** | `python -m src.train.run --config configs/e5_focal.yaml --fold 1` | sẵn sàng (W4); `configs/e5_focal.yaml` = baseline + focal loss, khác đúng khối `loss:` |
| **EMA** | `configs/e7_ema.yaml` (`train.ema_decay: 0.999`) | mặc định TẮT ở baseline. Khi bật, **mọi số trong `train_log.csv`/`metrics_best.json`/`val_probs_*.npz` là của model EMA** |
| **Build cache CGHNet** (một lần, ~20 phút, **CPU**) | `notebooks/18_build_cache_cghnet.ipynb` trên Kaggle, **Accelerator = None** | sẵn sàng (2026-08-10), **chưa chạy**. Lưới **128×128×16** (`configs/preprocess_cghnet.yaml`: `target_size [112,112,14]` + lề `[8,8,1]`), đúng hình học của bài CGHNet. ~2,0 GB, nhỏ hơn cache E4. ⚠️ **z=14 nên KHÔNG dùng được cho config DenseNet121** (cần ≥32 mọi chiều, S-063); `tests/test_models.py` chặn cả hai chiều |
| **UniFormer-Base** | `notebooks/23_uniformer_base.ipynb` trên Kaggle, **bật Internet** | sẵn sàng (2026-08-14), **chưa chạy**. `configs/uniformer_base.yaml` khác `uniformer_s.yaml` **đúng hai khoá** (`model.variant`, `output_dir`) — thí nghiệm MỘT biến, đóng chỗ lệch đã ghi so với recipe gốc (họ dùng `base`, ta chọn `small` vì HF chỉ có file trọng số của small). ⚠️ Hai chỗ lệch của file: **k600 thay k400**, **32x4 thay 16x8** — nạp được vì không tham số nào phụ thuộc số frame, nhưng phải ghi vào báo cáo. ⚠️⚠️ **Cổng C bắt buộc**: depth stage 3 đi từ 8 lên 20 block trên 2744 token, ước lượng thô **13–16 h/fold** ⇒ vượt trần session 12h. `resume: true` xử lý được (2 session/fold) — **đừng suy giờ từ GFLOPs**, đọc `s/epoch` thật |
| **UniFormerV2-B/16 + CLIP→K710** | `notebooks/24_uniformerv2.ipynb` trên Kaggle, **bật Internet** | sẵn sàng (2026-08-14), **chưa chạy**. `src/models/uniformerv2.py` + `configs/uniformerv2_b16.yaml`. ⚠️ Trọng số là **`k400+k710_uniformerv2_b16_8x224.pyth`** (458 MB) từ mirror HuggingFace `Andy1621/uniformerv2`. Bản **K710 thuần** mà MODEL_ZOO chỉ định thì **không còn tồn tại** — toàn bộ bucket Aliyun của họ trả 404 (kiểm 2026-08-14). Chuỗi pretrain vì thế là CLIP → K710 → **K400**, tức đặc trưng đã chuyên biệt hoá thêm một bước; **chỗ lệch này phải vào báo cáo**. ⚠️⚠️ **THÍ NGHIỆM NHIỀU BIẾN**: đổi cùng lúc kiến trúc (ViT phẳng), nguồn pretrain (CLIP), lớp vào (khởi tạo lại cho 8 kênh), và lưới token (49/lát so với 196 lúc pretrain vì crop 112 chứ không 224). Thắng thì **không quy kết được**; thua thì gần như không học được gì. ⚠️ **Cổng A đối chiếu tập khoá HAI CHIỀU** — chiều "checkpoint dư so với model" bắt được lỗi thiếu hẳn một module, thứ các notebook khác không có. Nó vẫn **không** phủ được lỗi nối dây |
| **⭐ SDR-Former (Siamese đa pha)** | `notebooks/25_sdrformer.ipynb` trên Kaggle, **KHÔNG cần Internet** | sẵn sàng (2026-08-17), **chưa chạy**. `src/models/sdrformer.py` + `configs/sdrformer.yaml`. Dùng **lại cache CGHNet** — §4.2 của bài (resize 16×128×128, crop 14×112×112) khớp chính xác, không build cache mới. ⭐ **Đổi trục THỨ BA mà dự án chưa từng thử: cách 8 pha được KẾT HỢP.** Mọi thí nghiệm cho tới nay là image-level fusion (8 pha = 8 kênh); đây là Siamese + APSM. Bảng 1 của họ đo đúng trục đó **một biến trên sáu backbone**, 6/6 đều dương, +0.022…+0.052 (xem §5). ⚠️⚠️ **Train FROM SCRATCH** — bỏ pretrained, tức bỏ đòn bẩy duy nhất từng thắng có ý nghĩa thống kê (+0.130). Thua thì **không kết luận được** "fusion vô ích": phép so gộp hai biến. ⚠️ Bản tái lập **~12.7M so với 19.34M** của bài (Bảng 4) — cố ý giữ literal theo Hình 2, xem cổng A. ⚠️ **Sáu cổng A–F**; cổng F là mới và riêng của kiến trúc này: kiểm encoder **thật sự dùng chung trọng số** giữa 8 pha (8 encoder riêng vẫn chạy, vẫn hội tụ, không có gì báo) |
| **⭐ Intra-class mixup trên UniFormer** | `notebooks/21_intra_mixup.ipynb` trên Kaggle, **bật Internet** | sẵn sàng (2026-08-13), **chưa chạy**. `configs/uniformer_s_intra_mixup.yaml` khác `uniformer_s.yaml` **đúng hai khoá khoa học** (`data.intra_class_mixup: 1.0`, `data.intra_class_mixup_exclude_majority: true`) — khoá bởi `tests/test_intra_class_mixup.py`. Đây là **mảnh cuối còn thiếu** của recipe hạng 2 (S-128). Notebook sinh **từ** notebook 20 nên năm cổng A–E giống hệt, cộng **cổng F** kiểm phép trộn: giải ngược λ từ voxel và đọc file gốc bằng `np.load` độc lập với dataset, kiểm đối tác cùng lớp, kiểm tập val **không** bị trộn. ⚠️ Chạy **1 fold trước** (fold 1, để so ghép cặp với fold 1 của `uniformer_s`); 6.5h/fold, đọc đĩa gấp đôi đã nằm trong số của cổng C |
| **⭐ UniFormer-S + Kinetics — CẤU HÌNH CHÍNH** | `notebooks/20_uniformer.ipynb` trên Kaggle, **bật Internet** | ✅ **đã chạy đủ 5 fold** (S-169) → out-of-fold **0.8147**, hơn E4 **+0.130** P<0.001. Kết quả ở `runs/Uniformer3D`. Dùng **lại cache CGHNet** (`--img_size 16 128 128 --crop_size 14 112 112` của họ khớp chính xác), không build cache mới. Tự tải `uniformer_small_k400_16x8.pth` (~200 MB) từ `Sense-X/uniformer_video`. **Năm cổng A–E chạy trước khi cam kết fold nào** — xem §5. ⚠️ Cổng C bắt buộc: `patch_embed1` stride `(1,2,2)` không hạ mẫu trục lát nên stage 3 có 2744 token so với 1568 của bản pretrained, **đắt hơn** CGHNet. Quá 60 s/epoch thì đặt `patch_embed1_stride: [2,2,2]` |
| Đánh giá (CPU, không cần GPU) | `python -m src.eval.run --run-dir artifacts/runs/baseline_3dpatch` | sẵn sàng (W3); đọc `val_probs_*.npz` đã lưu → bảng metric ± CI bootstrap + gộp out-of-fold |
| **So hai cấu hình, có ghép cặp** (CPU) | `python -m src.eval.compare --baseline runs/E4_cv_results --candidate runs/E8` | sẵn sàng (2026-08-10). Bootstrap **trên hiệu**, cùng bệnh nhân, phân tầng theo lớp. Chỉ dùng fold có ở **cả hai** bên; nổ nếu tập bệnh nhân hoặc nhãn lệch. Thay cho việc so hai CI riêng lẻ — cách đó bỏ mất phần phương sai triệt tiêu và cho phép kiểm yếu hơn thực tế |
| **⭐ Chẩn đoán lớp yếu** (CPU, vài giây) | `python -m src.eval.weak_classes --run-dir runs/E4_cv_results --compare runs/E6b --build-log runs/E4_per_phase_results/fold_1/cache_build_log.csv` | sẵn sàng (2026-08-10). Sáu phân tích trên xác suất đã lưu, **không cần GPU**. Nó **LOẠI bảy hướng chữa** hiển nhiên (trọng số lớp, logit adjustment, ngưỡng theo lớp, focal mạnh hơn, thêm augmentation, gộp với biến thể gần, cắt sát hơn) — đọc trước khi đề xuất bất cứ cách nâng macro-F1 nào. Chi tiết ở §5 |
| **E14 / CGHNet + mixup** | `configs/e14_mixup.yaml` · `configs/cghnet_mixup.yaml` | sẵn sàng (2026-08-10), **chưa chạy**. Mỗi cái khác base **đúng ba khoá**: `data.mixup_alpha 0.2`, `loss.label_smoothing 0.05`, `output_dir`. Hai can thiệp duy nhất còn khớp chẩn đoán. ⚠️ `train_loss` khi bật mixup là loss **trên nhãn đã trộn**, không so trực tiếp với run cũ; `val_loss` thì so được |
| **Bảng trustworthiness** (CPU) | `python -m src.eval.trust --run-dir runs/E4_cv_results` | sẵn sàng (W3); calibration + selective từ cùng các `.npz`. Temperature fit **leave-one-fold-out**, không fit gộp — xem docstring module |
| Bảng trên + bất định epistemic | `python -m src.eval.trust --run-dir runs/E4_cv_results --members` | sẵn sàng (W3); cần `fold*/mc_dropout.npz` đã sinh sẵn trong `runs/`. Notebook sinh ra chúng đã xoá ở S-176 — muốn sinh mới thì khôi phục từ git history. ⚠️ Và nó **vô nghĩa** trên cấu hình chính: `head_dropout: 0.0` nên không có lớp Dropout nào |
| **Test-104 — chạm lần 1 (ĐÃ DÙNG)** | *(notebook đã xoá ở S-176)* | hồ sơ lần chạm 2026-08-07 (S-110), cấu hình E4, `--pin-set e4`. Kết quả còn nguyên ở `runs/test104/`; đọc lại bằng `src.eval.test_report` |
| **🔒 Test-104 — chạm lần 2** (GPU, ~2 phút) | `notebooks/22_test104_uniformer.ipynb` trên Kaggle | sẵn sàng (2026-08-14, WORKLOG S-170), **chưa chạy**. UniFormer ensemble 5 fold, `--pin-set uniformer`. Protocol khoá ở `docs/TEST104_PREREGISTRATION.md` **§B**, phải **commit + push trước** khi chạy — notebook clone từ GitHub và cổng 0 kiểm bằng `git log`. Bốn cổng: §B đã commit · hình học cache khớp `preprocess_cghnet.yaml` · sha256 khớp bộ ghim · không checkpoint trùng. Checkpoint được nhận diện bằng **sha256**, không bằng đường dẫn — bố cục Dataset thế nào cũng được, kể cả phẳng và đặt tên tuỳ ý. Cổng B băm mọi `.pt` đã mount, đối chiếu bộ ghim, rồi dựng cây chuẩn bằng symlink cho `test_once`. **Đo latency** và in ngay — lần chạm 1 đã bỏ lỡ và không truy lại được (S-116) |
| **Đọc số test-104 lần 2** (CPU, chạy lại được) | `python -m src.eval.test_report --run-dir runs/test104_uniformer --oof-dir runs/Uniformer3D` | ⚠️ `--oof-dir` phải là run out-of-fold của **chính** cấu hình đó — `T` fit ở đó rồi áp mù lên test. Trỏ nhầm là sai **im lặng** |
| **Đọc số test-104** (CPU, chạy lại được) | `python -m src.eval.test_report --run-dir runs/test104` | sẵn sàng; đọc từ `test_probs.npz` nên **không** thành lần chạm thứ hai. `T` lấy từ out-of-fold, không fit trên test |
| Cài backend web app (một lần / máy) | `pip install -r webapp/backend/requirements.txt` | sẵn sàng; **tách hẳn** khỏi `requirements.txt` train, không kéo torch/monai |
| Cài frontend web app (một lần / máy) | `cd webapp/frontend && npm install` | sẵn sàng |
| **Chạy web app** — backend | `python -m uvicorn webapp.backend.main:app --reload` | sẵn sàng; cổng 8000. Ảnh thật từ `LLDMMRI_SAMPLE_DIR`; **số thật** từ `LLDMMRI_PREDICTIONS_DIR` (mặc định `runs/E4_per_phase_results`) — 394 ca out-of-fold, `provenance.source = oof`. Ca ngoài 394 đó rơi về `simulated` |
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
