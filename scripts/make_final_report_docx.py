"""Dựng KHUNG RỖNG (template) cho báo cáo kết thúc dự án, ra file .docx.

    python scripts/make_final_report_docx.py
    python scripts/make_final_report_docx.py --out reports/BAO_CAO_CUOI.docx
    python scripts/make_final_report_docx.py --force        # cho phép ghi đè

Script này **không viết nội dung báo cáo**. Nó dựng cây tiêu đề bảy mục
(Background / Problem / Method / Result / Conclusion / Discussion / Reference), các
bảng đã có sẵn dòng tiêu đề và nhãn hàng cố định nhưng **ô số để trống**, và các khung
ảnh để trống. Người dùng tự viết phần văn xuôi và tự điền số.

Vì sao dùng python-docx chứ không pandoc/LaTeX: cùng lý do đã ghi ở `scripts/md2pdf.py`
— không phải cài thêm toolchain nặng trên máy Windows. python-docx là thư viện thuần
Python, chỉ dùng khi soạn deliverable trên máy local nên **cố ý không** nằm trong
`requirements.txt` (môi trường train Kaggle không cần nó).

⚠️ Script GHI ĐÈ file đích. Nếu file đã tồn tại thì nó dừng lại và bắt truyền `--force`.
Đây là lớp bảo vệ duy nhất chống việc chạy lại làm mất bản đã viết tay.

Kiểu chữ: chỉ dùng font có sẵn trên Windows và phủ đủ dấu tiếng Việt — Cambria cho phần
chữ chạy, Segoe UI cho tiêu đề và bảng. Giống `md2pdf.py` để hai deliverable nhìn cùng
một hệ.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import docx
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Mm, Pt, RGBColor
except ModuleNotFoundError:  # pragma: no cover - phụ thuộc chỉ dùng ở máy local
    raise SystemExit(
        "Thiếu thư viện python-docx. Cài bằng:\n\n    pip install python-docx\n\n"
        "Nó cố ý không nằm trong requirements.txt — đây là công cụ soạn deliverable "
        "trên máy local, không thuộc môi trường train."
    ) from None


# --- Hằng số trình bày --------------------------------------------------------------

BODY_FONT = "Cambria"
HEAD_FONT = "Segoe UI"
HINT_COLOR = RGBColor(0x8A, 0x8A, 0x8A)
HEADER_FILL = "EFEFEF"
RUO_FOOTER = "Research Use Only — không dùng cho chẩn đoán lâm sàng"

DEFAULT_OUT = Path("reports/FINAL_REPORT.docx")


# --- Tiện ích XML mà python-docx không bọc sẵn --------------------------------------


def _set_style_font(style: Any, name: str, size_pt: float, *, bold: bool = False) -> None:
    """Đặt font cho một style, kể cả nhánh eastAsia để Word không tự thay chữ."""
    style.font.name = name
    style.font.size = Pt(size_pt)
    style.font.bold = bold
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), name)


def _shade_cell(cell: Any, fill: str) -> None:
    """Tô nền một ô bảng (python-docx không có API cho w:shd)."""
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(shd)


def _repeat_header_row(row: Any) -> None:
    """Đánh dấu hàng này là hàng tiêu đề, để Word lặp lại nó khi bảng tràn trang."""
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def _add_field(paragraph: Any, instruction: str) -> None:
    """Chèn một field code của Word (PAGE, TOC, ...) vào paragraph.

    Field là thứ Word tự tính lúc mở/refresh; python-docx không có API nên phải dựng
    tay bốn phần tử fldChar/instrText.
    """
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instr, separate, end):
        run._r.append(element)


def _add_paragraph_border(paragraph: Any) -> None:
    """Viền quanh một paragraph — dùng làm khung ảnh để trống."""
    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    for side in ("top", "left", "bottom", "right"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:val"), "dashed")
        edge.set(qn("w:sz"), "6")
        edge.set(qn("w:space"), "8")
        edge.set(qn("w:color"), "B0B0B0")
        borders.append(edge)
    p_pr.append(borders)


# --- Khối nội dung ------------------------------------------------------------------


class Builder:
    """Gom trạng thái đánh số bảng/hình để các hàm dựng không phải truyền tay."""

    def __init__(self, document: Any) -> None:
        self.doc = document
        self.table_no = 0
        self.figure_no = 0

    # -- văn bản --

    def heading(self, number: str, text: str, level: int) -> None:
        """Tiêu đề đánh số THỦ CÔNG.

        Không dùng list numbering tự động của Word: nó hay trôi khi người viết chèn
        hoặc xoá mục, và bản template này chắc chắn sẽ bị chèn/xoá mục.
        """
        paragraph = self.doc.add_heading(level=level)
        run = paragraph.add_run(f"{number} {text}" if number else text)
        run.font.name = HEAD_FONT
        run.font.color.rgb = RGBColor(0, 0, 0)
        rpr = run._r.get_or_add_rPr()
        rfonts = rpr.get_or_add_rFonts()
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(attr), HEAD_FONT)

    def hint(self, text: str) -> None:
        """Dòng gợi ý 'viết gì ở đây'.

        Xám, nghiêng, luôn mở đầu bằng `[Viết:` để xoá hàng loạt được bằng Ctrl+H.
        """
        paragraph = self.doc.add_paragraph()
        run = paragraph.add_run(f"[Viết: {text}]")
        run.italic = True
        run.font.color.rgb = HINT_COLOR
        run.font.size = Pt(10)

    def note(self, text: str) -> None:
        """Ghi chú cho người viết, không phải nội dung báo cáo."""
        paragraph = self.doc.add_paragraph()
        run = paragraph.add_run(f"[Ghi chú: {text}]")
        run.italic = True
        run.font.color.rgb = HINT_COLOR
        run.font.size = Pt(9)

    # -- bảng --

    def table(
        self,
        caption: str,
        headers: list[str],
        row_labels: list[str],
        *,
        bold_rows: tuple[str, ...] = (),
    ) -> None:
        """Bảng đã có tiêu đề cột và nhãn hàng; mọi ô còn lại để TRỐNG.

        `row_labels` đi vào cột đầu tiên. Nhãn nào nằm trong `bold_rows` thì in đậm —
        dùng cho các dòng tổng hợp (Tổng, Gộp out-of-fold, Nghiên cứu này).
        """
        self.table_no += 1
        self._caption(f"Bảng {self.table_no}. {caption}")

        table = self.doc.add_table(rows=1 + len(row_labels), cols=len(headers))
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        head = table.rows[0]
        _repeat_header_row(head)
        for cell, text in zip(head.cells, headers, strict=True):
            _shade_cell(cell, HEADER_FILL)
            run = cell.paragraphs[0].add_run(text)
            run.bold = True
            run.font.name = HEAD_FONT
            run.font.size = Pt(9)

        for row, label in zip(table.rows[1:], row_labels, strict=True):
            run = row.cells[0].paragraphs[0].add_run(label)
            run.bold = label in bold_rows
            run.font.name = HEAD_FONT
            run.font.size = Pt(9)
            for cell in row.cells[1:]:
                cell.paragraphs[0].add_run("").font.size = Pt(9)

        self.doc.add_paragraph()

    def _caption(self, text: str) -> None:
        paragraph = self.doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(text)
        run.italic = True
        run.font.size = Pt(9)

    # -- hình --

    def figure(self, caption: str, hint: str) -> None:
        """Khung ảnh ĐỂ TRỐNG kèm caption đã đánh số.

        Cố ý không nhúng ảnh: người dùng chốt tự thêm ảnh sau.
        """
        self.figure_no += 1
        box = self.doc.add_paragraph()
        box.alignment = WD_ALIGN_PARAGRAPH.CENTER
        box.paragraph_format.space_before = Pt(6)
        box.paragraph_format.space_after = Pt(2)
        _add_paragraph_border(box)
        for line in ("", f"[Chèn ảnh: {hint}]", "", ""):
            run = box.add_run(line)
            run.italic = True
            run.font.color.rgb = HINT_COLOR
            run.font.size = Pt(10)
            run.add_break()

        self._caption(f"Hình {self.figure_no}. {caption}")
        self.doc.add_paragraph()


# --- Cấu trúc tài liệu, khai báo dạng DỮ LIỆU ---------------------------------------
#
# Sửa khung báo cáo sau này = sửa danh sách dưới đây, không đụng logic dựng ở trên.
# Mỗi phần tử là một tuple ("loại", ...):
#   ("h", số, tiêu đề, cấp)
#   ("hint", text)                          — dòng gợi ý xám
#   ("note", text)                          — ghi chú cho người viết
#   ("table", caption, [cột], [nhãn hàng], (nhãn in đậm,))
#   ("fig", caption, gợi ý ảnh)
#   ("pagebreak",)

CLASS_ROWS = ["u máu", "ICC", "áp-xe", "di căn", "nang", "FNH", "HCC"]

STRUCTURE: list[tuple[Any, ...]] = [
    # ============================== 1. BACKGROUND ==============================
    ("h", "1.", "Background", 1),
    ("h", "1.1.", "Bối cảnh lâm sàng", 2),
    (
        "hint",
        "vì sao phân loại tổn thương gan trên MRI đa thì là bài toán đáng làm — gánh nặng "
        "bệnh gan, vai trò của động học ngấm thuốc trong chẩn đoán phân biệt, và chỗ khó "
        "khi phân biệt bảy loại tổn thương bằng mắt",
    ),
    ("h", "1.2.", "Bối cảnh kỹ thuật và công trình liên quan", 2),
    (
        "hint",
        "challenge LLD-MMRI 2023 và mức điểm của nó; các phương pháp công bố sau đó "
        "(SDR-Former, STM-Former, RadioFormer, CGHNet); khoảng trống mà dự án nhắm vào là "
        "độ tin cậy của xác suất chứ không phải điểm số leaderboard",
    ),
    ("h", "1.3.", "Lịch sử phạm vi của dự án", 2),
    (
        "hint",
        "pha CT ban đầu (phân loại nhị phân lát cắt trên LiTS) và lý do chuyển sang MRI 3D "
        "đa thì bảy lớp — độ khớp giữa nhãn, dữ liệu và câu hỏi nghiên cứu",
    ),
    # =============================== 2. PROBLEM ================================
    ("h", "2.", "Problem", 1),
    ("h", "2.1.", "Phát biểu bài toán", 2),
    (
        "hint",
        "phân loại đa lớp bảy loại tổn thương gan ở mức ROI trên volume MRI 3D đa thì; nêu "
        "rõ đây không phải phát hiện và không phải segmentation vì vị trí tổn thương cho "
        "trước",
    ),
    ("h", "2.2.", "Đầu vào và đầu ra", 2),
    (
        "hint",
        "đầu vào là tám thì MRI xếp thành tám kênh; đầu ra gồm bảy xác suất, một mức bất "
        "định và một cờ từ chối — nói rõ hai thứ sau là đóng góp chính chứ không phải phụ "
        "kiện",
    ),
    ("h", "2.3.", "Câu hỏi nghiên cứu và đóng góp", 2),
    (
        "hint",
        "câu hỏi chính về trustworthiness (xác suất hiệu chỉnh + selective prediction) và "
        "các câu hỏi phụ trợ về fusion đa thì và về pre-training",
    ),
    ("h", "2.4.", "Phạm vi và ràng buộc", 2),
    (
        "hint",
        "Research Use Only; một người, sáu tuần; compute là Kaggle với session tối đa 12 "
        "giờ và quota 30 giờ/tuần; ba loại deliverable là code, web app và slide/report",
    ),
    ("pagebreak",),
    # ================================ 3. METHOD =================================
    ("h", "3.", "Method", 1),
    ("h", "3.1.", "Dữ liệu", 2),
    ("h", "3.1.1.", "Dataset LLD-MMRI", 3),
    (
        "hint",
        "498 bệnh nhân, mỗi bệnh nhân đúng một tổn thương, tám thì mỗi ca; nguồn dữ liệu "
        "thực nhận và giấy phép; mức mất cân bằng lớp",
    ),
    (
        "table",
        "Phân bố bảy lớp trên toàn bộ dataset.",
        ["Lớp", "Tên đầy đủ", "Nhóm", "n"],
        [*CLASS_ROWS, "Tổng"],
        ("Tổng",),
    ),
    ("h", "3.1.2.", "Tám thì MRI và đặc điểm hình học", 3),
    (
        "hint",
        "liệt kê tám thì; nêu việc tám thì của cùng một bệnh nhân không nằm trên cùng lưới "
        "voxel, khác mặt phẳng chụp và khác ma trận, đa máy 1.5T và 3T; độ tán tâm tổn "
        "thương giữa các thì do chuyển động hô hấp",
    ),
    ("h", "3.1.3.", "Nhãn, mask và gold standard", 3),
    (
        "hint",
        "nhãn lấy từ giải phẫu bệnh chứ không từ đọc ảnh; bbox theo từng lát; mask "
        "segmentation bổ sung và mức dè dặt phải giữ khi dùng nó",
    ),
    ("h", "3.2.", "Chia dữ liệu", 2),
    ("h", "3.2.1.", "Split official 316 / 78 / 104", 3),
    (
        "hint",
        "cách tái lập split official và cách kiểm chứng nó khớp tài liệu challenge; vì sao "
        "điều này quan trọng — nó khôi phục khả năng so benchmark trực tiếp",
    ),
    (
        "table",
        "Phân bố lớp theo tập sau khi tái lập split official.",
        ["Lớp", "train + val", "test", "Tổng"],
        [*CLASS_ROWS, "Tổng"],
        ("Tổng",),
    ),
    ("h", "3.2.2.", "Cross-validation 5 fold", 3),
    (
        "hint",
        "5 fold official trên 394 ca train+val; năm tập validation phân hoạch sạch và đã "
        "kiểm chứng giao mọi cặp bằng rỗng",
    ),
    (
        "table",
        "Cỡ tập train và validation của từng fold.",
        ["Fold", "n train", "n val"],
        ["1", "2", "3", "4", "5", "Tổng out-of-fold"],
        ("Tổng out-of-fold",),
    ),
    ("h", "3.2.3.", "Nguyên tắc chống rò rỉ dữ liệu", 3),
    (
        "hint",
        "split tuyệt đối ở mức bệnh nhân; thống kê chuẩn hoá chỉ tính trong phạm vi từng "
        "bệnh nhân; không chọn model, ngưỡng hay nhiệt độ trên test; test-104 khoá kín; "
        "unit test kiểm giao tập bệnh nhân bằng rỗng",
    ),
    ("h", "3.3.", "Tiền xử lý", 2),
    ("h", "3.3.1.", "Gate hình học và phán quyết thứ tự trục", 3),
    (
        "hint",
        "đối chiếu spacing trong header ảnh với spacing khai trong annotation trên toàn bộ "
        "3.984 volume; cách giải quyết chuyện annotation không nói rõ bbox là (x, y) hay "
        "(y, x) bằng độ tán tâm bbox trong toạ độ thế giới",
    ),
    ("h", "3.3.2.", "Cắt trong không gian mm và căn các thì", 3),
    (
        "hint",
        "vì tám thì khác lưới nên phải đổi tâm bbox sang mm, dựng lưới đích chung rồi lấy "
        "mẫu cả tám thì lên đó; chế độ cắt bám tổn thương; phép căn từng thì về tâm tổn "
        "thương của chính nó, và điều nó KHÔNG làm (không khử xoay, không khử biến dạng)",
    ),
    ("h", "3.3.3.", "Chuẩn hoá cường độ", 3),
    (
        "hint",
        "clip theo phân vị rồi z-score, thống kê lấy trên chính volume của bệnh nhân đó nên "
        "không gộp xuyên bệnh nhân",
    ),
    ("h", "3.3.4.", "Các bản cache đã dựng", 3),
    (
        "table",
        "Ba bản cache tiền xử lý và phạm vi sử dụng của mỗi bản.",
        [
            "Cache",
            "target_size [X,Y,Z]",
            "Lề mỗi phía",
            "Kích thước mảng",
            "Dung lượng",
            "Dùng cho",
        ],
        ["E4", "E12", "CGHNet"],
    ),
    ("h", "3.4.", "Kiến trúc mô hình", 2),
    (
        "hint",
        "mô tả từng kiến trúc đã thử và lý do chọn; nhấn vào điểm khác biệt của cấu hình "
        "chính là nguồn khởi tạo trọng số 3D thay vì 2D hoặc ngẫu nhiên",
    ),
    (
        "table",
        "Các kiến trúc đã huấn luyện và đánh giá.",
        ["Kiến trúc", "Nguồn khởi tạo", "Hình học đầu vào", "Số tham số", "Trạng thái"],
        [
            "DenseNet121-3D",
            "Siamese đa thì (encoder dùng chung)",
            "CGHNet (bản tái lập)",
            "UniFormer-S 3D + Kinetics-400",
        ],
    ),
    (
        "note",
        "repo còn config của UniFormer-Base, UniFormerV2-B/16 và SDR-Former nhưng chưa "
        "chạy fold nào — thêm hàng nếu muốn nêu chúng ở mục Hướng phát triển",
    ),
    ("h", "3.5.", "Cấu hình huấn luyện", 2),
    (
        "hint",
        "nêu rằng mọi siêu tham số đi qua file YAML và seed cố định, không hardcode trong "
        "code train; giải thích các chỗ cố ý lệch so với recipe gốc được tái lập",
    ),
    (
        "table",
        "Siêu tham số của hai cấu hình chính.",
        ["Siêu tham số", "DenseNet121-3D (mốc đối chứng)", "UniFormer-S + Kinetics (chính)"],
        [
            "Số epoch",
            "Optimizer",
            "Learning rate",
            "Weight decay",
            "Warmup",
            "Lịch learning rate",
            "Batch size",
            "Batch hiệu dụng",
            "Hàm mất mát",
            "Trọng số lớp",
            "Label smoothing",
            "Bộ lấy mẫu",
            "Drop-path",
            "AMP",
            "Seed",
        ],
    ),
    ("h", "3.6.", "Tăng cường dữ liệu", 2),
    (
        "hint",
        "liệt kê các phép biến đổi và xác suất áp dụng; nêu lỗi đệm 0 phát hiện ở giữa dự "
        "án và cách xử lý",
    ),
    (
        "table",
        "Các phép tăng cường dữ liệu áp dụng lúc huấn luyện.",
        ["Phép biến đổi", "Tham số", "Xác suất áp dụng", "Ghi chú"],
        [
            "Lật theo trục x / y / z",
            "Xoay trong mặt phẳng",
            "Cắt ngẫu nhiên",
            "Nhiễu cường độ",
            "Edge",
            "Emboss",
            "Blur",
            "Sharpen",
            "Unsharp",
            "Không áp phép nào",
        ],
    ),
    ("h", "3.7.", "Danh sách thí nghiệm", 2),
    (
        "hint",
        "trình bày chuỗi thí nghiệm như một mạch có logic: mỗi lần chỉ đổi một cụm biến, và "
        "nêu quy tắc đã chốt là một phép sàng cỡ nhỏ chỉ đủ để loại chứ không đủ để chọn",
    ),
    (
        "table",
        "Toàn bộ thí nghiệm đã chạy, theo thứ tự thời gian.",
        ["Mã", "Thay đổi so với mốc trước", "Số fold", "macro-F1", "Kết luận"],
        [
            "E0",
            "E1",
            "E2",
            "E3",
            "E4",
            "E5 — focal loss",
            "E6 — tăng cường mạnh hơn",
            "E6b — bỏ nhiễu cường độ",
            "E12 — cắt ngẫu nhiên",
            "TTA lật",
            "CGHNet (tái lập)",
            "UniFormer-S + Kinetics",
        ],
        ("UniFormer-S + Kinetics",),
    ),
    ("h", "3.8.", "Phương pháp đánh giá", 2),
    ("h", "3.8.1.", "Metric", 3),
    (
        "hint",
        "macro-F1 là metric chốt và vì sao (lớp hiếm có trọng số ngang lớp phổ biến); "
        "Cohen's κ vì đó là metric xếp hạng của challenge; các metric phụ",
    ),
    ("h", "3.8.2.", "Khoảng tin cậy bootstrap và so cặp", 3),
    (
        "hint",
        "bootstrap ở mức bệnh nhân, phân tầng theo lớp, tối thiểu 2.000 lần; vì sao so hai "
        "cấu hình phải dùng bootstrap GHÉP CẶP trên hiệu thay vì so hai khoảng tin cậy rời",
    ),
    ("h", "3.8.3.", "Calibration", 3),
    (
        "hint",
        "định nghĩa ECE, MCE, Brier, NLL; temperature scaling và cách fit leave-one-fold-out "
        "để không ca nào được hiệu chỉnh bởi một T đã nhìn thấy nó; khác biệt giữa T tối ưu "
        "theo NLL và T tối ưu theo ECE",
    ),
    ("h", "3.8.4.", "Selective prediction", 3),
    (
        "hint",
        "định nghĩa risk–coverage và AURC; hai cách xếp hạng đã so (xác suất cao nhất và "
        "mức bất đồng giữa các mô hình); vì sao macro-F1 tại một mức coverage đơn lẻ là "
        "metric yếu ở cỡ mẫu này",
    ),
    ("h", "3.9.", "Hạ tầng và ràng buộc compute", 2),
    (
        "hint",
        "Kaggle Notebook với session tối đa 12 giờ và quota 30 giờ/tuần; checkpoint và "
        "resume mỗi epoch; cache tiền xử lý đẩy lên Kaggle Dataset có đánh phiên bản; các "
        "cổng kiểm tra chạy trước khi cam kết giờ GPU",
    ),
    ("h", "3.10.", "Web app demo", 2),
    (
        "hint",
        "kiến trúc FastAPI + React tự code full-stack; luồng làm việc từ lúc tải dữ liệu tới "
        "lúc trả kết quả; cách trình bày mức bất định và cờ từ chối cho người đọc",
    ),
    (
        "fig",
        "Giao diện bàn đọc MRI của web app sau khi xử lý một ca.",
        "ảnh chụp giao diện web app — có sẵn ở reports/assets/w4-webapp-current-mri.png",
    ),
    ("pagebreak",),
    # ================================ 4. RESULT =================================
    ("h", "4.", "Result", 1),
    ("h", "4.1.", "Chuỗi thí nghiệm sàng lọc", 2),
    (
        "hint",
        "kể lại mức tăng từ số mốc đầu tiên tới cấu hình E4, và điểm đáng nói là toàn bộ mức "
        "tăng đến từ cách chuẩn bị dữ liệu chứ không từ siêu tham số",
    ),
    (
        "note",
        "mọi số trong bảng này đo trên val fold 1 (82 ca, 1 seed) — phải ghi rõ đây là số "
        "sàng lọc, không phải số báo cáo",
    ),
    (
        "table",
        "Chuỗi thí nghiệm sàng lọc trên validation fold 1.",
        ["Thí nghiệm", "Thay đổi", "macro-F1 [95% CI]", "κ", "AURC", "ECE thô → sau T"],
        ["E0", "E1", "E3", "E4"],
    ),
    ("h", "4.2.", "Cross-validation của cấu hình chính", 2),
    (
        "hint",
        "năm lần huấn luyện cùng seed, cấu hình giống hệt nhau trừ chỉ số fold; nói rõ con "
        "số báo cáo là bản gộp out-of-fold chứ không phải trung bình các fold, và vì sao",
    ),
    (
        "table",
        "Kết quả cross-validation 5 fold của cấu hình chính.",
        ["Fold", "n val", "macro-F1", "κ", "Epoch tốt nhất"],
        ["1", "2", "3", "4", "5", "Gộp out-of-fold"],
        ("Gộp out-of-fold",),
    ),
    (
        "hint",
        "thiên lệch do cách chọn checkpoint, đo bằng chênh giữa checkpoint tốt nhất và "
        "epoch cuối trên cùng tập — con số này phải nêu ngay cạnh kết quả, không giấu xuống "
        "mục Giới hạn",
    ),
    ("h", "4.3.", "Đánh giá trên tập test khoá kín", 2),
    (
        "hint",
        "protocol khoá trước khi chạy: cấu hình mô hình, bộ dự đoán, không TTA, nhiệt độ fit "
        "trên out-of-fold rồi áp mù, danh sách metric và các mức coverage; nói rõ tập test "
        "đã được chạm hai lần và lần nào là lần nào",
    ),
    (
        "table",
        "Kết quả trên tập test 104 ca khoá kín, hai lần đánh giá.",
        ["Lần chạm", "Cấu hình", "macro-F1 [95% CI]", "κ", "Balanced accuracy", "Accuracy"],
        ["Lần 1", "Lần 2"],
        ("Lần 2",),
    ),
    (
        "hint",
        "so mức hụt giữa out-of-fold và test với thiên lệch chọn checkpoint đã đo trước — "
        "hai con số đó khớp nhau nghĩa là không có nguồn thổi phồng nào khác lộ ra",
    ),
    ("h", "4.4.", "So sánh có kiểm soát với cấu hình cũ", 2),
    (
        "hint",
        "nêu vì sao phép so hợp lệ: cấu hình chính được chọn hoàn toàn trên out-of-fold, "
        "không dùng thông tin nào của tập test",
    ),
    (
        "table",
        "So sánh bootstrap ghép cặp trên cùng bệnh nhân, phân tầng theo lớp.",
        ["Phép so", "Tập đánh giá", "Hiệu macro-F1", "95% CI", "P"],
        [
            "UniFormer − DenseNet121-3D",
            "UniFormer − DenseNet121-3D",
            "Ensemble − trung bình 5 mô hình đơn",
        ],
    ),
    ("h", "4.5.", "Vị trí so với văn liệu", 2),
    (
        "note",
        "chỉ đặt cạnh nhau những con số đo trên CÙNG tập test 104 ca; không so số "
        "out-of-fold với bảng văn liệu",
    ),
    (
        "table",
        "Các phương pháp công bố trên cùng tập test 104 ca.",
        ["Phương pháp", "macro-F1", "κ"],
        [
            "Hạng 1 challenge",
            "CGHNet (2026)",
            "Hạng 2 challenge",
            "STM-Former",
            "Hạng 3 challenge",
            "Hạng 4 challenge",
            "Nghiên cứu này (ensemble 5 fold)",
            "Hạng 5 challenge",
            "DenseNet121-3D (lần chạm 1)",
            "Baseline ban tổ chức",
        ],
        ("Nghiên cứu này (ensemble 5 fold)",),
    ),
    (
        "hint",
        "phát biểu định vị cho đúng bề rộng khoảng tin cậy: mốc nào bị loại được về mặt "
        "thống kê và mốc nào không phân biệt được",
    ),
    ("h", "4.6.", "Độ tin cậy của xác suất", 2),
    (
        "hint",
        "đây là một nửa của đóng góp chính; nêu ECE khi chưa hiệu chỉnh, mức tự tin thái quá "
        "và vì sao hiệu chỉnh thêm ở cấu hình này là một đánh đổi chứ không phải một cải "
        "thiện",
    ),
    (
        "table",
        "Calibration của ensemble 5 fold trên tập test.",
        [
            "Cấu hình xác suất",
            "ECE",
            "MCE",
            "Brier",
            "NLL",
            "Tự tin trung bình (lệch so accuracy)",
        ],
        ["Chưa hiệu chỉnh (số chính)", "Temperature scaling, T fit trên out-of-fold"],
        ("Chưa hiệu chỉnh (số chính)",),
    ),
    (
        "fig",
        "Reliability diagram của ensemble 5 fold trên tập test.",
        "reliability diagram — chưa sinh, cần vẽ từ xác suất đã lưu",
    ),
    ("h", "4.7.", "Cơ chế từ chối ca không chắc", 2),
    (
        "hint",
        "nửa còn lại của đóng góp chính; phát biểu dùng được là từ chối bao nhiêu phần trăm "
        "ca khó thì macro-F1 lên tới đâu, kèm P; và ở mức chấp nhận sai số nào thì hệ thống "
        "tự quyết được bao nhiêu phần trăm số ca",
    ),
    (
        "table",
        "Selective prediction trên tập test, hai cách xếp hạng.",
        [
            "Cách xếp hạng",
            "AURC",
            "F1@100%",
            "F1@90%",
            "F1@80%",
            "F1@70%",
            "Coverage @ risk ≤ 10%",
        ],
        [
            "Xác suất cao nhất",
            "Mức bất đồng giữa 5 mô hình",
            "Xếp ngẫu nhiên (mốc dưới)",
            "Xếp hoàn hảo (mốc trên)",
        ],
        ("Xác suất cao nhất",),
    ),
    (
        "fig",
        "Đường risk–coverage trên tập test.",
        "đường risk–coverage — chưa sinh, cần vẽ từ xác suất đã lưu",
    ),
    ("h", "4.8.", "Kết quả từng lớp", 2),
    (
        "note",
        "n mỗi lớp trên tập test chỉ 10–16 ca — nêu cảnh báo này trước khi diễn giải sâu "
        "từng con số",
    ),
    (
        "table",
        "macro-F1 từng lớp trên out-of-fold và trên tập test.",
        ["Lớp", "n val", "F1 out-of-fold", "n test", "F1 test", "Precision", "Recall"],
        CLASS_ROWS,
    ),
    (
        "fig",
        "Ma trận nhầm lẫn bảy lớp trên tập test.",
        "ma trận nhầm lẫn — chưa sinh, cần vẽ từ xác suất đã lưu",
    ),
    (
        "hint",
        "ba hướng nhầm lớn nhất và phép tính trần: nếu các lớp còn lại đều đạt mức cao mà "
        "lớp yếu nhất giữ nguyên thì macro-F1 tối đa là bao nhiêu",
    ),
    ("h", "4.9.", "Các hướng đã thử không hiệu quả", 2),
    (
        "hint",
        "kết quả âm cũng là kết quả; với mỗi hướng nêu rõ nó bị loại bởi bằng chứng nào, và "
        "phân biệt 'ý tưởng sai' với 'bộ đo quá yếu ở cỡ mẫu này'",
    ),
    (
        "table",
        "Các can thiệp không đạt ý nghĩa thống kê.",
        ["Thí nghiệm", "Tập đánh giá", "Hiệu macro-F1", "95% CI", "P"],
        [
            "Focal loss (γ = 2)",
            "Tăng cường dữ liệu mạnh hơn",
            "Bỏ nhiễu cường độ theo thì",
            "Test-time augmentation bằng phép lật",
            "Bản tái lập CGHNet",
            "Gộp DenseNet121-3D với CGHNet",
            "Gộp UniFormer với DenseNet121-3D",
        ],
    ),
    ("h", "4.10.", "Thời gian xử lý một ca", 2),
    (
        "note",
        "phân biệt latency đo theo LÔ trong lượt đánh giá với thời gian đáp ứng end-to-end "
        "của web app khi phục vụ từng ca",
    ),
    (
        "table",
        "Thời gian xử lý một ca, theo thành phần.",
        ["Thành phần", "Thiết bị", "Thời gian"],
        [
            "Tiền xử lý tám chuỗi MRI",
            "Suy luận, 1 mô hình",
            "Suy luận, ensemble 5 mô hình",
            "Tổng end-to-end (CPU laptop)",
            "Tổng end-to-end (GPU Tesla T4)",
        ],
        ("Tổng end-to-end (CPU laptop)", "Tổng end-to-end (GPU Tesla T4)"),
    ),
    ("pagebreak",),
    # ============================== 5. CONCLUSION ===============================
    ("h", "5.", "Conclusion", 1),
    ("h", "5.1.", "Trả lời câu hỏi nghiên cứu", 2),
    (
        "hint",
        "trả lời thẳng câu hỏi đặt ra ở mục 2.3, bằng con số, trong vài câu",
    ),
    ("h", "5.2.", "Đóng góp chính", 2),
    (
        "hint",
        "hai nhánh của trustworthiness (xác suất hiệu chỉnh và cơ chế từ chối) cộng phần "
        "phương pháp luận: protocol khoá trước, bootstrap ghép cặp, test-104 chỉ chạm theo "
        "pre-registration",
    ),
    ("h", "5.3.", "Mức hoàn thành so với kế hoạch", 2),
    (
        "table",
        "Mức hoàn thành từng mục tiêu của dự án.",
        ["Mục tiêu", "Mức hoàn thành", "Bằng chứng"],
        [
            "Pipeline tái lập từ MRI thô đến bảng metric",
            "Split khoá mức bệnh nhân, test chống rò rỉ",
            "Cross-validation 5 fold có khoảng tin cậy",
            "Backbone pre-trained so với huấn luyện từ đầu",
            "Đánh giá trên tập test khoá kín",
            "Calibration",
            "Selective prediction",
            "Web app demo tự code full-stack",
            "Slide và báo cáo",
            "External validation và OOD probe",
        ],
    ),
    # ============================== 6. DISCUSSION ===============================
    ("h", "6.", "Discussion", 1),
    ("h", "6.1.", "Diễn giải kết quả", 2),
    (
        "hint",
        "vì sao đổi nguồn khởi tạo trọng số là can thiệp duy nhất ăn tiền, trong khi bảy "
        "hướng chỉnh loss, ngưỡng và augmentation đều không; ràng buộc nằm ở biểu diễn đặc "
        "trưng chứ không ở siêu tham số",
    ),
    ("h", "6.2.", "Nút thắt lớp di căn", 2),
    (
        "hint",
        "chẩn đoán đảo chiều giữa hai cấu hình (thừa dự đoán so với thiếu recall); trần số "
        "học mà lớp này áp lên macro-F1; và việc lớp yếu nhất của các phương pháp công bố "
        "cũng là lớp này",
    ),
    ("h", "6.3.", "Bài học phương pháp luận", 2),
    (
        "hint",
        "một phép sàng cỡ nhỏ chỉ đủ để loại chứ không đủ để chọn — dẫn các lần dự án bị "
        "một hai fold đánh lừa; và luật đối chiếu mốc ngoài trước khi debug",
    ),
    ("h", "6.4.", "Giới hạn", 2),
    (
        "hint",
        "cỡ mẫu test 104 ca và bề rộng khoảng tin cậy; thiên lệch chọn checkpoint; phép căn "
        "thì mới chỉ khử tịnh tiến; chưa có external validation và OOD probe; nhãn mask; "
        "tính tất định trên CUDA; và trên hết là RUO — chưa kiểm định lâm sàng",
    ),
    ("h", "6.5.", "Hướng phát triển", 2),
    (
        "hint",
        "các hướng còn để ngỏ: trục fusion đa thì kiểu Siamese, backbone lớn hơn, bộ phối "
        "hợp học được thay cho trung bình xác suất, external validation, và phần triển khai",
    ),
    # =============================== 7. REFERENCE ===============================
    ("h", "7.", "Reference", 1),
]


# --- Danh mục tài liệu tham khảo -----------------------------------------------------
#
# Đây là phần DUY NHẤT được điền sẵn nội dung: nó là danh mục nguồn đã thực sự dùng
# trong dự án (lấy từ AGENTS.md §5, configs/*.yaml và papers/), không phải văn xuôi
# phải viết. Người dùng đổi định dạng trích dẫn hoặc bổ sung tuỳ nhu cầu.

REFERENCES: list[str] = [
    "LLD-MMRI2023 Challenge — Liver Lesion Diagnosis Challenge on Multi-phase MRI, "
    "MICCAI 2023. Repo chính thức: https://github.com/LMMMEng/LLD-MMRI2023 "
    "(baseline official và bảng xếp hạng test-104).",
    "Lou, J. và cs. SDR-Former: A Siamese Dual-Resolution Transformer for Liver Lesion "
    "Classification Using 3D Multi-Phase Imaging. arXiv:2402.17246.",
    "Li và cs. CGHNet: Cross-Guided 2D–3D Hybrid Network with attention mechanism for "
    "focal liver lesion classification. Computerized Medical Imaging and Graphics 132 "
    "(2026) 102780. doi:10.1016/j.compmedimag.2026.102780.",
    "NPUBXY — giải pháp hạng 2 LLD-MMRI 2023. Repo: https://github.com/ZHEGG/miccai2023.",
    "Li, K. và cs. UniFormer: Unifying Convolution and Self-attention for Visual "
    "Recognition. Trọng số pre-trained: https://huggingface.co/Sense-X/uniformer_video "
    "(uniformer_small_k400_16x8.pth).",
    "Kay, W. và cs. The Kinetics Human Action Video Dataset. arXiv:1705.06950.",
    "Cui, Y. và cs. Class-Balanced Loss Based on Effective Number of Samples. CVPR 2019.",
    "Lin, T.-Y. và cs. Focal Loss for Dense Object Detection. ICCV 2017.",
    "Guo, C. và cs. On Calibration of Modern Neural Networks. ICML 2017 "
    "(temperature scaling, ECE).",
    "El-Yaniv, R. và Wiener, Y. On the Foundations of Noise-free Selective "
    "Classification. JMLR 11 (2010) (risk–coverage, selective prediction).",
    "Cardoso, M. J. và cs. MONAI: An open-source framework for deep learning in "
    "healthcare imaging. arXiv:2211.02701.",
    "Paszke, A. và cs. PyTorch: An Imperative Style, High-Performance Deep Learning "
    "Library. NeurIPS 2019.",
    "Tài liệu nội bộ của dự án: docs/MRI_Classification_Spec_Sheet.md (chốt kỹ thuật), "
    "docs/TEST104_PREREGISTRATION.md (protocol khoá trước khi chạm tập test).",
]


# --- Dựng tài liệu ------------------------------------------------------------------


def configure_styles(document: Any) -> None:
    """Khổ giấy, lề và font. Chỉ dùng font có sẵn trên Windows, phủ đủ dấu tiếng Việt."""
    section = document.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    for attr in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(section, attr, Cm(2.0))

    styles = document.styles
    _set_style_font(styles["Normal"], BODY_FONT, 11)
    normal = styles["Normal"].paragraph_format
    normal.line_spacing = 1.15
    normal.space_after = Pt(6)

    for level, size in ((1, 16), (2, 13), (3, 11.5)):
        style = styles[f"Heading {level}"]
        _set_style_font(style, HEAD_FONT, size, bold=True)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(14 if level == 1 else 10)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.keep_with_next = True


def build_footer(document: Any) -> None:
    """Footer: RUO bên trái, số trang bên phải. RUO phải có ở mọi trang (AGENTS.md §12)."""
    for section in document.sections:
        paragraph = section.footer.paragraphs[0]
        paragraph.text = ""
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        # tab phải sát mép trong của lề, để số trang canh phải
        tab_stops = paragraph.paragraph_format.tab_stops
        width = section.page_width - section.left_margin - section.right_margin
        tab_stops.add_tab_stop(width)

        run = paragraph.add_run(RUO_FOOTER + "\t")
        run.font.size = Pt(8)
        run.font.name = HEAD_FONT
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
        _add_field(paragraph, " PAGE ")
        for tail in paragraph.runs[1:]:
            tail.font.size = Pt(8)
            tail.font.name = HEAD_FONT


def build_cover(document: Any) -> None:
    """Trang bìa. Điền sẵn các giá trị ổn định, để trống ngày."""
    for _ in range(3):
        document.add_paragraph()

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("BÁO CÁO KẾT THÚC DỰ ÁN")
    run.bold = True
    run.font.size = Pt(22)
    run.font.name = HEAD_FONT

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run(
        "Phân loại đa lớp tổn thương gan trên MRI 3D đa thì,\n"
        "với xác suất được hiệu chỉnh và cơ chế từ chối ca không chắc"
    )
    run.font.size = Pt(13)
    run.font.name = HEAD_FONT

    document.add_paragraph()
    document.add_paragraph()

    meta = [
        ("Người thực hiện", "Hoàng Đức Trường"),
        ("Người hướng dẫn", "Nguyễn Hoàng Bảo Lam"),
        ("Khối", "VSF-KD&VHVMEC-DL&AI"),
        ("Ngày báo cáo", ""),
        ("Trạng thái", "Research Use Only (RUO) — chưa kiểm định lâm sàng"),
    ]
    table = document.add_table(rows=len(meta), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for row, (label, value) in zip(table.rows, meta, strict=True):
        left = row.cells[0].paragraphs[0].add_run(label)
        left.bold = True
        left.font.size = Pt(11)
        left.font.name = HEAD_FONT
        right = row.cells[1].paragraphs[0].add_run(value)
        right.font.size = Pt(11)
        right.font.name = BODY_FONT

    document.add_paragraph()
    warning = document.add_paragraph()
    warning.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = warning.add_run(
        "Tài liệu nghiên cứu. Không dùng để chẩn đoán, điều trị hay thay thế ý kiến của bác sĩ."
    )
    run.italic = True
    run.font.size = Pt(9)


def build_toc(document: Any) -> None:
    """Mục lục dạng field — Word tự điền khi mở file hoặc khi bấm F9."""
    heading = document.add_paragraph()
    run = heading.add_run("MỤC LỤC")
    run.bold = True
    run.font.size = Pt(14)
    run.font.name = HEAD_FONT

    paragraph = document.add_paragraph()
    _add_field(paragraph, r' TOC \o "1-3" \h \z \u ')

    note = document.add_paragraph()
    run = note.add_run(
        "[Ghi chú: bấm chuột phải vào mục lục rồi chọn Update Field (hoặc F9) để Word "
        "điền số trang.]"
    )
    run.italic = True
    run.font.color.rgb = HINT_COLOR
    run.font.size = Pt(9)


def build_body(builder: Builder) -> None:
    """Duyệt STRUCTURE và dựng từng khối."""
    for block in STRUCTURE:
        kind = block[0]
        if kind == "h":
            builder.heading(block[1], block[2], block[3])
        elif kind == "hint":
            builder.hint(block[1])
        elif kind == "note":
            builder.note(block[1])
        elif kind == "table":
            bold_rows = block[4] if len(block) > 4 else ()
            builder.table(block[1], block[2], block[3], bold_rows=bold_rows)
        elif kind == "fig":
            builder.figure(block[1], block[2])
        elif kind == "pagebreak":
            builder.doc.add_page_break()
        else:  # pragma: no cover - lỗi lập trình, không phải lỗi người dùng
            raise ValueError(f"Loại khối không biết: {kind!r}")


def build_references(document: Any) -> None:
    """Danh mục tham khảo, đánh số thủ công để không phụ thuộc list style của Word."""
    note = document.add_paragraph()
    run = note.add_run(
        "[Ghi chú: danh mục dưới đây là các nguồn đã dùng trong dự án. Đổi định dạng "
        "trích dẫn hoặc bổ sung tuỳ yêu cầu nơi nộp.]"
    )
    run.italic = True
    run.font.color.rgb = HINT_COLOR
    run.font.size = Pt(9)

    for index, reference in enumerate(REFERENCES, start=1):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(0.8)
        paragraph.paragraph_format.first_line_indent = Cm(-0.8)
        paragraph.paragraph_format.space_after = Pt(4)
        run = paragraph.add_run(f"[{index}]\t{reference}")
        run.font.size = Pt(10)


def build_document() -> Any:
    """Ráp toàn bộ tài liệu và trả về đối tượng Document."""
    document = Document()
    configure_styles(document)
    build_footer(document)

    build_cover(document)
    document.add_page_break()
    build_toc(document)
    document.add_page_break()

    builder = Builder(document)
    build_body(builder)
    build_references(document)

    return document


# --- CLI -----------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dựng khung rỗng cho báo cáo kết thúc dự án, ra file .docx."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Đường dẫn file .docx đầu ra (mặc định: {DEFAULT_OUT}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Cho phép ghi đè file đã tồn tại. Không có cờ này thì script từ chối ghi đè.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out: Path = args.out

    if out.exists() and not args.force:
        raise SystemExit(
            f"'{out}' đã tồn tại. Script này dựng lại khung RỖNG, nên chạy đè sẽ xoá sạch "
            "nội dung đã viết tay.\n"
            "Nếu chắc chắn muốn dựng lại, chạy với --force; nếu không, đổi --out."
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    document = build_document()
    document.save(out)

    n_tables = len(document.tables)
    n_paragraphs = len(document.paragraphs)
    print(f"Đã ghi: {out}")
    print(f"  python-docx {docx.__version__} · {n_tables} bảng · {n_paragraphs} đoạn")
    print("  Mở bằng Word rồi bấm F9 trên mục lục để điền số trang.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
