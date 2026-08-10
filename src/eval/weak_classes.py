"""Chẩn đoán ba lớp yếu (ICC · áp-xe · di căn) — vì sao chúng thấp, và cái gì KHÔNG chữa được.

    python -m src.eval.weak_classes --run-dir runs/E4_cv_results --compare runs/E6b \\
        --build-log runs/E4_per_phase_results/fold_1/cache_build_log.csv

Chạy hoàn toàn trên xác suất đã lưu (`val_probs_best.npz`) — **không cần GPU, không train
lại gì**. Mọi bảng ở đây in ra từ dữ liệu có sẵn.

## Vì sao module này tồn tại

Hai lớp yếu chặn mục tiêu về mặt **số học**: với F1 của ICC 0.519 và di căn 0.273 trên
test-104, kể cả 5 lớp còn lại đều đạt 0.90 thì macro-F1 cũng chỉ tới **0.756**. Nên trước
khi chi thêm một giờ GPU nào, phải biết chúng thấp vì lý do gì.

Sáu phân tích dưới đây **loại bỏ bảy hướng chữa** mà mỗi hướng lẽ ra tốn 4–20 giờ GPU để
phát hiện là vô ích (WORKLOG S-123). Đó là giá trị chính của nó, không phải các con số.

## Cái gì bị loại, và bằng chứng nào loại nó

| hướng | bị loại bởi |
|---|---|
| `class_weights: balanced` / `effective_number` | §1 — hai lớp yếu đã bị **thừa** dự đoán |
| logit adjustment, prior correction | §1 + §3 — sai chiều, và 0% lỗi sát sao |
| ngưỡng riêng từng lớp, vector scaling | §3 — không lỗi nào có biên < 0.10 |
| focal loss mạnh hơn | §1 |
| thêm augmentation | §5 — 74% lỗi trùng giữa hai cấu hình khác augmentation |
| gộp với một biến thể gần nó | §5 — đã đo, macro-F1 tệ đi |
| cắt sát tổn thương hơn | §2 — kích thước không tương quan với F1 |

## Sáu phân tích

1. **Cân bằng dự đoán** — số ca model *dự đoán* mỗi lớp so với số ca *thật*. Đây là phép
   kiểm quyết định: nếu lớp yếu bị dự đoán *thiếu* thì cân bằng lại lớp là đúng hướng; nếu
   bị dự đoán *thừa* thì mọi thứ nâng lớp hiếm lên sẽ làm tệ hơn.
2. **Kích thước tổn thương** theo lớp, từ `fov_mm` trong `cache_build_log.csv`, kèm tỉ lệ ca
   bị chạm sàn `min_fov_mm`.
3. **Độ tự tin của lỗi** — biên giữa `p(lớp đoán)` và `p(lớp thật)`. Biên nhỏ nghĩa là một
   chỉnh sửa ở tầng quyết định lật được; biên lớn nghĩa là không.
4. **Top-k** — lớp thật có nằm trong 2–3 ứng viên đầu không. Phân biệt "biểu diễn không mã
   hoá được lớp" với "mã hoá được nhưng xếp sai hạng".
5. **Trùng lặp lỗi giữa hai cấu hình** — lỗi có cấu trúc hay là nhiễu. So với kỳ vọng nếu
   hai bên độc lập.
6. **Ma trận nhầm lẫn + nguồn false positive** — lỗi của lớp *nào* tạo ra false positive cho
   lớp yếu, và chữa được thì macro-F1 tăng bao nhiêu.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np

from src.data.taxonomy import SHORT_NAMES
from src.eval.compare import align, load_run
from src.eval.metrics import macro_f1
from src.eval.run import find_fold_predictions, load_predictions, pool_out_of_fold
from src.utils.ids import normalize_pid
from src.utils.io import resolve_repo_path

# Dưới ngưỡng này thì một chỉnh sửa ở tầng quyết định (ngưỡng, prior, temperature) còn có
# cơ lật được lỗi. Trên nó thì không.
NARROW_MARGIN = 0.10

__all__ = [
    "NARROW_MARGIN",
    "confusion_report",
    "error_confidence",
    "error_overlap",
    "fp_source_gain",
    "lesion_geometry",
    "prediction_balance",
    "topk_report",
]


# --- §1 cân bằng dự đoán -------------------------------------------------------


def prediction_balance(labels: np.ndarray, pred: np.ndarray) -> dict[int, dict[str, float]]:
    """Số ca **dự đoán** so với số ca **thật** cho từng lớp, kèm precision/recall.

    Phép kiểm quan trọng nhất của module. ``predicted / actual > 1`` nghĩa là model đã
    *thiên vị* lớp đó rồi, và mọi cách "nâng lớp hiếm lên" (trọng số lớp, logit adjustment,
    focal mạnh hơn) sẽ đẩy nó xa hơn khỏi đúng.
    """
    out: dict[int, dict[str, float]] = {}
    for index in sorted(SHORT_NAMES):
        actual = int((labels == index).sum())
        predicted = int((pred == index).sum())
        tp = int(((pred == index) & (labels == index)).sum())
        out[index] = {
            "actual": actual,
            "predicted": predicted,
            "ratio": predicted / max(actual, 1),
            "precision": tp / max(predicted, 1),
            "recall": tp / max(actual, 1),
            "f1": 2 * tp / max(predicted + actual, 1),
        }
    return out


# --- §2 hình học tổn thương ----------------------------------------------------


def lesion_geometry(
    labels: np.ndarray, ids: list[str], build_log: str | Path, margin_factor: float = 1.6
) -> dict[int, dict[str, float]]:
    """Kích thước tổn thương theo lớp, từ ``fov_mm`` của `cache_build_log.csv`.

    ``fov_mm = max(extent_mm * margin_factor, min_fov_mm)``, nên ``fov`` đúng bằng sàn
    (40mm ở mọi cache của dự án) nghĩa là tổn thương nhỏ hơn ``40 / margin_factor``. Tỉ lệ
    ca chạm sàn là thứ đáng xem: ở đó tổn thương chỉ chiếm một phần nhỏ của khối đưa vào.
    """
    with Path(build_log).open(encoding="utf-8") as handle:
        rows = {normalize_pid(r["patient_id"]): r for r in csv.DictReader(handle)}
    thieu = [i for i in ids if normalize_pid(i) not in rows]
    if thieu:
        raise ValueError(f"{len(thieu)} bệnh nhân không có trong build log, vd {thieu[:3]}")
    fov = np.array([[float(v) for v in rows[normalize_pid(i)]["fov_mm"].split()] for i in ids])
    floor = np.abs(fov - fov.min()) < 0.05  # sàn = giá trị nhỏ nhất xuất hiện

    out: dict[int, dict[str, float]] = {}
    for index in sorted(SHORT_NAMES):
        m = labels == index
        out[index] = {
            "n": int(m.sum()),
            "extent_xy_median": float(np.median(fov[m, :2]) / margin_factor),
            "extent_z_median": float(np.median(fov[m, 2]) / margin_factor),
            "floor_xy_frac": float(floor[m, :2].all(axis=1).mean()),
            "floor_all_frac": float(floor[m].all(axis=1).mean()),
        }
    return out


# --- §3 độ tự tin của lỗi ------------------------------------------------------


def error_confidence(
    labels: np.ndarray, probs: np.ndarray, narrow: float = NARROW_MARGIN
) -> dict[int, dict[str, float]]:
    """Biên giữa ``p(lớp đoán)`` và ``p(lớp thật)`` trên các ca SAI.

    Nếu tỉ lệ lỗi có biên < `narrow` gần 0 thì **không ngưỡng nào, prior nào, hay
    temperature nào lật được chúng** — cả họ sửa-ở-tầng-quyết-định bị loại. Temperature
    scaling càng không: nó là phép biến đổi đơn điệu, giữ nguyên thứ hạng.
    """
    pred = probs.argmax(axis=1)
    top = probs.max(axis=1)
    true_p = probs[np.arange(len(labels)), labels]
    wrong = pred != labels

    out: dict[int, dict[str, float]] = {}
    for index in sorted(SHORT_NAMES):
        m = (labels == index) & wrong
        if not m.any():
            out[index] = {
                "n_wrong": 0,
                "p_pred": float("nan"),
                "p_true": float("nan"),
                "margin": float("nan"),
                "narrow_frac": float("nan"),
            }
            continue
        gap = top[m] - true_p[m]
        out[index] = {
            "n_wrong": int(m.sum()),
            "p_pred": float(np.median(top[m])),
            "p_true": float(np.median(true_p[m])),
            "margin": float(np.median(gap)),
            "narrow_frac": float((gap < narrow).mean()),
        }
    return out


# --- §4 top-k ------------------------------------------------------------------


def topk_report(labels: np.ndarray, probs: np.ndarray) -> dict[int, dict[str, float]]:
    """Lớp thật xếp hạng thứ mấy trong dự đoán.

    Phân biệt hai bệnh hoàn toàn khác nhau, và chúng cần hai cách chữa khác nhau:

    - ``top2 >> top1``: thông tin **có** trong biểu diễn, chỉ xếp sai hạng ⇒ bài toán phân
      biệt giữa vài ứng viên.
    - ``top2 == top1``: không một ca sai nào có lớp thật ở vị trí thứ hai ⇒ biểu diễn
      **không mã hoá** được lớp đó. Không mẹo xếp hạng nào cứu được.
    """
    order = np.argsort(-probs, axis=1)
    rank = np.array([int(np.flatnonzero(order[i] == labels[i])[0]) for i in range(len(labels))])
    out: dict[int, dict[str, float]] = {}
    for index in sorted(SHORT_NAMES):
        m = labels == index
        if not m.any():
            # Lớp hiếm có thể vắng hẳn ở một fold. Trả nan tường minh thay vì để numpy
            # kêu "Mean of empty slice" rồi cho nan — người đọc bảng cần biết là VẮNG,
            # không phải 0.0.
            out[index] = dict.fromkeys(("top1", "top2", "top3", "rank_median"), float("nan"))
            out[index]["n"] = 0
            continue
        out[index] = {
            "n": int(m.sum()),
            "top1": float((rank[m] == 0).mean()),
            "top2": float((rank[m] < 2).mean()),
            "top3": float((rank[m] < 3).mean()),
            "rank_median": float(np.median(rank[m]) + 1),
        }
    return out


# --- §5 trùng lặp lỗi ----------------------------------------------------------


def error_overlap(labels: np.ndarray, pred_a: np.ndarray, pred_b: np.ndarray) -> dict[str, Any]:
    """Lỗi của hai cấu hình có trùng nhau hơn mức ngẫu nhiên không.

    Trùng lặp cao hơn hẳn kỳ vọng độc lập nghĩa là lỗi **có cấu trúc** — cùng những ca đó
    sai bất kể cấu hình, nên đổi augmentation hay seed không chạm được vào chúng.

    Cũng trả về macro-F1 của phép **gộp xác suất** và của **oracle** (một trong hai đúng).
    Khoảng giữa hai số đó là phần ensemble không khai thác được.
    """
    wa, wb = pred_a != labels, pred_b != labels
    per_class: dict[int, dict[str, float]] = {}
    for index in sorted(SHORT_NAMES):
        m = labels == index
        na, nb = int((wa & m).sum()), int((wb & m).sum())
        per_class[index] = {
            "n": int(m.sum()),
            "wrong_a": na,
            "wrong_b": nb,
            "wrong_both": int((wa & wb & m).sum()),
            "expected_if_independent": na * nb / max(int(m.sum()), 1),
        }
    na, nb = int(wa.sum()), int(wb.sum())
    return {
        "per_class": per_class,
        "wrong_a": na,
        "wrong_b": nb,
        "wrong_both": int((wa & wb).sum()),
        "expected_if_independent": na * nb / max(len(labels), 1),
        "overlap_frac": (wa & wb).sum() / max(min(na, nb), 1),
        "oracle_accuracy": float((~wa | ~wb).mean()),
    }


# --- §6 ma trận nhầm lẫn và nguồn false positive -------------------------------


def confusion_report(labels: np.ndarray, pred: np.ndarray) -> np.ndarray:
    """Ma trận nhầm lẫn ``[thật, đoán]`` với thứ tự lớp của `SHORT_NAMES`."""
    n = len(SHORT_NAMES)
    matrix = np.zeros((n, n), dtype=int)
    for t, p in zip(labels, pred, strict=True):
        matrix[t, p] += 1
    return matrix


def fp_source_gain(labels: np.ndarray, pred: np.ndarray, source: int) -> dict[str, Any]:
    """Macro-F1 tăng bao nhiêu nếu chữa hết lỗi mà lớp `source` gây ra cho lớp khác.

    Đây là phép tính đáng giá nhất ở §6: lớp đa số (HCC, 125/394 ca) sinh ra phần lớn
    **false positive** của hai lớp yếu, nên nút thắt precision của chúng phần lớn là lỗi
    của lớp *mạnh*. Muốn nâng lớp yếu thì có thể phải chữa lớp mạnh.

    Không phải một can thiệp — là một phép đo trần, để biết hướng nào đáng theo.
    """
    fixed = pred.copy()
    leaked = (labels == source) & (pred != source)
    fixed[leaked] = source
    return {
        "source": SHORT_NAMES[source],
        "n_leaked": int(leaked.sum()),
        "leaked_to": {
            SHORT_NAMES[k]: int((leaked & (pred == k)).sum())
            for k in sorted(SHORT_NAMES)
            if (leaked & (pred == k)).any()
        },
        "macro_f1_before": float(macro_f1(labels, pred)),
        "macro_f1_after": float(macro_f1(labels, fixed)),
    }


# --- in báo cáo ----------------------------------------------------------------


def _p(title: str) -> None:
    print(f"\n=== {title} ===")


def report(
    run_dir: str | Path,
    compare_dir: str | Path | None = None,
    build_log: str | Path | None = None,
) -> dict[str, Any]:
    """In đủ sáu phân tích; trả về dict để test và notebook dùng lại."""
    root = resolve_repo_path(run_dir)
    pooled = pool_out_of_fold(
        {n: load_predictions(p) for n, p in find_fold_predictions(root).items()}
    )
    labels, probs, ids = pooled["labels"], pooled["probs"], pooled["patient_ids"]
    pred = probs.argmax(axis=1)
    print(
        f"{Path(run_dir).name}: {len(labels)} ca out-of-fold · "
        f"macro-F1 {macro_f1(labels, pred):.4f} · accuracy {(pred == labels).mean():.4f}"
    )

    out: dict[str, Any] = {"n": len(labels), "labels": labels, "probs": probs}

    _p("§1 CÂN BẰNG DỰ ĐOÁN — lớp yếu bị dự đoán thừa hay thiếu")
    bal = out["balance"] = prediction_balance(labels, pred)
    print(f"{'lớp':<10}{'thật':>6}{'đoán':>7}{'tỉ lệ':>8}{'P':>7}{'R':>7}{'F1':>7}")
    print("-" * 52)
    for i in sorted(SHORT_NAMES):
        r = bal[i]
        print(
            f"{SHORT_NAMES[i]:<10}{r['actual']:>6}{r['predicted']:>7}{r['ratio']:>8.2f}"
            f"{r['precision']:>7.3f}{r['recall']:>7.3f}{r['f1']:>7.3f}"
        )
    thua = [SHORT_NAMES[i] for i in bal if bal[i]["ratio"] > 1.1]
    if thua:
        print(f"\n⚠ {thua} bị dự đoán THỪA -> trọng số lớp / logit adjustment sẽ làm TỆ ĐI.")

    if build_log:
        _p("§2 KÍCH THƯỚC TỔN THƯƠNG — có tương quan với F1 không")
        geo = out["geometry"] = lesion_geometry(labels, ids, build_log)
        print(
            f"{'lớp':<10}{'n':>4}{'F1':>7}{'extent XY':>11}{'extent Z':>10}"
            f"{'sàn XY':>9}{'sàn cả 3':>10}"
        )
        print("-" * 61)
        for i in sorted(SHORT_NAMES):
            g = geo[i]
            print(
                f"{SHORT_NAMES[i]:<10}{g['n']:>4}{bal[i]['f1']:>7.3f}"
                f"{g['extent_xy_median']:>11.1f}{g['extent_z_median']:>10.1f}"
                f"{100 * g['floor_xy_frac']:>8.0f}%{100 * g['floor_all_frac']:>9.0f}%"
            )

    _p("§3 ĐỘ TỰ TIN CỦA LỖI — tầng quyết định có cứu được không")
    conf = out["confidence"] = error_confidence(labels, probs)
    print(f"{'lớp':<10}{'n sai':>7}{'p(đoán)':>10}{'p(thật)':>10}{'biên':>8}{'sát sao':>9}")
    print("-" * 54)
    for i in sorted(SHORT_NAMES):
        c = conf[i]
        if not c["n_wrong"]:
            continue
        print(
            f"{SHORT_NAMES[i]:<10}{c['n_wrong']:>7}{c['p_pred']:>10.3f}{c['p_true']:>10.3f}"
            f"{c['margin']:>8.3f}{100 * c['narrow_frac']:>8.0f}%"
        )
    tong_sat = sum(c["narrow_frac"] * c["n_wrong"] for c in conf.values() if c["n_wrong"])
    tong_sai = sum(c["n_wrong"] for c in conf.values())
    print(f"\nsát sao = biên < {NARROW_MARGIN}: {tong_sat:.0f}/{tong_sai} lỗi")
    if tong_sai and tong_sat / tong_sai < 0.05:
        print("⚠ Gần như không lỗi nào sát sao -> ngưỡng/prior/temperature KHÔNG lật được.")

    _p("§4 TOP-K — biểu diễn có mã hoá được lớp không")
    tk = out["topk"] = topk_report(labels, probs)
    print(f"{'lớp':<10}{'n':>4}{'top-1':>8}{'top-2':>8}{'top-3':>8}{'hạng tv':>9}")
    print("-" * 47)
    for i in sorted(SHORT_NAMES):
        t = tk[i]
        if not t["n"]:
            print(f"{SHORT_NAMES[i]:<10}{0:>4}   (vắng ở tập này)")
            continue
        print(
            f"{SHORT_NAMES[i]:<10}{t['n']:>4}{t['top1']:>8.3f}{t['top2']:>8.3f}"
            f"{t['top3']:>8.3f}{t['rank_median']:>9.0f}"
        )
    mu = [SHORT_NAMES[i] for i in tk if tk[i]["n"] and tk[i]["top2"] <= tk[i]["top1"] + 1e-9]
    if mu:
        print(f"\n⚠ {mu}: top-2 KHÔNG hơn top-1 — không ca sai nào có lớp thật ở hạng hai.")
        print("  Biểu diễn không mã hoá được lớp này; mẹo xếp hạng không cứu được.")

    _p("§6 MA TRẬN NHẦM LẪN (hàng = thật, cột = đoán)")
    matrix = out["confusion"] = confusion_report(labels, pred)
    print("       " + "".join(f"{SHORT_NAMES[i][:6]:>8}" for i in sorted(SHORT_NAMES)))
    for i in sorted(SHORT_NAMES):
        print(f"{SHORT_NAMES[i]:<7}" + "".join(f"{v:>8}" for v in matrix[i]))
    big = sorted(
        ((matrix[t, p], t, p) for t in sorted(SHORT_NAMES) for p in sorted(SHORT_NAMES) if t != p),
        reverse=True,
    )[:3]
    print(
        "\nba hướng nhầm lớn nhất: "
        + " · ".join(f"{SHORT_NAMES[t]} -> {SHORT_NAMES[p]} ({n})" for n, t, p in big)
    )

    major = max(sorted(SHORT_NAMES), key=lambda i: bal[i]["actual"])
    gain = out["fp_gain"] = fp_source_gain(labels, pred, major)
    print(
        f"\nTrần nếu chữa hết {gain['n_leaked']} lỗi của lớp đa số "
        f"'{gain['source']}': macro-F1 {gain['macro_f1_before']:.4f} -> "
        f"{gain['macro_f1_after']:.4f} ({gain['macro_f1_after'] - gain['macro_f1_before']:+.4f})"
    )
    print(f"  lỗi đó rơi vào: {gain['leaked_to']}")

    if compare_dir:
        _p("§5 TRÙNG LẶP LỖI VỚI CẤU HÌNH KHÁC — có cấu trúc hay là nhiễu")
        a, b = load_run(root), load_run(resolve_repo_path(compare_dir))
        folds = sorted(set(a) & set(b))
        Y, PA, PB = [], [], []
        for f in folds:
            yy, pa, pb = align(a[f], b[f], f)
            Y.append(yy)
            PA.append(pa)
            PB.append(pb)
        yy = np.concatenate(Y)
        pa, pb = np.concatenate(PA), np.concatenate(PB)
        ov = out["overlap"] = error_overlap(yy, pa.argmax(axis=1), pb.argmax(axis=1))
        name_b = Path(compare_dir).name
        print(f"trên {len(yy)} ca, fold {folds}")
        print(f"{'lớp':<10}{'n':>4}{'sai A':>7}{'sai B':>7}{'sai CẢ HAI':>12}{'kỳ vọng':>10}")
        print("-" * 50)
        for i in sorted(SHORT_NAMES):
            r = ov["per_class"][i]
            print(
                f"{SHORT_NAMES[i]:<10}{r['n']:>4}{r['wrong_a']:>7}{r['wrong_b']:>7}"
                f"{r['wrong_both']:>12}{r['expected_if_independent']:>10.1f}"
            )
        print("-" * 50)
        print(
            f"{'TẤT CẢ':<10}{len(yy):>4}{ov['wrong_a']:>7}{ov['wrong_b']:>7}"
            f"{ov['wrong_both']:>12}{ov['expected_if_independent']:>10.1f}"
        )
        print(
            f"\ntrùng lặp {ov['overlap_frac']:.0%} của bên ít lỗi hơn, so với kỳ vọng "
            f"{ov['expected_if_independent'] / max(min(ov['wrong_a'], ov['wrong_b']), 1):.0%} "
            f"nếu độc lập"
        )
        if ov["overlap_frac"] > 0.5:
            print("⚠ Lỗi CÓ CẤU TRÚC -> đổi augmentation/seed không chạm được vào chúng.")
        ens = (pa + pb) / 2
        print(
            f"\ngộp xác suất: {macro_f1(yy, ens.argmax(axis=1)):.4f}  so với "
            f"A {macro_f1(yy, pa.argmax(axis=1)):.4f} / B {macro_f1(yy, pb.argmax(axis=1)):.4f}"
            f"   ({name_b})"
        )
        print(f"oracle (một trong hai đúng): accuracy {ov['oracle_accuracy']:.3f}")
        print("  khoảng giữa 'gộp' và 'oracle' là phần ensemble KHÔNG khai thác được")

    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="thư mục run có val_probs_best.npz")
    parser.add_argument("--compare", default=None, help="run thứ hai, để đo trùng lặp lỗi (§5)")
    parser.add_argument("--build-log", default=None, help="cache_build_log.csv, để đo §2")
    args = parser.parse_args(argv)
    report(args.run_dir, args.compare, args.build_log)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
