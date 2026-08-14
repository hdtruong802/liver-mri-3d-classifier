"""Đánh giá **thuần** từ file xác suất đã lưu — không dựng lại model, không cần GPU.

    python -m src.eval.run --run-dir artifacts/runs/baseline_3dpatch

Đọc `val_probs_best.npz` / `val_probs_last.npz` mà vòng train ghi ra cho từng fold,
rồi in bảng metric kèm CI bootstrap. Tách hẳn khỏi `src/train/` (AGENTS.md §8): chạy
lại được trên checkpoint cũ hàng tuần sau, và không tranh GPU với việc train.

Hai thứ bảng này trả lời mà một điểm ước lượng không trả lời được:

1. **Gộp out-of-fold.** 5 fold phân hoạch đúng 394 bệnh nhân trainval, nên mỗi bệnh
   nhân có đúng **một** dự đoán từ fold mà họ nằm trong tập val. Gộp lại cho một tập
   đánh giá 394 người thay vì 82 — CI hẹp hơn hẳn.
2. **best-epoch so với last-epoch.** Epoch "tốt nhất" được chọn bằng macro-F1 trên
   chính tập val nhỏ đó, mà dãy macro-F1 của fold 1 dao động 0.115–0.265 không xu
   hướng (WORKLOG S-042). Chênh lệch giữa hai cột chính là độ lớn của thiên lệch do
   chọn lọc — cùng bệnh lý mà AGENTS.md §3.5 cấm dưới tên *best-of-many-seeds*.

⚠️ Script này **không bao giờ** chạm test-104. Nó chỉ đọc file `val_probs_*` (AGENTS.md §3.4).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from src.data.taxonomy import SHORT_NAMES
from src.eval.bootstrap import bootstrap_all, default_metrics, format_ci
from src.eval.metrics import confusion_matrix, per_class_f1
from src.utils.io import resolve_repo_path

BEST = "val_probs_best.npz"
LAST = "val_probs_last.npz"
# Sinh bởi một lượt TTA trên checkpoint đã có, hoặc bởi cell TTA của
# một cell TTA chạy ngay sau khi train. Vắng mặt là bình thường —
# `report` bỏ qua nhãn nào không có file, không nổ.
TTA = "val_probs_best_tta.npz"


def load_predictions(path: str | Path) -> dict[str, Any]:
    """Đọc một file ``val_probs_*.npz`` thành dict tiện dùng."""
    with np.load(path, allow_pickle=False) as data:
        return {
            "probs": np.asarray(data["probs"], dtype=float),
            "labels": np.asarray(data["labels"], dtype=int),
            "patient_ids": [str(p) for p in data["patient_ids"]],
            "epoch": int(data["epoch"]) if "epoch" in data else -1,
        }


def find_fold_predictions(run_root: str | Path, filename: str = BEST) -> dict[str, Path]:
    """Tìm file dự đoán của từng fold dưới thư mục run.

    Khớp cả tên thư mục kiểu cũ (`fold1/`) lẫn kiểu hiện tại có hash kiến trúc
    (`fold1_4c2cf705/`). Trả về dict đã sắp theo tên thư mục.
    """
    root = Path(run_root)
    return {path.parent.name: path for path in sorted(root.glob(f"fold*/{filename}"))}


def pool_out_of_fold(predictions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Gộp dự đoán val của các fold thành một tập out-of-fold duy nhất.

    **Có cổng chặn leakage.** Nếu một bệnh nhân xuất hiện ở tập val của hai fold thì
    các fold không phân hoạch đúng, và gộp lại sẽ đếm người đó hai lần — con số ra
    trông vẫn hợp lý nên lỗi này không tự lộ. Ném lỗi thay vì báo số sai (AGENTS.md §3.2).
    """
    from src.utils.ids import normalize_pid

    seen: dict[str, str] = {}
    labels: list[np.ndarray] = []
    probs: list[np.ndarray] = []
    ids: list[str] = []

    for fold_name, pred in sorted(predictions.items()):
        for patient_id in pred["patient_ids"]:
            key = normalize_pid(patient_id)
            if key in seen:
                raise ValueError(
                    f"LEAK: bệnh nhân {patient_id} có mặt ở val của cả {seen[key]} và "
                    f"{fold_name}. Các fold phải phân hoạch trainval."
                )
            seen[key] = fold_name
        labels.append(pred["labels"])
        probs.append(pred["probs"])
        ids.extend(pred["patient_ids"])

    return {
        "labels": np.concatenate(labels),
        "probs": np.concatenate(probs),
        "patient_ids": ids,
        "n_folds": len(predictions),
    }


def evaluate(labels: np.ndarray, probs: np.ndarray, **kwargs: Any) -> dict[str, dict[str, float]]:
    """Metric + CI bootstrap từ nhãn thật và ma trận xác suất."""
    return bootstrap_all(labels, probs.argmax(axis=1), default_metrics(), **kwargs)


def format_table(rows: dict[str, dict[str, dict[str, float]]]) -> str:
    """Bảng ``hàng = nguồn dự đoán · cột = metric ± CI``."""
    if not rows:
        return "(không có dữ liệu)"
    metric_names = list(next(iter(rows.values())).keys())
    width = max(len(name) for name in rows) + 2

    lines = [f"{'':<{width}}" + "".join(f"{m:>26}" for m in metric_names)]
    lines.append("-" * (width + 26 * len(metric_names)))
    for name, result in rows.items():
        cells = "".join(f"{format_ci(result[m]):>26}" for m in metric_names)
        lines.append(f"{name:<{width}}" + cells)
    return "\n".join(lines)


def format_per_class(labels: np.ndarray, probs: np.ndarray) -> str:
    """F1 từng lớp + ma trận nhầm lẫn — để thấy lớp hiếm bị bỏ quên hay không."""
    pred = probs.argmax(axis=1)
    scores = per_class_f1(labels, pred)
    matrix = confusion_matrix(labels, pred)

    lines = ["F1 từng lớp:"]
    for index in sorted(SHORT_NAMES):
        support = int((labels == index).sum())
        lines.append(f"  {SHORT_NAMES[index]:>7}: {scores[index]:.3f}  (n={support})")

    lines.append("")
    lines.append("Ma trận nhầm lẫn (hàng = thật, cột = đoán):")
    lines.append("        " + "".join(f"{SHORT_NAMES[i]:>8}" for i in sorted(SHORT_NAMES)))
    for index, row in enumerate(matrix):
        lines.append(f"{SHORT_NAMES[index]:>7} " + "".join(f"{v:>8d}" for v in row))
    return "\n".join(lines)


def report(run_root: str | Path, n_resamples: int = 2000, seed: int = 20260727) -> dict[str, Any]:
    """Dựng toàn bộ báo cáo cho một thư mục run; trả về dict để test/tái dùng."""
    root = resolve_repo_path(run_root)
    output: dict[str, Any] = {"run_root": str(root), "folds": {}, "pooled": {}}

    for label, filename in (("best", BEST), ("last", LAST), ("best+TTA", TTA)):
        found = find_fold_predictions(root, filename)
        if not found:
            continue
        predictions = {name: load_predictions(path) for name, path in found.items()}

        for fold_name, pred in predictions.items():
            output["folds"].setdefault(fold_name, {})[label] = evaluate(
                pred["labels"], pred["probs"], n_resamples=n_resamples, seed=seed
            )

        pooled = pool_out_of_fold(predictions)
        output["pooled"][label] = {
            "metrics": evaluate(
                pooled["labels"], pooled["probs"], n_resamples=n_resamples, seed=seed
            ),
            "n_patients": len(pooled["patient_ids"]),
            "n_folds": pooled["n_folds"],
            "labels": pooled["labels"],
            "probs": pooled["probs"],
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Đánh giá từ xác suất val đã lưu (CPU, không cần GPU)"
    )
    parser.add_argument("--run-dir", required=True, help="vd artifacts/runs/baseline_3dpatch")
    parser.add_argument("--n-resamples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260727)
    args = parser.parse_args()

    result = report(args.run_dir, n_resamples=args.n_resamples, seed=args.seed)
    print(f"run: {result['run_root']}\n")

    if not result["folds"]:
        raise SystemExit(
            f"không thấy file {BEST} nào dưới {result['run_root']}/fold*/. "
            "Tải output của Kaggle về trước, hoặc trỏ --run-dir đúng chỗ."
        )

    print("=== Từng fold (val riêng của fold đó) ===")
    for fold_name, by_source in sorted(result["folds"].items()):
        print(format_table({f"{fold_name} · {k}": v for k, v in by_source.items()}))
        print()

    if result["pooled"]:
        rows = {}
        for label, pooled in result["pooled"].items():
            rows[f"out-of-fold · {label} (n={pooled['n_patients']})"] = pooled["metrics"]
        print(f"=== Gộp out-of-fold ({next(iter(result['pooled'].values()))['n_folds']} fold) ===")
        print(format_table(rows))
        print()

        if "best" in result["pooled"]:
            pooled = result["pooled"]["best"]
            print(format_per_class(pooled["labels"], pooled["probs"]))

    print(
        "\nLƯU Ý: cột `best` chọn epoch theo macro-F1 trên chính tập val đó nên **lệch "
        "lạc quan**; chênh lệch so với cột `last` là độ lớn của thiên lệch (WORKLOG S-042)."
    )


if __name__ == "__main__":
    main()
