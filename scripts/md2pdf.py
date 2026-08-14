"""Kết xuất một file Markdown thành PDF để gửi đi.

    python scripts/md2pdf.py reports/W2_REPORT.md
    python scripts/md2pdf.py reports/W2_REPORT.md --out /duong/dan/khac.pdf

Đường đi: Markdown -> HTML có CSS in ấn -> Chrome (hoặc Edge) headless in ra PDF.
Chọn cách này vì hai thứ đó đã có sẵn trên máy Windows, không phải cài LaTeX hay
pandoc, và Chrome dựng bảng markdown đúng hơn hẳn các thư viện PDF thuần Python.

File HTML trung gian là **tạm**, mặc định ghi vào thư mục tạm của hệ điều hành và
xoá sau khi in. Nó không được để trong `reports/` vì đó là thư mục deliverable.

Ghi chú kiểu chữ: chỉ dùng font có sẵn trên Windows và phủ đủ dấu tiếng Việt
(Cambria cho phần chữ chạy, Segoe UI cho tiêu đề và bảng). Không nhúng font
ngoài để bản PDF mở được ở mọi máy mà không lệch chữ.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page {
  size: A4;
  margin: 18mm 16mm 16mm 16mm;
}

html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }

body {
  font-family: Cambria, Georgia, "Times New Roman", serif;
  font-size: 10pt;
  line-height: 1.42;
  color: #111;
  margin: 0;
  /* không để một hai dòng lẻ rơi sang đầu hoặc cuối trang */
  orphans: 3;
  widows: 3;
}

/* --- Tiêu đề: sans để tách khỏi phần chữ chạy, không màu mè --- */
h1, h2, h3 {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  color: #000;
  break-after: avoid;
  page-break-after: avoid;
  margin-bottom: 0.35em;
}
h1 {
  font-size: 19pt;
  line-height: 1.25;
  margin: 0 0 0.6em 0;
  padding-bottom: 0.45em;
  border-bottom: 2px solid #111;
}
h2 {
  font-size: 13.5pt;
  margin-top: 1.5em;
  padding-bottom: 0.25em;
  border-bottom: 1px solid #bbb;
}
h3 { font-size: 11.5pt; margin-top: 1.2em; }

p { margin: 0.55em 0; text-align: justify; }

/* --- Khối thông tin đầu trang: Người thực hiện / Ngày / Trạng thái --- */
.meta {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 9.5pt;
  line-height: 1.7;
  background: #f4f5f6;
  border-left: 3px solid #333;
  padding: 0.7em 1em;
  margin-bottom: 1.4em;
}
.meta p { margin: 0; text-align: left; }

/* --- Bảng: số liệu là nhân vật chính nên phải dễ dò --- */
table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.9em 0;
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 8.6pt;
  break-inside: avoid;
  page-break-inside: avoid;
}
th, td {
  border: 1px solid #c8ccd0;
  padding: 5px 7px;
  text-align: left;
  vertical-align: top;
}
th {
  background: #eceef0;
  font-weight: 600;
  border-bottom: 1.5px solid #8a8f94;
}
tbody tr:nth-child(even) { background: #fafbfb; }
/* cột số dễ so hàng dọc hơn khi chữ số đều bề ngang */
td { font-variant-numeric: tabular-nums; }

/* --- Ghi chú cảnh báo (blockquote trong markdown) --- */
blockquote {
  margin: 0.9em 0;
  padding: 0.6em 0.9em;
  background: #f7f7f4;
  border-left: 3px solid #6b6b63;
  font-size: 9.8pt;
  break-inside: avoid;
}
blockquote p { margin: 0.2em 0; }

ul, ol { margin: 0.55em 0; padding-left: 1.5em; }
li { margin: 0.28em 0; text-align: justify; }

code {
  font-family: Consolas, "Courier New", monospace;
  font-size: 0.9em;
  background: #f0f1f2;
  padding: 0.5px 3px;
  border-radius: 2px;
}

strong { font-weight: 700; }
hr { border: none; border-top: 1px solid #ccc; margin: 1.4em 0 1em 0; }
img { display: block; max-width: 100%; height: auto; margin: 0.9em auto; }

/* --- Dòng RUO cuối bài --- */
hr + p em {
  display: block;
  font-size: 9pt;
  color: #333;
  background: #f4f5f6;
  border-left: 3px solid #333;
  padding: 0.6em 0.9em;
  font-style: normal;
}
"""


def find_browser() -> str:
    """Tìm Chrome hoặc Edge; cả hai đều in PDF được như nhau."""
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    for name in ("chrome", "msedge", "chromium"):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit(
        "Không tìm thấy Chrome hay Edge để in PDF. Cài một trong hai, hoặc thêm "
        "đường dẫn vào CHROME_CANDIDATES trong scripts/md2pdf.py."
    )


def build_html(md_text: str, title: str, base_href: str = "") -> str:
    """Markdown -> HTML hoàn chỉnh, đã gắn CSS in ấn."""
    import markdown

    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
        output_format="html5",
    )

    # Bốn dòng đầu (Người thực hiện / Ngày / Kỳ / Trạng thái) markdown gộp thành
    # MỘT thẻ <p> vì chúng chỉ cách nhau bằng xuống dòng đơn, nên in ra bị dồn
    # thành một dòng chạy dài. Tách lại bằng <br> rồi bọc thành khối meta, để nó
    # đọc như phần đầu đề của báo cáo chứ không lẫn vào phần chữ chạy.
    marker = "<p><strong>Người thực hiện:</strong>"
    if marker in body:
        start = body.index(marker)
        end = body.index("</p>", start) + len("</p>")
        # trong <p> này các nhãn cách nhau đúng bằng một ký tự xuống dòng
        meta = body[start:end].replace("\n<strong>", "<br>\n<strong>")
        body = body[:start] + '<div class="meta">' + meta + "</div>" + body[end:]

    return (
        "<!doctype html>\n<html lang='vi'><head><meta charset='utf-8'>\n"
        f"<title>{title}</title>\n<base href='{base_href}'>\n"
        f"<style>{CSS}</style>\n</head>\n<body>\n{body}\n</body></html>\n"
    )


def print_pdf(html_path: Path, pdf_path: Path, browser: str) -> None:
    """Gọi trình duyệt ở chế độ headless để in ra PDF."""
    url = html_path.resolve().as_uri()
    base = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path.resolve()}",
        url,
    ]
    result = subprocess.run(base, capture_output=True, text=True, timeout=180)
    if pdf_path.exists():
        return

    # Bản Chrome cũ không hiểu --headless=new hoặc --no-pdf-header-footer.
    fallback = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={pdf_path.resolve()}",
        url,
    ]
    subprocess.run(fallback, capture_output=True, text=True, timeout=180)
    if not pdf_path.exists():
        raise SystemExit(
            "Trình duyệt chạy xong nhưng không sinh ra PDF.\n"
            f"stdout: {result.stdout.strip()[:500]}\nstderr: {result.stderr.strip()[:500]}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Kết xuất Markdown thành PDF")
    parser.add_argument("markdown", help="vd reports/W2_REPORT.md")
    parser.add_argument("--out", help="mặc định: cùng tên, đuôi .pdf, cùng thư mục")
    parser.add_argument("--keep-html", action="store_true", help="giữ file HTML trung gian để soi")
    args = parser.parse_args()

    md_path = Path(args.markdown)
    if not md_path.exists():
        raise SystemExit(f"không thấy {md_path}")
    pdf_path = Path(args.out) if args.out else md_path.with_suffix(".pdf")

    md_text = md_path.read_text(encoding="utf-8")
    title = md_text.lstrip().splitlines()[0].lstrip("# ").strip() or md_path.stem
    html = build_html(md_text, title, md_path.resolve().parent.as_uri() + "/")

    tmp_dir = Path(tempfile.mkdtemp(prefix="md2pdf_"))
    html_path = tmp_dir / (md_path.stem + ".html")
    html_path.write_text(html, encoding="utf-8")

    browser = find_browser()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()
    print_pdf(html_path, pdf_path, browser)

    size_kb = pdf_path.stat().st_size / 1024
    print(f"trinh duyet : {browser}")
    print(f"da ghi      : {pdf_path}  ({size_kb:.0f} KiB)")
    if args.keep_html:
        print(f"html tam    : {html_path}")
    else:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
