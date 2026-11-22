"""Build the Lab 6 PDF with equations typeset as embedded math images.

Pandoc's WeasyPrint backend does not typeset TeX math. This script converts
the report's standard $...$ and $$...$$ expressions with Matplotlib MathText,
then passes the temporary Markdown file to Pandoc.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from matplotlib.mathtext import math_to_image
from matplotlib.font_manager import FontProperties


HERE = Path(__file__).resolve().parent
REPORT = HERE / "report.md"
OUTPUT_DIR = HERE / "output" / "pdf_math"
TEMP_REPORT = HERE / "output" / "report_pdf.md"
PDF = HERE.parent / "R236699C LAB 6.pdf"

DISPLAY_MATH = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
INLINE_MATH = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)")
# Currency in prose is not math. Convert it to an unambiguous label in the
# temporary PDF source so adjacent amounts cannot be mistaken for delimiters.
CURRENCY = re.compile(r"\$(\d{1,3}(?:,\d{3})+(?:\s+million)?|\d+\s+million)")


def mathtext(expression: str) -> str:
    expression = " ".join(expression.split()).rstrip(",.")
    expression = expression.replace(r"\Pr", r"\mathrm{P}")
    expression = expression.replace(r"\text{false prime}", r"\mathrm{false\ prime}")
    expression = expression.replace(r"\operatorname{Cov}", r"\mathrm{Cov}")
    expression = expression.replace(r"\operatorname{Var}", r"\mathrm{Var}")
    return expression


def main() -> None:
    source = REPORT.read_text(encoding="utf-8")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    display_count = 0
    inline_count = 0

    def render_display(match: re.Match[str]) -> str:
        nonlocal display_count
        display_count += 1
        expression = mathtext(match.group(1))
        filename = f"display_{display_count:02d}.png"
        math_to_image(f"${expression}$", OUTPUT_DIR / filename,
                      dpi=220, format="png", prop=FontProperties(size=13))
        return (
            f'<div class="math-display"><img src="output/pdf_math/{filename}" '
            f'alt="{expression}" /></div>'
        )

    source = DISPLAY_MATH.sub(render_display, source)

    def render_inline(match: re.Match[str]) -> str:
        nonlocal inline_count
        inline_count += 1
        expression = mathtext(match.group(1))
        filename = f"inline_{inline_count:03d}.png"
        math_to_image(f"${expression}$", OUTPUT_DIR / filename,
                      dpi=220, format="png", prop=FontProperties(size=10))
        return (
            f'<img class="math-inline" src="output/pdf_math/{filename}" '
            f'alt="{expression}" />'
        )

    source = CURRENCY.sub(lambda m: f"USD {m.group(1)}", source)
    source = INLINE_MATH.sub(render_inline, source)
    source = source.replace(
        "  img { max-width: 4.6in; height: auto; display: block; margin: 0.25em auto; }",
        "  img { max-width: 4.6in; height: auto; display: block; margin: 0.25em auto; }\n"
        "  .math-inline { display: inline; height: 0.95em; width: auto; "
        "vertical-align: -0.1em; margin: 0; }\n"
        "  .math-display { text-align: center; margin: 0.45em 0; }\n"
        "  .math-display img { display: inline-block; max-width: 4.6in; "
        "margin: 0; }",
    )

    TEMP_REPORT.write_text(source, encoding="utf-8")
    try:
        subprocess.run(
            ["pandoc", str(TEMP_REPORT), "-o", str(PDF), "--pdf-engine=weasyprint"],
            cwd=HERE,
            check=True,
        )
    finally:
        TEMP_REPORT.unlink(missing_ok=True)

    print(f"Created {PDF} with {display_count} display and {inline_count} inline equations.")


if __name__ == "__main__":
    main()
