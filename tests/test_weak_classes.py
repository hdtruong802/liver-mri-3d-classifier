"""Test chẩn đoán ba lớp yếu, và **neo lại các con số đã đo**.

Hai loại test ở đây:

1. **Đúng đắn của hàm** trên dữ liệu bịa — chạy mọi nơi.
2. **Neo số thật** trên `runs/E4_cv_results` — chỉ chạy nếu thư mục run có ở máy này
   (skip trên máy khác / CI). Đây là phần quan trọng: bảy hướng chữa bị loại dựa trên đúng
   những con số này (WORKLOG S-123), nên nếu ai sửa code làm chúng trôi thì lập luận loại
   trừ mất hiệu lực mà không có gì báo.
"""

from __future__ import annotations

import numpy as np
import pytest
from src.data.taxonomy import SHORT_NAMES
from src.eval.weak_classes import (
    NARROW_MARGIN,
    confusion_report,
    error_confidence,
    error_overlap,
    fp_source_gain,
    prediction_balance,
    report,
    topk_report,
)
from src.utils.io import repo_root

RUN = repo_root() / "runs" / "E4_cv_results"
COMPARE = repo_root() / "runs" / "E6b"
BUILD_LOG = repo_root() / "runs" / "E4_per_phase_results" / "fold_1" / "cache_build_log.csv"

co_run = pytest.mark.skipif(
    not (RUN / "fold_1" / "val_probs_best.npz").exists(),
    reason="cần runs/E4_cv_results ở máy này",
)


def _onehot(labels, n=7):
    p = np.full((len(labels), n), 0.01)
    p[np.arange(len(labels)), labels] = 0.94
    return p / p.sum(axis=1, keepdims=True)


# --- đúng đắn trên dữ liệu bịa -------------------------------------------------


def test_prediction_balance_bat_duoc_du_doan_thua():
    """Cốt lõi của §1: tỉ lệ > 1 nghĩa là model đã thiên vị lớp đó rồi."""
    labels = np.array([0, 0, 0, 1])
    pred = np.array([1, 1, 0, 1])  # lớp 1 thật 1 ca, đoán 3 lần
    bal = prediction_balance(labels, pred)
    assert bal[1]["actual"] == 1
    assert bal[1]["predicted"] == 3
    assert bal[1]["ratio"] == pytest.approx(3.0)
    assert bal[0]["ratio"] == pytest.approx(1 / 3)


def test_prediction_balance_khop_precision_recall_f1():
    labels = np.array([0, 0, 1, 1])
    pred = np.array([0, 1, 1, 1])
    b = prediction_balance(labels, pred)[1]
    assert b["precision"] == pytest.approx(2 / 3)
    assert b["recall"] == pytest.approx(1.0)
    assert b["f1"] == pytest.approx(0.8)


def test_error_confidence_phan_biet_loi_sat_sao():
    """Lỗi biên nhỏ thì tầng quyết định còn cứu được; biên lớn thì không."""
    labels = np.array([0, 0])
    probs = np.zeros((2, 7))
    probs[0, 1], probs[0, 0] = 0.50, 0.48  # sát sao
    probs[1, 1], probs[1, 0] = 0.99, 0.001  # dứt khoát
    c = error_confidence(labels, probs)[0]
    assert c["n_wrong"] == 2
    assert c["narrow_frac"] == pytest.approx(0.5)


def test_error_confidence_khong_loi_thi_khong_no():
    labels = np.array([0, 1])
    c = error_confidence(labels, _onehot(labels))
    assert c[0]["n_wrong"] == 0
    assert np.isnan(c[0]["margin"])


def test_topk_phan_biet_hai_benh_khac_nhau():
    """`top2 > top1` = xếp sai hạng; `top2 == top1` = biểu diễn không mã hoá được lớp."""
    labels = np.array([0, 0])
    probs = np.zeros((2, 7))
    probs[0, 1], probs[0, 0] = 0.6, 0.3  # lớp thật ở hạng 2
    probs[1, 1], probs[1, 2], probs[1, 0] = 0.6, 0.3, 0.05  # lớp thật ở hạng 3
    t = topk_report(labels, probs)[0]
    assert t["top1"] == 0.0
    assert t["top2"] == pytest.approx(0.5)
    assert t["top3"] == pytest.approx(1.0)
    assert t["rank_median"] == pytest.approx(2.5)


def test_error_overlap_doc_lap_thi_gan_ky_vong():
    rng = np.random.default_rng(0)
    labels = rng.integers(0, 7, 700)
    pa, pb = labels.copy(), labels.copy()
    ia, ib = rng.choice(700, 140, replace=False), rng.choice(700, 140, replace=False)
    pa[ia] = (pa[ia] + 1) % 7
    pb[ib] = (pb[ib] + 1) % 7
    ov = error_overlap(labels, pa, pb)
    assert ov["wrong_both"] == pytest.approx(ov["expected_if_independent"], rel=0.5)


def test_error_overlap_giong_het_thi_trung_100():
    labels = np.array([0, 1, 2, 3])
    pred = np.array([1, 1, 2, 3])
    ov = error_overlap(labels, pred, pred)
    assert ov["overlap_frac"] == pytest.approx(1.0)
    assert ov["oracle_accuracy"] == pytest.approx(0.75)


def test_fp_source_gain_chua_het_loi_thi_lop_do_hoan_hao():
    labels = np.array([0, 0, 0, 1, 1])
    pred = np.array([1, 0, 0, 1, 1])  # lớp 0 rò 1 ca sang lớp 1
    g = fp_source_gain(labels, pred, source=0)
    assert g["n_leaked"] == 1
    assert g["leaked_to"] == {SHORT_NAMES[1]: 1}
    assert g["macro_f1_after"] > g["macro_f1_before"]


def test_confusion_report_dung_chieu():
    labels = np.array([0, 0, 1])
    pred = np.array([0, 1, 1])
    m = confusion_report(labels, pred)
    assert m[0, 0] == 1 and m[0, 1] == 1 and m[1, 1] == 1
    assert m.sum() == 3


# --- neo số thật ---------------------------------------------------------------


@co_run
def test_neo_so_that_cua_chan_doan():
    """Bảy hướng chữa bị loại dựa trên đúng những con số này. Đừng để chúng trôi."""
    out = report(
        RUN, COMPARE if COMPARE.exists() else None, BUILD_LOG if BUILD_LOG.exists() else None
    )
    assert out["n"] == 394

    ten = {v: k for k, v in SHORT_NAMES.items()}
    bal = out["balance"]

    # §1 — hai lớp yếu bị dự đoán THỪA. Đây là căn cứ loại trọng số lớp và logit adjustment.
    assert bal[ten["ICC"]]["ratio"] == pytest.approx(58 / 46, abs=0.01)
    assert bal[ten["áp-xe"]]["ratio"] == pytest.approx(55 / 42, abs=0.01)
    assert bal[ten["HCC"]]["ratio"] < 0.9, "HCC phải bị dự đoán THIẾU"
    for lop in ("ICC", "áp-xe"):
        assert bal[ten[lop]]["ratio"] > 1.2, f"{lop} không còn bị dự đoán thừa — xem lại §1"

    # §3 — gần như không lỗi nào sát sao. Căn cứ loại cả họ sửa-ở-tầng-quyết-định.
    conf = out["confidence"]
    n_sai = sum(c["n_wrong"] for c in conf.values())
    n_sat = sum(c["narrow_frac"] * c["n_wrong"] for c in conf.values() if c["n_wrong"])
    assert n_sai == 117
    assert n_sat / n_sai < 0.02, f"{n_sat:.0f}/{n_sai} lỗi sát sao — kết luận §3 đã đổi"
    for lop in ("ICC", "áp-xe", "di căn"):
        assert conf[ten[lop]]["narrow_frac"] == 0.0

    # §4 — di căn: top-2 KHÔNG hơn top-1. Đây là chỗ nó khác ICC về bản chất.
    tk = out["topk"]
    assert tk[ten["di căn"]]["top1"] == pytest.approx(0.5)
    assert tk[ten["di căn"]]["top2"] == pytest.approx(tk[ten["di căn"]]["top1"])
    assert tk[ten["ICC"]]["top2"] > tk[ten["ICC"]]["top1"] + 0.2, "ICC phải hồi mạnh ở top-2"

    # §6 — ba hướng nhầm lớn nhất, và trần nếu chữa lớp đa số.
    m = out["confusion"]
    assert m[ten["HCC"], ten["di căn"]] == 15
    assert m[ten["ICC"], ten["áp-xe"]] == 10
    assert m[ten["HCC"], ten["ICC"]] == 9
    gain = out["fp_gain"]
    assert gain["source"] == "HCC"
    assert gain["macro_f1_after"] - gain["macro_f1_before"] > 0.05

    # §5 — lỗi có cấu trúc, không phải nhiễu.
    if "overlap" in out:
        ov = out["overlap"]
        assert ov["wrong_both"] == 86
        assert ov["overlap_frac"] > 0.7
        assert ov["wrong_both"] > 2 * ov["expected_if_independent"]


@co_run
def test_chay_duoc_khi_khong_co_compare_va_build_log():
    """Hai tham số kia là tuỳ chọn — thiếu chúng thì bỏ §2 và §5, không nổ."""
    out = report(RUN)
    assert "balance" in out and "topk" in out
    assert "overlap" not in out and "geometry" not in out


def test_nguong_sat_sao_la_hang_so_cong_khai():
    """Con số này đi vào lập luận loại trừ nên phải khai ở một chỗ, không rải rác."""
    assert NARROW_MARGIN == 0.10
