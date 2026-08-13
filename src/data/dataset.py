"""Dataset đọc cache đã tiền xử lý — đầu vào trực tiếp cho vòng train.

Bản trước đọc thẳng 8 volume thô rồi `np.stack`. Cách đó **không dùng được**: 8 pha
có lưới voxel khác nhau (pha động 512²×88, T2WI 512²×24, DWI 256²×24 — WORKLOG S-029)
nên `np.stack` sẽ ném lỗi shape. Việc đưa 8 pha về cùng lưới thuộc về
`src/preprocess/build_cache.py`; module này chỉ đọc kết quả đó.

Nhãn và danh sách bệnh nhân lấy từ `splits/` đã khoá — không tự sinh (AGENTS.md §3.6).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from src.data.splits import Splits
from src.utils.ids import normalize_pid
from src.utils.io import resolve_repo_path


class CachedLesionDataset:
    """Đọc các patch đã tiền xử lý; trả về dict dùng được cho vòng train.

    Trả về ``{"image": tensor[8, X, Y, Z] float32, "label": int, "patient_id": str}``.
    `torch` được import **lười** để module vẫn nạp được khi chưa cài deep-learning stack.

    ## `intra_class_mixup` — nội suy hai ca **cùng chẩn đoán**

    Khác hẳn `data.mixup_alpha` (cài ở `src/train/loop.py`). Bảng so:

    | | `mixup_alpha` ở vòng train | `intra_class_mixup` ở đây |
    |---|---|---|
    | trộn với | ca **bất kỳ** trong cùng batch | ca **cùng lớp**, bốc từ **toàn tập train** |
    | nhãn | trộn ``λ·y + (1−λ)·y'`` | **giữ nguyên** |
    | λ | ``Beta(α, α)`` với α nhỏ ⇒ lệch về hai đầu | ``Beta(1, 1)`` = đều trên (0, 1) |
    | phạm vi | mọi lớp | bỏ lớp đa số, chỉ 6 lớp thiểu số |

    Vì phải bốc một ca cùng lớp từ **toàn tập train**, phép này không cài được ở tầng
    `run_epoch` — batch chỉ có 4 mẫu nên phần lớn batch không chứa hai ca cùng một lớp
    hiếm. Nó buộc phải nằm ở dataset.

    **Vì sao nó ăn khớp với `data.sampling` khác `instance`:** lấy mẫu lại *có hoàn lại*
    sinh ra **bản sao y hệt** của ca hiếm, nên một epoch có thể thấy cùng một file 5–6
    lần với đúng cùng nội dung. Nội suy trong cùng lớp biến mỗi bản sao đó thành một
    điểm mới trên đoạn thẳng nối hai ca thật ⇒ phép lấy mẫu lại **thêm thông tin** thay
    vì chỉ nhân bản.

    ⚠️ Ba tính chất phải biết trước khi đọc kết quả:

    1. **Nhãn không trộn**, nên `train_loss` vẫn so trực tiếp được với run không mixup —
       khác `data.mixup_alpha`, thứ làm `train_loss` mất nghĩa so sánh.
    2. **Ca đối tác có thể là chính nó** (pool gồm cả `index`), khi đó phép trộn là đồng
       nhất bất kể λ. Xác suất ``1/n_c``, tức 2–3% ở các lớp hiếm. Giữ như vậy để phân bố
       đúng "bốc đều trong lớp", không phải một chỗ cần sửa.
    3. **Đọc đĩa gấp đôi** cho mọi mẫu đủ điều kiện. Với cache ~8 MB/ca thì đây là chi phí
       thật, phải đo `s/epoch` chứ không suy đoán.
    """

    def __init__(
        self,
        cache_dir: str | Path,
        samples: Sequence[tuple[str, int]],
        transform: Any | None = None,
        *,
        intra_class_mixup: float = 0.0,
        intra_class_mixup_exclude_majority: bool = True,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.transform = transform
        self.samples: list[tuple[Path, int, str]] = []

        missing: list[str] = []
        for patient_id, label in samples:
            path = self._find_file(patient_id)
            if path is None:
                missing.append(patient_id)
            else:
                self.samples.append((path, int(label), patient_id))

        if missing:
            raise FileNotFoundError(
                f"thiếu {len(missing)}/{len(samples)} file cache trong {self.cache_dir} "
                f"(vd {missing[:3]}). Chạy `python -m src.preprocess.build_cache` trước."
            )

        self.intra_class_mixup = float(intra_class_mixup)
        if self.intra_class_mixup < 0:
            raise ValueError(f"intra_class_mixup phải >= 0, nhận {self.intra_class_mixup}")

        # Chỉ dựng chỉ mục khi thật sự bật, để dataset val không mang theo state vô dụng.
        self.class_pools: dict[int, list[int]] = {}
        self.mixup_excluded_class: int | None = None
        if self.intra_class_mixup > 0:
            for index, (_, label, _) in enumerate(self.samples):
                self.class_pools.setdefault(label, []).append(index)
            if intra_class_mixup_exclude_majority:
                # Suy từ nhãn train của chính fold này, không ghi cứng số lớp: cách đó
                # vẫn đúng nếu split đổi, và nó **tự khai** ra lớp nào bị loại (thuộc
                # tính này được cổng kiểm in ra) thay vì ẩn trong một hằng số.
                self.mixup_excluded_class = max(
                    self.class_pools, key=lambda c: (len(self.class_pools[c]), -c)
                )

    @property
    def mixup_classes(self) -> list[int]:
        """Các lớp thật sự được trộn — rỗng khi tắt."""
        return sorted(c for c in self.class_pools if c != self.mixup_excluded_class)

    def _find_file(self, patient_id: str) -> Path | None:
        """Tìm file cache; khớp cả khi ID viết có/không gạch nối."""
        direct = self.cache_dir / f"{patient_id}.npz"
        if direct.exists():
            return direct
        key = normalize_pid(patient_id)
        for candidate in self.cache_dir.glob("*.npz"):
            if normalize_pid(candidate.stem) == key:
                return candidate
        return None

    def __len__(self) -> int:
        return len(self.samples)

    @staticmethod
    def _load_image(path: Path) -> Any:
        with np.load(path) as data:
            return np.asarray(data["image"], dtype=np.float32)

    def _mix(self, image: Any, index: int, label: int) -> tuple[Any, float, str | None]:
        """Nội suy với một ca cùng lớp. Trả ``(ảnh, λ, id_ca_đối_tác)``.

        RNG đi qua `torch` chứ không `random`/`np.random`, vì hàm này chạy **trong worker
        của DataLoader**: PyTorch gieo lại RNG của `torch` riêng cho từng worker, còn
        `numpy` thì **không** — dùng `np.random` ở đây sẽ cho 4 worker sinh cùng một dãy
        số, tức λ và ca đối tác lặp theo chu kỳ. Cùng lý do như `src/data/transforms.py`.
        """
        import torch

        if self.intra_class_mixup <= 0 or label == self.mixup_excluded_class:
            return image, 1.0, None

        pool = self.class_pools.get(label, ())
        if not pool:
            return image, 1.0, None

        alpha = self.intra_class_mixup
        other_index = pool[int(torch.randint(len(pool), (1,)).item())]
        other_path, _, other_id = self.samples[other_index]
        other = self._load_image(other_path)
        if other.shape != image.shape:
            raise ValueError(
                f"không trộn được: {self.samples[index][2]} có shape {image.shape} còn "
                f"{other_id} có {other.shape}. Hai file cùng cache phải cùng lưới — dấu hiệu "
                f"{self.cache_dir} bị trộn từ hai lần build khác hình học."
            )

        lam = float(torch.distributions.Beta(alpha, alpha).sample())
        return lam * image + (1.0 - lam) * other, lam, other_id

    def __getitem__(self, index: int) -> dict[str, Any]:
        import torch

        path, label, patient_id = self.samples[index]
        image = self._load_image(path)
        image, lam, mixed_with = self._mix(image, index, label)

        item: dict[str, Any] = {
            "image": torch.from_numpy(np.ascontiguousarray(image)),
            "label": label,
            "patient_id": patient_id,
        }
        if self.intra_class_mixup > 0:
            # ⚠️ Điều kiện là `intra_class_mixup > 0`, **không phải** `mixed_with is not None`.
            # `default_collate` gom batch theo khoá của phần tử đầu và nổ nếu phần tử khác
            # thiếu khoá đó. Một batch train bình thường chứa cả ca thuộc lớp bị loại (không
            # trộn) và ca thuộc lớp hiếm (có trộn), nên thêm khoá có điều kiện là lỗi nổ ngẫu
            # nhiên theo thành phần batch — loại lỗi chỉ xuất hiện sau vài chục bước.
            # Không trộn thì λ = 1 và đối tác là chính nó, đúng nghĩa "ảnh giữ nguyên".
            item["mixup_lambda"] = lam
            item["mixup_partner"] = mixed_with if mixed_with is not None else patient_id
        if self.transform is not None:
            item = self.transform(item)
        return item


def find_label_mismatches(dataset: CachedLesionDataset) -> list[tuple[str, int, int]]:
    """Đối chiếu nhãn trong file cache với nhãn trong `splits/`.

    Vì sao cần: `CachedLesionDataset` lấy nhãn từ **split** và bỏ qua nhãn lưu trong
    ``.npz``. Nếu lúc build cache ID bị lệch (ví dụ ghi nhầm file của bệnh nhân khác),
    model sẽ train trên nhãn sai mà **không có dấu hiệu nào** — loss vẫn giảm, metric
    vẫn ra số, chỉ là toàn bộ kết quả vô nghĩa. Đây là kiểm tra rẻ (đọc mỗi mảng nhãn,
    không đọc ảnh) cho một lỗi cực đắt.

    Trả về danh sách ``(patient_id, nhãn_theo_split, nhãn_trong_cache)`` — rỗng là tốt.
    """
    mismatches: list[tuple[str, int, int]] = []
    for path, split_label, patient_id in dataset.samples:
        with np.load(path) as data:
            if "label" not in data:
                continue
            cached_label = int(data["label"])
        if cached_label != split_label:
            mismatches.append((patient_id, split_label, cached_label))
    return mismatches


def build_fold_datasets(
    cache_dir: str | Path,
    fold_index: int,
    splits_dir: str | Path = "splits",
    train_transform: Any | None = None,
    val_transform: Any | None = None,
    intra_class_mixup: float = 0.0,
    intra_class_mixup_exclude_majority: bool = True,
) -> tuple[CachedLesionDataset, CachedLesionDataset]:
    """Dựng cặp (train, val) cho một fold của CV chính thức.

    `fold_index` đếm từ 1 (khớp tên file `train_fold1.txt`). Split đã khoá và đã có
    test chống leakage ở `tests/test_no_leakage.py`.

    `splits_dir` tương đối được hiểu theo **gốc repo**, không phải CWD — xem
    `resolve_repo_path`.

    ⚠️ `intra_class_mixup` **chỉ** truyền cho dataset train. Cho val ăn ảnh đã trộn thì
    mọi con số báo cáo thành vô nghĩa mà không có dấu hiệu gì — cùng lý do
    `src/train/loop.py` chốt `mixup = 0` khi không train thay vì tin người gọi. Chốt ở
    đây, không để chỗ gọi quyết định.
    """
    splits = Splits(resolve_repo_path(splits_dir))
    if not 1 <= fold_index <= len(splits.folds):
        raise ValueError(f"fold_index phải trong 1..{len(splits.folds)}, nhận {fold_index}")

    fold = splits.folds[fold_index - 1]
    return (
        CachedLesionDataset(
            cache_dir,
            fold.train,
            train_transform,
            intra_class_mixup=intra_class_mixup,
            intra_class_mixup_exclude_majority=intra_class_mixup_exclude_majority,
        ),
        CachedLesionDataset(cache_dir, fold.val, val_transform),
    )


def build_test_dataset(
    cache_dir: str | Path,
    splits_dir: str | Path = "splits",
    transform: Any | None = None,
) -> CachedLesionDataset:
    """Dựng dataset cho **test-104 official**.

    ⚠️ Held-out khoá kín, **chạm đúng một lần** sau khi đã khoá protocol/model/threshold.
    Phải ghi WORKLOG trước khi dùng (AGENTS.md §3.4 và §10).
    """
    return CachedLesionDataset(cache_dir, Splits(resolve_repo_path(splits_dir)).test, transform)
