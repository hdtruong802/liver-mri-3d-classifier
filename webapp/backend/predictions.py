"""Nạp dự đoán out-of-fold THẬT từ `.npz`, không cần torch, không cần GPU.

## Vì sao không chạy model trong backend

Backend bị ràng buộc **không kéo theo torch/monai** (AGENTS.md §4, và
`webapp/backend/requirements.txt` nói rõ điều đó). Nhưng ta không cần: 394 dự đoán
out-of-fold đã được tính và lưu sẵn thành `val_probs_best.npz`, cùng với bất định
epistemic ở `mc_dropout.npz`. Đây là **số đo được thật**, không phải mô phỏng — mỗi ca
được chấm bởi đúng model chưa từng thấy nó khi train.

Đánh đổi, phải nói rõ: app **chỉ tra cứu được 394 bệnh nhân đó**. Ảnh mới tải lên
không suy luận được. Đó là giới hạn thật của bản demo, và `PRODUCT.md` đã chọn hướng
"ca demo dựng sẵn là đường đi chính" từ trước vì một lý do độc lập (pipeline cắt bám
tổn thương nên cần ROI, ảnh thô chưa đủ).

## Ba đại lượng, ba nguồn khác nhau — đừng gộp

Kết quả đo ở WORKLOG S-087 buộc phải tách ba đường:

1. **Lớp dự đoán** ← `argmax` của model tất định. MC-dropout hạ macro-F1 0.6851 → 0.5852
   nên **không** dùng trung bình MC làm dự đoán.
2. **Xác suất hiển thị** ← model tất định, đã temperature scaling. Model thô tự tin quá
   mức nghiêm trọng (trung bình 0.889 khi accuracy 0.703, trung vị 0.987), nên đưa số
   thô lên màn hình là nói dối người đọc.
3. **Xếp hạng / ngưỡng defer** ← **epistemic** của MC-dropout, KHÔNG phải max-prob.
   Đo được: xếp theo epistemic nâng macro-F1@80% thêm +0.035 [+0.004, +0.065] P=0.030;
   xếp theo max-prob nâng −0.003 (P=0.88), tức là vô ích.

## Temperature và ngưỡng defer ở đây khác lúc đánh giá

Lúc **báo cáo** (`src/eval/trust.py`), `T` được fit leave-one-fold-out để không ca nào
được hiệu chỉnh bởi một `T` đã nhìn thấy nó. Lúc **phục vụ**, không còn khái niệm đó:
ta cần đúng một `T` chốt sẵn, và fit nó trên toàn bộ validation là hợp lệ — đây là dữ
liệu validation, và ta không báo metric nào trên nó.

Cùng lý do với ngưỡng defer: lấy phân vị epistemic ở mức coverage mục tiêu trên
validation. **Không chọn tay** (AGENTS.md).
"""

from __future__ import annotations

import functools
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from src.eval.calibration import apply_temperature, fit_temperature
from src.eval.selective import uncertainty_decomposition
from src.utils.ids import normalize_pid

from webapp.backend.config import REPO_ROOT

# Coverage mục tiêu: model tự quyết 80% số ca, chuyển bác sĩ 20% khó nhất. 0.8 là mức
# trung tâm của dự án (Spec Sheet) — chọn TRƯỚC khi nhìn kết quả, không phải mức đẹp nhất.
TARGET_COVERAGE: float = float(os.environ.get("LLDMMRI_TARGET_COVERAGE", "0.8"))

PREDICTIONS_DIR: Path = Path(
    os.environ.get("LLDMMRI_PREDICTIONS_DIR", REPO_ROOT / "runs" / "E4_per_phase_results")
)

DETERMINISTIC_FILE = "val_probs_best.npz"
MEMBERS_FILE = "mc_dropout.npz"


@dataclass(frozen=True)
class CasePrediction:
    """Dự đoán out-of-fold của một bệnh nhân. Mọi trường đều là số đo được."""

    patient_id: str
    fold: str
    probs_raw: np.ndarray
    probs_calibrated: np.ndarray
    epistemic: float | None
    true_label: int | None

    @property
    def pred_index(self) -> int:
        """Lớp đoán — từ model TẤT ĐỊNH, không phải trung bình MC."""
        return int(self.probs_raw.argmax())


@dataclass(frozen=True)
class PredictionStore:
    cases: dict[str, CasePrediction]
    temperature: float
    defer_threshold: float
    has_epistemic: bool
    n_folds: int
    run_dir: Path

    def get(self, patient_id: str) -> CasePrediction | None:
        """Tra cứu theo ID đã chuẩn hoá chữ số, nên `MR-207769` và `MR207769` như nhau."""
        return self.cases.get(normalize_pid(patient_id))

    def should_defer(self, case: CasePrediction) -> bool:
        """Từ chối khi bất định epistemic vượt ngưỡng đã khoá trên validation.

        Không có epistemic thì **không** rơi về max-prob: đã đo được rằng max-prob
        xếp hạng vô ích (P=0.88). Trả về False và để lớp trên nói rõ là chưa đánh giá
        được, thay vì đưa ra một quyết định defer không có cơ sở.
        """
        return case.epistemic is not None and case.epistemic > self.defer_threshold


def _load_folds(run_dir: Path) -> tuple[list[dict], bool]:
    folds: list[dict] = []
    has_epistemic = True
    for det_path in sorted(run_dir.glob(f"fold*/{DETERMINISTIC_FILE}")):
        data = np.load(det_path, allow_pickle=True)
        ids = [str(x) for x in data["patient_ids"]]
        entry = {
            "fold": det_path.parent.name,
            "ids": ids,
            "probs": np.asarray(data["probs"], dtype=np.float64),
            "labels": np.asarray(data["labels"], dtype=int),
            "epistemic": None,
        }
        mc_path = det_path.parent / MEMBERS_FILE
        if mc_path.exists():
            mc = np.load(mc_path, allow_pickle=True)
            if [str(x) for x in mc["patient_ids"]] != ids:
                raise ValueError(
                    f"{entry['fold']}: thứ tự ca ở {MEMBERS_FILE} lệch khỏi {DETERMINISTIC_FILE}. "
                    "Ghép nhầm thứ tự sẽ gán bất định của người này cho người khác."
                )
            entry["epistemic"] = uncertainty_decomposition(mc["member_probs"])["epistemic"]
        else:
            has_epistemic = False
        folds.append(entry)
    return folds, has_epistemic


@functools.lru_cache(maxsize=1)
def load_store(run_dir: str | None = None) -> PredictionStore | None:
    """Nạp toàn bộ dự đoán một lần lúc startup. `None` nếu chưa có file nào.

    `lru_cache` vì đây là dữ liệu bất biến đọc từ đĩa: nạp lại mỗi request là lãng phí,
    và AGENTS.md §5 đã chốt "load model 1 lần lúc startup".
    """
    root = Path(run_dir) if run_dir else PREDICTIONS_DIR
    if not root.is_dir():
        return None
    folds, has_epistemic = _load_folds(root)
    if not folds:
        return None

    all_probs = np.concatenate([f["probs"] for f in folds])
    all_labels = np.concatenate([f["labels"] for f in folds])
    temperature = fit_temperature(all_probs, all_labels)

    if has_epistemic:
        all_epi = np.concatenate([f["epistemic"] for f in folds])
        # Ngưỡng = phân vị epistemic sao cho đúng TARGET_COVERAGE ca nằm dưới.
        defer_threshold = float(np.quantile(all_epi, TARGET_COVERAGE))
    else:
        defer_threshold = float("inf")  # không có epistemic thì không defer ai cả

    cases: dict[str, CasePrediction] = {}
    for fold in folds:
        calibrated = apply_temperature(fold["probs"], temperature)
        for i, pid in enumerate(fold["ids"]):
            key = normalize_pid(pid)
            if key in cases:
                raise ValueError(f"bệnh nhân {pid} xuất hiện ở hai fold — các fold phải phân hoạch")
            cases[key] = CasePrediction(
                patient_id=pid,
                fold=fold["fold"],
                probs_raw=fold["probs"][i],
                probs_calibrated=calibrated[i],
                epistemic=float(fold["epistemic"][i]) if fold["epistemic"] is not None else None,
                true_label=int(fold["labels"][i]),
            )

    return PredictionStore(
        cases=cases,
        temperature=temperature,
        defer_threshold=defer_threshold,
        has_epistemic=has_epistemic,
        n_folds=len(folds),
        run_dir=root,
    )
