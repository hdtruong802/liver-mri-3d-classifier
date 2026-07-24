# `splits/` — Official LLD-MMRI split (đã tái lập) · KHOÁ, BẤT BIẾN

> **Research Use Only.** Đây là **danh sách chia tập official 316/78/104** của LLD-MMRI2023, đã tái lập và verify.
> **KHÔNG sửa/sinh lại các file này.** Quality gate chặn mọi thay đổi trong `splits/` (đặt `ALLOW_SPLIT_CHANGE=1` mới qua được — chỉ dùng cho lần tạo đầu). Nguyên tắc: AGENTS.md §3.6.

## File

| File | Nội dung | Số dòng |
|---|---|---|
| `labels_trainval.txt` | 394 bệnh nhân train+val official | 394 |
| `train_fold{1..5}.txt` · `val_fold{1..5}.txt` | 5-fold CV official trên 394 train+val | ~312 / ~82 mỗi fold |
| `test_official.txt` | **104 bệnh nhân test — held-out KHOÁ KÍN, chạm đúng 1 lần** (AGENTS.md §3.4) | 104 |

**Định dạng mỗi dòng:** `<patient_id> <class_index>` (whitespace-separated, tương thích baseline `mp_liver_dataset.py`).
**Class index** (theo `Category_info` trong `LLD_MMRI_Annotation.json`): 0 u máu · 1 ICC · 2 áp-xe · 3 di căn · 4 nang · 5 FNH · 6 HCC.

## Nguồn & cách tái lập (2026-07-24)

Bản dữ liệu thực nhận (`wanglab/LLD-MMRI-MedSAM2`) **không kèm file split**. Tái lập như sau:

1. `labels_trainval.txt` + `train_fold*/val_fold*` lấy từ repo đội thi **[ZHEGG/miccai2023](https://github.com/ZHEGG/miccai2023)** (`data/trainval_labels/`) — nhãn train+val official mà đội thi công khai.
2. `test_official.txt` = **498 bệnh nhân (trong `LLD_MMRI_Annotation.json`) − 394 train+val**.
3. ID map theo **chữ số** (annotation có 16/498 key dạng `MR-xxxxxx` có gạch nối, còn lại `MRxxxxxx`; label dùng `MRxxxxxx`). Ở đây lưu theo **key annotation** để khớp trực tiếp dữ liệu.
4. Class ở đây lấy từ **`Category_info`** (annotation, gold standard). Đã kiểm chéo với class của ZHEGG: **0 mismatch**.

## Verify (khớp PDF challenge official 100%)

| Lớp | test tái lập | PDF official | trainval tái lập | PDF official |
|---|---|---|---|---|
| HCC | 32 | 32 ✓ | 125 | 125 ✓ |
| U máu | 16 | 16 ✓ | 63 | 63 ✓ |
| ICC | 12 | 12 ✓ | 46 | 46 ✓ |
| Áp-xe | 12 | 12 ✓ | 42 | 42 ✓ |
| Di căn | 11 | 11 ✓ | 40 | 40 ✓ |
| Nang | 11 | 11 ✓ | 42 | 42 ✓ |
| FNH | 10 | 10 ✓ | 36 | 36 ✓ |
| **Tổng** | **104** | **104 ✓** | **394** | **394 ✓** |

`trainval ∩ test = ∅` · `trainval ∪ test = 498`. Khớp 7/7 lớp ⇒ đúng official split.

## Dùng

- **Chọn model:** 5-fold CV trên 394 train+val (`train_fold{i}`/`val_fold{i}`).
- **test-104:** chỉ chạm **một lần** sau khi khoá protocol/model/threshold (ghi WORKLOG trước — AGENTS.md §3.4 / §10).
- Reader map `patient_id` → key annotation → đường dẫn ảnh bằng **chuẩn hoá chữ số**.
- Vì là official split ⇒ **so benchmark trực tiếp được** với SOTA trên test-104.
