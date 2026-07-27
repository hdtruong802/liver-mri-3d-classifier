# Quy trình Kaggle — chạy code repo trên Kaggle & xuất output dùng lại

> **Vấn đề:** dữ liệu LLD-MMRI là **~83.7GB** trên Kaggle (`marcohoang/lldmmridataset`, private).
> Máy local không có data. Tải về là bất khả thi/không cần thiết.
> **Giải pháp:** code sống trong git, chạy trên Kaggle, **output nặng đẩy ngược lên Kaggle Dataset có version** để mọi notebook/phiên sau chỉ mount, không tính lại.

Nguyên tắc nền: AGENTS.md §7 (ràng buộc Kaggle) · §4 (notebook chỉ là lớp mỏng gọi `src/`).

---

## 0. Bức tranh tổng thể

```
   GitHub repo (code, splits/)          Kaggle Dataset (data thô 83.7GB)
              │                                      │
              └──────────────┬───────────────────────┘
                             ▼
                   Kaggle Notebook (GPU/CPU)
                   - clone repo → sys.path
                   - mount data thô (read-only)
                   - chạy src/... 
                             │
                             ▼
                   /kaggle/working/  (ổ ghi DUY NHẤT)
                             │
                             ▼
        Kaggle Dataset mới, có version  ← output tái dùng
        (manifest, cache tiền xử lý, checkpoint)
```

**Ba thứ KHÔNG BAO GIỜ vào git:** data bệnh nhân, cache tiền xử lý, checkpoint. Chúng đi đường Kaggle Dataset. Xem `.gitignore`.

---

## 1. Chuẩn bị một lần

### 1.1. Kaggle API token (đã có trên máy này)

Token nằm ở `~/.kaggle/kaggle.json` (đã cấu hình). Nếu máy mới:
Kaggle → Settings → API → *Create New Token* → lưu vào `~/.kaggle/kaggle.json`.

```bash
pip install kaggle
python -m kaggle datasets list -m      # kiểm tra token hoạt động
```

> `kaggle.json` **đã nằm trong `.gitignore`** — không bao giờ commit.

### 1.2. Repo phải public (hoặc dùng token) để notebook clone được

Repo hiện tại: `https://github.com/hdtruong802/liver-mri-3d-classifier` (public) → clone thẳng được, không cần secret.

---

## 2. Chạy code repo trên Kaggle Notebook

### 2.1. Tạo notebook

Kaggle → *Create* → *New Notebook*. Rồi:

1. **Add Input** → *Datasets* → tìm `lldmmridataset` → Add.
   Data xuất hiện ở `/kaggle/input/datasets/marcohoang/lldmmridataset/`
   *(Kaggle có lúc mount thành `/kaggle/input/lldmmridataset/` — sơ đồ thay đổi tuỳ lúc,
   nên **đừng hardcode**; `resolve_data_root()` tự dò theo `data_root_candidates` trong
   `configs/data.yaml` và chỉ nhận đường dẫn thật sự chứa annotation).*
2. **Settings** → *Internet* → **On** (cần để `git clone`).
   *(Nếu phải tắt internet — xem §5 phương án offline.)*
3. **Settings** → *Accelerator* → `None` cho EDA (tiết kiệm quota GPU), `GPU` khi train.

### 2.2. Cell bootstrap (dán vào cell đầu tiên)

```python
# 1. Lấy code từ GitHub
!git clone -q https://github.com/hdtruong802/liver-mri-3d-classifier.git /kaggle/working/repo

import sys
sys.path.insert(0, "/kaggle/working/repo")

# 2. Dependency thiếu trên Kaggle (đa số đã có sẵn)
!pip install -q nibabel SimpleITK

# 3. Data root: KHÔNG hardcode. resolve_data_root() dò các ứng viên trong
#    configs/data.yaml và chỉ nhận đường dẫn thật sự chứa annotation.
from src.utils.io import load_yaml, resolve_data_root
from src.data.splits import Splits

CONFIG = load_yaml("/kaggle/working/repo/configs/data.yaml")
DATA_ROOT = resolve_data_root(CONFIG)
print("data root:", DATA_ROOT)

Splits("/kaggle/working/repo/splits").validate()
print("OK: code + splits đã sẵn sàng")
```

> Mount ở chỗ khác hai ứng viên mặc định? Chạy `!ls /kaggle/input` để xem đường dẫn
> thật, rồi hoặc đặt `os.environ["LLDMMRI_DATA_ROOT"] = "<path>"`, hoặc thêm vào
> `data_root_candidates` trong `configs/data.yaml` (cách này bền hơn — commit là xong).

**Cập nhật code giữa chừng?** Chạy lại cell bootstrap sau khi `git pull`:
```python
!cd /kaggle/working/repo && git pull -q
import importlib, src; importlib.reload(src)   # hoặc Restart & Run All cho chắc
```

### 2.3. Chạy việc thật

```python
# EDA (không cần ảnh, chỉ annotation)
from src.data.annotation import Annotation
from src.data.eda import class_distribution, format_class_distribution

ann = Annotation(DATA_ROOT / CONFIG["annotation_rel"])   # DATA_ROOT từ cell bootstrap
print(format_class_distribution(class_distribution(ann)))
```

Xem `notebooks/01_eda.ipynb` — notebook EDA đầy đủ, đã viết sẵn theo T2.1 (bao gồm **gate geometry bắt buộc**).

---

## 3. Xuất output để dùng lại (phần quan trọng nhất)

Mọi thứ ghi vào `/kaggle/working/` sẽ được lưu khi notebook *Save Version*. Nhưng
**để phiên sau dùng lại mà không chạy lại**, phải biến nó thành **Kaggle Dataset**.

### 3.1. Cách A — "New Dataset từ notebook output" (đơn giản nhất)

1. Notebook chạy xong → **Save Version** (*Save & Run All*).
2. Version chạy xong → tab **Output** → **Create Dataset** (hoặc *New Dataset*).
3. Đặt tên rõ ràng, vd `lldmmri-cache-v1`.
4. Notebook sau: **Add Input** → dataset vừa tạo → mount ở `/kaggle/input/lldmmri-cache-v1/`.

### 3.2. Cách B — đẩy bằng Kaggle API ngay trong notebook (chủ động version)

```python
import json, os, subprocess

OUT = "/kaggle/working/cache"          # thư mục chứa output cần xuất
SLUG = "lldmmri-cache"                 # slug dataset (không dấu, không hoa)
USER = "marcohoang"

# metadata bắt buộc
os.makedirs(OUT, exist_ok=True)
json.dump(
    {"title": "LLD-MMRI preprocessed cache", "id": f"{USER}/{SLUG}", "licenses": [{"name": "other"}]},
    open(f"{OUT}/dataset-metadata.json", "w"),
)

# lần đầu: create ; các lần sau: version
subprocess.run(["kaggle", "datasets", "create", "-p", OUT, "--dir-mode", "zip"])
# subprocess.run(["kaggle","datasets","version","-p",OUT,"-m","them N4","--dir-mode","zip"])
```

> ⚠️ **License CC BY-NC-ND** của LLD-MMRI: dataset output là **bản phái sinh** →
> để **Private**, không public. Repro pack (W6) chỉ chia code + split IDs + config,
> không kèm ảnh/cache. Xem `docs/W2_plan.md §0`.

### 3.3. Đặt tên version cho tái lập

Mỗi lần đẩy, ghi lại **slug + version number** vào `configs/preprocess.yaml` (comment)
và WORKLOG. Không có dòng đó thì 3 tuần sau không ai biết checkpoint train bằng cache nào.

---

## 4. Tải data về local (nếu thật sự cần)

Không khuyến khích (83.7GB), nhưng nếu cần vài file để debug:

```bash
# Chỉ một file (vd annotation 18MB — đủ cho phần lớn EDA)
python -m kaggle datasets download marcohoang/lldmmridataset \
    -f "lld/LLD_MMRI_Annotation.json" -p ./data --force

# Vài ảnh mẫu cho gate geometry
python -m kaggle datasets download marcohoang/lldmmridataset \
    -f "lld/images/MR-391135_1_C+A_0000.nii.gz" -p ./data/images --force

# Toàn bộ (83.7GB — cân nhắc kỹ)
python -m kaggle datasets download marcohoang/lldmmridataset -p ./data --unzip
```

Rồi trỏ env:
```bash
export LLDMMRI_DATA_ROOT="$PWD/data"          # bash
$env:LLDMMRI_DATA_ROOT = "$PWD\data"          # PowerShell
```

> `data/` đã gitignore (neo `/data/` — xem WORKLOG S-023).

---

## 5. Phương án offline (khi Internet phải tắt)

Một số chế độ Kaggle (đặc biệt khi submit competition) không cho internet →
`git clone` và `pip install` đều fail. Khi đó:

1. Đóng gói repo thành Kaggle Dataset: `kaggle datasets create -p <repo_dir>`
   (loại `.git`, `data/`, `artifacts/`).
2. Notebook **Add Input** dataset đó, rồi:
   ```python
   import sys; sys.path.insert(0, "/kaggle/input/liver-mri-repo")
   ```
3. Dependency: pin sẵn trong `requirements.txt`, cài từ Kaggle Dataset chứa wheel,
   hoặc dùng bản có sẵn trong image Kaggle. **Không tải runtime** (AGENTS.md §7).

Nhược điểm: phải đẩy lại dataset mỗi lần đổi code → chỉ dùng khi buộc phải offline.

---

## 6. Checklist trước khi rời một phiên Kaggle

- [ ] Output cần dùng lại đã thành **Kaggle Dataset có version** (không chỉ nằm trong `/kaggle/working`).
- [ ] Slug + version đã ghi vào config/WORKLOG.
- [ ] Dataset phái sinh để **Private** (license CC BY-NC-ND).
- [ ] Code thay đổi đã **push lên GitHub** (notebook clone từ đó, không phải nguồn sự thật).
- [ ] Không có checkpoint/ảnh nào lọt vào git (`git status` sạch).

---

## 7. Ràng buộc phải nhớ (AGENTS.md §7)

| Ràng buộc | Hệ quả khi viết code |
|---|---|
| Session ≤ 12h, ngắt bất cứ lúc nào | checkpoint + resume **mỗi epoch**; log CSV flush từng dòng (`src/utils/logging.py`) |
| Ổ ghi duy nhất = `/kaggle/working` | mọi path ghi đi qua config/env, không hardcode |
| VRAM ~16GB | AMP + gradient accumulation + gradient checkpointing |
| Không tiền xử lý lại mỗi session | cache 1 lần → Kaggle Dataset versioned |
| Kaggle **không phải server** | không chạy FastAPI ở đó; web app chạy local (W6) |
