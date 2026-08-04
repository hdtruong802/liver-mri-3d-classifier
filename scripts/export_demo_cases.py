"""Trích ảnh 8 thì (+ mask) của vài bệnh nhân ra một thư mục, để dùng làm ca demo.

Chạy ở nơi CÓ dữ liệu LLD-MMRI gốc — thực tế là Kaggle, vì bộ ảnh 83.7GB không nằm
ở máy local:

    python scripts/export_demo_cases.py --out /kaggle/working/demo_cases

Không tham số nào cần khai đường dẫn: `resolve_data_root` tự lùng dataset gốc bằng
cách tìm file annotation (`configs/data.yaml`).

## Vì sao danh sách ca lại cố định trong file này

Bốn ca dưới đây **không phải chọn cho đẹp**. Chúng được chọn từ hành vi đo được của
model trên out-of-fold (WORKLOG S-089), mỗi ca minh hoạ một trạng thái mà giao diện
phải xử lý được — kể cả trạng thái model sai. Đổi danh sách này là đổi câu chuyện
bản demo kể, nên nó nằm trong git chứ không phải một tham số dòng lệnh.

⚠️ Cả bốn đều là ca **out-of-fold trong trainval**, không phải test-104. Test-104 là
held-out khoá kín, chạm đúng một lần (AGENTS.md §3.4) — dùng nó làm ca demo là tiêu
mất lần chạm đó cho một cái ảnh minh hoạ.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

# Chạy bằng `python scripts/export_demo_cases.py` thì gốc repo chưa nằm trên sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.images import scan_image_index
from src.utils.ids import normalize_pid
from src.utils.io import load_yaml, repo_root, resolve_data_root
from src.utils.logging import get_logger

logger = get_logger(__name__)

# pid -> vì sao ca này có mặt. Số liệu lấy từ `runs/E4_per_phase_results` (S-089).
DEMO_CASES: dict[str, str] = {
    "MR170828": (
        "Chạy tốt: u máu, đoán đúng, confidence 1.000, epistemic 0.0000. "
        "Trạng thái model tự tin và có quyền tự tin."
    ),
    "MR207769": (
        "CA HEADLINE. Thật là di căn, model đoán áp-xe — SAI — nhưng softmax vẫn nói "
        "0.936. Epistemic 0.3192, cao nhất tập, nên bị defer. Đây là toàn bộ luận điểm "
        "của đề tài trong một ca: độ tự tin của softmax không phát hiện được lỗi này, "
        "mức bất đồng giữa các lượt dự đoán thì có."
    ),
    "MR113627": (
        "Ác tính bắt đúng: ICC, đoán đúng, confidence 1.000, epistemic 0.0993 (dưới "
        "ngưỡng defer). Ca có ý nghĩa lâm sàng mà model xử lý được."
    ),
    "MR127280": (
        "THẤT BẠI THẬT, phải giữ trong demo. Thật là di căn, đoán u máu, confidence "
        "1.000, epistemic 0.0000 — defer KHÔNG bắt được. Giấu ca này đi là bán một "
        "bức tranh sai về mức tin cậy của hệ thống (PRODUCT.md)."
    ),
}


def export(out_dir: Path, patient_ids: list[str], with_masks: bool = True) -> dict[str, int]:
    """Chép ảnh (và mask) của từng bệnh nhân sang `out_dir/<pid>/`.

    Trả về ``{pid: số file đã chép}``. Bệnh nhân thiếu pha vẫn được chép phần có, và
    ghi cảnh báo — thiếu pha là thông tin cần biết, không phải lý do bỏ ngang.
    """
    config = load_yaml(repo_root() / "configs" / "data.yaml")
    data_root = resolve_data_root(config)
    annotation = data_root / config["annotation_rel"]
    if not annotation.exists():
        raise SystemExit(
            f"Không thấy {annotation}. Đang chạy ở máy không có dữ liệu gốc?\n"
            "Script này phải chạy trên Kaggle (hoặc nơi đã mount LLD-MMRI)."
        )

    images_dir = data_root / config["images_rel"]
    image_suffixes = config.get("image_suffixes", ("_0000.nii.gz", "_0000.nii"))
    index = scan_image_index(images_dir, image_suffixes)
    logger.info("quét %d file ảnh ở %s", len(index), images_dir)

    labels_dir = data_root / config["labels_rel"] if with_masks else None
    mask_index = (
        scan_image_index(labels_dir, config.get("label_suffixes", (".nii.gz", ".nii")))
        if labels_dir and labels_dir.is_dir()
        else {}
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    for pid in patient_ids:
        key = normalize_pid(pid)
        dest = out_dir / pid
        dest.mkdir(exist_ok=True)
        n = 0
        for (pkey, _token), path in sorted(index.items()):
            if pkey == key:
                shutil.copy2(path, dest / path.name)
                n += 1
        for (pkey, _token), path in sorted(mask_index.items()):
            if pkey == key:
                mask_dir = dest / "labels"
                mask_dir.mkdir(exist_ok=True)
                shutil.copy2(path, mask_dir / path.name)
                n += 1
        counts[pid] = n
        if n == 0:
            logger.warning("%s: KHÔNG thấy file nào (key chuẩn hoá %s)", pid, key)
        else:
            logger.info("%s: %d file -> %s", pid, n, dest)

    (out_dir / "cases.json").write_text(
        json.dumps(
            {
                pid: {"n_files": counts[pid], "vi_sao": DEMO_CASES.get(pid, "")}
                for pid in patient_ids
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="thư mục đích")
    parser.add_argument(
        "--cases",
        nargs="*",
        default=sorted(DEMO_CASES),
        help="patient id; mặc định là 4 ca demo đã chốt",
    )
    parser.add_argument("--no-masks", action="store_true", help="chỉ chép ảnh, bỏ mask")
    args = parser.parse_args()

    counts = export(Path(args.out), list(args.cases), with_masks=not args.no_masks)

    print(f"\n{'bệnh nhân':<14}{'số file':>9}")
    print("-" * 23)
    for pid, n in counts.items():
        print(f"{pid:<14}{n:>9}")
    thieu = [pid for pid, n in counts.items() if n == 0]
    if thieu:
        raise SystemExit(f"\nKhông trích được: {thieu}")
    print(f"\nĐã ghi {args.out}. Tải về, giải nén MỘT LỚP, đặt vào data/sample/.")


if __name__ == "__main__":
    main()
