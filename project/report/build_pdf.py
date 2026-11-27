"""Build the project report PDF: Markdown -> HTML (pandoc + KaTeX) -> PDF
(headless Chrome). This is the same route as the Lab 1 and Lab 3 PDFs, so
equations are typeset by KaTeX rather than pasted in as images.

Needs pandoc and Google Chrome (or Microsoft Edge). KaTeX is loaded from its
CDN, so the build needs an internet connection.

    python report/build_pdf.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "report.md"
HTML = HERE / "_report.html"
PDF = HERE.parent.parent / "GROUP 11 ETE PROJECT REPORT.pdf"

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "chrome",
]

# Pandoc's standalone template adds screen padding and a narrow column;
# these rules restore the print layout set in the report's own <style>.
PRINT_CSS = """<style>
  html { background: white; }
  body { padding: 0 !important; margin: 0 auto !important; max-width: 7.4in !important;
         font-family: "Times New Roman", Times, serif; color: #000; hyphens: none; }
  table { border-collapse: collapse; margin: 0.6em 0; }
  th, td { padding: 2px 8px; border-bottom: 1px solid #bbb; text-align: left; vertical-align: top; }
  thead th { border-bottom: 1.5px solid #333; }
  code { font-family: Consolas, monospace; font-size: 0.9em; }
  pre { font-size: 9.5pt; line-height: 1.25; background: #f6f6f4; padding: 6px 8px; }
  .katex { font-size: 1.05em; }
  .katex-display { margin: 0.5em 0; }
  h2 { break-after: avoid; } h3 { break-after: avoid; }
  img, table, pre { break-inside: avoid; }
</style>
"""


def find_browser():
    for b in BROWSERS:
        if os.path.isabs(b) and os.path.exists(b):
            return b
        found = shutil.which(b)
        if found:
            return found
    sys.exit("Chrome or Edge not found; install one or edit BROWSERS.")


def main():
    header = HERE / "_print.html"
    header.write_text(PRINT_CSS, encoding="utf-8")
    try:
        subprocess.run(
            ["pandoc", str(REPORT), "-s", "--math-method=katex", "-o", str(HTML),
             "--include-in-header", str(header),
             "--metadata", "pagetitle=ETE Project Report - Group 11"],
            cwd=HERE, check=True)
        subprocess.run(
            [find_browser(), "--headless=new", "--disable-gpu",
             "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
             "--virtual-time-budget=20000", f"--print-to-pdf={PDF}",
             HTML.as_uri()],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        header.unlink(missing_ok=True)
        HTML.unlink(missing_ok=True)
    print(f"Created {PDF}")


if __name__ == "__main__":
    main()
