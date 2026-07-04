"""Professional PDF report generation with ReportLab (platypus)."""

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from models import Report

DARK = colors.HexColor("#0d0d10")
GOLD = colors.HexColor("#c9962e")
INK = colors.HexColor("#1a1a1e")
MUTED = colors.HexColor("#5a5a64")
LINE = colors.HexColor("#d9d9de")

STYLES = {
    "brand": ParagraphStyle(
        "brand", fontName="Helvetica-Bold", fontSize=8, textColor=GOLD,
        spaceAfter=4, leading=11,
    ),
    "title": ParagraphStyle(
        "title", fontName="Helvetica-Bold", fontSize=22, textColor=colors.white,
        leading=26,
    ),
    "section": ParagraphStyle(
        "section", fontName="Helvetica-Bold", fontSize=10.5, textColor=GOLD,
        spaceBefore=14, spaceAfter=4, leading=14,
    ),
    "label": ParagraphStyle(
        "label", fontName="Helvetica-Bold", fontSize=9, textColor=INK, leading=13,
    ),
    "body": ParagraphStyle(
        "body", fontName="Helvetica", fontSize=9, textColor=INK, leading=13.5,
    ),
    "muted": ParagraphStyle(
        "muted", fontName="Helvetica", fontSize=8, textColor=MUTED, leading=11,
    ),
    "link": ParagraphStyle(
        "link", fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#2456c4"),
        leading=13.5,
    ),
}


def _section(title: str) -> list:
    return [
        Paragraph(title.upper(), STYLES["section"]),
        HRFlowable(width="100%", thickness=0.7, color=LINE, spaceAfter=7),
    ]


def build_pdf(report: Report) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=14 * mm, bottomMargin=16 * mm,
        title=f"{report.company_name} — Company Research Report",
    )

    story: list = []

    # Dark header band with brand line + company name.
    header_content = [
        [Paragraph("COMPANY RESEARCH REPORT", STYLES["brand"])],
        [Paragraph(report.company_name, STYLES["title"])],
    ]
    header = Table(header_content, colWidths=[doc.width])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (0, 0), 12),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
        ("LINEBELOW", (0, -1), (-1, -1), 2, GOLD),
    ]))
    story.append(header)
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Generated on {date.today().strftime('%B %d, %Y')}", STYLES["muted"]))

    # Company information.
    story += _section("Company Information")
    info_rows = [
        [Paragraph("Website", STYLES["label"]),
         Paragraph(f'<link href="{report.website}">{report.website}</link>' if report.website else "—", STYLES["link"])],
        [Paragraph("Phone", STYLES["label"]), Paragraph(report.phone or "Not publicly listed", STYLES["body"])],
        [Paragraph("Address", STYLES["label"]), Paragraph(report.address or "Not publicly listed", STYLES["body"])],
    ]
    info = Table(info_rows, colWidths=[32 * mm, doc.width - 32 * mm])
    info.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(info)

    if report.summary:
        story += _section("Executive Summary")
        story.append(Paragraph(report.summary, STYLES["body"]))

    if report.products_services:
        story += _section("Products & Services")
        for item in report.products_services:
            story.append(Paragraph(f"•&nbsp;&nbsp;{item}", STYLES["body"]))
            story.append(Spacer(1, 2))

    if report.pain_points:
        story += _section("AI-Generated Pain Points")
        for item in report.pain_points:
            story.append(Paragraph(f"•&nbsp;&nbsp;{item}", STYLES["body"]))
            story.append(Spacer(1, 3))

    if report.pricing:
        story += _section("Pricing")
        price_rows = [
            [Paragraph(p.item, STYLES["label"]), Paragraph(p.price, STYLES["body"])]
            for p in report.pricing
        ]
        prices = Table(price_rows, colWidths=[70 * mm, doc.width - 70 * mm])
        prices.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
        ]))
        story.append(prices)

    if report.competitors:
        story += _section("Competitors")
        comp_rows = [
            [Paragraph(c.name, STYLES["label"]),
             Paragraph(f'<link href="{c.website}">{c.website}</link>' if c.website else "—", STYLES["link"])]
            for c in report.competitors
        ]
        comp = Table(comp_rows, colWidths=[52 * mm, doc.width - 52 * mm])
        comp.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
        ]))
        story.append(comp)

    if report.sources:
        story += _section("Sources")
        for src in report.sources[:10]:
            story.append(Paragraph(src, STYLES["muted"]))

    doc.build(story)
    return buffer.getvalue()
