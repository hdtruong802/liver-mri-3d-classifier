"""Suy luận trên **test-104 official** — held-out khoá kín, chạm ĐÚNG MỘT LẦN.

    python -m src.eval.test_once --ckpt-dir <thư mục 5 best_fold_N.pt> \
        --config configs/baseline_3dpatch.yaml --out runs/test104 --i-know-this-is-final

Module này **chỉ suy luận và lưu xác suất**. Nó không tính metric, không in điểm số,
không hiệu chỉnh gì. Đọc số là việc của `src/eval/test_report.py`, chạy trên CPU từ
file `.npz` đã lưu.

Tách hai bước là có chủ đích, không phải để cho gọn:

- **Bước chạm test chỉ xảy ra một lần** và nó tốn GPU. Nếu gộp cả phần báo cáo vào
  đây thì mỗi lần muốn xem thêm một metric lại phải chạy lại inference — mà "chạy
  lại" trên test-104 là chính thứ AGENTS.md §3.4 cấm.
- Sau khi có `.npz`, phần đọc số chạy lại được bao nhiêu lần cũng vô hại: nó không
  đọc ảnh, không đổi dự đoán, không thể vô tình biến thành lần chạm thứ hai.

## Ba cổng chặn

1. Cờ `--i-know-this-is-final` — không có thì từ chối chạy.
2. `docs/TEST104_PREREGISTRATION.md` phải tồn tại **và đã được commit**. Pre-registration
   viết sau khi nhìn số thì vô nghĩa; kiểm bằng git chứ không kiểm sự tồn tại của file.
3. sha256 của 5 checkpoint phải khớp danh sách ghim trong pre-registration.

## Vì sao ensemble 5 fold hợp lệ ở ĐÂY mà bị cấm trên out-of-fold

Không model nào trong 5 cái từng thấy 104 ca này: cả 5 chỉ train trên tập con của 394
ca trainval, và `Splits.validate()` khẳng định ``val_fold_i ∩ test = ∅`` với mọi ``i``.
Trên out-of-fold thì ngược lại — mỗi ca ở val của fold ``f`` nằm trong tập train của
**cả 4 model kia**, nên gộp lại là để 4/5 thành viên chấm bài họ đã học thuộc
(AGENTS.md §3, WORKLOG S-080).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from src.data.dataset import build_test_dataset
from src.data.splits import N_TEST, Splits
from src.utils.io import load_yaml, resolve_cache_dir, resolve_repo_path

PREREG = "docs/TEST104_PREREGISTRATION.md"

# Ghim ở WORKLOG S-081, đối chiếu lại ở S-107. Đây là 5 checkpoint E4 duy nhất được
# phép chạm test — xem `docs/TEST104_PREREGISTRATION.md` §1.
PINNED_SHA256 = {
    1: "2e1f3e1ad477ad59",
    2: "30a8eb9ee221d453",
    3: "00c133e031bdf8fe",
    4: "3fe18f1eb3de4431",
    5: "d61cc7ed94b8ebf0",
}


def sha16(path: Path) -> str:
    """16 ký tự đầu của sha256 — đủ phân biệt, đủ ngắn để đọc bằng mắt."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def find_checkpoints(ckpt_dir: str | Path, folds: list[int]) -> dict[int, Path]:
    """Tìm checkpoint từng fold. Chấp cả `best_fold_N.pt` phẳng lẫn `fold_N/best.pt`.

    Không đoán bừa: fold nào không suy ra được từ tên thì bỏ, và hàm gọi sẽ nổ vì
    thiếu. Nhận nhầm fold ở đây tạo ra một "ensemble" có model bị đếm hai lần, và
    con số ra vẫn trông hoàn toàn hợp lý.
    """
    root = Path(ckpt_dir)
    found: dict[int, Path] = {}
    for fold in folds:
        flat = sorted(root.rglob(f"best_fold_{fold}.pt"))
        nested = [
            p
            for p in sorted(root.rglob("best.pt"))
            if p.parent.name in (f"fold_{fold}", f"fold{fold}")
        ]
        hits = flat or nested
        if hits:
            found[fold] = hits[0]
    return found


def check_prereg_committed(repo_root: Path) -> str:
    """Trả về sha commit chứa pre-registration; nổ nếu nó chưa được commit.

    Kiểm **git** chứ không kiểm sự tồn tại của file: một file viết ra rồi chạy ngay
    trong cùng một phiên thì không chứng minh được nó có trước khi nhìn số. Commit
    có timestamp và không sửa lại được mà không để dấu vết.
    """
    path = repo_root / PREREG
    if not path.exists():
        raise RuntimeError(
            f"chưa có {PREREG}. Test-104 chạm đúng một lần (AGENTS.md §3.4) — "
            f"phải khoá protocol bằng văn bản TRƯỚC, không phải sau."
        )
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", PREREG],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    sha = result.stdout.strip()
    if not sha:
        raise RuntimeError(
            f"{PREREG} tồn tại nhưng CHƯA COMMIT. Pre-registration chỉ có giá trị nếu "
            f"nó được ghim vào lịch sử trước khi chạy. Commit nó rồi chạy lại."
        )
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", PREREG],
        cwd=repo_root,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if dirty:
        raise RuntimeError(f"{PREREG} có thay đổi chưa commit: {dirty!r}. Commit rồi chạy lại.")
    return sha


def predict_members(
    config: dict[str, Any],
    checkpoints: dict[int, Path],
    cache_dir: str | Path,
    splits_dir: str | Path = "splits",
    batch_size: int | None = None,
) -> dict[str, Any]:
    """Chạy cả 5 model trên test-104; trả `member_probs` dạng ``(K, N, C)``.

    Không trung bình ở đây — lưu từng thành viên. Bất đồng giữa các thành viên chính
    là đại lượng epistemic mà §4 của pre-registration đã chốt làm điểm xếp hạng defer;
    trung bình sớm là vứt nó đi.
    """
    import torch
    from torch.utils.data import DataLoader

    from src.models import build_model

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_config = config.get("data") or {}
    dataset = build_test_dataset(cache_dir, splits_dir=splits_dir)
    if len(dataset) != N_TEST:
        raise RuntimeError(f"test dataset có {len(dataset)} ca, cần đúng {N_TEST}")

    loader = DataLoader(
        dataset,
        batch_size=int(batch_size or data_config.get("batch_size", 2)),
        shuffle=False,  # thứ tự phải cố định để ghép được các thành viên
        num_workers=int(data_config.get("num_workers", 2)),
    )
    amp = bool((config.get("train") or {}).get("amp", True))

    members: list[np.ndarray] = []
    labels_ref: np.ndarray | None = None
    ids_ref: list[str] | None = None

    for fold in sorted(checkpoints):
        state = torch.load(checkpoints[fold], map_location=device)
        if state.get("fold") not in (None, fold):
            raise RuntimeError(f"checkpoint ghi fold={state['fold']} nhưng đang nạp fold {fold}")

        model = build_model(config["model"]).to(device)
        model.load_state_dict(state["model"])
        # BẮT BUỘC — `build_model` trả về model ở chế độ train (WORKLOG S-096). Quên
        # dòng này thì BatchNorm dùng thống kê của batch hiện tại và kết quả đổi giữa
        # hai lần chạy giống hệt nhau. Trên test-104 thì không có lần chạy thứ hai.
        model.eval()
        if any(m.training for m in model.modules()):
            raise RuntimeError("còn module ở chế độ train")

        chunks: list[np.ndarray] = []
        labels: list[np.ndarray] = []
        ids: list[str] = []
        with torch.no_grad():
            for batch in loader:
                images = batch["image"].to(device, non_blocking=True)
                with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp):
                    logits = model(images)
                chunks.append(torch.softmax(logits.float(), dim=1).cpu().numpy())
                labels.append(batch["label"].cpu().numpy())
                ids.extend(batch["patient_id"])

        found_labels = np.concatenate(labels)
        if labels_ref is None:
            labels_ref, ids_ref = found_labels, ids
        elif ids != ids_ref:
            raise RuntimeError(
                f"fold {fold} xếp ca khác thứ tự fold đầu — loader phải shuffle=False"
            )
        members.append(np.concatenate(chunks))

        del model
        if device.type == "cuda":
            torch.cuda.empty_cache()

    assert labels_ref is not None and ids_ref is not None
    return {
        "member_probs": np.stack(members),
        "labels": labels_ref,
        "patient_ids": ids_ref,
        "folds": sorted(checkpoints),
    }


def run(
    ckpt_dir: str | Path,
    config_path: str | Path,
    out_dir: str | Path,
    cache_dir: str | Path | None = None,
    splits_dir: str | Path = "splits",
    folds: list[int] | None = None,
    skip_git_check: bool = False,
) -> Path:
    """Chạm test-104 một lần và lưu `test_probs.npz`. Trả về đường dẫn file."""
    repo = resolve_repo_path(".")
    folds = folds or [1, 2, 3, 4, 5]

    prereg_sha = "(bỏ qua kiểm git)" if skip_git_check else check_prereg_committed(repo)

    Splits(resolve_repo_path(splits_dir)).validate()

    checkpoints = find_checkpoints(ckpt_dir, folds)
    missing = [f for f in folds if f not in checkpoints]
    if missing:
        raise RuntimeError(f"thiếu checkpoint cho fold {missing} dưới {ckpt_dir}")

    digests = {f: sha16(p) for f, p in checkpoints.items()}
    if len(set(digests.values())) != len(digests):
        raise RuntimeError(
            f"có checkpoint trùng nhau — ensemble sẽ đếm một model hai lần: {digests}"
        )
    wrong = {f: (digests[f], PINNED_SHA256[f]) for f in folds if digests[f] != PINNED_SHA256.get(f)}
    if wrong:
        raise RuntimeError(
            f"sha256 lệch danh sách ghim trong {PREREG}: {wrong}.\n"
            f"Đây không phải bộ checkpoint đã khoá. DỪNG."
        )

    config = load_yaml(resolve_repo_path(config_path))
    cache = Path(cache_dir) if cache_dir else resolve_cache_dir(config)

    result = predict_members(config, checkpoints, cache, splits_dir=splits_dir)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "test_probs.npz"
    np.savez_compressed(
        path,
        member_probs=result["member_probs"],
        labels=result["labels"],
        patient_ids=np.array(result["patient_ids"]),
        folds=np.array(result["folds"]),
    )
    (out / "test_run_meta.json").write_text(
        json.dumps(
            {
                "prereg_commit": prereg_sha,
                "config": str(config_path),
                "cache_dir": str(cache),
                "checkpoint_sha256": digests,
                "n_cases": int(len(result["labels"])),
                "n_members": int(result["member_probs"].shape[0]),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Suy luận trên test-104 official (chạm đúng MỘT LẦN)"
    )
    parser.add_argument("--ckpt-dir", required=True, help="thư mục chứa 5 best_fold_N.pt")
    parser.add_argument("--config", default="configs/baseline_3dpatch.yaml")
    parser.add_argument("--out", required=True, help="thư mục ghi test_probs.npz")
    parser.add_argument("--cache-dir", default=None, help="mặc định lấy từ config/env")
    parser.add_argument("--splits-dir", default="splits")
    parser.add_argument(
        "--skip-git-check",
        action="store_true",
        help="chỉ dùng khi chạy ở nơi không có .git (vd Kaggle clone nông)",
    )
    parser.add_argument(
        "--i-know-this-is-final",
        action="store_true",
        help="bắt buộc; xác nhận đây là lần chạm test-104 đã được ghi WORKLOG",
    )
    args = parser.parse_args()

    if not args.i_know_this_is_final:
        raise SystemExit(
            "TỪ CHỐI CHẠY.\n"
            "test-104 là held-out khoá kín, chạm đúng một lần (AGENTS.md §3.4).\n"
            "Trước khi thêm cờ --i-know-this-is-final, phải có đủ:\n"
            f"  1. {PREREG} đã commit\n"
            "  2. một entry WORKLOG nêu lý do chạm\n"
            "  3. người dùng đồng ý (AGENTS.md §10)"
        )

    path = run(
        args.ckpt_dir,
        args.config,
        args.out,
        cache_dir=args.cache_dir,
        splits_dir=args.splits_dir,
        skip_git_check=args.skip_git_check,
    )
    print(f"đã lưu {path}")
    print("\nĐọc số bằng:  python -m src.eval.test_report --run-dir " + str(Path(path).parent))
    print("Module này cố ý KHÔNG in metric nào — xem docstring.")


if __name__ == "__main__":
    main()
