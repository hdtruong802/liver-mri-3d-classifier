"""Test lấy mẫu lại theo lớp (`data.sampling`), tái lập đội hạng 2 LLD-MMRI 2023.

Điều quan trọng nhất phải chứng minh: **`instance` giữ nguyên hành vi cũ**. `build_loaders`
là hàm mà MỌI thí nghiệm của dự án đi qua; nếu đường mặc định đổi dù chút ít thì mọi con số
cũ mất tính so sánh, và chuyện đó sẽ không lộ ra ở đâu cả.
"""

from __future__ import annotations

import numpy as np
import pytest
import yaml
from src.train.run import SAMPLING_EXPONENTS, build_sampler, sampling_weights
from src.utils.io import repo_root

# Thành phần lớp thật của 394 ca trainval (AGENTS.md §5, bảng CV 5-fold của E4), theo ĐÚNG
# chỉ số của `src/data/taxonomy.py`. ⚠️ HCC là lớp **6**, không phải 0 — ghim nhầm chỉ số làm
# test tự nhất quán mà chẳng kiểm đúng thứ nó nói đang kiểm.
COUNTS = {0: 63, 1: 46, 2: 42, 3: 40, 4: 42, 5: 36, 6: 125}
HCC, DI_CAN = 6, 3
LABELS = [c for c, n in COUNTS.items() for _ in range(n)]


def test_bang_dem_khop_taxonomy_that():
    """Neo lại rằng bảng trên dùng đúng chỉ số lớp, không phải một thứ tự tự bịa."""
    from src.data.taxonomy import NUM_CLASSES, SHORT_NAMES

    assert len(COUNTS) == NUM_CLASSES
    assert SHORT_NAMES[HCC] == "HCC"
    assert SHORT_NAMES[DI_CAN] == "di căn"
    assert sum(COUNTS.values()) == 394
    assert max(COUNTS, key=COUNTS.get) == HCC


# --- công thức ------------------------------------------------------------------------


def test_ba_che_do_va_so_mu_cua_chung():
    """`q` lấy thẳng từ `count_probabilities` của họ. `cbrt` (q=0.125) cố ý KHÔNG cài: tên
    của nó nói 1/3 mà code cho 1/8, và ta không cần một khoá gây hiểu nhầm."""
    assert SAMPLING_EXPONENTS == {"instance": 0.0, "sqrt": 0.5, "class": 1.0}


def test_sqrt_cho_dung_nghich_can_tan_suat():
    """``relative_freq**(-1)`` với q=0.5 rút gọn thành ``count**(-0.5)`` — chỗ rút gọn này
    là nơi dễ cài sai nhất, nên neo bằng công thức đóng."""
    got = sampling_weights(LABELS, "sqrt")
    counts = np.array([COUNTS[c] for c in range(7)], dtype=float)
    assert np.allclose(got, counts[np.asarray(LABELS)] ** -0.5)


def test_class_cho_can_bang_hoan_toan():
    """q=1 ⇒ kỳ vọng số ca mỗi lớp trong một epoch bằng nhau."""
    w = sampling_weights(LABELS, "class")
    p = w / w.sum()
    per_class = [p[np.asarray(LABELS) == c].sum() for c in range(7)]
    assert np.allclose(per_class, 1 / 7)


def test_instance_cho_trong_so_deu():
    assert len(set(sampling_weights(LABELS, "instance").tolist())) == 1


def test_sqrt_nam_giua_instance_va_class():
    """Đặc trưng định tính đáng neo: `sqrt` phải cân bằng MỘT PHẦN, không cực đoan."""
    ky_vong = {}
    for mode in ("instance", "sqrt", "class"):
        w = sampling_weights(LABELS, mode)
        p = w / w.sum()
        ky_vong[mode] = float(p[np.asarray(LABELS) == HCC].sum() * len(LABELS))
    # HCC: 125 ca thật -> sqrt kéo xuống ~86 -> class kéo xuống ~56.
    assert ky_vong["class"] < ky_vong["sqrt"] < ky_vong["instance"]
    assert ky_vong["instance"] == pytest.approx(COUNTS[HCC])  # không cân bằng gì
    assert ky_vong["sqrt"] == pytest.approx(86.1, abs=0.5)
    assert ky_vong["class"] == pytest.approx(394 / 7, abs=0.5)


def test_lop_vang_mat_khong_sinh_inf():
    """Một fold có thể thiếu hẳn một lớp hiếm. ``0 ** -0.5`` là vô cực, và một `inf` lọt vào
    `WeightedRandomSampler` sẽ làm nó lấy mãi một mẫu."""
    w = sampling_weights([0, 0, 6], "sqrt")
    assert np.isfinite(w).all()


def test_che_do_sai_thi_no():
    with pytest.raises(ValueError, match="data.sampling"):
        sampling_weights(LABELS, "balanced")


def test_khong_co_nhan_thi_no():
    with pytest.raises(ValueError, match="không có nhãn"):
        sampling_weights([], "sqrt")


# --- nối vào DataLoader ---------------------------------------------------------------


def test_instance_tra_none_de_giu_nguyen_shuffle():
    """Đường mặc định phải là đúng `shuffle=True` như trước, không phải một sampler tương
    đương. Xem docstring module."""
    pytest.importorskip("torch", reason="cần torch")
    assert build_sampler(LABELS, "instance") is None


def test_sqrt_tra_sampler_co_hoan_lai_dung_do_dai():
    pytest.importorskip("torch", reason="cần torch")
    sampler = build_sampler(LABELS, "sqrt")
    assert sampler is not None
    assert sampler.replacement is True
    assert sampler.num_samples == len(LABELS)
    assert len(list(iter(sampler))) == len(LABELS)


def test_sampler_ton_trong_set_seed():
    """AGENTS.md §8: mọi tính ngẫu nhiên đi qua `set_seed`. Để `WeightedRandomSampler` tự
    sinh generator thì run không lặp lại được, và điều đó không lộ ra ở đâu cả."""
    pytest.importorskip("torch", reason="cần torch")
    from src.utils.seed import set_seed

    lan = []
    for _ in range(2):
        set_seed(1337)
        lan.append(list(iter(build_sampler(LABELS, "sqrt"))))
    assert lan[0] == lan[1]

    set_seed(7)
    assert list(iter(build_sampler(LABELS, "sqrt"))) != lan[0], "seed khác phải cho dãy khác"


def test_sampler_that_su_keo_lop_hiem_len():
    """Cổng D của notebook 20 ở mức unit: đếm nhãn thực tế qua một epoch."""
    pytest.importorskip("torch", reason="cần torch")
    from src.utils.seed import set_seed

    set_seed(1337)
    drawn = np.asarray(LABELS)[list(iter(build_sampler(LABELS, "sqrt")))]
    # di căn (n=40) phải được lấy nhiều hơn tỉ lệ thật của nó...
    assert (drawn == DI_CAN).sum() > COUNTS[DI_CAN]
    # ...còn HCC (n=125, đông nhất) phải bị lấy ít đi.
    assert (drawn == HCC).sum() < COUNTS[HCC]


# --- tương thích ngược -----------------------------------------------------------------


def test_moi_config_cu_van_o_che_do_instance():
    """Thêm `data.sampling` không được đổi hành vi của bất kỳ config đã chạy nào. `uniformer_s`
    là config DUY NHẤT được phép khác."""
    lech = {}
    for path in sorted((repo_root() / "configs").glob("*.yaml")):
        if path.name.startswith("preprocess") or path.name == "data.yaml":
            continue
        cfg = yaml.safe_load(path.read_text("utf-8")) or {}
        mode = str((cfg.get("data") or {}).get("sampling", "instance"))
        if mode != "instance":
            lech[path.name] = mode
    assert lech == {"uniformer_s.yaml": "sqrt"}, lech


def test_build_loaders_doc_sampling_tu_khoi_data():
    """Kiểm ở mức mã nguồn vì `build_loaders` cần cache thật để chạy."""
    src = (repo_root() / "src" / "train" / "run.py").read_text(encoding="utf-8")
    assert 'data_config.get("sampling", "instance")' in src
    assert "shuffle=True" in src and "sampler=sampler" in src, "phải có cả hai nhánh"
