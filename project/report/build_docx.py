"""Build the project report as a Word document.

    python report/build_docx.py

Markdown -> .docx with pandoc (equations become native Word equations), then
Microsoft Word (via COM, Windows only) applies the report formatting: Times
New Roman, bordered tables, centred figures and cover, and page numbers.
Requires pandoc, and Microsoft Word for the formatting pass.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "report.md"
TEMP_MD = HERE / "_report_docx.md"
RAW_DOCX = HERE / "_report_raw.docx"
DOCX = HERE.parent.parent / "GROUP 11 ETE PROJECT REPORT.docx"

PAGE_BREAK = '\n```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n'


def prepare_markdown():
    text = REPORT.read_text(encoding="utf-8")
    text = re.sub(r"<style>.*?</style>\s*", "", text, flags=re.S)
    text = text.replace('<div style="page-break-after: always;"></div>', PAGE_BREAK)
    # Cover page: the centred <div> becomes a custom paragraph style.
    text = re.sub(r'<div style="text-align:center; margin-bottom: 2em;">\s*', '::: {custom-style="Cover"}\n', text, count=1)
    text = text.replace("</div>", ":::", 1)
    text = text.replace("<br>", " ")
    TEMP_MD.write_text(text, encoding="utf-8")


def run_pandoc():
    subprocess.run(["pandoc", str(TEMP_MD), "-f", "markdown", "-t", "docx",
                    "--resource-path", str(HERE), "-o", str(RAW_DOCX)],
                   cwd=HERE, check=True)


FORMAT_PS1 = r"""
$ErrorActionPreference = 'Stop'
$src = '{src}'; $dst = '{dst}'
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$d = $w.Documents.Open($src)
$font = 'Times New Roman'
foreach ($name in @('Normal','Body Text','First Paragraph','Compact','Title','Heading 1','Heading 2','Heading 3','Caption','Image Caption','Table Caption','Cover')) {{
  try {{ $s = $d.Styles.Item($name); $s.Font.Name = $font; $s.Font.Color = 0 }} catch {{}}
}}
foreach ($name in @('Normal','Body Text','First Paragraph')) {{
  try {{ $s = $d.Styles.Item($name); $s.Font.Size = 12; $s.ParagraphFormat.SpaceAfter = 6; $s.ParagraphFormat.LineSpacingRule = 0 }} catch {{}}
}}
try {{ $d.Styles.Item('Compact').Font.Size = 11 }} catch {{}}
$sizes = @{{ 'Heading 1' = 16; 'Heading 2' = 14; 'Heading 3' = 12 }}
foreach ($k in $sizes.Keys) {{ try {{ $s = $d.Styles.Item($k); $s.Font.Size = $sizes[$k]; $s.Font.Bold = $true; $s.ParagraphFormat.KeepWithNext = $true }} catch {{}} }}
try {{ $c = $d.Styles.Item('Cover'); $c.ParagraphFormat.Alignment = 1; $c.Font.Size = 12; $c.ParagraphFormat.SpaceAfter = 8 }} catch {{}}
foreach ($name in @('Image Caption','Caption')) {{ try {{ $s = $d.Styles.Item($name); $s.Font.Italic = $false; $s.Font.Size = 10; $s.ParagraphFormat.Alignment = 1 }} catch {{}} }}
# Figures: centre every paragraph that holds an inline picture.
foreach ($shape in $d.InlineShapes) {{ $shape.Range.ParagraphFormat.Alignment = 1 }}
# Tables: borders, smaller font, fit to page width.
foreach ($t in $d.Tables) {{
  $t.Borders.Enable = $true
  $t.Range.Font.Size = 10
  $t.Range.Font.Name = $font
  $t.Range.ParagraphFormat.SpaceAfter = 0
  $t.AutoFitBehavior(2)
  $t.Rows.Item(1).HeadingFormat = $true
  $t.Rows.Item(1).Range.Font.Bold = $true
  $t.Rows.Item(1).Shading.BackgroundPatternColor = 15132390
}}
# The cover table (members) is centred.
if ($d.Tables.Count -gt 0) {{ $d.Tables.Item(1).Rows.Alignment = 1; $d.Tables.Item(1).AutoFitBehavior(1) }}
# Page setup and page numbers (none on the cover).
$sec = $d.Sections.Item(1)
$sec.PageSetup.PaperSize = 7
$sec.PageSetup.TopMargin = 72; $sec.PageSetup.BottomMargin = 72
$sec.PageSetup.LeftMargin = 72; $sec.PageSetup.RightMargin = 72
$sec.PageSetup.DifferentFirstPageHeaderFooter = $true
$null = $sec.Footers.Item(1).PageNumbers.Add(1, $false)
$d.SaveAs2($dst, 16)
$d.Close()
$w.Quit()
'ok'
"""


def format_with_word():
    script = HERE / "_format.ps1"
    script.write_text(FORMAT_PS1.format(src=str(RAW_DOCX), dst=str(DOCX)), encoding="utf-8")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                              "-File", str(script)], capture_output=True, text=True)
        if out.returncode != 0 or "ok" not in out.stdout:
            sys.exit("Word formatting failed:\n" + out.stdout + out.stderr)
    finally:
        script.unlink(missing_ok=True)


def main():
    prepare_markdown()
    try:
        run_pandoc()
        format_with_word()
    finally:
        TEMP_MD.unlink(missing_ok=True)
        RAW_DOCX.unlink(missing_ok=True)
    print(f"Created {DOCX}")


if __name__ == "__main__":
    main()
