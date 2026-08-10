"""Kiểm hợp đồng giữa notebook và `src/` — chặn lớp lỗi chỉ lộ ra giữa session Kaggle.

Notebook là lớp mỏng gọi vào `src/` (AGENTS.md §4), nhưng nó **không được lint và không
được test**. Nên một cái tên khoá sai trong notebook chỉ nổ khi chạy thật trên Kaggle, và
tệ nhất là nổ **sau khi đã train xong cả fold** — đúng chuyện đã xảy ra với
`results[fold]["macro_f1"]` (WORKLOG S-123): `train()` trả `best_macro_f1`, và cell nổ ở
dòng `print` cuối cùng nên vòng lặp dừng và fold sau không chạy.

Bản trước của cùng dòng đó viết `.get("macro_f1", float("nan"))` — nên nó in `nan` **im
lặng suốt từ đầu**. Một lỗi im lặng khó phát hiện hơn một lỗi ồn ào, và test này chặn cả hai.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest
from src.train.run import CSV_FIELDS, TRAIN_RESULT_KEYS
from src.utils.io import repo_root

NOTEBOOKS = sorted((repo_root() / "notebooks").glob("*.ipynb"))
# Truy cập vào dict `train()` trả về, cả kiểu `results[fold]["x"]` lẫn `.get("x", ...)`.
RESULT_ACCESS = re.compile(r"""results\[[^\]]+\](?:\.get\(|\[)\s*['"]([a-z_0-9]+)['"]""")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _code(path: Path) -> str:
    nb = _load(path)
    return "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")


def test_co_notebook_de_kiem():
    assert NOTEBOOKS, "không tìm thấy notebook nào"


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_khoa_doc_tu_ket_qua_train_phai_ton_tai(path: Path):
    """Mọi khoá notebook đọc từ dict `train()` trả về phải nằm trong `TRAIN_RESULT_KEYS`."""
    lech = sorted(set(RESULT_ACCESS.findall(_code(path))) - set(TRAIN_RESULT_KEYS))
    assert not lech, (
        f"{path.name} đọc khoá {lech} từ kết quả train(), mà train() chỉ trả "
        f"{list(TRAIN_RESULT_KEYS)}. Nhắc lại cái bẫy: macro-F1 tốt nhất tên là "
        f"'best_macro_f1' ở đây, còn 'macro_f1' là tên trong metrics_best.json."
    )


def test_hai_ten_khac_nhau_cho_cung_dai_luong_van_con():
    """Neo lại nguồn gốc của cái bẫy, để ai đọc test cũng hiểu vì sao nó tồn tại.

    Nếu về sau hai tên được hợp nhất thì test này đỏ — và lúc đó xoá nó là đúng.
    """
    assert "best_macro_f1" in TRAIN_RESULT_KEYS
    assert "macro_f1" not in TRAIN_RESULT_KEYS
    assert "val_macro_f1" in CSV_FIELDS, "CSV lại dùng tên thứ ba nữa"


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_cell_code_parse_duoc(path: Path):
    """Cell nào là Python thuần thì phải parse được.

    Bỏ qua cell dùng magic của IPython (`!`, `%`) — chúng hợp lệ trong Jupyter nhưng không
    phải Python. Đây là lưới an toàn cho các notebook sinh bằng script: một dấu ngoặc
    lệch sẽ nổ ở Kaggle chứ không nổ ở đây, mà lên tới đó thì đã mất công mount cache.
    """
    nb = _load(path)
    loi = []
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if any(line.lstrip().startswith(("!", "%")) for line in src.splitlines()):
            continue
        try:
            ast.parse(src)
        except SyntaxError as exc:
            loi.append(f"cell {i}: {exc}")
    assert not loi, f"{path.name} có cell không parse được:\n  " + "\n  ".join(loi)


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_khong_doc_checkpoint_bang_torch_load_tran(path: Path):
    """Checkpoint của dự án phải đọc bằng `load_checkpoint`, không phải `torch.load` trần.

    torch 2.6 đổi mặc định của `torch.load` thành `weights_only=True`, mà payload của ta
    có cả dict metric. `src.train.loop.load_checkpoint` truyền `weights_only=False` — đừng
    phụ thuộc vào việc payload tình cờ hợp lệ.

    File trọng số của bên thứ ba (MedicalNet `.pth` tải từ HuggingFace) thì được dùng
    `torch.load` trực tiếp: chúng là state_dict thuần và `load_medicalnet_weights` trong
    `src/` mới là chỗ chịu trách nhiệm.

    Nên luật chỉ nhắm vào **checkpoint của dự án**, nhận diện bằng đúng hai tên file mà
    `src/train/run.py` ghi ra: `best.pt` và `last.pt`. Bắt theo `.pt` chung sẽ báo động sai
    ở dòng nạp trọng số MedicalNet.
    """
    OURS = ("best.pt", "last.pt")
    xau = [
        line.strip()
        for line in _code(path).splitlines()
        if "torch.load(" in line and "weights_only" not in line and any(n in line for n in OURS)
    ]
    assert not xau, f"{path.name} đọc checkpoint bằng torch.load trần:\n  " + "\n  ".join(xau)
