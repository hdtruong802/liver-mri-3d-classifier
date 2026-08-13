"""Test intra-class mixup ở tầng dataset, và config dùng nó.

Điều quan trọng nhất phải chứng minh: **`intra_class_mixup = 0` cho đường code y hệt bản
chưa có nó**. Phép này nằm trong `CachedLesionDataset.__getitem__` — hàm mà *mọi* run của
dự án đi qua, kể cả val và test-104. Nếu nó làm lệch dù chút ở đường mặc định thì mọi con
số cũ mất tính so sánh, và chuyện đó sẽ không lộ ra ở đâu cả.

Ba chế độ hỏng **im lặng** được neo riêng, vì cả ba đều chạy trơn và vẫn ra số hợp lý:

1. dataset **val** cũng trộn ⇒ mọi metric báo cáo thành vô nghĩa;
2. nhãn bị trộn theo ⇒ thành một phép khác hẳn (mixup chéo lớp), và `train_loss` mất nghĩa;
3. khoá `mixup_lambda` chỉ có ở *một số* mẫu ⇒ `default_collate` nổ theo thành phần batch,
   tức sau vài chục bước ngẫu nhiên chứ không phải ngay bước đầu.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest
import yaml
from src.data.dataset import CachedLesionDataset, build_fold_datasets
from src.utils.io import repo_root

try:
    import torch
except ImportError:  # pragma: no cover — máy chưa cài deep-learning stack
    torch = None

# ⚠️ Gate từng test, KHÔNG gate cả file. `__init__` của dataset không cần torch (chỉ
# `__getitem__` cần), nên phần kiểm hợp đồng — chữ ký, khoá config, cán cân lớp — chạy được
# trên máy chưa cài torch. `importorskip` ở mức module sẽ giấu mất đúng những test rẻ nhất
# và bắt lỗi sớm nhất.
requires_torch = pytest.mark.skipif(torch is None, reason="đọc mẫu cần torch")

# Lớp 6 lặp nhiều nhất ⇒ đóng vai lớp đa số, khớp HCC của taxonomy thật.
NHAN_GIA = [6, 6, 6, 6, 1, 1, 3, 3, 3, 4]


def _cache_gia(tmp_path, nhan=NHAN_GIA, shape=(8, 6, 6, 4)):
    """Cache tối giản: mỗi ca là một hằng số riêng, nên phép trộn đọc ra được λ."""
    mau = []
    for i, label in enumerate(nhan):
        pid = f"MR{i:04d}"
        # Giá trị = i + 1 ⇒ hai ca trộn cho λ·(a+1) + (1−λ)·(b+1), giải ra λ chính xác.
        np.savez(
            tmp_path / f"{pid}.npz",
            image=np.full(shape, float(i + 1), dtype=np.float32),
            label=label,
        )
        mau.append((pid, label))
    return mau


# --- hợp đồng, không cần cache -------------------------------------------------


def test_mac_dinh_la_tat():
    """Mặc định phải TẮT, để mọi config cũ không đổi hành vi."""
    sig = inspect.signature(CachedLesionDataset.__init__)
    assert sig.parameters["intra_class_mixup"].default == 0.0
    assert sig.parameters["intra_class_mixup_exclude_majority"].default is True
    assert inspect.signature(build_fold_datasets).parameters["intra_class_mixup"].default == 0.0


def test_tham_so_moi_la_keyword_only():
    """Truyền lẫn vị trí với `transform` là lỗi im lặng — chặn bằng chữ ký."""
    for name in ("intra_class_mixup", "intra_class_mixup_exclude_majority"):
        assert (
            inspect.signature(CachedLesionDataset.__init__).parameters[name].kind
            is inspect.Parameter.KEYWORD_ONLY
        )


def test_alpha_am_bi_tu_choi(tmp_path):
    with pytest.raises(ValueError, match="intra_class_mixup"):
        CachedLesionDataset(tmp_path, _cache_gia(tmp_path), intra_class_mixup=-0.5)


def test_val_khong_bao_gio_duoc_tron():
    """Chốt ở `build_fold_datasets`, không để chỗ gọi quyết định.

    Kiểm ở mức mã nguồn vì hàm này cần cache thật. Cùng lối với
    `tests/test_mixup.py::test_train_doc_mixup_tu_khoi_data...`.
    """
    src = (repo_root() / "src" / "data" / "dataset.py").read_text(encoding="utf-8")
    than = src[src.index("def build_fold_datasets") :]
    goi_val = than[than.index("CachedLesionDataset(cache_dir, fold.val") :]
    assert "intra_class_mixup" not in goi_val, "dataset val nhận tham số mixup — báo cáo sẽ sai"


def test_run_doc_khoa_tu_khoi_data():
    src = (repo_root() / "src" / "train" / "run.py").read_text(encoding="utf-8")
    assert 'data_config.get("intra_class_mixup", 0.0)' in src, "không đọc từ khối data:"
    assert "intra_class_mixup=intra_mixup" in src, "không truyền xuống build_fold_datasets"


# --- đường TẮT phải y hệt bản cũ -----------------------------------------------


@requires_torch
def test_tat_thi_khong_doc_file_thu_hai(tmp_path, monkeypatch):
    """Bằng chứng mạnh nhất cho "đường mặc định không đổi": đúng MỘT lần đọc đĩa mỗi mẫu."""
    ds = CachedLesionDataset(tmp_path, _cache_gia(tmp_path))
    dem = {"n": 0}
    goc = CachedLesionDataset._load_image

    def dem_load(path):
        dem["n"] += 1
        return goc(path)

    monkeypatch.setattr(CachedLesionDataset, "_load_image", staticmethod(dem_load))
    item = ds[4]
    assert dem["n"] == 1
    assert float(item["image"].min()) == float(item["image"].max()) == 5.0
    assert "mixup_lambda" not in item and "mixup_partner" not in item
    assert ds.class_pools == {} and ds.mixup_excluded_class is None


# --- đường BẬT ------------------------------------------------------------------


def test_lop_da_so_bi_loai_va_duoc_suy_tu_nhan(tmp_path):
    ds = CachedLesionDataset(tmp_path, _cache_gia(tmp_path), intra_class_mixup=1.0)
    assert ds.mixup_excluded_class == 6, "lớp đa số phải suy ra từ nhãn train của chính fold"
    assert ds.mixup_classes == [1, 3, 4]
    assert sorted(ds.class_pools) == [1, 3, 4, 6]


def test_khong_loai_lop_nao_khi_tat_co(tmp_path):
    ds = CachedLesionDataset(
        tmp_path,
        _cache_gia(tmp_path),
        intra_class_mixup=1.0,
        intra_class_mixup_exclude_majority=False,
    )
    assert ds.mixup_excluded_class is None
    assert ds.mixup_classes == [1, 3, 4, 6]


@requires_torch
def test_lop_bi_loai_giu_nguyen_anh(tmp_path):
    ds = CachedLesionDataset(tmp_path, _cache_gia(tmp_path), intra_class_mixup=1.0)
    for index in range(4):  # bốn ca đầu là lớp 6
        item = ds[index]
        assert float(item["image"].min()) == float(item["image"].max()) == float(index + 1)
        assert item["mixup_lambda"] == 1.0
        assert item["mixup_partner"] == item["patient_id"]


@requires_torch
def test_moi_mau_deu_co_du_khoa_mixup(tmp_path):
    """Chống lỗi `default_collate` nổ theo thành phần batch.

    Batch train bình thường chứa cả ca thuộc lớp bị loại và ca thuộc lớp hiếm. Nếu khoá
    `mixup_lambda` chỉ xuất hiện ở loại thứ hai thì collate nổ — nhưng chỉ ở những batch
    tình cờ trộn hai loại, tức sau vài chục bước, không phải bước đầu.
    """
    ds = CachedLesionDataset(tmp_path, _cache_gia(tmp_path), intra_class_mixup=1.0)
    khoa = [set(ds[i]) for i in range(len(ds))]
    assert all(k == khoa[0] for k in khoa), "khoá không đồng nhất giữa các mẫu"
    assert {"mixup_lambda", "mixup_partner"} <= khoa[0]


@requires_torch
def test_anh_la_to_hop_loi_cua_hai_ca_cung_lop(tmp_path):
    """Giải ngược λ từ giá trị pixel, rồi đối chiếu với λ mà dataset báo."""
    mau = _cache_gia(tmp_path)
    ds = CachedLesionDataset(tmp_path, mau, intra_class_mixup=1.0)
    gia_tri = {pid: float(i + 1) for i, (pid, _) in enumerate(mau)}

    torch.manual_seed(0)
    thay_tron = 0
    for _ in range(60):
        item = ds[6]  # lớp 3, pool = {ca 6, 7, 8} ⇒ giá trị 7, 8, 9
        lam = item["mixup_lambda"]
        doi_tac = item["mixup_partner"]
        assert 0.0 <= lam <= 1.0
        assert gia_tri[doi_tac] in (7.0, 8.0, 9.0), "bốc đối tác ngoài lớp"

        mong_doi = lam * 7.0 + (1.0 - lam) * gia_tri[doi_tac]
        thuc = float(item["image"].reshape(-1)[0])
        assert item["image"].min() == item["image"].max()
        assert thuc == pytest.approx(mong_doi, abs=1e-5)
        if doi_tac != "MR0006":
            thay_tron += 1
    assert thay_tron > 0, "60 lượt không lần nào bốc được ca khác — RNG không chạy"


@requires_torch
def test_nhan_khong_bao_gio_bi_tron(tmp_path):
    """Đây là điều tách phép này khỏi mixup chéo lớp. Nhãn trộn = phép khác hẳn."""
    ds = CachedLesionDataset(tmp_path, _cache_gia(tmp_path), intra_class_mixup=1.0)
    for index, (_, nhan) in enumerate(_cache_gia(tmp_path)):
        item = ds[index]
        assert item["label"] == nhan
        assert isinstance(item["label"], int)


@requires_torch
def test_doc_dia_gap_doi_dung_o_lop_duoc_tron(tmp_path, monkeypatch):
    """Chi phí thật của phép này. Neo lại để không ai ngạc nhiên khi `s/epoch` tăng."""
    ds = CachedLesionDataset(tmp_path, _cache_gia(tmp_path), intra_class_mixup=1.0)
    goc = CachedLesionDataset._load_image
    dem = {"n": 0}

    def dem_load(path):
        dem["n"] += 1
        return goc(path)

    monkeypatch.setattr(CachedLesionDataset, "_load_image", staticmethod(dem_load))
    ds[0]  # lớp 6, bị loại
    assert dem["n"] == 1
    dem["n"] = 0
    ds[4]  # lớp 1, được trộn
    assert dem["n"] == 2


@requires_torch
def test_shape_lech_thi_no_kem_ten_ca(tmp_path):
    """Cache trộn từ hai lần build khác hình học: nổ kèm ID, không broadcast im lặng."""
    mau = _cache_gia(tmp_path, nhan=[1, 1])
    np.savez(tmp_path / "MR0001.npz", image=np.ones((8, 6, 6, 8), np.float32), label=1)
    ds = CachedLesionDataset(tmp_path, mau, intra_class_mixup=1.0)
    with pytest.raises(ValueError, match=r"không trộn được"):
        for _ in range(40):
            ds[0]


@requires_torch
def test_transform_chay_tren_anh_da_tron(tmp_path):
    """Thứ tự: trộn TRƯỚC augment. Hai crop đều bám tổn thương nên nội suy còn nghĩa
    giải phẫu; augment sau đó áp một lần cho ảnh đã trộn, không phải hai lần độc lập."""
    thay: list[float] = []

    def transform(item):
        thay.append(float(item["image"].reshape(-1)[0]))
        return item

    ds = CachedLesionDataset(tmp_path, _cache_gia(tmp_path), transform, intra_class_mixup=1.0)
    ds[6]
    assert thay and 7.0 <= thay[0] <= 9.0, "transform nhận ảnh chưa trộn"


# --- config ---------------------------------------------------------------------


def test_config_khac_base_dung_ba_khoa():
    """Hai khoá khoa học + `output_dir`. Thừa một khoá là thí nghiệm hai biến."""

    def phang(d, tien=""):
        out = {}
        for k, v in d.items():
            key = f"{tien}{k}"
            out.update(phang(v, key + ".")) if isinstance(v, dict) else out.update({key: v})
        return out

    cfg = repo_root() / "configs"
    a = phang(yaml.safe_load((cfg / "uniformer_s.yaml").read_text("utf-8")))
    b = phang(yaml.safe_load((cfg / "uniformer_s_intra_mixup.yaml").read_text("utf-8")))
    lech = {k for k in set(a) | set(b) if a.get(k, "<vắng>") != b.get(k, "<vắng>")}
    assert lech == {
        "output_dir",
        "data.intra_class_mixup",
        "data.intra_class_mixup_exclude_majority",
    }, f"lệch ngoài dự kiến: {lech}"
    assert b["data.intra_class_mixup"] == 1.0
    assert b["data.mixup_alpha"] == 0.0, "hai phép mixup bật cùng lúc = thí nghiệm hai biến"
    assert b["output_dir"] != a["output_dir"], "trùng output_dir sẽ ghi đè run cũ"
