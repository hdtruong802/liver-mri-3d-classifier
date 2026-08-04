"""Bảng trustworthiness out-of-fold — calibration + selective prediction.

Đây là driver ghép `src/eval/calibration.py` và `src/eval/selective.py` lại thành
bảng số của đóng góp headline (AGENTS.md §1). Thuần numpy, chạy trên CPU, đọc từ
`val_probs_*.npz` đã lưu — không cần GPU, không cần dựng lại model.

    python -m src.eval.trust --run-dir runs/E4_cv_results

**Vì sao fit temperature theo kiểu leave-one-fold-out.** Cách hiển nhiên là gộp cả
394 ca out-of-fold, fit một `T` trên đó, rồi báo ECE trên chính 394 ca ấy. Cách đó
tự quy chiếu: `T` đã nhìn thấy đúng những ca mà nó sắp được chấm điểm, nên ECE sau
hiệu chỉnh bị hạ thấp giả tạo. Đây chính là dạng leakage mà AGENTS.md §3.3 cấm, chỉ
là ở quy mô một tham số thay vì cả model.

Cách làm ở đây: với mỗi fold `f`, fit `T_f` trên dự đoán out-of-fold của **bốn fold
còn lại**, rồi áp `T_f` lên fold `f`. Ghép lại được một tập 394 ca mà mọi ca đều
được hiệu chỉnh bởi một `T` chưa từng thấy nó. Con số "fit gộp" vẫn được in ra, dán
nhãn rõ là lạc quan, để thấy khoảng cách giữa hai cách làm là bao nhiêu.

⚠️ `T` học ở đây chỉ dùng cho **báo cáo out-of-fold**. Khi chạm test-104 (một lần
duy nhất, phải xin phép — AGENTS.md §10) thì `T` phải là giá trị chốt từ trainval,
không được fit lại trên test.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

from src.data.taxonomy import NUM_CLASSES, SHORT_NAMES
from src.eval.bootstrap import DEFAULT_SEED, N_RESAMPLES, bootstrap_metric
from src.eval.calibration import (
    adaptive_calibration_error,
    apply_temperature,
    brier_score,
    fit_temperature,
    fit_temperature_min_ece,
    maximum_calibration_error,
    negative_log_likelihood,
    per_class_calibration_error,
    reliability_curve,
)
from src.eval.metrics import macro_f1
from src.eval.run import BEST, find_fold_predictions, load_predictions, pool_out_of_fold
from src.eval.selective import (
    aurc,
    coverage_at_risk,
    metric_at_coverage,
    predictive_entropy,
    selective_accuracy,
)

# Mức coverage đem báo cáo. 0.8 là con số trung tâm của dự án (Spec Sheet); các mức
# khác có mặt để thấy đường cong chứ không phải để chọn hậu nghiệm mức đẹp nhất.
COVERAGES = (1.0, 0.9, 0.8, 0.7, 0.5)

# Mức sai số mà bác sĩ có thể chấp nhận để model tự quyết. Hai mức, không phải một,
# vì ngưỡng chấp nhận được là quyết định lâm sàng chứ không phải quyết định kỹ thuật.
RISK_LEVELS = (0.10, 0.20)


def calibration_row(probs: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    """Bộ metric calibration cho một tập dự đoán."""
    return {
        "ece": adaptive_calibration_error(probs, labels),
        "mce": maximum_calibration_error(probs, labels),
        "brier": brier_score(probs, labels),
        "nll": negative_log_likelihood(probs, labels),
        "macro_f1": macro_f1(labels, probs.argmax(axis=1)),
    }


Fitter = Callable[[np.ndarray, np.ndarray], float]

FITTERS: dict[str, Fitter] = {
    "nll": fit_temperature,
    "ece": fit_temperature_min_ece,
}


def fit_temperature_leave_one_fold_out(
    predictions: dict[str, dict[str, Any]],
    fitter: Fitter = fit_temperature,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    """Hiệu chỉnh từng fold bằng `T` học từ các fold khác.

    Trả về ``(probs_đã_hiệu_chỉnh, labels, {tên_fold: T})`` theo đúng thứ tự mà
    `pool_out_of_fold` ghép, nên ghép được thẳng với kết quả chưa hiệu chỉnh.
    """
    names = sorted(predictions)
    if len(names) < 2:
        raise ValueError("cần ít nhất 2 fold để fit leave-one-fold-out")

    out_probs: list[np.ndarray] = []
    out_labels: list[np.ndarray] = []
    temperatures: dict[str, float] = {}

    for held_out in names:
        others = [n for n in names if n != held_out]
        fit_probs = np.concatenate([predictions[n]["probs"] for n in others])
        fit_labels = np.concatenate([predictions[n]["labels"] for n in others])
        t = fitter(fit_probs, fit_labels)
        temperatures[held_out] = t
        out_probs.append(apply_temperature(predictions[held_out]["probs"], t))
        out_labels.append(predictions[held_out]["labels"])

    return np.concatenate(out_probs), np.concatenate(out_labels), temperatures


def selective_row(
    labels: np.ndarray, probs: np.ndarray, scores: np.ndarray
) -> dict[str, float | dict[str, float]]:
    """Bộ metric selective prediction cho một điểm tin cậy đã chọn."""
    preds = probs.argmax(axis=1)
    correct = preds == labels
    row: dict[str, float | dict[str, float]] = {
        "aurc": aurc(correct, scores),
        "risk_full": float(1.0 - correct.mean()),
    }
    at_cov: dict[str, float] = {}
    for c in COVERAGES:
        at_cov[f"acc@{c:.0%}"] = selective_accuracy(correct, scores, c)
        at_cov[f"f1@{c:.0%}"] = metric_at_coverage(labels, preds, scores, c, macro_f1)
        keep = max(1, int(round(c * len(labels))))
        order = np.argsort(-scores, kind="stable")[:keep]
        at_cov[f"classes@{c:.0%}"] = float(len(np.unique(labels[order])))
    row["at_coverage"] = at_cov
    row["coverage_at_risk"] = {
        f"risk<={r:.0%}": coverage_at_risk(correct, scores, r) for r in RISK_LEVELS
    }
    return row


def report(
    run_root: str | Path,
    n_resamples: int = N_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """Bảng trustworthiness đầy đủ cho một thư mục run nhiều fold."""
    root = Path(run_root)
    found = find_fold_predictions(root, BEST)
    if not found:
        raise FileNotFoundError(f"không thấy {BEST} nào dưới {root}/fold*/")

    predictions = {name: load_predictions(path) for name, path in found.items()}
    pooled = pool_out_of_fold(predictions)
    labels, raw = pooled["labels"], pooled["probs"]

    scaled: dict[str, np.ndarray] = {}
    temperatures: dict[str, dict[str, float]] = {}
    for objective, fitter in FITTERS.items():
        probs_o, labels_o, temps_o = fit_temperature_leave_one_fold_out(predictions, fitter)
        if not np.array_equal(labels_o, labels):
            raise RuntimeError("thứ tự ca sau hiệu chỉnh lệch khỏi bản gộp — không ghép được")
        scaled[objective] = probs_o
        temperatures[objective] = temps_o

    # `cal_probs` là bản dùng cho phần selective và CI: fit theo NLL, tức là mặc
    # định của văn liệu. Đổi mặc định này là một quyết định phải ghi WORKLOG.
    cal_probs = scaled["nll"]

    out: dict[str, Any] = {
        "run_root": str(root),
        "n_folds": len(predictions),
        "n_patients": int(len(labels)),
        "accuracy": float((raw.argmax(axis=1) == labels).mean()),
        "temperature": {
            "leave_one_fold_out": temperatures,
            "pooled_optimistic": {o: f(raw, labels) for o, f in FITTERS.items()},
        },
        "calibration": {
            "raw": calibration_row(raw, labels),
            "temp_scaled_nll": calibration_row(scaled["nll"], labels),
            "temp_scaled_ece": calibration_row(scaled["ece"], labels),
        },
        "mean_confidence": {
            "raw": float(raw.max(axis=1).mean()),
            "temp_scaled_nll": float(scaled["nll"].max(axis=1).mean()),
            "temp_scaled_ece": float(scaled["ece"].max(axis=1).mean()),
        },
        "per_class_ece": {
            "raw": per_class_calibration_error(raw, labels),
            "temp_scaled": per_class_calibration_error(cal_probs, labels),
        },
        "reliability": {
            "raw": reliability_curve(raw, labels),
            "temp_scaled": reliability_curve(cal_probs, labels),
        },
        "class_counts": np.bincount(labels, minlength=NUM_CLASSES).tolist(),
    }

    # Hai điểm tin cậy, không phải một: max-prob là thứ web app hiển thị, entropy
    # dùng cả phân bố. Cái nào xếp hạng ca sai tốt hơn là câu hỏi thực nghiệm.
    out["selective"] = {
        "raw · max-prob": selective_row(labels, raw, raw.max(axis=1)),
        "calibrated · max-prob": selective_row(labels, cal_probs, cal_probs.max(axis=1)),
        "calibrated · -entropy": selective_row(
            labels, cal_probs, -predictive_entropy(cal_probs, normalise=True)
        ),
    }

    # Hai mốc để đọc AURC. Không có chúng thì 0.21 là một con số không nghĩa lý gì:
    # AURC phụ thuộc mạnh vào risk nền, nên "thấp" hay "cao" chỉ có nghĩa khi so với
    # điểm tin cậy ngẫu nhiên (không thông tin) và với oracle (thông tin hoàn hảo).
    correct = raw.argmax(axis=1) == labels
    rng = np.random.default_rng(seed)
    chance = [aurc(correct, rng.random(len(labels))) for _ in range(200)]
    out["aurc_reference"] = {
        "chance": float(np.mean(chance)),
        "chance_ci": [float(np.percentile(chance, 2.5)), float(np.percentile(chance, 97.5))],
        "oracle": float(aurc(correct, correct.astype(float))),
    }

    # CI cho hai con số sẽ đi vào báo cáo. Bootstrap ở mức bệnh nhân, phân tầng.
    preds = cal_probs.argmax(axis=1)
    conf = cal_probs.max(axis=1)
    order80 = np.argsort(-conf, kind="stable")[: max(1, int(round(0.8 * len(labels))))]
    out["ci"] = {
        "macro_f1_full": bootstrap_metric(
            labels, preds, macro_f1, n_resamples=n_resamples, seed=seed
        ),
        "macro_f1_at_80": bootstrap_metric(
            labels[order80], preds[order80], macro_f1, n_resamples=n_resamples, seed=seed
        ),
    }
    return out


def _fmt_calibration(cal: dict[str, dict[str, float]]) -> str:
    head = f"{'':<26}{'ECE':>9}{'MCE':>9}{'Brier':>9}{'NLL':>9}{'macro-F1':>11}"
    lines = [head, "-" * len(head)]
    label = {
        "raw": "chưa hiệu chỉnh",
        "temp_scaled_nll": "temp-scaled, fit NLL",
        "temp_scaled_ece": "temp-scaled, fit ECE",
    }
    for key, row in cal.items():
        lines.append(
            f"{label.get(key, key):<26}{row['ece']:>9.4f}{row['mce']:>9.4f}"
            f"{row['brier']:>9.4f}{row['nll']:>9.4f}{row['macro_f1']:>11.4f}"
        )
    return "\n".join(lines)


def _fmt_selective(sel: dict[str, dict[str, Any]]) -> str:
    cov_cols = [f"{c:.0%}" for c in COVERAGES]
    head = f"{'điểm tin cậy':<26}{'AURC':>8}" + "".join(f"{'F1@' + c:>10}" for c in cov_cols)
    lines = [head, "-" * len(head)]
    for name, row in sel.items():
        cells = "".join(f"{row['at_coverage']['f1@' + c]:>10.4f}" for c in cov_cols)
        lines.append(f"{name:<26}{row['aurc']:>8.4f}{cells}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="thư mục chứa fold*/")
    parser.add_argument("--n-resamples", type=int, default=N_RESAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--json-out", help="ghi kết quả đầy đủ ra file JSON")
    args = parser.parse_args()

    r = report(args.run_dir, n_resamples=args.n_resamples, seed=args.seed)

    print(f"run: {r['run_root']}")
    print(f"{r['n_folds']} fold · {r['n_patients']} bệnh nhân out-of-fold\n")

    print("=== Temperature (fit leave-one-fold-out) ===")
    for objective, temps in r["temperature"]["leave_one_fold_out"].items():
        values = np.array(list(temps.values()))
        pooled_t = r["temperature"]["pooled_optimistic"][objective]
        print(
            f"  mục tiêu {objective.upper():<4}: T = {values.mean():.3f} "
            f"(dao động {values.min():.3f}–{values.max():.3f} qua 5 fold) · "
            f"fit gộp {pooled_t:.3f} ⚠"
        )
    print("  T > 1 nghĩa là model tự tin quá mức và xác suất đang bị kéo mềm xuống.\n")

    print("=== Calibration (out-of-fold) ===")
    print(_fmt_calibration(r["calibration"]))
    acc = r["accuracy"]
    print(f"\nĐộ tự tin trung bình so với accuracy thật ({acc:.4f}):")
    for key, conf in r["mean_confidence"].items():
        gap = conf - acc
        verdict = "tự tin quá mức" if gap > 0.02 else ("THIẾU tự tin" if gap < -0.02 else "khớp")
        print(f"  {key:<20} {conf:.4f}  lệch {gap:+.4f}  → {verdict}")
    print(
        "\nmacro-F1 không đổi sau temperature scaling — đúng như phải thế: chia logit\n"
        "cho một hằng số dương không đổi thứ hạng lớp. Calibration là thứ nhận được\n"
        "mà không đánh đổi độ chính xác."
    )
    print(
        "\n⚠ Cột `fit gộp` ở trên fit T trên chính 394 ca rồi chấm điểm trên đó — tự\n"
        "  quy chiếu, chỉ in ra để so. Mọi số trong bảng đều là LOFO."
    )

    print("\n=== ECE từng lớp ===")
    print(f"{'lớp':>10}{'n':>6}{'ECE thô':>11}{'ECE sau':>11}")
    print("-" * 38)
    raw_pc, cal_pc = r["per_class_ece"]["raw"], r["per_class_ece"]["temp_scaled"]
    counts = r["class_counts"]
    for k in sorted(raw_pc):
        print(
            f"{SHORT_NAMES[k]:>10}{counts[k]:>6}"
            f"{raw_pc[k]:>11.4f}{cal_pc.get(k, float('nan')):>11.4f}"
        )

    print("\n=== Selective prediction (macro-F1 theo coverage) ===")
    print(_fmt_selective(r["selective"]))
    ref = r["aurc_reference"]
    print(
        f"\nĐọc AURC bằng hai mốc: ngẫu nhiên {ref['chance']:.4f} "
        f"[{ref['chance_ci'][0]:.4f}, {ref['chance_ci'][1]:.4f}] · oracle {ref['oracle']:.4f}."
    )
    best_key = "calibrated · max-prob"
    car = r["selective"][best_key]["coverage_at_risk"]
    print(f"\nCoverage giữ được ở mức sai số cho trước ({best_key}):")
    for k, v in car.items():
        print(f"  {k}: coverage {v:.1%}")
    print(
        "\n⚠ Ở coverage thấp, lớp hiếm có thể biến mất khỏi tập giữ lại — macro-F1 khi\n"
        "  đó tính trên ít lớp hơn và KHÔNG so trực tiếp được với coverage 100%."
    )
    for c in COVERAGES:
        n_cls = r["selective"][best_key]["at_coverage"][f"classes@{c:.0%}"]
        if n_cls < NUM_CLASSES:
            print(f"  coverage {c:.0%}: chỉ còn {int(n_cls)}/{NUM_CLASSES} lớp")

    ci = r["ci"]
    print("\n=== Khoảng tin cậy (bootstrap mức bệnh nhân, phân tầng) ===")
    for key, row in ci.items():
        print(
            f"  {key:<18} {row['point']:.4f} [{row['ci_low']:.4f}, {row['ci_high']:.4f}]"
            f"  (n={row['n_patients']}, {row['n_resamples']} lần)"
        )

    if args.json_out:
        serialisable = json.loads(
            json.dumps(
                r,
                default=lambda o: (
                    o.tolist()
                    if isinstance(o, np.ndarray)
                    else (o.__dict__ if hasattr(o, "__dict__") else str(o))
                ),
            )
        )
        Path(args.json_out).write_text(json.dumps(serialisable, indent=2), encoding="utf-8")
        print(f"\nđã ghi {args.json_out}")


if __name__ == "__main__":
    main()
