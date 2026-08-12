"""Test lớp nạp dự đoán out-of-fold của web app.

Chạy trên `.npz` giả trong `tmp_path` — không phụ thuộc `runs/` có thật hay không, và
không cần torch (đó là ràng buộc của backend, AGENTS.md §4).
"""

import sys
from pathlib import Path

import numpy as np
import pytest
from webapp.backend.inference import oof_result, predict
from webapp.backend.predictions import load_store
from webapp.backend.schemas import DeferBasis, ProvenanceSource

N_CLASSES = 7


def _write_fold(directory: Path, ids: list[str], *, epistemic: bool = True, seed: int = 0) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    n = len(ids)
    labels = rng.integers(0, N_CLASSES, size=n)

    logits = rng.normal(0, 1, size=(n, N_CLASSES))
    logits[np.arange(n), labels] += 3.0  # cho model đoán đúng phần lớn
    probs = np.exp(logits - logits.max(1, keepdims=True))
    probs /= probs.sum(1, keepdims=True)
    np.savez_compressed(
        directory / "val_probs_best.npz",
        probs=probs,
        labels=labels,
        patient_ids=np.array(ids),
        epoch=1,
    )
    if epistemic:
        members = np.stack(
            [
                (lambda p: p / p.sum(1, keepdims=True))(
                    np.exp(
                        (logits + rng.normal(0, 0.8, size=(n, N_CLASSES)))
                        - logits.max(1, keepdims=True)
                    )
                )
                for _ in range(6)
            ]
        )
        np.savez_compressed(
            directory / "mc_dropout.npz",
            member_probs=members,
            labels=labels,
            patient_ids=np.array(ids),
            n_passes=6,
        )


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    _write_fold(tmp_path / "fold_1", [f"MR{100 + i}" for i in range(20)], seed=1)
    _write_fold(tmp_path / "fold_2", [f"MR{200 + i}" for i in range(15)], seed=2)
    return tmp_path


@pytest.fixture(autouse=True)
def _clear_cache():
    """`load_store` có lru_cache — không xoá thì fixture này ảnh hưởng fixture kia."""
    load_store.cache_clear()
    yield
    load_store.cache_clear()


def test_nap_du_ca_va_khong_keo_torch(run_dir: Path):
    store = load_store(str(run_dir))
    assert store is not None
    assert len(store.cases) == 35
    assert store.n_folds == 2
    assert "torch" not in sys.modules, "backend KHÔNG được kéo theo torch (AGENTS.md §4)"


def test_thu_muc_khong_ton_tai_thi_tra_None(tmp_path: Path):
    assert load_store(str(tmp_path / "khong-co")) is None


def test_thu_muc_rong_thi_tra_None(tmp_path: Path):
    (tmp_path / "fold_1").mkdir()
    assert load_store(str(tmp_path)) is None


def test_tra_cuu_bo_qua_dinh_dang_id(run_dir: Path):
    """`MR-100` và `MR100` phải ra cùng một ca — chuẩn hoá theo chữ số."""
    store = load_store(str(run_dir))
    assert store.get("MR100") is store.get("MR-100")
    assert store.get("MR100") is not None


def test_temperature_lam_mem_xac_suat(run_dir: Path):
    """T > 1 phải HẠ độ tự tin: model train bằng CE trần tự tin quá mức."""
    store = load_store(str(run_dir))
    assert store.temperature > 0
    case = next(iter(store.cases.values()))
    if store.temperature > 1.0:
        assert case.probs_calibrated.max() < case.probs_raw.max()


def test_hieu_chinh_khong_doi_lop_doan(run_dir: Path):
    """Temperature scaling giữ nguyên thứ hạng — nếu đổi thì có lỗi thật."""
    store = load_store(str(run_dir))
    for case in store.cases.values():
        assert case.probs_calibrated.argmax() == case.probs_raw.argmax()
        assert case.pred_index == case.probs_raw.argmax()


def test_nguong_defer_cho_dung_coverage_muc_tieu(run_dir: Path):
    """Ngưỡng là phân vị epistemic, không phải số chọn tay."""
    store = load_store(str(run_dir))
    epis = np.array([c.epistemic for c in store.cases.values()])
    duoi_nguong = (epis <= store.defer_threshold).mean()
    assert duoi_nguong == pytest.approx(0.8, abs=0.05)


def test_khong_co_mc_dropout_thi_khong_defer_ai(tmp_path: Path):
    """Không rơi về max-prob: đã đo được max-prob xếp hạng vô ích (P=0.88, S-087)."""
    _write_fold(tmp_path / "fold_1", [f"MR{i}" for i in range(300, 310)], epistemic=False)
    store = load_store(str(tmp_path))
    assert store.has_epistemic is False
    assert all(not store.should_defer(c) for c in store.cases.values())


def test_chan_thu_tu_ca_lech_giua_hai_file(tmp_path: Path):
    d = tmp_path / "fold_1"
    _write_fold(d, [f"MR{i}" for i in range(400, 410)])
    mc = dict(np.load(d / "mc_dropout.npz", allow_pickle=True))
    mc["patient_ids"] = np.array([f"MR{i}" for i in range(500, 510)])
    np.savez_compressed(d / "mc_dropout.npz", **mc)
    with pytest.raises(ValueError, match="lệch khỏi"):
        load_store(str(tmp_path))


def test_chan_benh_nhan_trung_giua_hai_fold(tmp_path: Path):
    ids = [f"MR{i}" for i in range(600, 610)]
    _write_fold(tmp_path / "fold_1", ids, seed=1)
    _write_fold(tmp_path / "fold_2", ids, seed=2)
    with pytest.raises(ValueError, match="hai fold"):
        load_store(str(tmp_path))


def test_oof_result_danh_dau_dung_nguon(run_dir: Path):
    store = load_store(str(run_dir))
    result = oof_result(store.get("MR100"), store)
    assert result.provenance.source is ProvenanceSource.OOF
    assert result.provenance.model_version is None, "không bịa chuỗi phiên bản"
    assert result.inference_ms is None, "tra cứu chứ không suy luận — báo ms là gây hiểu nhầm"


def test_defer_theo_epistemic_chu_khong_theo_confidence(run_dir: Path):
    """Bất biến trung tâm: một ca có thể defer DÙ confidence cao, và ngược lại."""
    store = load_store(str(run_dir))
    for case in store.cases.values():
        result = oof_result(case, store)
        assert result.defer == (case.epistemic > store.defer_threshold)


def test_predict_bao_ro_khi_khong_co_ca_oof(run_dir: Path, monkeypatch):
    monkeypatch.setenv("LLDMMRI_PREDICTIONS_DIR", str(run_dir))
    load_store.cache_clear()
    with pytest.raises(LookupError, match="Không có prediction out-of-fold"):
        predict("KHONG-TON-TAI-9")


def test_oof_bao_dung_co_so_va_diem_defer(run_dir: Path):
    """`defer_score` phải là epistemic, KHÔNG phải confidence — hai số khác nhau."""
    store = load_store(str(run_dir))
    case = store.get("MR100")
    r = oof_result(case, store)

    assert r.defer_basis is DeferBasis.EPISTEMIC
    assert r.defer_score == pytest.approx(case.epistemic)
    assert r.defer_threshold == pytest.approx(store.defer_threshold)
    assert r.defer_score != pytest.approx(r.confidence), "trùng nhau là dấu hiệu nối nhầm trường"


def test_predict_bao_ro_khi_khong_co_store(monkeypatch):
    monkeypatch.setattr("webapp.backend.inference.load_store", lambda: None)
    with pytest.raises(LookupError, match="Chưa có prediction out-of-fold"):
        predict("MR999999")


def test_id_khong_co_chu_so_khong_lam_no_api(run_dir: Path):
    """Chuỗi lạ do người dùng gõ là chuyện bình thường, không phải 500."""
    store = load_store(str(run_dir))
    assert store.get("KHONG-CO-CHU-SO") is None


def test_chieu_so_sanh_epistemic_la_NGUOC(run_dir: Path):
    """Epistemic CAO thì từ chối — ngược chiều với confidence."""
    store = load_store(str(run_dir))
    cao = max(store.cases.values(), key=lambda c: c.epistemic)
    thap = min(store.cases.values(), key=lambda c: c.epistemic)
    assert store.should_defer(cao) is True
    assert store.should_defer(thap) is False
