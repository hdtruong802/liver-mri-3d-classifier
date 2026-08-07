"""Test đường chạy test-104.

Phần suy luận cần torch nên không test được ở máy này; thứ test được — và cũng là thứ
đáng test hơn — là **các cổng chặn**. Chúng tồn tại để một lần chạm sai không bao giờ
xảy ra, nên một cổng hỏng thầm lặng thì tệ hơn nhiều so với một hàm metric hỏng.
"""

from __future__ import annotations

import os
import subprocess
import sys

import numpy as np
import pytest
from src.eval.test_once import PINNED_SHA256, find_checkpoints, sha16
from src.eval.test_report import COVERAGES, load_test, report, selective_rows, two_sided_p

# --- cổng chặn của test_once --------------------------------------------------


def test_sha256_ghim_khop_worklog():
    """Danh sách ghim phải trùng 5 mã ở WORKLOG S-081, không phải giá trị bịa ra."""
    assert set(PINNED_SHA256) == {1, 2, 3, 4, 5}
    assert PINNED_SHA256[1] == "2e1f3e1ad477ad59"
    assert PINNED_SHA256[5] == "d61cc7ed94b8ebf0"
    assert len(set(PINNED_SHA256.values())) == 5, "mã băm trùng nhau"


def test_find_checkpoints_nhan_ca_hai_bo_cuc(tmp_path):
    flat = tmp_path / "flat"
    flat.mkdir()
    for fold in (1, 2):
        (flat / f"best_fold_{fold}.pt").write_bytes(b"x")
    assert set(find_checkpoints(flat, [1, 2])) == {1, 2}

    nested = tmp_path / "nested"
    for fold in (1, 2):
        (nested / f"fold_{fold}").mkdir(parents=True)
        (nested / f"fold_{fold}" / "best.pt").write_bytes(b"x")
    got = find_checkpoints(nested, [1, 2])
    assert set(got) == {1, 2}
    assert got[2].parent.name == "fold_2", "suy fold từ thư mục cha bị lệch"


def test_find_checkpoints_khong_doan_bua(tmp_path):
    """`best.pt` không suy được fold thì phải BỎ, không gán bừa cho fold đang hỏi.

    Gán bừa tạo ra một 'ensemble' đếm cùng một model hai lần, và con số ra vẫn hợp lý.
    """
    (tmp_path / "linh_tinh").mkdir()
    (tmp_path / "linh_tinh" / "best.pt").write_bytes(b"x")
    assert find_checkpoints(tmp_path, [1, 2, 3]) == {}


def test_sha16_phan_biet_duoc_hai_file(tmp_path):
    a, b = tmp_path / "a.pt", tmp_path / "b.pt"
    a.write_bytes(b"aaa")
    b.write_bytes(b"bbb")
    assert sha16(a) != sha16(b)
    assert len(sha16(a)) == 16


def test_cli_tu_choi_khi_thieu_co():
    """Không có `--i-know-this-is-final` thì phải thoát khác 0 và KHÔNG chạy gì."""
    result = subprocess.run(
        [sys.executable, "-m", "src.eval.test_once", "--ckpt-dir", ".", "--out", "."],
        capture_output=True,
        text=True,
        # Console Windows mặc định cp1252 và thông báo từ chối viết bằng tiếng Việt.
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode != 0
    assert "TỪ CHỐI CHẠY" in result.stdout + result.stderr


def test_prereg_da_commit():
    """Pre-registration phải nằm trong lịch sử git trước khi chạm test.

    Kiểm ở đây chứ không chỉ trong `test_once`: nếu ai đó xoá file mà quên, cổng kia
    chỉ nổ đúng lúc chạy trên Kaggle — tức là đúng lúc không muốn nó nổ nhất.
    """
    out = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "docs/TEST104_PREREGISTRATION.md"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert out, "docs/TEST104_PREREGISTRATION.md chưa được commit"


# --- phần báo cáo (không cần torch) --------------------------------------------


def _fake_run(tmp_path, n=104, k=5, c=7, seed=0):
    tmp_path.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    labels = rng.integers(0, c, n)
    logits = rng.normal(size=(k, n, c))
    logits[:, np.arange(n), labels] += 2.0  # cho model đúng hơn ngẫu nhiên
    probs = np.exp(logits)
    probs /= probs.sum(axis=2, keepdims=True)
    path = tmp_path / "test_probs.npz"
    np.savez_compressed(
        path,
        member_probs=probs,
        labels=labels,
        patient_ids=np.array([f"MR-{i:06d}" for i in range(n)]),
        folds=np.arange(1, k + 1),
    )
    return tmp_path


def test_load_test_tra_ve_ensemble_la_trung_binh(tmp_path):
    d = load_test(_fake_run(tmp_path))
    np.testing.assert_allclose(d["ensemble"], d["member_probs"].mean(axis=0))
    np.testing.assert_allclose(d["ensemble"].sum(axis=1), 1.0, atol=1e-9)


def test_load_test_tu_choi_mot_thanh_vien(tmp_path):
    """Một model đơn không có epistemic theo định nghĩa — phải nổ, không trả 0 lặng lẽ."""
    rng = np.random.default_rng(1)
    probs = rng.dirichlet(np.ones(7), size=(1, 10))
    np.savez_compressed(
        tmp_path / "test_probs.npz",
        member_probs=probs,
        labels=rng.integers(0, 7, 10),
        patient_ids=np.array([f"MR-{i}" for i in range(10)]),
        folds=np.array([1]),
    )
    with pytest.raises(ValueError, match="bất đồng"):
        load_test(tmp_path)


def test_selective_coverage_100_bang_metric_toan_tap(tmp_path):
    """Neo: F1@100% phải bằng macro-F1 thường, bất kể xếp hạng thế nào."""
    from src.eval.metrics import macro_f1

    d = load_test(_fake_run(tmp_path))
    labels, ens = d["labels"], d["ensemble"]
    rows = selective_rows(labels, ens, {"a": ens.max(1), "b": -ens.max(1)})
    expected = macro_f1(labels, ens.argmax(1))
    for name in ("a", "b"):
        assert rows[name]["F1@100%"] == pytest.approx(expected)


def test_p_hai_phia_khong_bao_0_cho_hieu_ung_bang_khong():
    """Bẫy đã dính khi chạy thử: hai điểm xếp hạng giống hệt nhau ⇒ mọi hiệu = 0.

    Cách viết `2 * min(m, 1 - m)` cho P = 0 ở đây, tức tuyên bố ý nghĩa tối đa cho
    một hiệu ứng bằng không — đúng cái mà bảng test-104 sẽ in ra nếu bug còn sống.
    """
    assert two_sided_p(np.zeros(2000)) == pytest.approx(1.0)
    assert two_sided_p(np.full(2000, 0.05)) == pytest.approx(0.0)
    assert two_sided_p(np.full(2000, -0.05)) == pytest.approx(0.0)
    balanced = np.concatenate([np.full(1000, -0.01), np.full(1000, 0.01)])
    assert two_sided_p(balanced) == pytest.approx(1.0)
    assert 0.0 <= two_sided_p(np.random.default_rng(0).normal(size=2000)) <= 1.0


def test_coverage_da_chot_truoc():
    """Danh sách coverage là cam kết trong pre-registration, không phải tham số tuỳ ý."""
    assert COVERAGES == (1.0, 0.9, 0.8, 0.7)


def test_report_chay_duoc_va_khong_fit_T_tren_test(tmp_path, monkeypatch):
    """`T` phải đến từ out-of-fold. Bịa một OOF riêng và kiểm T đúng là của nó."""
    run_dir = _fake_run(tmp_path / "test", seed=2)

    oof = tmp_path / "oof"
    rng = np.random.default_rng(3)
    for fold in range(1, 6):
        d = oof / f"fold_{fold}"
        d.mkdir(parents=True)
        n = 20
        labels = rng.integers(0, 7, n)
        logits = rng.normal(size=(n, 7))
        logits[np.arange(n), labels] += 1.5
        probs = np.exp(logits)
        probs /= probs.sum(axis=1, keepdims=True)
        np.savez_compressed(
            d / "val_probs_best.npz",
            probs=probs,
            labels=labels,
            patient_ids=np.array([f"MR-{fold}-{i}" for i in range(n)]),
            epoch=1,
        )

    monkeypatch.setattr("src.eval.test_report.resolve_repo_path", lambda p: p)
    r = report(run_dir, oof)

    from src.eval.calibration import fit_temperature_min_ece

    on_test = fit_temperature_min_ece(r["ensemble"], r["labels"])
    assert r["temperature"] != pytest.approx(on_test, abs=1e-6), (
        "T trùng đúng giá trị tối ưu TRÊN TEST — nghi fit trên test, đó là leakage"
    )

    assert r["n_cases"] == 104
    assert "ensemble 5 fold" in r["classification"]
    assert len(r["per_member"]) == 5
    assert set(r["selective"]) == {"max-prob (đối chứng)", "−epistemic (bất đồng 5 model)"}
    assert "AURC" in r["paired"]


def test_epistemic_khong_am(tmp_path, monkeypatch):
    monkeypatch.setattr("src.eval.test_report.resolve_repo_path", lambda p: p)
    run_dir = _fake_run(tmp_path / "test", seed=4)
    oof = tmp_path / "oof"
    rng = np.random.default_rng(5)
    for fold in range(1, 6):
        d = oof / f"fold_{fold}"
        d.mkdir(parents=True)
        probs = rng.dirichlet(np.ones(7), size=20)
        np.savez_compressed(
            d / "val_probs_best.npz",
            probs=probs,
            labels=rng.integers(0, 7, 20),
            patient_ids=np.array([f"MR-{fold}-{i}" for i in range(20)]),
            epoch=1,
        )
    r = report(run_dir, oof)
    assert (r["epistemic"] >= 0).all()
