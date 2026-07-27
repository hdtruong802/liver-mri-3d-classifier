"""Báo cáo geometry đầy đủ cho T2.2 — chạy một lệnh trên Kaggle.

    python scripts/kaggle_geometry_report.py            # 60 bệnh nhân đầu
    python scripts/kaggle_geometry_report.py --limit 0   # toàn bộ 498 (chậm hơn)

In ra tất cả số liệu cần để chốt tham số tiền xử lý (T2.2):
thứ tự trục · ca thiếu pha · lưới từng pha · kích thước lesion + crop size.

Chỉ đọc header NIfTI (không nạp pixel) nên nhanh, không tốn RAM.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Console Windows mặc định cp1252 -> mọi print tiếng Việt sẽ ném UnicodeEncodeError.
# Kaggle (Linux) vốn UTF-8, nhưng ép ở đây để script chạy được ở cả hai nơi.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.data.annotation import Annotation  # noqa: E402
from src.data.eda import (  # noqa: E402
    bbox_stats,
    class_distribution,
    format_class_distribution,
    missing_phase_report,
    recommend_crop_size,
)
from src.data.geometry_gate import disambiguate_axis_order, run_gate  # noqa: E402
from src.data.images import scan_image_index  # noqa: E402
from src.utils.io import load_yaml, resolve_data_root  # noqa: E402


def _header(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def main() -> None:
    # description để ASCII: console Windows (cp1252) không in được tiếng Việt khi --help.
    parser = argparse.ArgumentParser(description="Geometry report for T2.2 (see module docstring)")
    parser.add_argument("--config", default="configs/data.yaml")
    parser.add_argument("--limit", type=int, default=60, help="so benh nhan quet; 0 = tat ca")
    parser.add_argument("--ref-phase", default="C+V", help="pha tham chieu cho bbox/crop")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    config = load_yaml(repo / args.config)
    data_root = resolve_data_root(config)
    phases = config["phases"]
    tokens = [p["file"] for p in phases]

    print("data root:", data_root)
    annotation_path = data_root / config["annotation_rel"]
    if not annotation_path.exists():
        print(f"\nKHÔNG THẤY DỮ LIỆU: {annotation_path}")
        print("Script này cần chạy ở nơi có data (Kaggle). Kiểm tra:")
        print("  - dataset đã Add Input vào notebook chưa;")
        print("  - hoặc đặt env LLDMMRI_DATA_ROOT trỏ tới thư mục chứa lld/.")
        raise SystemExit(1)

    ann = Annotation(annotation_path)
    index = scan_image_index(data_root / config["images_rel"], config["image_suffixes"])
    print(f"annotation: {len(ann)} bệnh nhân | ảnh đã lập chỉ mục: {len(index)} file")

    pids = ann.patient_ids()
    scan_pids = pids if args.limit == 0 else pids[: args.limit]

    _header("1. PHÂN BỐ LỚP")
    print(format_class_distribution(class_distribution(ann)))

    _header("2. CA THIẾU PHA (toàn bộ 498)")
    rep = missing_phase_report(ann, index, tokens)
    print(f"đủ 8 pha: {rep.n_complete}/{rep.n_patients} | thiếu: {rep.n_incomplete}")
    for token, n in rep.missing_by_phase.items():
        if n:
            print(f"  thiếu {token:<10}: {n} ca")
    for pid, missing in rep.incomplete_patients[:10]:
        print(f"    {pid}: {missing}")

    _header(f"3. GATE GEOMETRY ({len(scan_pids)} bệnh nhân)")
    gate = run_gate(scan_pids, ann, index, phases)
    print(gate.summary().split("\n\n")[0])  # chỉ dòng tổng kết, không liệt kê từng dòng

    _header("4. THỨ TỰ TRỤC (dựa trên ảnh KHÔNG vuông)")
    print(disambiguate_axis_order(scan_pids, ann, index, phases).summary())

    _header(f"5. LƯỚI TỪNG PHA ({len(scan_pids)} bệnh nhân)")
    print("Số slice/pha khác nhau ⇒ phải resample về grid chung trước khi fusion.")
    for phase in phases:
        name = phase["name"]
        shapes: Counter[str] = Counter()
        zs: list[float] = []
        for pid in scan_pids:
            try:
                entry = ann.phase_entry(pid, name)
            except KeyError:
                continue
            ps = entry.get("pixel_spacing") or [0, 0]
            shapes[f"{float(ps[0]):.3f}"] += 1
            zs.append(float(entry.get("slice_spacing") or 0))
        if not zs:
            continue
        zs.sort()
        top = ", ".join(f"{k}mm×{v}" for k, v in shapes.most_common(3))
        print(
            f"  {name:<11} pixel_spacing hay gặp: {top:<34} "
            f"slice_spacing p50={zs[len(zs) // 2]:.1f} [{zs[0]:.1f}..{zs[-1]:.1f}]"
        )

    _header(f"6. KÍCH THƯỚC LESION + CROP SIZE (pha {args.ref_phase})")
    stats = bbox_stats(ann, args.ref_phase)
    for label, values in [
        ("rộng (mm)", [s.width_mm for s in stats]),
        ("cao  (mm)", [s.height_mm for s in stats]),
        ("sâu  (mm)", [s.depth_mm for s in stats]),
        ("sâu  (slice)", [float(s.depth_slices) for s in stats]),
    ]:
        v = sorted(values)
        print(
            f"  {label:<13} p50={v[len(v) // 2]:7.1f}  "
            f"p95={v[int(0.95 * (len(v) - 1))]:7.1f}  max={v[-1]:7.1f}"
        )
    rec = recommend_crop_size(stats, target_spacing=(1.5, 1.5, 3.0), margin=1.3)
    print("\n  khuyến nghị @1.5×1.5×3.0mm, margin 1.3, phủ p95:")
    for k, val in rec.items():
        print(f"    {k:<26}: {val}")
    if rec:
        ok = rec["voxels_x"] <= 96 and rec["voxels_y"] <= 96 and rec["voxels_z"] <= 48
        print(f"\n  Spec Sheet chốt 96×96×48 → {'ĐỦ phủ p95' if ok else 'KHÔNG đủ, cần chỉnh'}")

    _header("XONG — dán toàn bộ output này để chốt T2.2")


if __name__ == "__main__":
    main()
