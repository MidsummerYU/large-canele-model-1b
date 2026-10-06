import re
import subprocess
import tempfile
from pathlib import Path

import markdown

from newcomer_qa.config import Settings

STYLE = """
@page { size: A4; margin: 15mm 16mm; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.2pt; line-height: 1.38; color: #0b0b0b; }
h1 { font-size: 15pt; margin: 0 0 6pt; }
h2 { font-size: 11.5pt; margin: 12pt 0 4pt; }
h3 { font-size: 10pt; margin: 9pt 0 3pt; }
p, ul, ol { margin: 0 0 5pt; }
li { margin-bottom: 2pt; }
blockquote { margin: 0 0 6pt; padding: 4pt 8pt; border-left: 2pt solid #2a78d6; background: #f3f6fb; }
hr { border: 0; border-top: 0.5pt solid #c3c2b7; margin: 6pt 0; }
table { border-collapse: collapse; margin: 4pt 0 6pt; font-size: 8.4pt; break-inside: avoid; }
th, td { border-bottom: 0.5pt solid #e1e0d9; padding: 2pt 6pt 2pt 0; text-align: left; vertical-align: top; }
th { border-bottom-color: #898781; }
code { font-size: 8.4pt; }
img { display: block; max-width: 100%; margin: 6pt auto 2pt; break-inside: avoid; }
p:has(> img) + p { break-before: avoid; }
p > em:only-child { font-size: 8.2pt; color: #52514e; }
a { color: #1c5cab; text-decoration: none; }
"""


def _html(report: Path) -> str:
    body = markdown.markdown(report.read_text(encoding="utf-8"), extensions=["tables"])
    # Images are referenced relative to the report, so the page needs the report's folder as its base.
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8"><base href="{report.parent.as_uri()}/">'
        f"<style>{STYLE}</style></head><body>{body}</body></html>"
    )


def page_count(pdf: Path) -> int:
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))


def build_pdf(settings: Settings) -> Path:
    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as page:
        page.write(_html(settings.report_path))
    subprocess.run(
        [
            str(settings.chrome),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={settings.report_pdf}",
            Path(page.name).as_uri(),
        ],
        check=True,
        capture_output=True,
    )
    Path(page.name).unlink()
    return settings.report_pdf
