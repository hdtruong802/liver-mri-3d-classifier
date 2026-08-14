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
import time
from pathlib import Path
from typing import Any

import numpy as np

from src.data.dataset import build_test_dataset
from src.data.splits import N_TEST, Splits
from src.utils.io import load_yaml, resolve_cache_dir, resolve_repo_path

PREREG = "docs/TEST104_PREREGISTRATION.md"

# Mỗi khoá là MỘT lần chạm test-104 đã được cho phép, kèm đúng bộ checkpoint của nó.
#
# Giữ cả bộ cũ sau khi đã dùng là có chủ đích: nó là hồ sơ của lần chạm đó. Xoá đi thì
# về sau không còn cách nào đối chiếu `test_run_meta.json` cũ với checkpoint nào đã sinh
# ra nó, và một con số test không truy được nguồn thì không dùng được trong báo cáo.
PIN_SETS: dict[str, dict[int, str]] = {
    # Lần chạm 1 — 2026-08-07 (WORKLOG S-110). E4, ghim ở S-081, đối chiếu lại ở S-107.
    # ĐÃ DÙNG. Xem `docs/TEST104_PREREGISTRATION.md` §1.
    "e4": {
        1: "2e1f3e1ad477ad59",
        2: "30a8eb9ee221d453",
        3: "00c133e031bdf8fe",
        4: "3fe18f1eb3de4431",
        5: "d61cc7ed94b8ebf0",
    },
    # Lần chạm 2 — UniFormer-S + Kinetics, 5 fold (WORKLOG S-169). Xem PREREG §B.
    "uniformer": {
        1: "62948396cdccd5a4",
        2: "0d36a6cd52fde563",
        3: "bc023a9a7662d38e",
        4: "1b44f40bf97d3b30",
        5: "8edf4fbc07f181b2",
    },
}

# Tên cũ, giữ để không phá chỗ gọi và test đã có. Mặc định vẫn là bộ của lần chạm 1.
PINNED_SHA256 = PIN_SETS["e4"]


def sha16(path: Path) -> str:
    """16 ký tự đầu của sha256 — đủ phân biệt, đủ ngắn để đọc bằng mắt."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def find_checkpoints(ckpt_dir: str | Path, folds: list[int]) -> dict[int, Path]:
    """Tìm checkpoint từng fold. Chấp ba bố cục đang tồn tại trong dự án:

    ``best_fold_N.pt`` phẳng · ``fold_N/best.pt`` · ``fold_N/<tiền tố>_best_N.pt``.

    Bố cục thứ ba do `train()` sinh khi config đặt tên riêng cho checkpoint (ví dụ
    ``uniformer3D_best_1.pt``). Nó **chỉ** được nhận khi số trong tên file khớp số
    trong tên thư mục cha — hai nguồn độc lập cùng nói một fold. Chấp riêng tên file
    thì một thư mục gom lẫn nhiều run sẽ ghép nhầm, mà hậu quả là một "ensemble" đếm
    một model hai lần và **con số ra vẫn trông hoàn toàn hợp lý**.

    Không đoán bừa: fold nào không suy ra được thì bỏ, và hàm gọi sẽ nổ vì thiếu.
    """
    root = Path(ckpt_dir)
    found: dict[int, Path] = {}
    for fold in folds:
        thu_muc = (f"fold_{fold}", f"fold{fold}")
        flat = sorted(root.rglob(f"best_fold_{fold}.pt"))
        nested = [p for p in sorted(root.rglob("best.pt")) if p.parent.name in thu_muc]
        # Tên file phải kết thúc bằng `_best_{fold}.pt` VÀ nằm trong thư mục `fold_{fold}`.
        co_tien_to = [
            p
            for p in sorted(root.rglob(f"*_best_{fold}.pt"))
            if p.parent.name in thu_muc and not p.name.startswith("best_fold_")
        ]
        hits = flat or nested or co_tien_to
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

    from src.data.transforms import build_val_transform
    from src.models import build_model

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_config = config.get("data") or {}
    # Cache có lề dư thì test cũng phải cắt giữa, y hệt val. Quên bước này thì model
    # nhận khối to hơn nó được train và nổ ở conv đầu.
    dataset = build_test_dataset(
        cache_dir,
        splits_dir=splits_dir,
        transform=build_val_transform(data_config.get("crop_size")),
    )
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
    # Đo latency ngay trong lượt chạy này. Lần chạm test-104 đầu tiên (S-110) đã có
    # sẵn con số này miễn phí và không ghi lại, nên sau đó không truy ra được nữa —
    # test chạm một lần nên không chạy lại để đo được (WORKLOG S-116).
    seconds_per_member: list[float] = []

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
        # Bấm giờ SAU khi nạp checkpoint: đo suy luận, không đo I/O đọc file .pt.
        # `synchronize` là bắt buộc — lệnh CUDA chạy bất đồng bộ, thiếu nó thì đồng
        # hồ dừng lúc hàng đợi được xếp xong chứ không phải lúc GPU tính xong.
        if device.type == "cuda":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.no_grad():
            for batch in loader:
                images = batch["image"].to(device, non_blocking=True)
                with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp):
                    logits = model(images)
                chunks.append(torch.softmax(logits.float(), dim=1).cpu().numpy())
                labels.append(batch["label"].cpu().numpy())
                ids.extend(batch["patient_id"])
        if device.type == "cuda":
            torch.cuda.synchronize()
        seconds_per_member.append(time.perf_counter() - t0)

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
    n = len(labels_ref)
    total = float(sum(seconds_per_member))
    return {
        "member_probs": np.stack(members),
        "labels": labels_ref,
        "patient_ids": ids_ref,
        "folds": sorted(checkpoints),
        "latency": {
            "device": device.type,
            "batch_size": loader.batch_size,
            "amp": amp,
            "n_cases": n,
            "seconds_per_member": [round(s, 3) for s in seconds_per_member],
            # Hai con số đáng báo cáo. `per_case_1model_ms` so được với văn liệu;
            # `per_case_ensemble_ms` là thứ hệ thống thật phải trả.
            "per_case_1model_ms": round(total / len(seconds_per_member) / n * 1000, 1),
            "per_case_ensemble_ms": round(total / n * 1000, 1),
        },
    }


def run(
    ckpt_dir: str | Path,
    config_path: str | Path,
    out_dir: str | Path,
    cache_dir: str | Path | None = None,
    splits_dir: str | Path = "splits",
    folds: list[int] | None = None,
    skip_git_check: bool = False,
    pin_set: str = "e4",
) -> Path:
    """Chạm test-104 một lần và lưu `test_probs.npz`. Trả về đường dẫn file.

    `pin_set` chọn bộ sha256 đã khoá trong pre-registration — xem `PIN_SETS`. Mặc định
    giữ nguyên bộ của lần chạm 1 để chỗ gọi cũ không đổi hành vi; chạy bộ checkpoint
    khác mà quên đổi khoá này thì **nổ vì lệch sha**, tức hỏng về phía an toàn.
    """
    repo = resolve_repo_path(".")
    folds = folds or [1, 2, 3, 4, 5]
    if pin_set not in PIN_SETS:
        raise RuntimeError(f"pin_set {pin_set!r} không có trong PIN_SETS: {sorted(PIN_SETS)}")
    pinned = PIN_SETS[pin_set]

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
    wrong = {f: (digests[f], pinned.get(f)) for f in folds if digests[f] != pinned.get(f)}
    if wrong:
        raise RuntimeError(
            f"sha256 lệch bộ ghim {pin_set!r} trong {PREREG}: {wrong}.\n"
            f"Đây không phải bộ checkpoint đã khoá. DỪNG.\n"
            f"Nếu đang chạy bộ checkpoint khác thì đổi --pin-set (có: {sorted(PIN_SETS)}) "
            f"— và bộ đó phải đã được ghi trong pre-registration TRƯỚC khi chạy."
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
                "pin_set": pin_set,
                "config": str(config_path),
                "cache_dir": str(cache),
                "checkpoint_sha256": digests,
                "n_cases": int(len(result["labels"])),
                "n_members": int(result["member_probs"].shape[0]),
                "latency": result["latency"],
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
        "--pin-set",
        default="e4",
        choices=sorted(PIN_SETS),
        help="bộ checkpoint đã khoá trong pre-registration (mặc định: bộ của lần chạm 1)",
    )
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
        pin_set=args.pin_set,
    )
    print(f"đã lưu {path}")
    lat = json.loads((Path(path).parent / "test_run_meta.json").read_text("utf-8"))["latency"]
    print(
        f"\nlatency suy luận: {lat['per_case_1model_ms']} ms/ca cho 1 model · "
        f"{lat['per_case_ensemble_ms']} ms/ca cho ensemble {len(lat['seconds_per_member'])} model"
        f"  ({lat['device']}, batch {lat['batch_size']}, amp={lat['amp']})"
    )
    print("  ⚠ chỉ là phần model. Tiền xử lý một ca mới tốn thêm ~3,4s trên CPU.")
    print("\nĐọc số bằng:  python -m src.eval.test_report --run-dir " + str(Path(path).parent))
    print("Module này cố ý KHÔNG in metric nào — xem docstring.")


if __name__ == "__main__":
    main()
