"""Vẽ ba hình cho báo cáo kết thúc dự án, từ xác suất ĐÃ LƯU.

    python scripts/make_final_report_figures.py

Đầu ra, ghi vào `reports/assets/`:

    fig-reliability.png     reliability diagram, ensemble 5 fold, test-104
    fig-risk-coverage.png   đường risk–coverage, test-104
    fig-confusion.png       ma trận nhầm lẫn 7 lớp, test-104

Chỉ CPU, chỉ đọc `runs/<...>/test_probs.npz`. **Không phải một lượt chạm test-104
mới** — đọc lại tệp xác suất đã lưu thì không có suy luận nào chạy (AGENTS.md §3.4).

Đường risk–coverage và AURC gọi thẳng `src.eval.selective`, không cài lại, để hình
trong báo cáo và bảng số trong báo cáo chắc chắn đến từ cùng một phép tính.

Bảng màu: bản in trên giấy trắng, nên KHÔNG dùng nền tối của `DESIGN.md`. Giữ đúng
vai trò của hai màu chức năng trong đó — Hoàng Thổ là màu của chú số và đường nhấn,
Lam Ngọc là màu đối lập — nhưng làm tối lại cho đủ tương phản trên nền trắng. Mọi
thông tin đều có nhãn chữ đi kèm, không có gì chỉ mã hoá bằng màu (AGENTS.md §12).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.taxonomy import SHORT_NAMES  # noqa: E402
from src.eval.calibration import (  # noqa: E402
    adaptive_calibration_error,
    expected_calibration_error,
    reliability_curve,
)
from src.eval.selective import risk_coverage_curve  # noqa: E402

# Bản in: mực đậm trên giấy trắng.
INK = "#10161B"
INK_SOFT = "#5C666D"
RULE = "#C9CFD3"
KEY = "#8A6D11"  # Hoàng Thổ làm tối cho nền trắng
COUNTER = "#1F6F8B"  # Lam Ngọc làm tối cho nền trắng

DEFAULT_TEST = Path("runs/Uniformer3D/test/test_probs.npz")
DEFAULT_OUT = Path("reports/assets")
CLASSES = [SHORT_NAMES[i] for i in range(7)]

# Bin đều dùng để VẼ. Xem docstring plot_reliability về việc nó khác bin tính ECE.
N_BINS_EQUAL_WIDTH = 10


def _style(plt: Any) -> None:
    """Kiểu chung cho cả ba hình: mảnh, không lưới rối, không khung thừa."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",  # phủ đủ dấu tiếng Việt
            "font.size": 9,
            "axes.edgecolor": RULE,
            "axes.labelcolor": INK,
            "axes.linewidth": 0.8,
            "text.color": INK,
            "xtick.color": INK_SOFT,
            "ytick.color": INK_SOFT,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "figure.dpi": 200,
            "savefig.dpi": 200,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
        }
    )


def load_ensemble(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Trả về (nhãn thật, xác suất ensemble) — trung bình softmax của 5 thành viên."""
    data = np.load(path, allow_pickle=True)
    return data["labels"], data["member_probs"].mean(0)


def plot_reliability(plt: Any, labels: np.ndarray, probs: np.ndarray, out: Path) -> None:
    """Reliability diagram: độ tự tin so với độ chính xác thật.

    Cột nằm dưới đường chéo nghĩa là model tự tin hơn mức nó xứng đáng. Đây là hình
    mang phần đóng góp thứ nhất của dự án, nên nó phải đọc được mà không cần chú giải.

    ⚠️ **Hai cách chia bin cho hai con số khác nhau, và hình này nói ra cả hai.**
    `src.eval.test_report` in ECE bằng `adaptive_calibration_error` — chia theo số
    ca bằng nhau — nên con số trong bảng báo cáo là 0.0833. Vẽ cột theo đúng cách
    chia đó thì hình không đọc được: quá nửa số ca nằm ở độ tự tin ≈ 1.0 nên các cột
    cuối mảnh như sợi chỉ. Vì vậy **cột vẽ theo bin đều** (dễ đọc, và là quy ước phổ
    biến của reliability diagram), còn chú thích ghi rõ cả ECE chia đều lẫn ECE chia
    theo số ca. Không được bỏ một trong hai: bỏ cái đầu thì cột không khớp con số,
    bỏ cái sau thì hình mâu thuẫn với bảng ngay cạnh nó.
    """
    curve = reliability_curve(probs, labels, n_bins=N_BINS_EQUAL_WIDTH)
    ece_equal_width = expected_calibration_error(probs, labels, n_bins=N_BINS_EQUAL_WIDTH)
    ece_reported = adaptive_calibration_error(probs, labels)

    keep = curve.count > 0
    lowers = curve.bin_lower[keep]
    uppers = curve.bin_upper[keep]
    accuracies = curve.accuracy[keep]
    weights = curve.count[keep]

    figure, axes = plt.subplots(figsize=(5.2, 4.0))
    axes.plot([0, 1], [0, 1], linestyle="--", linewidth=0.9, color=INK_SOFT, zorder=1)
    axes.bar(
        lowers,
        accuracies,
        width=(uppers - lowers) * 0.9,
        align="edge",
        color=KEY,
        edgecolor=INK,
        linewidth=0.5,
        zorder=2,
    )
    for lower, upper, accuracy, weight in zip(lowers, uppers, accuracies, weights, strict=True):
        axes.text(
            lower + (upper - lower) * 0.45,
            accuracy + 0.02,
            f"{weight}",
            ha="center",
            fontsize=6.5,
            color=INK_SOFT,
            zorder=3,
        )

    axes.text(
        0.03,
        1.13,
        "Xác suất chưa hiệu chỉnh\n"
        f"ECE = {ece_reported:.4f}  (chia theo số ca — con số dùng trong báo cáo)\n"
        f"ECE = {ece_equal_width:.4f}  (chia đều, đúng như các cột dưới đây)\n"
        "số trên cột = số ca trong khoảng",
        fontsize=7,
        va="top",
        color=INK,
    )
    axes.annotate(
        "đường lý tưởng",
        xy=(0.17, 0.17),
        xytext=(0.015, 0.055),
        fontsize=7,
        color=INK_SOFT,
        arrowprops={"arrowstyle": "-", "color": INK_SOFT, "lw": 0.6},
    )
    axes.set_xlabel("Độ tự tin của mô hình")
    axes.set_ylabel("Độ chính xác thật trong khoảng")
    axes.set_xlim(0, 1)
    axes.set_ylim(0, 1.20)
    axes.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)
    figure.savefig(out)
    plt.close(figure)


def plot_risk_coverage(plt: Any, labels: np.ndarray, probs: np.ndarray, out: Path) -> None:
    """Đường risk–coverage, kèm hai mốc đọc: xếp ngẫu nhiên và xếp hoàn hảo.

    Không có hai mốc đó thì một đường đi xuống trông luôn có vẻ tốt.
    """
    correct = (probs.argmax(1) == labels).astype(float)
    curve = risk_coverage_curve(correct, probs.max(1))
    oracle = risk_coverage_curve(correct, correct)

    base_risk = 1.0 - correct.mean()
    figure, axes = plt.subplots(figsize=(5.0, 3.6))
    axes.axhline(base_risk, linestyle=":", linewidth=0.9, color=INK_SOFT)
    axes.plot(
        oracle.coverage,
        oracle.risk,
        linewidth=1.0,
        color=COUNTER,
        linestyle="--",
        label=f"xếp hoàn hảo · AURC {oracle.aurc:.4f}",
    )
    axes.plot(
        curve.coverage,
        curve.risk,
        linewidth=1.8,
        color=KEY,
        label=f"xác suất cao nhất · AURC {curve.aurc:.4f}",
    )

    for coverage in (0.8, 0.7):
        index = int(np.argmin(np.abs(curve.coverage - coverage)))
        axes.plot([curve.coverage[index]], [curve.risk[index]], "o", ms=4, color=INK)
        axes.annotate(
            f"{curve.coverage[index]:.0%} → sai {curve.risk[index]:.1%}",
            (curve.coverage[index], curve.risk[index]),
            textcoords="offset points",
            xytext=(-8, 12),
            ha="right",
            fontsize=7,
            color=INK,
        )

    axes.text(
        0.995,
        base_risk + 0.008,
        f"xếp ngẫu nhiên — sai {base_risk:.1%} ở mọi mức coverage",
        fontsize=7,
        ha="right",
        color=INK_SOFT,
    )
    axes.set_xlabel("Coverage — tỉ lệ ca mô hình tự quyết")
    axes.set_ylabel("Sai số trên phần đã quyết")
    axes.set_xlim(0.2, 1.0)
    axes.set_ylim(0, max(curve.risk) * 1.25)
    axes.legend(frameon=False, fontsize=7.5, loc="upper left")
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)
    figure.savefig(out)
    plt.close(figure)


def plot_confusion(plt: Any, labels: np.ndarray, probs: np.ndarray, out: Path) -> None:
    """Ma trận nhầm lẫn 7 lớp. Số in trong ô, không chỉ mã hoá bằng độ đậm."""
    from sklearn.metrics import confusion_matrix

    matrix = confusion_matrix(labels, probs.argmax(1), labels=range(7))
    figure, axes = plt.subplots(figsize=(5.0, 4.4))
    axes.imshow(matrix, cmap="Greys", vmin=0, vmax=matrix.max())

    threshold = matrix.max() * 0.55
    for row in range(7):
        for column in range(7):
            value = matrix[row, column]
            if value == 0:
                text, color = "·", RULE
            else:
                text = str(value)
                color = "white" if value > threshold else INK
            weight = "bold" if row == column else "normal"
            axes.text(column, row, text, ha="center", va="center", color=color, fontweight=weight)

    axes.set_xticks(range(7), CLASSES, rotation=40, ha="right")
    axes.set_yticks(range(7), CLASSES)
    axes.set_xlabel("Mô hình dự đoán")
    axes.set_ylabel("Chẩn đoán thật")
    axes.set_xticks(np.arange(-0.5, 7, 1), minor=True)
    axes.set_yticks(np.arange(-0.5, 7, 1), minor=True)
    axes.grid(which="minor", color="white", linewidth=1.2)
    axes.tick_params(which="minor", length=0)
    for side in ("top", "right", "bottom", "left"):
        axes.spines[side].set_visible(False)
    figure.savefig(out)
    plt.close(figure)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--test-probs", type=Path, default=DEFAULT_TEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    if not args.test_probs.exists():
        raise SystemExit(f"Không thấy '{args.test_probs}'.")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _style(plt)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    labels, probs = load_ensemble(args.test_probs)

    targets = [
        ("fig-reliability.png", plot_reliability),
        ("fig-risk-coverage.png", plot_risk_coverage),
        ("fig-confusion.png", plot_confusion),
    ]
    for name, plotter in targets:
        path = args.out_dir / name
        plotter(plt, labels, probs, path)
        print(f"  {path}")

    print(f"Xong — {len(targets)} hình, n = {len(labels)} ca.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
