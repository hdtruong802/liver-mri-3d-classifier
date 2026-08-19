"""Entrypoint huấn luyện một fold.

    python -m src.train.run --config configs/baseline_3dpatch.yaml
    python -m src.train.run --config configs/baseline_3dpatch.yaml --fold 2

Mọi hyperparam nằm trong YAML, code chỉ đọc (AGENTS.md §8). Vòng train được thiết
kế quanh giả định **session có thể chết bất cứ lúc nào**:

- checkpoint `last.pt` ghi sau **mỗi** epoch (ghi nguyên tử);
- chạy lại cùng lệnh sẽ tự resume đúng epoch, kèm optimizer/scaler/early-stop counter;
- `train_log.csv` flush từng dòng, không buffer tới cuối;
- `val_probs_best.npz` lưu xác suất val của epoch tốt nhất → W3/W5 tính CI,
  calibration, selective prediction mà không phải train lại.

Chưa chạm test-104: script này chỉ đọc `train_fold*/val_fold*` (AGENTS.md §3.4).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from src.data.dataset import build_fold_datasets, find_label_mismatches
from src.data.taxonomy import SHORT_NAMES
from src.data.transforms import build_train_transform, build_val_transform
from src.eval.metrics import classification_metrics, confusion_matrix, per_class_f1
from src.models import build_model, count_parameters
from src.train.loop import (
    load_checkpoint,
    make_amp_scaler,
    run_epoch,
    save_checkpoint,
)
from src.utils.io import load_yaml, resolve_cache_dir, resolve_output_dir, resolve_repo_path
from src.utils.logging import CsvLogger, get_logger
from src.utils.seed import set_seed

logger = get_logger(__name__)

CSV_FIELDS = [
    "epoch",
    "train_loss",
    "val_loss",
    "val_macro_f1",
    "val_balanced_accuracy",
    "val_accuracy",
    "val_cohen_kappa",
    "lr",
    "seconds",
    # F1 từng lớp theo epoch, một cột mỗi lớp: `f1_u máu`, `f1_ICC`, ...
    #
    # Vì sao đáng một cột riêng chứ không chỉ in ra log: hai lớp yếu (ICC và di căn) là
    # thứ CHẶN mục tiêu về mặt số học — giữ nguyên ICC 0.519 và di căn 0.273 thì kể cả 5
    # lớp kia đều đạt 0.90, macro-F1 cũng chỉ tới 0.756. Có cột riêng thì vẽ được quỹ đạo
    # của đúng hai lớp đó theo epoch, thay vì chỉ thấy macro-F1 gộp che mất chúng.
    #
    # ⚠️ `CsvLogger` tôn trọng header đã có, nên một run bắt đầu TRƯỚC thay đổi này mà
    # resume sau đó sẽ giữ schema cũ và bỏ im lặng các cột mới. Đó là chủ ý: mất một cột
    # ở run cũ thì chấp nhận được, làm hỏng cả file log thì không.
    *(f"f1_{SHORT_NAMES[i]}" for i in sorted(SHORT_NAMES)),
]

# Khoá mà `train()` trả về. Là **hợp đồng công khai** với notebook, nên khai tường minh
# ở đây thay vì để notebook đoán.
#
# ⚠️ Lý do tồn tại: `train()` trả `best_macro_f1`, còn `metrics_best.json` ghi `macro_f1`
# — hai tên khác nhau cho cùng một đại lượng. Ba notebook đã viết
# `results[fold]["macro_f1"]` và nổ `KeyError` **sau khi train xong cả fold**; hai
# notebook khác viết `.get("macro_f1", nan)` nên in `nan` im lặng suốt từ đầu mà không
# ai để ý (WORKLOG S-123). `tests/test_notebook_contract.py` nay đối chiếu mọi notebook
# với hằng số này.
TRAIN_RESULT_KEYS = ("fold", "best_macro_f1", "best_epoch", "seed", "run_dir")


def model_fingerprint(model_config: dict[str, Any]) -> str:
    """Chuỗi định danh kiến trúc — đổi kiến trúc là đổi chuỗi này."""
    return json.dumps(model_config, sort_keys=True, ensure_ascii=False)


def run_dir(config: dict[str, Any], fold: int) -> Path:
    """Thư mục của một run: ``fold{N}_{hash kiến trúc}``.

    Hash **chỉ tính trên khối ``model:``**, có chủ ý. Đây là cách chặn tận gốc việc
    checkpoint của kiến trúc này bị nạp vào kiến trúc khác — thứ đã xảy ra thật khi
    `last.pt` của bản BatchNorm gặp bản InstanceNorm (WORKLOG S-038). Chốt kiểm tra
    lúc resume vẫn giữ, nhưng nó là lưới thứ hai; lưới thứ nhất là hai run khác
    kiến trúc thì **không bao giờ dùng chung thư mục**.

    Không hash cả config: đổi `lr` hay `epochs` vẫn phải resume được, vì trên Kaggle
    mất tiến trình của một run dài là mất thật.
    """
    digest = hashlib.sha1(model_fingerprint(config["model"]).encode("utf-8")).hexdigest()[:8]
    return resolve_output_dir(config) / f"fold{fold}_{digest}"


#: ``data.sampling`` → số mũ ``q`` trong công thức của đội hạng 2 LLD-MMRI 2023
#: (`ZHEGG/miccai2023`, `datasets/mp_liver_dataset.py::count_probabilities`). ``train.sh`` của
#: họ dùng ``--sampling sqrt``.
SAMPLING_EXPONENTS: dict[str, float] = {"instance": 0.0, "sqrt": 0.5, "class": 1.0}


def sampling_weights(labels: Sequence[int], mode: str) -> Any:
    """Trọng số lấy mẫu **cho từng mẫu**, theo công thức của đội hạng 2.

    Nguyên văn code của họ::

        relative_freq = class_count ** q / (class_count ** q).sum()
        sampling_probabilities = relative_freq ** (-1)
        sample_weights = sampling_probabilities[labels]

    Vì ``.sum()`` là hằng số, phần này rút gọn thành **trọng số mỗi lớp ∝ count^(−q)**:

    * ``instance`` (q=0) → đều nhau, tức không cân bằng gì.
    * ``sqrt`` (q=0.5) → nghịch **căn** tần suất. Nhẹ hơn nghịch tần suất trần, cùng tinh thần
      với `effective_number` ở `src/train/losses.py`.
    * ``class`` (q=1) → nghịch tần suất trần, cân bằng hoàn toàn.

    Hàm **thuần numpy** để test được mà không cần torch.

    ⚠️ **Xung đột đã biết với chẩn đoán §1 của AGENTS.md.** Recipe của họ bật *đồng thời*
    `--cb_loss` (trọng số lớp trong loss) **và** `--sampling sqrt` (lấy mẫu lại) — hai lớp cân
    bằng cùng lúc. Chẩn đoán của ta đo ICC bị dự đoán **thừa** 1.26× và áp-xe 1.31× trên E4,
    tức đẩy thêm lớp hiếm là đi ngược bằng chứng. Hai điều này không mâu thuẫn: §1 đo trên
    **E4/DenseNet from scratch**, một biểu diễn khác có cán cân dự đoán khác. Tái lập trung
    thực trước, đo cán cân dự đoán sau (cổng D của notebook 20).
    """
    import numpy as np

    if mode not in SAMPLING_EXPONENTS:
        raise ValueError(f"data.sampling phải thuộc {sorted(SAMPLING_EXPONENTS)}, nhận {mode!r}")
    q = SAMPLING_EXPONENTS[mode]
    arr = np.asarray(labels, dtype=int)
    if arr.size == 0:
        raise ValueError("không có nhãn train nào để tính trọng số lấy mẫu")
    counts = np.bincount(arr, minlength=int(arr.max()) + 1).astype(float)
    # Lớp vắng mặt trong fold này có count 0 → count^(-q) là vô cực. Không mẫu nào mang nhãn
    # đó nên giá trị không bao giờ được dùng; đặt 1.0 để không sinh inf/NaN trong mảng.
    per_class = np.ones_like(counts)
    present = counts > 0
    per_class[present] = counts[present] ** (-q)
    return per_class[arr]


def build_sampler(labels: Sequence[int], mode: str) -> Any:
    """`WeightedRandomSampler` cho `data.sampling`; ``None`` khi ``instance``.

    ``instance`` trả `None` để người gọi dùng ``shuffle=True`` — **giữ nguyên hành vi của mọi
    config cũ**. Nói cho chính xác thì đó không giống hệt bản của họ (họ vẫn qua sampler với
    trọng số đều và *có hoàn lại*, còn `shuffle` là một phép hoán vị **không** hoàn lại), nhưng
    tương thích ngược quan trọng hơn: mọi con số cũ của dự án phải so được với số mới.

    Generator lấy seed từ RNG toàn cục nên `src/utils/seed.py::set_seed` điều khiển được nó
    (AGENTS.md §8). Để `WeightedRandomSampler` tự sinh generator thì run không lặp lại được.
    """
    import torch
    from torch.utils.data import WeightedRandomSampler

    if mode == "instance":
        return None
    weights = sampling_weights(labels, mode)
    generator = torch.Generator()
    generator.manual_seed(int(torch.randint(0, 2**31 - 1, (1,)).item()))
    return WeightedRandomSampler(
        weights=torch.as_tensor(weights, dtype=torch.double),
        num_samples=len(weights),
        replacement=True,
        generator=generator,
    )


def build_loaders(config: dict[str, Any], fold: int) -> tuple[Any, Any, list[int]]:
    """Dựng DataLoader train/val cho một fold; trả kèm nhãn train (để tính class weight).

    Công khai (không còn `_` ở đầu) vì cell đo thời gian trong notebook **phải** dùng
    đúng hàm này. Probe mà tự dựng loader theo cách khác thì con số nó đo được không
    dự đoán được run thật — mà dự đoán run thật chính là toàn bộ mục đích của nó.

    `persistent_workers` là thứ đáng chú ý ở đây: mặc định DataLoader **tạo lại toàn
    bộ worker sau mỗi epoch**. Fold này chỉ có ~39 bước/epoch nên chi phí khởi động
    worker chiếm tỉ lệ lớn, và recipe official là 300 epoch — tức là 300 lần dựng lại
    (WORKLOG S-044).
    """
    from torch.utils.data import DataLoader

    data_config = config.get("data") or {}
    cache_dir = resolve_cache_dir(config)
    # `crop_size` chỉ có khi cache được build với lề dư (`crop_margin_voxels`). Vắng
    # mặt thì cả hai transform xuống thang về hành vi cũ, nên config cũ không đổi gì.
    crop_size = data_config.get("crop_size")
    intra_mixup = float(data_config.get("intra_class_mixup", 0.0))
    train_ds, val_ds = build_fold_datasets(
        cache_dir,
        fold,
        splits_dir=resolve_repo_path(config.get("splits_dir", "splits")),
        train_transform=build_train_transform(data_config.get("augment"), crop_size),
        val_transform=build_val_transform(crop_size),
        intra_class_mixup=intra_mixup,
        intra_class_mixup_exclude_majority=bool(
            data_config.get("intra_class_mixup_exclude_majority", True)
        ),
    )
    if intra_mixup > 0:
        logger.info(
            "intra-class mixup BẬT: alpha=%s · lớp bị loại=%s · lớp được trộn=%s",
            intra_mixup,
            train_ds.mixup_excluded_class,
            train_ds.mixup_classes,
        )

    batch_size = int(data_config.get("batch_size", 2))
    num_workers = int(data_config.get("num_workers", 2))
    common: dict[str, Any] = {
        "num_workers": num_workers,
        "pin_memory": bool(data_config.get("pin_memory", True)),
    }
    if num_workers > 0:
        # Hai khoá này chỉ hợp lệ khi có worker thật; truyền lúc num_workers=0 sẽ nổ.
        common["persistent_workers"] = bool(data_config.get("persistent_workers", True))
        common["prefetch_factor"] = int(data_config.get("prefetch_factor", 4))
    train_labels = [label for _, label, _ in train_ds.samples]

    # `shuffle` và `sampler` loại trừ nhau trong DataLoader — truyền cả hai là nổ.
    sampler = build_sampler(train_labels, str(data_config.get("sampling", "instance")))
    if sampler is None:
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, **common)
    else:
        train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler, **common)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, **common)

    return train_loader, val_loader, train_labels


def build_param_groups(model: Any, weight_decay: float) -> list[dict[str, Any]]:
    """Tách bias và tham số norm ra khỏi weight decay.

    Bắt buộc phải có khi `weight_decay` lớn. Recipe official dùng **wd = 0.05** thông
    qua timm, và `timm.optim.create_optimizer_v2` mặc định loại mọi tham số 1 chiều
    (bias, weight/bias của BatchNorm) khỏi decay. Nếu ta gọi thẳng
    ``AdamW(model.parameters(), weight_decay=0.05)`` thì decay đè lên cả tham số affine
    của BatchNorm — kéo scale của chúng về 0 và làm hỏng chuẩn hoá. Cùng một con số
    0.05 nhưng cho ra hai chế độ train hoàn toàn khác nhau (WORKLOG S-043).

    Quy ước nhận dạng: tham số **1 chiều** là bias/norm. Đơn giản, và đúng với mọi
    kiến trúc conv/norm/linear đang dùng.
    """
    decay: list[Any] = []
    no_decay: list[Any] = []
    for param in model.parameters():
        if not param.requires_grad:
            continue
        (no_decay if param.ndim <= 1 else decay).append(param)
    return [
        {"params": decay, "weight_decay": weight_decay},
        {"params": no_decay, "weight_decay": 0.0},
    ]


def build_scheduler(optimizer: Any, train_config: dict[str, Any], epochs: int) -> Any:
    """Warmup tuyến tính rồi cosine — theo recipe official (warmup 5 epoch, min-lr 1e-5).

    Trước đây chỉ có cosine trần từ epoch 1. Warmup có mặt trong recipe official
    (``--warmup-epochs 5``, ``--warmup-lr 1e-6``) nên đưa vào cho khớp.
    """
    import torch

    warmup_epochs = int(train_config.get("warmup_epochs", 0))
    min_lr = float(train_config.get("min_lr", 0.0))
    cosine_epochs = max(1, epochs - warmup_epochs)
    cosine = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=cosine_epochs, eta_min=min_lr
    )
    if warmup_epochs <= 0:
        return cosine

    base_lr = float(train_config.get("lr", 3e-4))
    warmup_lr = float(train_config.get("warmup_lr", 1e-6))
    start_factor = max(warmup_lr / base_lr, 1e-8) if base_lr > 0 else 1.0
    warmup = torch.optim.lr_scheduler.LinearLR(
        optimizer, start_factor=start_factor, end_factor=1.0, total_iters=warmup_epochs
    )
    return torch.optim.lr_scheduler.SequentialLR(
        optimizer, schedulers=[warmup, cosine], milestones=[warmup_epochs]
    )


def _build_criterion(config: dict[str, Any], train_labels: list[int], device: Any) -> Any:
    """CE hoặc focal, tuỳ chọn trọng số lớp tính **chỉ từ nhãn train**.

    Uỷ quyền cho `src/train/losses.py` — ở đó có lý do khoa học của từng lựa chọn.
    """
    from src.train.losses import build_criterion

    loss_config = config.get("loss") or {}
    logger.info(
        "loss: %s · class_weights=%s · label_smoothing=%s%s",
        loss_config.get("name", "cross_entropy"),
        loss_config.get("class_weights", "none"),
        loss_config.get("label_smoothing", 0.0),
        f" · gamma={loss_config['gamma']}" if loss_config.get("name") == "focal" else "",
    )
    return build_criterion(config, train_labels, device)


def train(config_path: str | Path, fold_override: int | None = None) -> dict[str, Any]:
    """Train một fold tới khi hết epoch hoặc early stop. Trả về metric val tốt nhất."""
    import torch

    config = load_yaml(config_path)
    fold = int(fold_override if fold_override is not None else config.get("fold", 1))
    train_config = config.get("train") or {}
    seed = int(config.get("seed", 1337))
    set_seed(seed, deterministic=bool(train_config.get("deterministic", True)))

    output_dir = run_dir(config, fold)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Chụp lại đúng config đã dùng (dạng JSON) — để đọc lại số cũ mà không phải
    # đoán xem YAML lúc đó có gì.
    (output_dir / "config_used.json").write_text(
        json.dumps({**config, "fold": fold}, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    amp = bool(train_config.get("amp", True)) and device.type == "cuda"

    # Version thư viện đi vào log của chính run này: notebook Kaggle cài monai không
    # pin (xem cell bootstrap), nên đây là chỗ duy nhất ghi lại số đã thật sự dùng.
    try:
        import monai

        monai_version = monai.__version__
    except ImportError:  # pragma: no cover - chỉ xảy ra khi chưa cài deep-learning stack
        monai_version = "không có"
    logger.info("torch %s | monai %s", torch.__version__, monai_version)

    train_loader, val_loader, train_labels = build_loaders(config, fold)
    logger.info(
        "fold %d | train=%d val=%d | device=%s | amp=%s",
        fold,
        len(train_loader.dataset),
        len(val_loader.dataset),
        device,
        amp,
    )

    # Cổng chặn trước khi tốn GPU: nhãn trong cache phải khớp nhãn trong splits/.
    # Lệch nhãn không làm train báo lỗi — loss vẫn giảm, metric vẫn ra số, chỉ là
    # kết quả vô nghĩa. Vài giây kiểm ở đây rẻ hơn nhiều so với một run hỏng.
    if config.get("verify_labels", True):
        mismatches = find_label_mismatches(train_loader.dataset) + find_label_mismatches(
            val_loader.dataset
        )
        if mismatches:
            raise RuntimeError(
                f"{len(mismatches)} ca có nhãn trong cache khác nhãn trong splits/ "
                f"(vd {mismatches[:3]} dạng (id, nhãn_split, nhãn_cache)). "
                "Cache và split không cùng một nguồn — dừng lại, đừng train."
            )
        logger.info(
            "nhãn cache khớp splits/ trên toàn bộ %d ca",
            len(train_labels) + len(val_loader.dataset),
        )

    model = build_model(config["model"]).to(device)
    logger.info("model=%s | %d tham số", config["model"]["name"], count_parameters(model))

    criterion = _build_criterion(config, train_labels, device)
    weight_decay = float(train_config.get("weight_decay", 1e-5))
    optimizer = torch.optim.AdamW(
        build_param_groups(model, weight_decay),
        lr=float(train_config.get("lr", 3e-4)),
    )
    epochs = int(train_config.get("epochs", 60))
    scheduler = build_scheduler(optimizer, train_config, epochs)
    scaler = make_amp_scaler(amp)

    start_epoch = 1
    best_score = -1.0
    best_epoch = 0
    epochs_without_gain = 0

    checkpoint_path = output_dir / "last.pt"
    fingerprint = model_fingerprint(config["model"])
    if train_config.get("resume", True):
        state = load_checkpoint(checkpoint_path)
        if state is not None:
            # Checkpoint của một kiến trúc khác thì resume là vô nghĩa: hoặc
            # load_state_dict nổ với một trang lỗi khó đọc, hoặc tệ hơn — khôi phục
            # đúng `epochs_without_gain` cũ rồi early-stop ngay mà không train gì,
            # trông y như "đã chạy xong".
            #
            # `get(...)` trả None với checkpoint đời cũ (ghi trước khi có trường này).
            # KHÔNG được coi None là "chắc khớp" — đó đúng là lỗ hổng đã để lọt một
            # checkpoint BatchNorm vào model InstanceNorm (WORKLOG S-038). Không biết
            # thì phải từ chối.
            previous = state.get("model_fingerprint")
            if previous != fingerprint:
                shown = previous if previous is not None else "(không ghi — checkpoint đời cũ)"
                raise RuntimeError(
                    f"{checkpoint_path} không phải checkpoint của cấu hình model này.\n"
                    f"  đang chạy : {fingerprint}\n"
                    f"  trong ckpt: {shown}\n"
                    "Xoá file đó nếu muốn train lại từ đầu. Bình thường thì không nên gặp "
                    "lỗi này: mỗi kiến trúc đã có thư mục riêng theo hash (xem run_dir)."
                )
            model.load_state_dict(state["model"])
            optimizer.load_state_dict(state["optimizer"])
            scheduler.load_state_dict(state["scheduler"])
            scaler.load_state_dict(state["scaler"])
            start_epoch = int(state["epoch"]) + 1
            best_score = float(state["best_score"])
            best_epoch = int(state["best_epoch"])
            epochs_without_gain = int(state["epochs_without_gain"])
            logger.info(
                "RESUME từ %s: tiếp epoch %d, best macro-F1 %.4f @ epoch %d",
                checkpoint_path,
                start_epoch,
                best_score,
                best_epoch,
            )

    accum_steps = max(1, int(train_config.get("accum_steps", 1)))
    patience = int(train_config.get("early_stop_patience", 15))
    # Mixup nằm ở khối `data:` vì nó là phép biến đổi dữ liệu, không phải tham số tối ưu hoá.
    # Mặc định 0 = tắt, nên không config cũ nào đổi hành vi.
    mixup_alpha = float((config.get("data") or {}).get("mixup_alpha", 0.0))
    if mixup_alpha < 0:
        raise ValueError(f"data.mixup_alpha phải >= 0, nhận {mixup_alpha}")
    if mixup_alpha > 0:
        logger.info(
            "MIXUP BẬT (alpha=%.2f) — train_loss dưới đây là loss trên NHÃN ĐÃ TRỘN, "
            "không so trực tiếp được với run không mixup",
            mixup_alpha,
        )

    # EMA đã được GỠ khỏi cây làm việc (WORKLOG S-197): hai config duy nhất dùng nó
    # (`e7_ema`, `e9_e6b_ema`) chưa bao giờ chạy fold nào và không có mặt trong báo cáo
    # cuối. Nổ ra thay vì lặng lẽ bỏ qua — một config cũ bật `ema_decay` mà train không
    # EMA sẽ cho ra một thí nghiệm KHÁC nhưng trông y hệt.
    if float(train_config.get("ema_decay", 0.0)) > 0:
        raise ValueError(
            "train.ema_decay > 0 nhưng đường EMA đã được gỡ khỏi repo (WORKLOG S-197). "
            "Bỏ khoá này khỏi config, hoặc khôi phục src/train/ema.py từ git history."
        )
    csv_logger = CsvLogger(output_dir / "train_log.csv", CSV_FIELDS)

    try:
        for epoch in range(start_epoch, epochs + 1):
            started = time.time()
            train_out = run_epoch(
                model,
                train_loader,
                device,
                criterion,
                optimizer=optimizer,
                scaler=scaler,
                accum_steps=accum_steps,
                amp=amp,
                mixup_alpha=mixup_alpha,
            )
            val_out = run_epoch(model, val_loader, device, criterion, amp=amp)
            scheduler.step()

            val_pred = val_out["probs"].argmax(axis=1)
            metrics = classification_metrics(val_out["labels"], val_pred)
            class_f1 = per_class_f1(val_out["labels"], val_pred)
            csv_logger.log(
                {
                    "epoch": epoch,
                    "train_loss": round(train_out["loss"], 5),
                    "val_loss": round(val_out["loss"], 5),
                    "val_macro_f1": round(metrics["macro_f1"], 5),
                    "val_balanced_accuracy": round(metrics["balanced_accuracy"], 5),
                    "val_accuracy": round(metrics["accuracy"], 5),
                    "val_cohen_kappa": round(metrics["cohen_kappa"], 5),
                    "lr": optimizer.param_groups[0]["lr"],
                    "seconds": round(time.time() - started, 1),
                    **{
                        f"f1_{SHORT_NAMES[i]}": round(float(class_f1[i]), 5)
                        for i in sorted(SHORT_NAMES)
                    },
                }
            )
            logger.info(
                "epoch %d/%d | train %.4f | val %.4f | macro-F1 %.4f | %.0fs",
                epoch,
                epochs,
                train_out["loss"],
                val_out["loss"],
                metrics["macro_f1"],
                time.time() - started,
            )
            # F1 từng lớp trên một dòng riêng. Hai lớp yếu (ICC, di căn) là thứ chặn mục
            # tiêu về số học, nên xem quỹ đạo của chúng theo epoch quan trọng ngang
            # macro-F1 — mà macro-F1 gộp thì che mất chúng.
            logger.info(
                "        F1: %s",
                " · ".join(f"{SHORT_NAMES[i]} {class_f1[i]:.3f}" for i in sorted(SHORT_NAMES)),
            )

            # Xác suất val của epoch CUỐI, ghi đè mỗi epoch. Không phải bản sao thừa
            # của `val_probs_best.npz`: epoch "tốt nhất" được chọn bằng macro-F1 trên
            # đúng 82 ca val, mà dãy macro-F1 của fold 1 dao động 0.115–0.265 không
            # xu hướng (WORKLOG S-042) — chọn max của 26 lần bốc như vậy là chọn
            # nhiễu, và con số báo ra lệch lạc quan. Giữ cả hai để W3 đối chiếu được
            # "ước lượng theo best-epoch" với "ước lượng không qua chọn lọc".
            np.savez_compressed(
                output_dir / "val_probs_last.npz",
                probs=val_out["probs"],
                labels=val_out["labels"],
                patient_ids=np.array(val_out["patient_ids"]),
                epoch=epoch,
            )

            improved = metrics["macro_f1"] > best_score
            if improved:
                best_score = metrics["macro_f1"]
                best_epoch = epoch
                epochs_without_gain = 0
                save_checkpoint(
                    output_dir / "best.pt",
                    {
                        "model": model.state_dict(),
                        "epoch": epoch,
                        "metrics": metrics,
                        "fold": fold,
                    },
                )
                np.savez_compressed(
                    output_dir / "val_probs_best.npz",
                    probs=val_out["probs"],
                    labels=val_out["labels"],
                    patient_ids=np.array(val_out["patient_ids"]),
                    epoch=epoch,
                )
                (output_dir / "metrics_best.json").write_text(
                    json.dumps(
                        {
                            "fold": fold,
                            "epoch": epoch,
                            "seed": seed,
                            **metrics,
                            "per_class_f1": per_class_f1(val_out["labels"], val_pred).tolist(),
                            "confusion_matrix": confusion_matrix(
                                val_out["labels"], val_pred
                            ).tolist(),
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            else:
                epochs_without_gain += 1

            # Ghi last.pt SAU khi đã xử lý best: nếu session chết ngay lúc này thì
            # lần resume tiếp theo vẫn thấy đúng trạng thái early-stop.
            save_checkpoint(
                checkpoint_path,
                {
                    "model": model.state_dict(),
                    "optimizer": optimizer.state_dict(),
                    "scheduler": scheduler.state_dict(),
                    "scaler": scaler.state_dict(),
                    "epoch": epoch,
                    "best_score": best_score,
                    "best_epoch": best_epoch,
                    "epochs_without_gain": epochs_without_gain,
                    "fold": fold,
                    "seed": seed,
                    "model_fingerprint": fingerprint,
                },
            )

            if patience and epochs_without_gain >= patience:
                logger.info("EARLY STOP: %d epoch không cải thiện macro-F1", epochs_without_gain)
                break
    finally:
        csv_logger.close()

    logger.info("XONG fold %d | best macro-F1 val = %.4f @ epoch %d", fold, best_score, best_epoch)
    return {
        "fold": fold,
        "best_macro_f1": best_score,
        "best_epoch": best_epoch,
        "seed": seed,
        "run_dir": str(output_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train một fold trên cache đã tiền xử lý")
    parser.add_argument("--config", required=True)
    parser.add_argument("--fold", type=int, default=None, help="ghi đè fold trong config (1..5)")
    args = parser.parse_args()
    train(args.config, args.fold)


if __name__ == "__main__":
    main()
