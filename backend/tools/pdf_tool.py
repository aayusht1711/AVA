"""
AVA PDF Generator Tool — ReportLab
Generates professional PDFs from structured content.
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import base64


# AVA color palette
AVA_PURPLE = colors.HexColor("#6366f1")
AVA_DARK   = colors.HexColor("#03060f")
AVA_LIGHT  = colors.HexColor("#dde4ff")
AVA_MUTED  = colors.HexColor("#6878aa")


def generate_pdf(title: str, sections: list[dict]) -> bytes:
    """
    Generate a PDF document.

    sections: [
        {"heading": "Introduction", "content": "..."},
        {"heading": "Results",      "content": "...", "table": [[...], [...]]},
    ]

    Returns raw PDF bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "AVATitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=AVA_PURPLE,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    heading_style = ParagraphStyle(
        "AVAHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=AVA_PURPLE,
        spaceBefore=14,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "AVABody",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#333333"),
        spaceAfter=8,
        leading=16,
    )

    story = []

    # Title
    story.append(Paragraph(title, title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=AVA_PURPLE))
    story.append(Spacer(1, 0.3*cm))

    # Sections
    for section in sections:
        if section.get("heading"):
            story.append(Paragraph(section["heading"], heading_style))

        if section.get("content"):
            for para in section["content"].split("\n\n"):
                if para.strip():
                    story.append(Paragraph(para.strip(), body_style))

        if section.get("table"):
            table_data = section["table"]
            t = Table(table_data, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND",  (0, 0), (-1, 0), AVA_PURPLE),
                ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
                ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",    (0, 0), (-1, 0), 11),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5ff")]),
                ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                ("FONTSIZE",    (0, 1), (-1, -1), 10),
                ("TOPPADDING",  (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3*cm))

        story.append(Spacer(1, 0.2*cm))

    doc.build(story)
    return buffer.getvalue()


def pdf_to_base64(pdf_bytes: bytes) -> str:
    return base64.b64encode(pdf_bytes).decode("utf-8")
