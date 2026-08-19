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
| `README.md` | **Điểm vào của repo**: kết quả chốt, cách cài, cách tái lập | Mọi tool, ghi WORKLOG |
| `AGENTS.md` | **Nguồn sự thật** ngữ cảnh dự án | Bất kỳ tool nào, nhưng phải ghi WORKLOG |
| `CLAUDE.md` | Cầu nối → import AGENTS.md | Chỉ khi thêm quy tắc *riêng Claude Code* |
| `.cursor/rules/00-project-context.mdc` | Cầu nối → AGENTS.md | Chỉ khi thêm quy tắc *riêng Cursor* |
| `WORKLOG.md` | Nhật ký bàn giao giữa các tool, **append-only** | Mọi tool, chỉ được **thêm** |
| `docs/MRI_Classification_Spec_Sheet.md` | Chốt kỹ thuật (khoa học) | Người dùng duyệt; agent đề xuất diff |
| `docs/liver_mri_3d_classification_plan.md` | Kế hoạch & lộ trình | Người dùng duyệt; agent đề xuất diff |
| `docs/plan.md` | Kế hoạch chi tiết W2–W6 (triển khai Plan thành task/tuần) | Mọi tool, ghi WORKLOG |
| `docs/W2_plan.md` | Plan làm việc chi tiết Tuần 2 (task theo ngày) | Mọi tool, ghi WORKLOG |
| `docs/EXPERIMENT_ARCHIVE.md` | **Hồ sơ** thí nghiệm đã bị thay thế / đã dừng. Không phải căn cứ | Chỉ thêm, không sửa mục cũ |
| `docs/TEST104_PREREGISTRATION.md` | Protocol khoá TRƯỚC mỗi lần chạm tập test | Người dùng duyệt |
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
4. **Test-104 là held-out khoá kín.** Mỗi lượt chạm cần: xin phép người dùng, một pre-registration **commit trước khi chạy** (`docs/TEST104_PREREGISTRATION.md`), và một entry WORKLOG. **Tình trạng hiện tại: đã chạm HAI lần hợp lệ** — §A (E4, 2026-08-07) và §B (UniFormer, 2026-08-14). Lượt tiếp theo cần §C mới.
   ⛔ Có một lượt chạy **KHÔNG hợp lệ** trên `runs/Uniformer3D-mixup/test104/` (`prereg_commit: "(bỏ qua kiểm git)"`). Nó **không được tính** và số của nó **không được dùng ở bất kỳ đâu** — xem đính chính ở §5.
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
├── README.md                    # điểm vào: kết quả chốt, cài đặt, tái lập, RUO
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
│   ├── W2_plan.md               # plan làm việc chi tiết Tuần 2
│   ├── TEST104_PREREGISTRATION.md   # protocol khoá trước mỗi lần chạm test
│   └── EXPERIMENT_ARCHIVE.md    # hồ sơ thí nghiệm đã bị thay thế (S-197)
├── configs/                     # YAML hyperparam (mọi run 1 file)
├── splits/                      # file fold đã khoá — COMMIT, bất biến
├── src/
│   ├── data/                    # dataset, transform MONAI, loader
│   ├── preprocess/              # N4, resample, registration, ROI-crop
│   ├── models/                  # backbone 3D + các biến thể fusion
│   ├── train/                   # vòng train, checkpoint/resume
│   ├── eval/                    # metric, calibration, selective, thống kê
│   └── utils/                   # seed.py, io, logging
├── tests/                       # trong đó có test chống leakage
├── notebooks/                   # notebook Kaggle (đã strip output)
├── webapp/
│   ├── README.md                # cách chạy, biến môi trường, ràng buộc dữ liệu
│   ├── DESIGN.md                # thị giác của WEB APP ("bàn đọc tối")
│   ├── backend/                 # FastAPI — requirements.txt RIÊNG, không có torch
│   └── frontend/                # React + Vite + Tailwind + TS (node_modules/, dist/ gitignore)
├── slides/                      # HTML slide
├── reports/                     # FINAL_REPORT.docx + báo cáo tuần + hình
├── scripts/
│   ├── quality-gate.sh          # gate cho Bash thật
│   └── quality-gate.ps1         # gate cho Windows PowerShell, không cần WSL
├── artifacts/                   # checkpoint, log, hình — GITIGNORE
├── runs/                        # kết quả train + xác suất đã lưu — GITIGNORE
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

> 📁 *Bảng SDR-Former: fusion Siamese so image-level, 6/6 backbone dương* — chuyển sang [`docs/EXPERIMENT_ARCHIVE.md`](docs/EXPERIMENT_ARCHIVE.md) ở S-197.

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

> 📁 *TEST-104 lần chạm 1 (E4/DenseNet, 2026-08-07) — hồ sơ đầy đủ* — chuyển sang [`docs/EXPERIMENT_ARCHIVE.md`](docs/EXPERIMENT_ARCHIVE.md) ở S-197.

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

> 📁 *Ensemble E4 ⊕ CGHNet — kết luận đã bị 5 fold bác bỏ* — chuyển sang [`docs/EXPERIMENT_ARCHIVE.md`](docs/EXPERIMENT_ARCHIVE.md) ở S-197.

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

> 📁 *UniFormer fold 1 = 0.8111 — đã bị bản 5 fold thay* — chuyển sang [`docs/EXPERIMENT_ARCHIVE.md`](docs/EXPERIMENT_ARCHIVE.md) ở S-197.

> 📁 *UniFormer: thiết kế, ngân sách, và các chỗ lệch so với recipe gốc* — chuyển sang [`docs/EXPERIMENT_ARCHIVE.md`](docs/EXPERIMENT_ARCHIVE.md) ở S-197.

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
train. Chỉ những can thiệp đổi được **biểu diễn** mới khớp — và trong toàn dự án đúng một
can thiệp làm được: đổi nguồn khởi tạo trọng số (`uniformer_s`, +0.130 P<0.001). Hai config
mixup chéo lớp từng được dựng cho chẩn đoán này (`e14_mixup`, `cghnet_mixup`) chưa bao giờ
chạy fold nào và đã gỡ ở S-197.

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

### 📉 KẾT QUẢ ÂM — bảng tổng hợp (đọc trước khi đề xuất lại một hướng đã thử)

Tất cả dùng **bootstrap ghép cặp trên hiệu**, cùng bệnh nhân. Chi tiết từng thí nghiệm ở
[`docs/EXPERIMENT_ARCHIVE.md`](docs/EXPERIMENT_ARCHIVE.md).

| thí nghiệm | tập đánh giá | hiệu macro-F1 | CI95 | P |
|---|---|---|---|---|
| E5 · focal loss γ=2 | 2 fold, 162 ca | −0.029 | [−0.105, +0.048] | 0.47 |
| E6 · augmentation mạnh hơn | 2 fold, 162 ca | −0.014 | [−0.078, +0.052] | 0.68 |
| E6b · bỏ nhiễu cường độ theo pha | 5 fold, 394 ca | −0.002 | [−0.042, +0.036] | 0.92 |
| TTA lật | 5 fold, 394 ca | −0.015 | [−0.035, +0.004] | 0.15 |
| CGHNet (tái lập) | 5 fold, 394 ca | −0.019 | [−0.068, +0.031] | 0.46 |
| gộp E4 ⊕ CGHNet | 5 fold, 394 ca | −0.010 | [−0.039, +0.018] | 0.47 |
| **`uniformer_s_intra_mixup`** | **5 fold, 394 ca** | **−0.011** (0.8038 so 0.8147) | — | — |

Gộp UniFormer với E4 cũng **tệ đi ở mọi trọng số** đã quét (0.7349 khi chia đều → 0.8129 ở
w=0.9), đều dưới 0.8147 của UniFormer một mình.

⚠️ **Ba bài học đi kèm, quan trọng hơn bản thân các con số trên:**

1. **Một phép sàng cỡ nhỏ chỉ đủ để LOẠI, không đủ để CHỌN.** E6b cho +0.038 ở 2 fold rồi
   −0.002 ở 5 fold; ensemble E4⊕CGHNet cho +0.065 ở 1 fold rồi −0.010 ở 5 fold.
2. **Focal loss không cần thiết vì một lý do cụ thể:** lợi thế ECE thô của nó (0.154 so
   0.221) **biến mất sau hiệu chỉnh** (0.1255 so 0.1281) — tức qua đúng bước pipeline vốn đã
   làm.
3. **Trùng lặp lỗi thấp KHÔNG bảo đảm ensemble ăn.** UniFormer so E4 chỉ trùng 61% lỗi
   (kỳ vọng 30% nếu độc lập) và oracle 0.901, vậy mà trung bình xác suất không lấy được điểm
   nào trong 8.6 điểm dư địa đó. Muốn khai thác thì cần bộ phối hợp **học được**.

#### 🔴 ĐÍNH CHÍNH — `uniformer_s_intra_mixup` ĐÃ CHẠY, và nó ÂM

Bản trước của §5 và §6 ghi cấu hình này là *"chưa chạy fold nào"*. **Sai.** `runs/Uniformer3D-mixup/`
có đủ 5 fold **và** một lượt test-104:

| | out-of-fold (394) | test-104 |
|---|---|---|
| `uniformer_s` (cấu hình chính) | **0.8147** | **0.7682** |
| `uniformer_s_intra_mixup` | 0.8038 | 0.7488 |

⛔ **Lượt test-104 đó KHÔNG hợp lệ và không được dùng làm kết quả.**
`runs/Uniformer3D-mixup/test104/test_run_meta.json` ghi `prereg_commit: "(bỏ qua kiểm git)"`
— nó chạy **không có pre-registration**, trái §3.4 và §10. Vì vậy nó **không** xuất hiện
trong `reports/FINAL_REPORT.docx`, và **không** được tính là một lần chạm hợp lệ khi đếm.

Code (`data.intra_class_mixup` ở `src/data/dataset.py`), config và notebook 21 đều **giữ
nguyên** — kết quả âm là kết quả, và xoá dấu vết một thí nghiệm đã chạy là làm hỏng hồ sơ.

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

> 📁 Bốn mục nữa đã chuyển sang [`docs/EXPERIMENT_ARCHIVE.md`](docs/EXPERIMENT_ARCHIVE.md)
> ở S-197: **E5 focal loss** (2 fold) · **Grad-CAM 4 ca demo** (module đã gỡ) ·
> **Trustworthiness E4** (calibration & selective đầu tiên) · **MC-dropout & phép lai**.

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
| **Build cache CGHNet** (một lần, ~20 phút, **CPU**) | `notebooks/18_build_cache_cghnet.ipynb` trên Kaggle, **Accelerator = None** | sẵn sàng (2026-08-10), **chưa chạy**. Lưới **128×128×16** (`configs/preprocess_cghnet.yaml`: `target_size [112,112,14]` + lề `[8,8,1]`), đúng hình học của bài CGHNet. ~2,0 GB, nhỏ hơn cache E4. ⚠️ **z=14 nên KHÔNG dùng được cho config DenseNet121** (cần ≥32 mọi chiều, S-063); `tests/test_models.py` chặn cả hai chiều |
| **Intra-class mixup trên UniFormer** | `notebooks/21_intra_mixup.ipynb` trên Kaggle, **bật Internet** | ✅ **đã chạy đủ 5 fold** → out-of-fold **0.8038**, tức **THẤP HƠN** 0.8147 của `uniformer_s`. Kết quả âm, không dùng làm cấu hình chính và không có trong báo cáo cuối. `configs/uniformer_s_intra_mixup.yaml` khác `uniformer_s.yaml` **đúng hai khoá khoa học** (`data.intra_class_mixup`, `data.intra_class_mixup_exclude_majority`) — khoá bởi `tests/test_intra_class_mixup.py`. ⛔ `runs/Uniformer3D-mixup/test104/` là một lượt chạm test-104 **KHÔNG có pre-registration** (`prereg_commit: "(bỏ qua kiểm git)"`) — số của nó không hợp lệ, xem đính chính ở §5 |
| **⭐ UniFormer-S + Kinetics — CẤU HÌNH CHÍNH** | `notebooks/20_uniformer.ipynb` trên Kaggle, **bật Internet** | ✅ **đã chạy đủ 5 fold** (S-169) → out-of-fold **0.8147**, hơn E4 **+0.130** P<0.001. Kết quả ở `runs/Uniformer3D`. Dùng **lại cache CGHNet** (`--img_size 16 128 128 --crop_size 14 112 112` của họ khớp chính xác), không build cache mới. Tự tải `uniformer_small_k400_16x8.pth` (~200 MB) từ `Sense-X/uniformer_video`. **Năm cổng A–E chạy trước khi cam kết fold nào** — xem §5. ⚠️ Cổng C bắt buộc: `patch_embed1` stride `(1,2,2)` không hạ mẫu trục lát nên stage 3 có 2744 token so với 1568 của bản pretrained, **đắt hơn** CGHNet. Quá 60 s/epoch thì đặt `patch_embed1_stride: [2,2,2]` |
| Đánh giá (CPU, không cần GPU) | `python -m src.eval.run --run-dir artifacts/runs/baseline_3dpatch` | sẵn sàng (W3); đọc `val_probs_*.npz` đã lưu → bảng metric ± CI bootstrap + gộp out-of-fold |
| **So hai cấu hình, có ghép cặp** (CPU) | `python -m src.eval.compare --baseline runs/E4_cv_results --candidate runs/E8` | sẵn sàng (2026-08-10). Bootstrap **trên hiệu**, cùng bệnh nhân, phân tầng theo lớp. Chỉ dùng fold có ở **cả hai** bên; nổ nếu tập bệnh nhân hoặc nhãn lệch. Thay cho việc so hai CI riêng lẻ — cách đó bỏ mất phần phương sai triệt tiêu và cho phép kiểm yếu hơn thực tế |
| **⭐ Chẩn đoán lớp yếu** (CPU, vài giây) | `python -m src.eval.weak_classes --run-dir runs/E4_cv_results --compare runs/E6b --build-log runs/E4_per_phase_results/fold_1/cache_build_log.csv` | sẵn sàng (2026-08-10). Sáu phân tích trên xác suất đã lưu, **không cần GPU**. Nó **LOẠI bảy hướng chữa** hiển nhiên (trọng số lớp, logit adjustment, ngưỡng theo lớp, focal mạnh hơn, thêm augmentation, gộp với biến thể gần, cắt sát hơn) — đọc trước khi đề xuất bất cứ cách nâng macro-F1 nào. Chi tiết ở §5 |
| **Bảng trustworthiness** (CPU) | `python -m src.eval.trust --run-dir runs/E4_cv_results` | sẵn sàng (W3); calibration + selective từ cùng các `.npz`. Temperature fit **leave-one-fold-out**, không fit gộp — xem docstring module |
| Bảng trên + bất định epistemic | `python -m src.eval.trust --run-dir runs/E4_cv_results --members` | sẵn sàng (W3); cần `fold*/mc_dropout.npz` đã sinh sẵn trong `runs/`. Notebook sinh ra chúng đã xoá ở S-176 — muốn sinh mới thì khôi phục từ git history. ⚠️ Và nó **vô nghĩa** trên cấu hình chính: `head_dropout: 0.0` nên không có lớp Dropout nào |
| **Test-104 — chạm lần 1 (ĐÃ DÙNG)** | *(notebook đã xoá ở S-176)* | hồ sơ lần chạm 2026-08-07 (S-110), cấu hình E4, `--pin-set e4`. Kết quả còn nguyên ở `runs/test104/`; đọc lại bằng `src.eval.test_report` |
| **🔒 Test-104 — chạm lần 2** (GPU, ~2 phút) | `notebooks/22_test104_uniformer.ipynb` trên Kaggle | sẵn sàng (2026-08-14, WORKLOG S-170), **chưa chạy**. UniFormer ensemble 5 fold, `--pin-set uniformer`. Protocol khoá ở `docs/TEST104_PREREGISTRATION.md` **§B**, phải **commit + push trước** khi chạy — notebook clone từ GitHub và cổng 0 kiểm bằng `git log`. Bốn cổng: §B đã commit · hình học cache khớp `preprocess_cghnet.yaml` · sha256 khớp bộ ghim · không checkpoint trùng. Checkpoint được nhận diện bằng **sha256**, không bằng đường dẫn — bố cục Dataset thế nào cũng được, kể cả phẳng và đặt tên tuỳ ý. Cổng B băm mọi `.pt` đã mount, đối chiếu bộ ghim, rồi dựng cây chuẩn bằng symlink cho `test_once`. **Đo latency** và in ngay — lần chạm 1 đã bỏ lỡ và không truy lại được (S-116) |
| **Đọc số test-104 lần 2** (CPU, chạy lại được) | `python -m src.eval.test_report --run-dir runs/test104_uniformer --oof-dir runs/Uniformer3D` | ⚠️ `--oof-dir` phải là run out-of-fold của **chính** cấu hình đó — `T` fit ở đó rồi áp mù lên test. Trỏ nhầm là sai **im lặng** |
| **Đọc số test-104** (CPU, chạy lại được) | `python -m src.eval.test_report --run-dir runs/test104` | sẵn sàng; đọc từ `test_probs.npz` nên **không** thành lần chạm thứ hai. `T` lấy từ out-of-fold, không fit trên test |
| Cài backend web app (một lần / máy) | `pip install -r webapp/backend/requirements.txt` | sẵn sàng; **tách hẳn** khỏi `requirements.txt` train, không kéo torch/monai |
| Cài frontend web app (một lần / máy) | `cd webapp/frontend && npm install` | sẵn sàng |
| **Chạy web app** — backend | `python -m uvicorn webapp.backend.main:app --reload` | sẵn sàng; cổng 8000. Chỉ còn **một luồng**: thả ZIP → kiểm contract 8 MRI + 8 mask → suy luận ensemble UniFormer-S ngay trên máy chủ. Trọng số lấy từ `LLDMMRI_LIVE_WEIGHTS_DIR` (mặc định `runs/Uniformer3D`); `runs/` bị gitignore nên máy mới clone về sẽ báo `model_loaded: false` cho tới khi trỏ đúng. ⚠️ Đường **ca demo dựng sẵn** và **heatmap** đã gỡ ở S-197 — cả hai cần artefact ngoài repo, và thư mục heatmap đã không tồn tại từ lâu |
| **Chạy web app** — frontend | `cd webapp/frontend && npm run dev` | sẵn sàng; proxy `/api` sang 8000. Mở **`http://localhost:5173`** — trên Windows Vite bind vào `::1`, nên `127.0.0.1:5173` **không** vào được |
| Build frontend | `cd webapp/frontend && npm run build` · `npm run typecheck` | sẵn sàng |
| Test | `pytest -q` | sẵn sàng (113 test; 8 test cần torch/monai sẽ tự skip nếu chưa cài) |
| Lint | `ruff check src tests` · `ruff format src tests` | sẵn sàng (W2 ngày 1) |
| **Kết xuất báo cáo ra PDF** | `python scripts/md2pdf.py reports/W2_REPORT.md` | sẵn sàng; Markdown → HTML → Chrome/Edge headless. Không cần pandoc hay LaTeX. `--keep-html` để soi bản trung gian |
| **Dựng DOCX báo cáo kết thúc dự án** | `python scripts/make_final_report_docx.py --force` | sẵn sàng (2026-08-18, WORKLOG S-196). Sinh `reports/FINAL_REPORT.docx` — **bản ĐẦY ĐỦ**, không phải khung rỗng: 7 mục (Background → Reference), 21 bảng đã điền số, 4 hình đã nhúng, 13 tham khảo. ⚠️ **Mọi con số là hằng số chép tay trong `CONTENT`**, không tính lại lúc chạy — đối chiếu bằng `src.eval.test_report`/`trust`/`compare` trước khi sửa ô nào, kẻo drift. ⚠️ **Chạy đè xoá mọi chỉnh sửa làm trực tiếp trong Word** — script từ chối ghi đè trừ khi truyền `--force`. Cần `pip install python-docx` (cố ý **không** nằm trong `requirements.txt`: công cụ soạn deliverable ở máy local, môi trường train Kaggle không cần) |
| **Vẽ 3 hình cho báo cáo cuối** | `python scripts/make_final_report_figures.py` | sẵn sàng (2026-08-18, WORKLOG S-196). CPU, vài giây. Đọc `runs/Uniformer3D/test/test_probs.npz` → `reports/assets/fig-{reliability,risk-coverage,confusion}.png`. **Không phải lượt chạm test-104 mới** (chỉ đọc xác suất đã lưu). Gọi thẳng `src.eval.calibration` và `src.eval.selective` nên hình và bảng chắc chắn cùng một phép tính. ⚠️ ECE trong báo cáo là bản **adaptive** (chia theo số ca) = 0.0833; cột trong hình chia đều nên hình in cả hai số — đừng "sửa" cho khớp một số |

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
