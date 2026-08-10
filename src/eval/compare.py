"""So **có ghép cặp** hai cấu hình trên cùng bệnh nhân.

    python -m src.eval.compare --baseline runs/E4_cv_results --candidate runs/E8

Vì sao cần một module riêng thay vì so hai bảng metric bằng mắt: hai cấu hình chạy trên
**cùng** các bệnh nhân, nên phần lớn phương sai là phương sai của *tập dữ liệu* và nó
triệt tiêu khi lấy hiệu. Bootstrap riêng từng bên rồi so hai CI là bỏ mất đúng phần
triệt tiêu đó, và cho một phép kiểm yếu hơn thực tế rất nhiều.

Dự án đã cần phép so này năm lần (E5, E6, E6b, E12, E8 so với E4) và mỗi lần viết lại
một script rời. Nó ở đây để lần sau không phải viết lại, và để cách tính không trôi.

## Ba cổng chặn, mỗi cổng chặn một cách báo số sai

1. **Chỉ dùng fold có ở CẢ HAI bên.** Gộp 5 fold của một bên với 2 fold của bên kia là
   so trên hai tập bệnh nhân khác nhau, mà con số ra vẫn trông hợp lý.
2. **Tập bệnh nhân từng fold phải trùng khớp**, và dự đoán được sắp lại theo cùng thứ
   tự. Lệch thứ tự thì phép ghép cặp ghép sai người với người, và kết quả là nhiễu
   thuần đội lốt một phép kiểm.
3. **Nhãn thật của hai bên phải giống nhau** sau khi sắp. Khác nhau nghĩa là một bên đọc
   sai file split.

⚠️ Chỉ đọc `val_probs_*.npz`, không bao giờ chạm test-104 (AGENTS.md §3.4).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import numpy as np

from src.data.taxonomy import SHORT_NAMES
from src.eval.bootstrap import DEFAULT_SEED, N_RESAMPLES, stratified_indices
from src.eval.metrics import macro_f1, per_class_f1
from src.eval.run import BEST, find_fold_predictions, load_predictions
from src.utils.ids import normalize_pid
from src.utils.io import resolve_repo_path

FOLD_RE = re.compile(r"fold_?(\d+)")


def fold_number(dir_name: str) -> int:
    """Số fold suy từ tên thư mục: ``fold_1``, ``fold1``, ``fold1_4c2cf705`` đều được."""
    match = FOLD_RE.match(dir_name)
    if match is None:
        raise ValueError(f"không suy được số fold từ {dir_name!r}")
    return int(match.group(1))


def load_run(run_dir: str | Path, filename: str = BEST) -> dict[int, dict[str, Any]]:
    """Đọc dự đoán của một run, khoá theo **số fold** thay vì tên thư mục.

    Khoá theo số vì hai run khác kiến trúc có hash khác nhau trong tên thư mục
    (`fold1_4c2cf705` so với `fold1_9a1b2c3d`), nên khớp theo tên là không bao giờ khớp.
    """
    root = resolve_repo_path(run_dir)
    found = find_fold_predictions(root, filename)
    if not found:
        raise FileNotFoundError(f"không thấy {filename} nào dưới {root}")
    return {fold_number(name): load_predictions(path) for name, path in found.items()}


def align(a: dict[str, Any], b: dict[str, Any], fold: int) -> tuple[np.ndarray, ...]:
    """Sắp hai bộ dự đoán của cùng một fold về cùng thứ tự bệnh nhân.

    Trả về ``(labels, probs_a, probs_b)``. Nổ nếu tập bệnh nhân lệch hoặc nhãn lệch.
    """
    key_a = [normalize_pid(p) for p in a["patient_ids"]]
    key_b = [normalize_pid(p) for p in b["patient_ids"]]
    if set(key_a) != set(key_b):
        chi_a, chi_b = set(key_a) - set(key_b), set(key_b) - set(key_a)
        raise ValueError(
            f"fold {fold}: tập bệnh nhân lệch. Chỉ ở baseline: {sorted(chi_a)[:5]} "
            f"({len(chi_a)}); chỉ ở candidate: {sorted(chi_b)[:5]} ({len(chi_b)}). "
            "Hai run không chạy trên cùng split — phép ghép cặp vô nghĩa."
        )

    order_b = {key: i for i, key in enumerate(key_b)}
    take = np.array([order_b[key] for key in key_a], dtype=int)
    labels_a = np.asarray(a["labels"], dtype=int)
    labels_b = np.asarray(b["labels"], dtype=int)[take]
    if not np.array_equal(labels_a, labels_b):
        n = int((labels_a != labels_b).sum())
        raise ValueError(
            f"fold {fold}: {n} ca có nhãn thật khác nhau giữa hai run. Một bên đọc sai "
            "split hoặc sai cache."
        )
    return labels_a, np.asarray(a["probs"], dtype=float), np.asarray(b["probs"], dtype=float)[take]


def two_sided_p(diffs: np.ndarray) -> float:
    """P hai phía từ phân bố bootstrap của hiệu.

    Cùng cách tính với `src.eval.test_report.two_sided_p`, và cùng lý do: viết
    ``2 * min(m, 1 - m)`` cho P = 0 khi mọi hiệu bằng đúng 0, tức tuyên bố ý nghĩa
    tối đa cho một hiệu ứng bằng không.
    """
    low = float((diffs <= 0).mean())
    high = float((diffs >= 0).mean())
    return float(min(1.0, 2 * min(low, high)))


def paired_test(
    labels: np.ndarray,
    probs_a: np.ndarray,
    probs_b: np.ndarray,
    metric: Any = macro_f1,
    n_resamples: int = N_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> dict[str, float]:
    """Bootstrap ghép cặp trên **hiệu** ``metric(b) − metric(a)``.

    Mỗi lượt lấy mẫu lại **một** bộ chỉ số bệnh nhân rồi tính cả hai bên trên đúng bộ
    đó. Đây là chỗ phương sai của tập dữ liệu triệt tiêu; lấy mẫu hai bộ độc lập thì
    không triệt tiêu gì và CI rộng ra vô cớ.
    """
    pred_a, pred_b = probs_a.argmax(axis=1), probs_b.argmax(axis=1)
    observed = float(metric(labels, pred_b)) - float(metric(labels, pred_a))

    rng = np.random.default_rng(seed)
    diffs = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        idx = stratified_indices(labels, rng)
        diffs[i] = float(metric(labels[idx], pred_b[idx])) - float(metric(labels[idx], pred_a[idx]))

    return {
        "diff": observed,
        "lo": float(np.percentile(diffs, 2.5)),
        "hi": float(np.percentile(diffs, 97.5)),
        "p": two_sided_p(diffs),
        "n": int(labels.size),
    }


def compare(
    baseline_dir: str | Path,
    candidate_dir: str | Path,
    filename: str = BEST,
    n_resamples: int = N_RESAMPLES,
) -> dict[str, Any]:
    """So hai run trên các fold có ở cả hai bên."""
    a_runs, b_runs = load_run(baseline_dir, filename), load_run(candidate_dir, filename)
    folds = sorted(set(a_runs) & set(b_runs))
    if not folds:
        raise ValueError(
            f"không fold nào có ở cả hai bên. baseline: {sorted(a_runs)}, "
            f"candidate: {sorted(b_runs)}"
        )

    per_fold, labels_all, a_all, b_all = [], [], [], []
    for fold in folds:
        labels, pa, pb = align(a_runs[fold], b_runs[fold], fold)
        per_fold.append(
            {
                "fold": fold,
                "n": int(labels.size),
                "a": float(macro_f1(labels, pa.argmax(axis=1))),
                "b": float(macro_f1(labels, pb.argmax(axis=1))),
            }
        )
        labels_all.append(labels)
        a_all.append(pa)
        b_all.append(pb)

    labels = np.concatenate(labels_all)
    probs_a, probs_b = np.concatenate(a_all), np.concatenate(b_all)

    return {
        "folds": folds,
        "bo_qua": {
            "baseline": sorted(set(a_runs) - set(folds)),
            "candidate": sorted(set(b_runs) - set(folds)),
        },
        "per_fold": per_fold,
        "n": int(labels.size),
        "labels": labels,
        "probs_a": probs_a,
        "probs_b": probs_b,
        "pooled_a": float(macro_f1(labels, probs_a.argmax(axis=1))),
        "pooled_b": float(macro_f1(labels, probs_b.argmax(axis=1))),
        "paired": paired_test(labels, probs_a, probs_b, n_resamples=n_resamples),
    }


def format_report(result: dict[str, Any], name_a: str, name_b: str) -> str:
    """Bảng để dán thẳng vào WORKLOG."""
    lines: list[str] = []
    bo_qua = result["bo_qua"]
    if bo_qua["baseline"] or bo_qua["candidate"]:
        lines.append(
            f"⚠ bỏ qua fold chỉ có một bên — {name_a}: {bo_qua['baseline']} · "
            f"{name_b}: {bo_qua['candidate']}"
        )
        lines.append("")

    lines.append(f"{'fold':>5}{'n':>6}{name_a:>12}{name_b:>12}{'hiệu':>10}")
    lines.append("-" * 45)
    for row in result["per_fold"]:
        lines.append(
            f"{row['fold']:>5}{row['n']:>6}{row['a']:>12.4f}{row['b']:>12.4f}"
            f"{row['b'] - row['a']:>+10.4f}"
        )
    lines.append("-" * 45)
    lines.append(
        f"{'gộp':>5}{result['n']:>6}{result['pooled_a']:>12.4f}{result['pooled_b']:>12.4f}"
        f"{result['pooled_b'] - result['pooled_a']:>+10.4f}"
    )

    p = result["paired"]
    lines.append("")
    lines.append(f"bootstrap ghép cặp trên hiệu macro-F1 ({p['n']} ca, {N_RESAMPLES} lượt):")
    lines.append(
        f"  {name_b} − {name_a} = {p['diff']:+.4f}  CI95 [{p['lo']:+.4f}, {p['hi']:+.4f}]"
        f"  P = {p['p']:.3f}"
    )
    ket = (
        "CI chứa 0 — không phân biệt được về thống kê, giữ cấu hình gốc"
        if p["lo"] <= 0 <= p["hi"]
        else (
            "CI hoàn toàn dương — candidate thắng"
            if p["lo"] > 0
            else "CI hoàn toàn âm — candidate thua"
        )
    )
    lines.append(f"  => {ket}")

    labels = result["labels"]
    fa = per_class_f1(labels, result["probs_a"].argmax(axis=1))
    fb = per_class_f1(labels, result["probs_b"].argmax(axis=1))
    lines.append("")
    lines.append(f"{'lớp':<10}{'n':>5}{name_a:>13}{name_b:>13}{'hiệu':>10}")
    lines.append("-" * 51)
    for index in sorted(SHORT_NAMES):
        support = int((labels == index).sum())
        lines.append(
            f"{SHORT_NAMES[index]:<10}{support:>5}{fa[index]:>13.3f}{fb[index]:>13.3f}"
            f"{fb[index] - fa[index]:>+10.3f}"
        )

    lines.append("")
    lines.append(
        "⚠ Chênh lệch TỪNG FOLD là nhiễu nếu nhìn riêng (CI mỗi fold ~±0.19). Chỉ dòng "
        "'gộp' kèm CI mới đọc được."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, help="thư mục run của cấu hình gốc")
    parser.add_argument("--candidate", required=True, help="thư mục run của cấu hình mới")
    parser.add_argument("--file", default=BEST, help=f"tên file dự đoán (mặc định {BEST})")
    parser.add_argument("--resamples", type=int, default=N_RESAMPLES)
    args = parser.parse_args(argv)

    result = compare(args.baseline, args.candidate, args.file, args.resamples)
    name_a = Path(args.baseline).name[:11]
    name_b = Path(args.candidate).name[:11]
    print(format_report(result, name_a, name_b))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
