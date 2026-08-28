from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "01_academic" / "religious_authority_as_epistemic_architecture_v0_3.md"
OUTPUT = ROOT / "output" / "pdf" / "religious_authority_as_epistemic_architecture_v0_3_philpapers.pdf"


def clean_markdown(text: str) -> str:
    text = text.replace("\\---", "---")
    text = text.replace("\\.", ".")
    text = text.replace("\\*", "*")
    text = text.replace("\u2010", "-")
    text = text.replace("\u2011", "-")
    text = text.replace("\u2012", "-")
    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")
    return text


def inline_markup(text: str) -> str:
    text = clean_markdown(text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(
        r"(https?://[^\s<]+)",
        r'<font color="#1f5f8b">\1</font>',
        text,
    )
    return text


def read_blocks() -> list[str]:
    raw = SOURCE.read_text(encoding="utf-8-sig")
    lines = raw.splitlines()
    blocks: list[str] = []
    current: list[str] = []
    table: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            if current:
                blocks.append(" ".join(current))
                current = []
            table.append(stripped)
            continue
        if table:
            blocks.append("__TABLE__\n" + "\n".join(table))
            table = []
        if not stripped:
            if current:
                blocks.append(" ".join(current))
                current = []
            continue
        if stripped == "\\---" or stripped == "---":
            if current:
                blocks.append(" ".join(current))
                current = []
            blocks.append("---")
            continue
        if stripped.startswith("#") or stripped.startswith(">") or re.match(r"^\d+\.\s+", stripped):
            if current:
                blocks.append(" ".join(current))
                current = []
            blocks.append(stripped)
            continue
        current.append(stripped)

    if current:
        blocks.append(" ".join(current))
    if table:
        blocks.append("__TABLE__\n" + "\n".join(table))
    return blocks


def make_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Times-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Times-Italic",
            fontSize=13,
            leading=17,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#333333"),
            spaceAfter=16,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=10.5,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#333333"),
            spaceAfter=2,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="Times-Bold",
            fontSize=14,
            leading=18,
            spaceBefore=15,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "Heading3",
            parent=base["Heading3"],
            fontName="Times-BoldItalic",
            fontSize=12,
            leading=16,
            spaceBefore=10,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=10.6,
            leading=15.2,
            alignment=TA_JUSTIFY,
            firstLineIndent=0.22 * inch,
            spaceAfter=6,
        ),
        "noindent": ParagraphStyle(
            "NoIndent",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=10.6,
            leading=15.2,
            alignment=TA_JUSTIFY,
            firstLineIndent=0,
            spaceAfter=6,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName="Times-Italic",
            fontSize=10.2,
            leading=14.5,
            leftIndent=0.38 * inch,
            rightIndent=0.25 * inch,
            firstLineIndent=0,
            spaceBefore=3,
            spaceAfter=8,
        ),
        "list": ParagraphStyle(
            "List",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=10.6,
            leading=15.2,
            leftIndent=0.32 * inch,
            firstLineIndent=-0.18 * inch,
            spaceAfter=4,
        ),
        "refs": ParagraphStyle(
            "References",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=10.2,
            leading=13.8,
            leftIndent=0.25 * inch,
            firstLineIndent=-0.25 * inch,
            spaceAfter=5,
        ),
        "table": ParagraphStyle(
            "Table",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=8.8,
            leading=11,
            alignment=TA_LEFT,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["BodyText"],
            fontName="Times-Bold",
            fontSize=8.8,
            leading=11,
            alignment=TA_LEFT,
        ),
    }
    return styles


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 9)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawRightString(
        doc.pagesize[0] - doc.rightMargin,
        0.42 * inch,
        str(canvas.getPageNumber()),
    )
    canvas.restoreState()


def build_pdf() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = make_styles()
    story = []
    in_references = False

    for block in read_blocks():
        if block == "---":
            continue
        if block.startswith("__TABLE__\n"):
            rows = []
            for row in block.splitlines()[1:]:
                cells = [cell.strip() for cell in row.strip("|").split("|")]
                if all(set(cell) <= {"-"} for cell in cells):
                    continue
                rows.append(cells)
            rendered = []
            for row_index, row in enumerate(rows):
                style = styles["table_header"] if row_index == 0 else styles["table"]
                rendered.append([Paragraph(inline_markup(cell), style) for cell in row])
            table = Table(
                rendered,
                colWidths=[1.32 * inch, 1.9 * inch, 3.08 * inch],
                hAlign="LEFT",
                repeatRows=1,
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#888888")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(KeepTogether([table, Spacer(1, 0.08 * inch)]))
            continue
        if block.startswith("# "):
            story.append(Paragraph(inline_markup(block[2:]), styles["title"]))
            continue
        if block.startswith("## "):
            heading = clean_markdown(block[3:])
            if re.match(r"^(Pluralism|Abstract$)", heading):
                style = "subtitle" if heading.startswith("Pluralism") else "h2"
            else:
                style = "h2"
            if heading == "References":
                in_references = True
            story.append(Paragraph(inline_markup(heading), styles[style]))
            continue
        if block.startswith("### "):
            story.append(Paragraph(inline_markup(block[4:]), styles["h3"]))
            continue
        if block.startswith("**Anthony Paterson"):
            parts = re.findall(r"\*\*(.*?)\*\*", clean_markdown(block))
            for part in parts:
                if part:
                    story.append(Paragraph(inline_markup(part), styles["meta"]))
            story.append(Spacer(1, 0.12 * inch))
            continue
        if block.startswith(">"):
            story.append(Paragraph(inline_markup(block[1:].strip()), styles["quote"]))
            continue
        if re.match(r"^\d+\.\s+", block):
            story.append(Paragraph(inline_markup(block), styles["list"]))
            continue
        if block.startswith("**Keywords:**"):
            story.append(Paragraph(inline_markup(block), styles["noindent"]))
            story.append(Spacer(1, 0.08 * inch))
            continue

        style = styles["refs"] if in_references else styles["body"]
        if story and getattr(story[-1], "style", None) in (styles["h2"], styles["h3"]):
            style = styles["noindent"] if not in_references else styles["refs"]
        story.append(Paragraph(inline_markup(block), style))

    frame = Frame(
        0.9 * inch,
        0.72 * inch,
        LETTER[0] - 1.8 * inch,
        LETTER[1] - 1.42 * inch,
        id="normal",
    )
    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=LETTER,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.72 * inch,
        title="Religious Authority as Epistemic Architecture",
        author="Anthony Paterson / Instance001",
        subject="Philosophy of religion; religious epistemology",
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])
    doc.build(story)


if __name__ == "__main__":
    build_pdf()
