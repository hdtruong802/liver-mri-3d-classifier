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
    uncertainty_decomposition,
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


def report_members(run_root: str | Path, filename: str = "mc_dropout.npz") -> dict[str, Any]:
    """Bảng bất định epistemic từ nhiều thành viên mỗi fold (MC-dropout hoặc ensemble).

    Đọc ``fold*/<filename>`` chứa `member_probs` dạng ``(K, N, C)``. Gộp qua các fold
    rồi so ba điểm tin cậy: max-prob của trung bình, entropy toàn phần, và **epistemic**
    (mutual information giữa các thành viên).

    ⚠️ Chỉ hợp lệ khi mọi thành viên của một fold đều **mù với val của fold đó**. Đúng
    với MC-dropout (cùng một model) và với ensemble nhiều seed cùng split; **sai** với
    5 checkpoint của 5 fold khác nhau — xem docstring `src/eval/mc_dropout.py`.
    """
    root = Path(run_root)
    paths = {p.parent.name: p for p in sorted(root.glob(f"fold*/{filename}"))}
    if not paths:
        raise FileNotFoundError(f"không thấy {filename} nào dưới {root}/fold*/")

    labels_all: list[np.ndarray] = []
    mean_all: list[np.ndarray] = []
    epistemic_all: list[np.ndarray] = []
    total_all: list[np.ndarray] = []
    seen: dict[str, str] = {}
    n_passes: set[int] = set()

    deterministic_all: list[np.ndarray] = []

    for fold_name, path in paths.items():
        data = np.load(path, allow_pickle=True)
        members = data["member_probs"]
        if members.ndim != 3:
            raise ValueError(f"{path}: member_probs phải là (K, N, C), nhận {members.shape}")
        ids = data["patient_ids"].tolist()
        for pid in ids:
            if pid in seen:
                raise ValueError(f"bệnh nhân {pid} có ở cả {seen[pid]} và {fold_name}")
            seen[pid] = fold_name
        unc = uncertainty_decomposition(members)
        labels_all.append(data["labels"])
        mean_all.append(members.mean(axis=0))
        epistemic_all.append(unc["epistemic"])
        total_all.append(unc["total"])
        n_passes.add(int(data["n_passes"]))

        # Dự đoán tất định của cùng fold, nếu có. Phải khớp TỪNG ca theo thứ tự —
        # ghép nhầm thứ tự sẽ cho ra một bảng số trông hợp lý mà sai hoàn toàn.
        det_path = path.parent / BEST
        if det_path.exists():
            det = load_predictions(det_path)
            if det["patient_ids"] != ids:
                raise ValueError(f"{fold_name}: thứ tự ca ở {BEST} lệch khỏi {filename}")
            deterministic_all.append(det["probs"])

    labels = np.concatenate(labels_all)
    mean_probs = np.concatenate(mean_all)
    epistemic = np.concatenate(epistemic_all)
    total = np.concatenate(total_all)
    deterministic = (
        np.concatenate(deterministic_all) if len(deterministic_all) == len(paths) else None
    )

    selective_rows = {
        "MC · max-prob": selective_row(labels, mean_probs, mean_probs.max(axis=1)),
        "MC · -entropy": selective_row(labels, mean_probs, -total),
        "MC · -epistemic": selective_row(labels, mean_probs, -epistemic),
    }
    if deterministic is not None:
        # PHÉP LAI: dự đoán lấy từ model tất định, chỉ ĐIỂM XẾP HẠNG defer lấy từ
        # epistemic của MC-dropout. Lý do: MC-dropout hạ macro-F1 rõ rệt (0.6851 →
        # 0.5852 trên out-of-fold E4) nên không dùng làm bộ dự đoán được; nhưng mức
        # bất đồng giữa các lượt vẫn là tín hiệu tốt về ca nào KHÓ, và "khó" là tính
        # chất của ca chứ không phải của người dự đoán. Đo được: xếp theo epistemic
        # nâng macro-F1@80% thêm +0.035 [+0.004, +0.065] P=0.030, trong khi xếp theo
        # max-prob của chính model đó không nâng được gì (−0.003, P=0.88) — WORKLOG S-087.
        selective_rows["LAI · tất định + -epistemic"] = selective_row(
            labels, deterministic, -epistemic
        )
        selective_rows["tất định · max-prob"] = selective_row(
            labels, deterministic, deterministic.max(axis=1)
        )

    return {
        "run_root": str(root),
        "n_folds": len(paths),
        "n_patients": int(len(labels)),
        "n_passes": sorted(n_passes),
        "macro_f1": macro_f1(labels, mean_probs.argmax(axis=1)),
        "macro_f1_deterministic": (
            macro_f1(labels, deterministic.argmax(axis=1)) if deterministic is not None else None
        ),
        "ece": adaptive_calibration_error(mean_probs, labels),
        "epistemic_summary": {
            "mean": float(epistemic.mean()),
            "min": float(epistemic.min()),
            "max": float(epistemic.max()),
        },
        "selective": selective_rows,
        "hybrid_available": deterministic is not None,
    }


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
    parser.add_argument(
        "--members",
        nargs="?",
        const="mc_dropout.npz",
        help="tên file member_probs trong mỗi fold* (mặc định mc_dropout.npz); "
        "thêm bảng bất định epistemic",
    )
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

    if args.members:
        m = report_members(args.run_dir, args.members)
        print(
            f"\n=== Bất định epistemic ({args.members}) ===\n"
            f"{m['n_folds']} fold · {m['n_patients']} ca · K = {m['n_passes']} lượt/ca"
        )
        print(f"macro-F1 của trung bình thành viên: {m['macro_f1']:.4f} · ECE {m['ece']:.4f}")
        if m.get("macro_f1_deterministic") is not None:
            delta = m["macro_f1"] - m["macro_f1_deterministic"]
            print(
                f"macro-F1 của model tất định:        {m['macro_f1_deterministic']:.4f}"
                f"   (MC-dropout {delta:+.4f})"
            )
            if delta < -0.02:
                print(
                    "  → MC-dropout LÀM TỆ đi độ chính xác, đừng dùng làm bộ dự đoán.\n"
                    "    Dùng hàng LAI: dự đoán tất định, chỉ xếp hạng defer bằng epistemic."
                )
        es = m["epistemic_summary"]
        print(f"epistemic: TB {es['mean']:.4f} · khoảng {es['min']:.4f}–{es['max']:.4f}")
        if es["max"] < 1e-9:
            print("⚠ epistemic bằng 0 khắp nơi — các thành viên giống hệt nhau, MC-dropout")
            print("  không thực sự chạy. Kiểm `count_dropout_modules` và `dropout_prob`.")
        print(_fmt_selective(m["selective"]))

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
