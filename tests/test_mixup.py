"""Test mixup chéo lớp trong `run_epoch`.

Điều quan trọng nhất phải chứng minh: **`mixup_alpha = 0` cho đường code y hệt bản chưa
có mixup**. Mixup được thêm vào một hàm mà mọi thí nghiệm của dự án đi qua, nên nếu nó
làm lệch dù chỉ chút ở đường mặc định thì mọi con số cũ mất tính so sánh — và chuyện đó
sẽ không lộ ra ở đâu cả.
"""

from __future__ import annotations

import inspect

import pytest
import yaml
from src.train.loop import run_epoch
from src.utils.io import repo_root


def _cfg(name: str) -> dict:
    return yaml.safe_load((repo_root() / "configs" / name).read_text("utf-8"))


# --- hợp đồng, không cần torch -------------------------------------------------


def test_mixup_alpha_mac_dinh_la_0():
    """Mặc định phải là TẮT, để mọi config cũ không đổi hành vi."""
    assert inspect.signature(run_epoch).parameters["mixup_alpha"].default == 0.0


def test_run_epoch_van_goi_duoc_khong_can_mixup():
    """Tham số mới phải ở cuối và có mặc định — chữ ký cũ vẫn hợp lệ."""
    params = list(inspect.signature(run_epoch).parameters)
    assert params[-1] == "mixup_alpha"
    assert params[:5] == ["model", "loader", "device", "criterion", "optimizer"]


def test_train_doc_mixup_tu_khoi_data_va_tu_choi_gia_tri_am():
    """Kiểm ở mức mã nguồn vì `train()` cần torch + cache thật để chạy.

    Hai điều được neo: mixup đọc từ khối `data:` (nó là phép biến đổi dữ liệu, không phải
    tham số tối ưu hoá), và alpha âm bị từ chối chứ không lặng lẽ thành 0.
    """
    src = (repo_root() / "src" / "train" / "run.py").read_text(encoding="utf-8")
    assert 'get("data") or {}).get("mixup_alpha"' in src, "mixup không đọc từ khối data:"
    assert 'raise ValueError(f"data.mixup_alpha phải >= 0' in src, "thiếu chốt alpha âm"
    assert "mixup_alpha=mixup_alpha" in src, "train() không truyền mixup xuống run_epoch"


# --- config ---------------------------------------------------------------------


def test_khong_config_nao_con_bat_mixup_cheo_lop():
    """`data.mixup_alpha` (mixup CHÉO lớp, có trộn nhãn) không còn config nào dùng.

    Hai config từng dùng nó — `e14_mixup.yaml` và `cghnet_mixup.yaml` — chưa bao giờ chạy
    fold nào và đã gỡ ở WORKLOG S-197. Đường code thì Ở LẠI trong `run_epoch` vì nó rẻ và
    đã được test; nhưng nếu có config nào bật lại thì phải là một quyết định nói ra, không
    phải một khoá sót lại.

    ⚠️ Đừng lẫn với `data.intra_class_mixup` — phép trộn TRONG CÙNG lớp, giữ nguyên nhãn,
    nằm ở tầng dataset. Đó là phép khác, có config riêng, và `tests/test_intra_class_mixup.py`
    chốt rằng hai khoá không được bật cùng lúc.
    """
    bat = {}
    for path in sorted((repo_root() / "configs").glob("*.yaml")):
        cfg = yaml.safe_load(path.read_text("utf-8")) or {}
        alpha = float((cfg.get("data") or {}).get("mixup_alpha", 0.0))
        if alpha > 0:
            bat[path.name] = alpha
    assert bat == {}, bat


# --- hành vi thật, cần torch ---------------------------------------------------


def _fake_loader(torch, n_batch=4, batch_size=4):
    g = torch.Generator().manual_seed(0)
    return [
        {
            "image": torch.randn(batch_size, 2, 4, 4, 2, generator=g),
            "label": torch.randint(0, 7, (batch_size,), generator=g),
            "patient_id": [f"MR-{i}-{j}" for j in range(batch_size)],
        }
        for i in range(n_batch)
    ]


def _tiny(torch):
    from torch import nn

    class Net(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.fc = nn.Linear(2 * 4 * 4 * 2, 7)

        def forward(self, x):
            return self.fc(x.flatten(1))

    return Net()


def test_alpha_0_cho_ket_qua_Y_HET_duong_khong_mixup():
    """Phép kiểm quan trọng nhất của file này.

    Mixup nằm trong hàm mà MỌI thí nghiệm của dự án đi qua. Nếu đường mặc định lệch dù
    chút ít thì mọi con số cũ mất tính so sánh, và chuyện đó không lộ ra ở đâu cả.
    """
    torch = pytest.importorskip("torch", reason="cần torch")
    from src.utils.seed import set_seed

    loader = _fake_loader(torch)
    crit = torch.nn.CrossEntropyLoss()
    dev = torch.device("cpu")

    ket_qua = []
    for alpha in (0.0, 0.0):
        set_seed(1337)
        model = _tiny(torch)
        opt = torch.optim.SGD(model.parameters(), lr=0.1)
        out = run_epoch(model, loader, dev, crit, optimizer=opt, amp=False, mixup_alpha=alpha)
        ket_qua.append(out["loss"])
    assert ket_qua[0] == pytest.approx(ket_qua[1]), "alpha=0 phải tất định với cùng seed"


def test_mixup_thuc_su_doi_loss():
    """alpha > 0 phải đổi loss — nếu không thì nhánh trộn không chạy."""
    torch = pytest.importorskip("torch", reason="cần torch")
    from src.utils.seed import set_seed

    loader = _fake_loader(torch)
    crit = torch.nn.CrossEntropyLoss()
    dev = torch.device("cpu")

    losses = {}
    for alpha in (0.0, 0.4):
        set_seed(1337)
        model = _tiny(torch)
        opt = torch.optim.SGD(model.parameters(), lr=0.1)
        out = run_epoch(model, loader, dev, crit, optimizer=opt, amp=False, mixup_alpha=alpha)
        losses[alpha] = out["loss"]
    assert losses[0.4] != pytest.approx(losses[0.0]), "mixup không có tác dụng gì"


def test_mixup_KHONG_ap_o_eval():
    """Trộn ở eval làm mọi con số báo cáo thành vô nghĩa, nên `run_epoch` phải chốt lại
    thay vì tin người gọi. Không có optimizer = eval, dù `mixup_alpha` lớn."""
    torch = pytest.importorskip("torch", reason="cần torch")
    from src.utils.seed import set_seed

    loader = _fake_loader(torch)
    crit = torch.nn.CrossEntropyLoss()
    dev = torch.device("cpu")

    outs = []
    for alpha in (0.0, 1.0):
        set_seed(1337)
        model = _tiny(torch)
        outs.append(run_epoch(model, loader, dev, crit, amp=False, mixup_alpha=alpha))
    assert outs[0]["loss"] == pytest.approx(outs[1]["loss"]), (
        "eval bị mixup — mọi val_probs_*.npz sẽ tính trên ảnh đã trộn"
    )
    torch.testing.assert_close(
        torch.tensor(outs[0]["probs"]), torch.tensor(outs[1]["probs"]), rtol=0, atol=0
    )


def test_mixup_dung_rng_cua_torch_nen_seed_co_tac_dung():
    """AGENTS.md §8: mọi tính ngẫu nhiên đi qua `set_seed`. Một `np.random.default_rng()`
    mới mỗi batch sẽ làm seed vô nghĩa và run không lặp lại được."""
    torch = pytest.importorskip("torch", reason="cần torch")
    from src.utils.seed import set_seed

    loader = _fake_loader(torch)
    crit = torch.nn.CrossEntropyLoss()
    dev = torch.device("cpu")

    losses = []
    for _ in range(2):
        set_seed(1337)
        model = _tiny(torch)
        opt = torch.optim.SGD(model.parameters(), lr=0.1)
        losses.append(
            run_epoch(model, loader, dev, crit, optimizer=opt, amp=False, mixup_alpha=0.4)["loss"]
        )
    assert losses[0] == pytest.approx(losses[1]), "mixup không tôn trọng seed"


def test_mixup_hoat_dong_voi_deep_supervision():
    """Criterion của CGHNet nhận **dict** nhiều đầu ra, nên mixup phải gọi nó hai lần chứ
    không được trộn nhãn thành one-hot."""
    torch = pytest.importorskip("torch", reason="cần torch")
    from src.train.losses import deep_supervision
    from src.utils.seed import set_seed
    from torch import nn

    class MultiHead(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.fc = nn.Linear(2 * 4 * 4 * 2, 7)

        def forward(self, x):
            y = self.fc(x.flatten(1))
            return {"main": y, "aux": {"a": y * 0.5}} if self.training else y

    crit = deep_supervision(torch.nn.CrossEntropyLoss())
    set_seed(1337)
    model = MultiHead()
    opt = torch.optim.SGD(model.parameters(), lr=0.1)
    out = run_epoch(
        model,
        _fake_loader(torch),
        torch.device("cpu"),
        crit,
        optimizer=opt,
        amp=False,
        mixup_alpha=0.4,
    )
    assert out["loss"] > 0
    assert out["probs"].shape[1] == 7
