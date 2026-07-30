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
  2. **Web app demo tự code full-stack** — FastAPI backend + frontend thuần. **KHÔNG Streamlit, KHÔNG Gradio.**
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
| `DESIGN.md` | Thế giới thị giác & design system | *(chưa tạo — xuất hiện khi chạy `/impeccable shape`, KHÔNG phải từ `init`)* |
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
8. **Web app: FastAPI + frontend tự code.** Ai đề xuất Streamlit/Gradio/bất kỳ framework demo dựng sẵn nào → từ chối.
9. **Không làm segmentation.** Bài toán là classification.
10. **Không commit dữ liệu bệnh nhân, checkpoint, hay file NIfTI/DICOM.** Xem `.gitignore`.

---

## 4. Cấu trúc thư mục

> **Trạng thái hiện tại:** repo mới, chưa có code. Phần khung ngữ cảnh/workflow đã có; các thư mục code là **đích đến đã chốt** — tool nào tạo thư mục đầu tiên thì theo đúng cây này, không tự đặt tên khác.

```
liver-mri-3d-classifier/
├── AGENTS.md                    # ← nguồn sự thật (file này)
├── CLAUDE.md                    # cầu nối cho Claude Code (@AGENTS.md)
├── WORKLOG.md                   # nhật ký bàn giao, append-only
├── README.md                    # mô tả public + RUO disclaimer          [chưa có]
├── PRODUCT.md                   # Impeccable init sinh ra                [chưa có]
├── DESIGN.md                    # Impeccable init sinh ra — ràng buộc UI [chưa có]
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
│   ├── backend/                 # FastAPI
│   └── frontend/                # HTML/CSS/JS thuần (+ vendor/ nếu cần lib)
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
| Frontend | HTML + CSS + JS thuần | `<canvas>` slice-viewer; Chart.js hoặc SVG thuần |
| Slide / Report | HTML tĩnh | không phụ thuộc build tool nặng |
| Compute | **Kaggle Notebook** (train) · local (web app, slide) | Kaggle KHÔNG dùng để host API |

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
| Đánh giá (CPU, không cần GPU) | `python -m src.eval.run --run-dir artifacts/runs/baseline_3dpatch` | sẵn sàng (W3); đọc `val_probs_*.npz` đã lưu → bảng metric ± CI bootstrap + gộp out-of-fold |
| Test (chạm 1 lần!) | `python -m src.eval.run --ckpt <path> --split test --i-know-this-is-final` | chưa có |
| Chạy web app | `uvicorn webapp.backend.main:app --reload` | chưa có |
| Test | `pytest -q` | sẵn sàng (113 test; 8 test cần torch/monai sẽ tự skip nếu chưa cài) |
| Lint | `ruff check src tests` · `ruff format src tests` | sẵn sàng (W2 ngày 1) |

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
- **Frontend:** không kéo framework nặng. Vanilla JS, module ES6, CSS có biến. Chi tiết thẩm mỹ sẽ do `DESIGN.md` quy định (bước 4 của thiết lập).
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

Ba thứ có mặt người dùng — **web app** (`webapp/`), **HTML slide** (`slides/`), **HTML report** (`reports/`) — phải nhìn như một hệ thống.

**Bắt buộc, với mọi tool, kể cả tool không có `/impeccable`:**

1. **Đọc [`PRODUCT.md`](PRODUCT.md) trước khi viết dòng UI đầu tiên** — đặc biệt mục *Product Principles*, *Brand Commitments*, *Evidence on Hand*, *Accessibility & Inclusion*. Đây là ràng buộc, không phải gợi ý. Khi [`DESIGN.md`](DESIGN.md) đã tồn tại thì đọc cả nó. *(DESIGN.md xuất hiện lần đầu khi chạy `/impeccable shape`, không phải từ `init` — xem `docs/MULTI_TOOL_WORKFLOW.md` §7.1.)*
2. **Giọng: công cụ y tế nghiêm túc.** Không gradient rực rỡ, không hiệu ứng khoe kỹ thuật, không micro-interaction vui vẻ. Người dùng là bác sĩ chẩn đoán hình ảnh và người review nghiên cứu.
3. **Số liệu là nhân vật chính.** Xác suất, mức bất định và cờ `defer` phải nổi bật nhất trên màn hình. Không hiệu ứng nào được cạnh tranh với chúng.
4. **Màu chỉ mang thông tin, không trang trí.** Thông tin **không bao giờ** chỉ mã hoá bằng màu — luôn kèm nhãn chữ hoặc hình dạng (yêu cầu a11y, và bác sĩ mù màu là chuyện có thật).
5. **RUO hiển thị trên mọi màn hình có kết quả**, ở vị trí không thể bỏ sót.
6. **Không trình bày kết quả như chẩn đoán chắc chắn.** Mức bất định là nội dung hạng nhất, không phải chú thích nhỏ.
7. **Motion chỉ để giải thích chuyển trạng thái.** Tôn trọng `prefers-reduced-motion`.
8. **Trước khi chốt bất kỳ deliverable UI nào:** chạy quality gate phù hợp với shell (Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-gate.ps1`; Bash thật: `sh scripts/quality-gate.sh`) để dùng detector Impeccable cho cả 4 tool.

**Việc dựng UI mới nên giao cho Claude Code / Codex / Cursor** (có `/impeccable shape` và `critique`). Antigravity nên nhận backend, xử lý dữ liệu, sửa lỗi logic — lý do ở `docs/MULTI_TOOL_WORKFLOW.md` §9.3.

---

*Cập nhật lần cuối: 2026-07-24 · Mọi thay đổi file này phải kèm một entry trong `WORKLOG.md`.*
