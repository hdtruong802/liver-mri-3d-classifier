"""Đọc số từ test-104 — chạy trên CPU, từ file `.npz` mà `test_once` đã lưu.

    python -m src.eval.test_report --run-dir runs/test104 --oof-dir runs/E4_per_phase_results

Module này **không chạm dữ liệu ảnh** và không dựng lại model, nên chạy lại bao nhiêu
lần cũng không thành "lần chạm thứ hai" vào test-104. Toàn bộ danh sách metric và cách
đọc đã khoá ở `docs/TEST104_PREREGISTRATION.md`; ở đây chỉ hiện thực đúng danh sách đó,
không thêm bớt.

Ba thứ module này cố ý làm khác một script báo cáo thông thường:

1. **Nhiệt độ `T` lấy từ out-of-fold, không fit trên test.** Fit trên test là leakage
   loại nghiêm trọng nhất còn có thể mắc ở giai đoạn này (AGENTS.md §3.3).
2. **Ensemble báo cả cột chưa hiệu chỉnh lẫn đã hiệu chỉnh.** `T` học từ phân bố của
   *model đơn* mà áp lên *ensemble* — vốn đã bớt tự tin — nên nhiều khả năng hiệu chỉnh
   quá tay. Giấu một trong hai cột là giấu đúng chỗ yếu.
3. **Selective luôn in dòng đối chứng `max-prob`.** Không có nó thì "xếp hạng theo bất
   đồng có tác dụng" là một khẳng định không kiểm được.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from src.data.taxonomy import SHORT_NAMES
from src.eval.bootstrap import bootstrap_all, default_metrics, format_ci, stratified_indices
from src.eval.calibration import (
    adaptive_calibration_error,
    apply_temperature,
    brier_score,
    fit_temperature_min_ece,
    maximum_calibration_error,
    negative_log_likelihood,
)
from src.eval.metrics import confusion_matrix, macro_f1, per_class_f1
from src.eval.run import find_fold_predictions, load_predictions, pool_out_of_fold
from src.eval.selective import (
    aurc,
    coverage_at_risk,
    metric_at_coverage,
    uncertainty_decomposition,
)
from src.utils.io import resolve_repo_path

# Chốt ở pre-registration §4. Đừng thêm mức sau khi đã nhìn số.
COVERAGES = (1.0, 0.9, 0.8, 0.7)
MAX_RISK = 0.10
N_RESAMPLES = 2000
SEED = 20260727


def load_test(run_dir: str | Path) -> dict[str, Any]:
    """Đọc `test_probs.npz`; trả `member_probs` (K,N,C) và trung bình ensemble."""
    with np.load(Path(run_dir) / "test_probs.npz", allow_pickle=False) as data:
        members = np.asarray(data["member_probs"], dtype=float)
        out = {
            "member_probs": members,
            "ensemble": members.mean(axis=0),
            "labels": np.asarray(data["labels"], dtype=int),
            "patient_ids": [str(p) for p in data["patient_ids"]],
            "folds": [int(f) for f in data["folds"]],
        }
    if members.shape[0] < 2:
        raise ValueError("cần ≥2 thành viên: epistemic đo bằng mức bất đồng")
    return out


def temperature_from_oof(oof_dir: str | Path) -> float:
    """`T` fit trên 394 ca out-of-fold, gộp chung.

    Gộp chứ không leave-one-fold-out: trên test không có cấu trúc fold để chừa ra, và
    mọi ca test đều mù với cả 394 ca này. Dùng `min_ece` vì `T` tối ưu NLL bắn quá
    sang thiếu tự tin trên chính bộ này (WORKLOG S-079).
    """
    found = find_fold_predictions(resolve_repo_path(oof_dir))
    if not found:
        raise FileNotFoundError(f"không thấy val_probs_best.npz nào dưới {oof_dir}/fold*/")
    pooled = pool_out_of_fold({name: load_predictions(p) for name, p in found.items()})
    return float(fit_temperature_min_ece(pooled["probs"], pooled["labels"]))


def calibration_row(probs: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    accuracy = float((probs.argmax(1) == labels).mean())
    confidence = float(probs.max(1).mean())
    return {
        "ECE": adaptive_calibration_error(probs, labels),
        "MCE": maximum_calibration_error(probs, labels),
        "Brier": brier_score(probs, labels),
        "NLL": negative_log_likelihood(probs, labels),
        "tự tin TB": confidence,
        "lệch so acc": confidence - accuracy,
    }


def selective_rows(
    labels: np.ndarray, probs: np.ndarray, scores: dict[str, np.ndarray]
) -> dict[str, dict[str, float]]:
    """Một hàng mỗi điểm xếp hạng. Dự đoán KHÔNG đổi giữa các hàng — chỉ thứ tự defer."""
    pred = probs.argmax(1)
    correct = (pred == labels).astype(float)
    out: dict[str, dict[str, float]] = {}
    for name, score in scores.items():
        row: dict[str, float] = {"AURC": aurc(correct, score)}
        for coverage in COVERAGES:
            row[f"F1@{coverage:.0%}"] = metric_at_coverage(labels, pred, score, coverage, macro_f1)
        row[f"cov@risk≤{MAX_RISK:.0%}"] = coverage_at_risk(correct, score, MAX_RISK)
        out[name] = row
    return out


def two_sided_p(diffs: np.ndarray) -> float:
    """P hai phía từ phân bố bootstrap của một hiệu.

    Cách viết tắt ``2 * min(mean(d <= 0), 1 - mean(d <= 0))`` **sai ở trường hợp biên**:
    khi mọi hiệu đúng bằng 0 (hai điểm xếp hạng cho kết quả y hệt nhau) nó trả P = 0,
    tức là tuyên bố ý nghĩa tối đa cho một hiệu ứng bằng không. Dùng cả hai bất đẳng
    thức không nghiêm thì cả hai vế bằng 1, cho P = 1 — đúng như phải thế.
    """
    diffs = np.asarray(diffs, dtype=float)
    low = float((diffs <= 0).mean())
    high = float((diffs >= 0).mean())
    return float(min(1.0, 2 * min(low, high)))


def paired_selective_test(
    labels: np.ndarray,
    probs: np.ndarray,
    score_a: np.ndarray,
    score_b: np.ndarray,
    coverage: float = 0.8,
) -> dict[str, dict[str, float]]:
    """Bootstrap ghép cặp trên HIỆU giữa hai điểm xếp hạng, cùng ca cùng dự đoán.

    Bắt buộc ghép cặp: F1@80% và F1@100% tính trên tập lồng nhau nên CI của chúng
    chồng lấn kể cả khi hiệu là thật. So hai CI rời nhau ở đây là sai phương pháp.
    """
    pred = probs.argmax(1)
    correct = (pred == labels).astype(float)
    rng = np.random.default_rng(SEED)
    diffs: dict[str, list[float]] = {"AURC": [], f"F1@{coverage:.0%}": []}
    for _ in range(N_RESAMPLES):
        idx = stratified_indices(labels, rng)
        y, p, c = labels[idx], pred[idx], correct[idx]
        a, b = score_a[idx], score_b[idx]
        diffs["AURC"].append(aurc(c, b) - aurc(c, a))
        diffs[f"F1@{coverage:.0%}"].append(
            metric_at_coverage(y, p, b, coverage, macro_f1)
            - metric_at_coverage(y, p, a, coverage, macro_f1)
        )
    out: dict[str, dict[str, float]] = {}
    for key, values in diffs.items():
        arr = np.asarray(values)
        low, high = np.percentile(arr, [2.5, 97.5])
        out[key] = {
            "diff": float(arr.mean()),
            "ci_low": float(low),
            "ci_high": float(high),
            "p": two_sided_p(arr),
        }
    return out


def _fmt(rows: dict[str, dict[str, float]], digits: int = 4) -> str:
    if not rows:
        return "(trống)"
    columns = list(next(iter(rows.values())))
    width = max(len(name) for name in rows) + 2
    lines = [f"{'':<{width}}" + "".join(f"{c:>13}" for c in columns)]
    lines.append("-" * (width + 13 * len(columns)))
    for name, row in rows.items():
        lines.append(f"{name:<{width}}" + "".join(f"{row[c]:>13.{digits}f}" for c in columns))
    return "\n".join(lines)


def report(run_dir: str | Path, oof_dir: str | Path) -> dict[str, Any]:
    test = load_test(run_dir)
    labels = test["labels"]
    ensemble = test["ensemble"]
    members = test["member_probs"]
    temperature = temperature_from_oof(oof_dir)

    metrics = default_metrics()
    kwargs = {"n_resamples": N_RESAMPLES, "seed": SEED}

    classification = {
        "ensemble 5 fold": bootstrap_all(labels, ensemble.argmax(1), metrics, **kwargs),
    }
    per_member = {}
    for i, fold in enumerate(test["folds"]):
        per_member[f"model đơn · fold {fold}"] = bootstrap_all(
            labels, members[i].argmax(1), metrics, **kwargs
        )

    member_f1 = np.array([macro_f1(labels, m.argmax(1)) for m in members])

    calibrated = apply_temperature(ensemble, temperature)
    calibration = {
        "ensemble, chưa hiệu chỉnh": calibration_row(ensemble, labels),
        f"ensemble, T={temperature:.2f} (từ OOF)": calibration_row(calibrated, labels),
    }
    for i, fold in enumerate(test["folds"]):
        calibration[f"model đơn fold {fold}, T={temperature:.2f}"] = calibration_row(
            apply_temperature(members[i], temperature), labels
        )

    unc = uncertainty_decomposition(members)
    scores = {
        "max-prob (đối chứng)": ensemble.max(1),
        "−epistemic (bất đồng 5 model)": -unc["epistemic"],
    }
    selective = selective_rows(labels, ensemble, scores)
    paired = paired_selective_test(
        labels, ensemble, scores["max-prob (đối chứng)"], scores["−epistemic (bất đồng 5 model)"]
    )

    return {
        "n_cases": int(len(labels)),
        "temperature": temperature,
        "classification": classification,
        "per_member": per_member,
        "member_f1": member_f1,
        "calibration": calibration,
        "selective": selective,
        "paired": paired,
        "labels": labels,
        "ensemble": ensemble,
        "epistemic": unc["epistemic"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Báo cáo test-104 từ xác suất đã lưu (CPU)")
    parser.add_argument("--run-dir", required=True, help="thư mục chứa test_probs.npz")
    parser.add_argument(
        "--oof-dir",
        default="runs/E4_per_phase_results",
        help="thư mục out-of-fold, dùng để fit T (KHÔNG fit trên test)",
    )
    args = parser.parse_args()

    r = report(args.run_dir, args.oof_dir)
    labels, ensemble = r["labels"], r["ensemble"]

    print(f"=== TEST-104 OFFICIAL · n={r['n_cases']} · chạm lần thứ nhất ===\n")

    print("1) Phân loại — bộ dự đoán CHÍNH là ensemble 5 fold")
    columns = list(next(iter(r["classification"].values())))
    width = 26
    print(f"{'':<{width}}" + "".join(f"{c:>26}" for c in columns))
    print("-" * (width + 26 * len(columns)))
    for name, row in {**r["classification"], **r["per_member"]}.items():
        print(f"{name:<{width}}" + "".join(f"{format_ci(row[c]):>26}" for c in columns))
    f1s = r["member_f1"]
    print(
        f"\n   5 model đơn: trung bình {f1s.mean():.4f} ± {f1s.std(ddof=1):.4f} (SD mẫu) · "
        f"trải {f1s.min():.4f}–{f1s.max():.4f}"
    )
    print(
        "   ⚠ Số CHÍNH là dòng ensemble. Model đơn in ra để thấy độ phân tán, "
        "KHÔNG được báo cái tốt nhất."
    )

    print("\n2) Từng lớp (ensemble)")
    scores = per_class_f1(labels, ensemble.argmax(1))
    for index in sorted(SHORT_NAMES):
        print(
            f"   {SHORT_NAMES[index]:>7}: {scores[index]:.3f}  (n={int((labels == index).sum())})"
        )
    print("\n   Ma trận nhầm lẫn (hàng = thật, cột = đoán):")
    print("       " + "".join(f"{SHORT_NAMES[i]:>8}" for i in sorted(SHORT_NAMES)))
    for index, row in enumerate(confusion_matrix(labels, ensemble.argmax(1))):
        print(f"{SHORT_NAMES[index]:>6} " + "".join(f"{v:>8d}" for v in row))

    print(f"\n3) Calibration — T={r['temperature']:.2f} fit trên 394 ca out-of-fold, áp mù")
    print(_fmt(r["calibration"]))
    print(
        "   ⚠ T học từ phân bố của MODEL ĐƠN, áp lên ENSEMBLE vốn đã bớt tự tin, nên\n"
        "     nhiều khả năng hiệu chỉnh quá tay. Không được fit lại T trên test."
    )

    print("\n4) Selective — cùng dự đoán ensemble, chỉ đổi cách xếp hạng defer")
    print(_fmt(r["selective"]))
    print("\n   Bootstrap ghép cặp trên hiệu (−epistemic so với max-prob):")
    for key, d in r["paired"].items():
        print(
            f"     {key:<10}{d['diff']:+.4f}  CI95 [{d['ci_low']:+.4f}, {d['ci_high']:+.4f}]  "
            f"P={d['p']:.4f}"
        )
    print(
        "\n   Dòng 'max-prob' là ĐỐI CHỨNG và nó mang cả lập luận: cùng model, cùng dự\n"
        "   đoán, chỉ đổi thứ tự defer."
    )

    print(
        "\n=== RÀNG BUỘC ===\n"
        "Đây là lần chạm test-104 duy nhất được cho phép. Không đổi config, checkpoint,\n"
        "T, hay ngưỡng defer vì các con số trên. Chi tiết: docs/TEST104_PREREGISTRATION.md"
    )


if __name__ == "__main__":
    main()
