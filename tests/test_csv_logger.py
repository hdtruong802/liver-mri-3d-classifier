"""Test `CsvLogger` — trọng tâm là an toàn khi resume.

`train_log.csv` mở ở chế độ append và một run trên Kaggle có thể bị ngắt rồi chạy tiếp
nhiều lần. Nếu schema cột đổi giữa hai lần chạy mà logger không xử lý, file sẽ có những
dòng nhiều cột hơn header và **không đọc lại được bằng `csv.DictReader`** — mất toàn bộ
lịch sử `val_loss` của run đó, tức mất luôn chẩn đoán "epoch chạm đáy" (ρ=0.770, S-107).
"""

from __future__ import annotations

import csv

from src.utils.logging import CsvLogger

FIELDS = ["epoch", "loss"]


def _rows(path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_ghi_header_va_dong_binh_thuong(tmp_path):
    path = tmp_path / "log.csv"
    with CsvLogger(path, FIELDS) as log:
        log.log({"epoch": 1, "loss": 0.5})
        log.log({"epoch": 2, "loss": 0.4})
    assert _rows(path) == [
        {"epoch": "1", "loss": "0.5"},
        {"epoch": "2", "loss": "0.4"},
    ]


def test_append_khong_ghi_lai_header(tmp_path):
    path = tmp_path / "log.csv"
    with CsvLogger(path, FIELDS) as log:
        log.log({"epoch": 1, "loss": 0.5})
    with CsvLogger(path, FIELDS) as log:
        log.log({"epoch": 2, "loss": 0.4})
    assert path.read_text(encoding="utf-8").count("epoch") == 1
    assert len(_rows(path)) == 2


def test_resume_voi_schema_MOI_giu_header_cu(tmp_path):
    """Đây là ca chính. Run bắt đầu trước khi thêm cột `f1_*` rồi resume sau đó.

    Cột mới phải bị bỏ **im lặng**, và file vẫn đọc lại được. Mất một cột ở run cũ thì
    chấp nhận được; làm hỏng cả file log thì không.
    """
    path = tmp_path / "log.csv"
    with CsvLogger(path, FIELDS) as log:
        log.log({"epoch": 1, "loss": 0.5})

    moi = [*FIELDS, "f1_ICC", "f1_di căn"]
    with CsvLogger(path, moi) as log:
        log.log({"epoch": 2, "loss": 0.4, "f1_ICC": 0.3, "f1_di căn": 0.1})

    rows = _rows(path)
    assert len(rows) == 2, "file phải còn đọc được bằng DictReader"
    assert set(rows[0]) == set(FIELDS), "header giữ nguyên schema cũ"
    assert rows[1] == {"epoch": "2", "loss": "0.4"}


def test_run_moi_lay_du_schema_moi(tmp_path):
    """Mặt còn lại: file chưa tồn tại thì lấy đủ cột mới."""
    path = tmp_path / "log.csv"
    moi = [*FIELDS, "f1_ICC"]
    with CsvLogger(path, moi) as log:
        log.log({"epoch": 1, "loss": 0.5, "f1_ICC": 0.3})
    assert _rows(path) == [{"epoch": "1", "loss": "0.5", "f1_ICC": "0.3"}]


def test_thieu_khoa_thi_de_trong_chu_khong_no(tmp_path):
    """`restval=""`: một epoch không tính được F1 của lớp vắng mặt vẫn ghi được dòng."""
    path = tmp_path / "log.csv"
    with CsvLogger(path, [*FIELDS, "f1_ICC"]) as log:
        log.log({"epoch": 1, "loss": 0.5})
    assert _rows(path) == [{"epoch": "1", "loss": "0.5", "f1_ICC": ""}]


def test_file_rong_duoc_coi_nhu_chua_co_header(tmp_path):
    path = tmp_path / "log.csv"
    path.write_text("", encoding="utf-8")
    with CsvLogger(path, FIELDS) as log:
        log.log({"epoch": 1, "loss": 0.5})
    assert _rows(path) == [{"epoch": "1", "loss": "0.5"}]


def test_fieldnames_phan_anh_header_thuc_te(tmp_path):
    path = tmp_path / "log.csv"
    with CsvLogger(path, FIELDS) as log:
        pass
    with CsvLogger(path, [*FIELDS, "them"]) as log:
        assert log.fieldnames == FIELDS
