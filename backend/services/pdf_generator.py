"""
ScotlandAI Navigator — Professional PDF Brief Generator

Generates a board-ready PDF from a validated AI Opportunity Brief.

WHY PDF:
- The brief may be the first thing a board member sees from DataVita
- A well-formatted PDF says "this is a professional recommendation"
- A plain text message says "a chatbot wrote this"
- The PDF is the artefact that gets forwarded, printed, and presented
- It must look like it came from a consultancy, not a prototype

WHY REPORTLAB:
- Pure Python — no external service, no API key, no cost
- Full control over layout, fonts, colours, tables
- Works in any Python environment (local, Render, Docker)
- Produces consistent output regardless of platform

DESIGN DECISIONS:
- Dark blue (#1B3A5C) as primary colour — professional, trustworthy
- Teal (#2E86AB) as accent — modern, approachable
- Helvetica fonts throughout — universally available, clean
- Cover page with generation timestamp
- Discovery answers included so the reader can verify accuracy
- Each opportunity in a clear, structured card format
- DataVita contact info as the final call to action
"""

import io
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Table, TableStyle, Spacer, PageBreak, NextPageTemplate,
)

from schemas.brief import BriefResponse

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════
# Colour Palette
# ═══════════════════════════════════════════════

PRIMARY = HexColor('#1B3A5C')       # Dark navy — trust, professionalism
SECONDARY = HexColor('#2E86AB')     # Teal — modern, approachable
ACCENT = HexColor('#1A936F')        # Green accent — growth, Scotland
LIGHT_BG = HexColor('#F0F4F8')      # Light grey background
DARK_TEXT = HexColor('#2C3E50')      # Near-black text
WHITE = colors.white
DIVIDER = HexColor('#CBD5E1')       # Subtle divider grey


# ═══════════════════════════════════════════════
# Custom Styles
# ═══════════════════════════════════════════════

def _get_styles():
    """Build the custom style sheet for the brief PDF."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CoverTitle',
        parent=styles['Title'],
        fontSize=28,
        fontName='Helvetica-Bold',
        textColor=WHITE,
        spaceAfter=6,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        parent=styles['Normal'],
        fontSize=13,
        fontName='Helvetica',
        textColor=HexColor('#B0C4DE'),
        spaceAfter=20,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading1'],
        fontSize=16,
        fontName='Helvetica-Bold',
        textColor=PRIMARY,
        spaceBefore=20,
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name='SubHeading',
        parent=styles['Heading2'],
        fontSize=13,
        fontName='Helvetica-Bold',
        textColor=SECONDARY,
        spaceBefore=14,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name='OpportunityName',
        parent=styles['Heading2'],
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=PRIMARY,
        spaceBefore=16,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name='BodyText2',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=DARK_TEXT,
        leading=14,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
    ))

    styles.add(ParagraphStyle(
        name='Label',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=SECONDARY,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name='FieldValue',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=DARK_TEXT,
        leading=13,
        spaceAfter=6,
        leftIndent=10,
    ))

    styles.add(ParagraphStyle(
        name='ExecSummary',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica',
        textColor=DARK_TEXT,
        leading=16,
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        borderPadding=12,
    ))

    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        textColor=colors.grey,
    ))

    styles.add(ParagraphStyle(
        name='CTA',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=PRIMARY,
        spaceBefore=12,
        spaceAfter=4,
        alignment=TA_CENTER,
    ))

    return styles


# ═══════════════════════════════════════════════
# Page Templates (Cover + Body)
# ═══════════════════════════════════════════════

def _cover_page(canvas, doc):
    """Render the cover page — dark blue background with title."""
    canvas.saveState()
    width, height = A4

    # Full dark blue background
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, height - 300, width, 300, fill=True, stroke=False)

    # Scottish flag emoji would go here in a real product
    # For now, text-based branding
    canvas.setFillColor(WHITE)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawCentredString(width / 2, height - 50, "🏴󠁧󠁢󠁳󠁣󠁴󠁿  SCOTLANDAI NAVIGATOR")

    # Subtle accent line
    canvas.setStrokeColor(SECONDARY)
    canvas.setLineWidth(2)
    canvas.line(width / 2 - 60, height - 60, width / 2 + 60, height - 60)

    canvas.restoreState()


def _body_page(canvas, doc):
    """Render headers and footers on body pages."""
    canvas.saveState()
    width, height = A4

    # Header line
    canvas.setStrokeColor(PRIMARY)
    canvas.setLineWidth(1)
    canvas.line(doc.leftMargin, height - 45, width - doc.rightMargin, height - 45)

    # Header text
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(PRIMARY)
    canvas.drawString(doc.leftMargin, height - 40, "SCOTLAND AI OPPORTUNITY BRIEF")
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(width - doc.rightMargin, height - 40, "CONFIDENTIAL")

    # Footer line
    canvas.setStrokeColor(DIVIDER)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 38, width - doc.rightMargin, 38)

    # Footer text
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.grey)
    canvas.drawString(doc.leftMargin, 26, "Generated by ScotlandAI Navigator · Powered by DataVita Infrastructure")
    canvas.drawRightString(width - doc.rightMargin, 26, f"Page {doc.page}")

    canvas.restoreState()


# ═══════════════════════════════════════════════
# PDF Generation
# ═══════════════════════════════════════════════

def generate_pdf(
    brief: BriefResponse,
    organisation_name: str = "Organisation",
    discovery_answers: dict | None = None,
) -> tuple[str, bytes]:
    """
    Generate a professional PDF from a validated brief.

    Returns (filename, pdf_bytes).
    The filename is a UUID — unique, non-guessable, safe for URLs.
    """
    buffer = io.BytesIO()
    styles = _get_styles()

    # Document setup
    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=55,
        bottomMargin=50,
        leftMargin=45,
        rightMargin=45,
    )

    width, height = A4
    frame_width = width - doc.leftMargin - doc.rightMargin
    frame_height = height - doc.topMargin - doc.bottomMargin

    body_frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        frame_width, frame_height,
        id='body',
    )

    cover_template = PageTemplate(id='Cover', frames=[body_frame], onPage=_cover_page)
    main_template = PageTemplate(id='Main', frames=[body_frame], onPage=_body_page)
    doc.addPageTemplates([cover_template, main_template])

    story = []
    now = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")

    # ── Cover Page ──
    story.append(Spacer(1, 80))
    story.append(Paragraph(
        "AI OPPORTUNITY BRIEF",
        styles['CoverTitle'],
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"{organisation_name}",
        ParagraphStyle(
            name='OrgName',
            parent=styles['CoverSubtitle'],
            fontSize=18,
            fontName='Helvetica-Bold',
            textColor=WHITE,
        ),
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"Generated: {now}",
        styles['CoverSubtitle'],
    ))
    story.append(Paragraph(
        "ScotlandAI Navigator v1.0",
        styles['CoverSubtitle'],
    ))

    # Transition to body pages
    story.append(Spacer(1, 200))
    story.append(NextPageTemplate('Main'))
    story.append(PageBreak())

    # ── Executive Summary ──
    story.append(Paragraph("Executive Summary", styles['SectionHeading']))

    # Executive summary in a highlighted box (using table as container)
    exec_data = [[Paragraph(brief.executive_summary, styles['ExecSummary'])]]
    exec_table = Table(exec_data, colWidths=[frame_width - 20])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1, SECONDARY),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(exec_table)
    story.append(Spacer(1, 16))

    # ── AI Opportunities ──
    story.append(Paragraph("AI Opportunities", styles['SectionHeading']))
    story.append(Paragraph(
        "Three specific AI products this organisation could realistically build, "
        "each mapped to the right DataVita infrastructure tier.",
        styles['BodyText2'],
    ))

    for i, opp in enumerate(brief.opportunities, 1):
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f"Opportunity {i} — {opp.name}",
            styles['OpportunityName'],
        ))

        # Opportunity details as a structured card
        fields = [
            ("What it does", opp.what_it_does),
            ("Problem solved", opp.problem_solved),
            ("Data required", ", ".join(opp.data_required)),
            ("Expected impact", opp.expected_impact),
            ("Infrastructure", opp.infrastructure),
            ("Build complexity", opp.build_complexity),
            ("Time to value", opp.time_to_value),
        ]

        for label, value in fields:
            story.append(Paragraph(label, styles['Label']))
            story.append(Paragraph(value, styles['FieldValue']))

        # Divider between opportunities
        if i < len(brief.opportunities):
            divider_data = [["" * 1]]
            divider_table = Table(divider_data, colWidths=[frame_width - 20])
            divider_table.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (-1, 0), 0.5, DIVIDER),
            ]))
            story.append(Spacer(1, 8))
            story.append(divider_table)

    # ── Recommended First Step ──
    story.append(PageBreak())
    story.append(Paragraph("Recommended First Step", styles['SectionHeading']))
    story.append(Paragraph(
        "The single most valuable thing this organisation could build in 90 days:",
        styles['BodyText2'],
    ))

    # First step in a highlighted box
    step_data = [[Paragraph(brief.recommended_first_step, styles['ExecSummary'])]]
    step_table = Table(step_data, colWidths=[frame_width - 20])
    step_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1, ACCENT),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(step_table)

    # ── Discovery Summary (optional) ──
    if discovery_answers:
        story.append(Spacer(1, 30))
        story.append(Paragraph("Discovery Summary", styles['SectionHeading']))
        story.append(Paragraph(
            "The answers provided during the discovery conversation, "
            "included here so you can verify the brief reflects what you said.",
            styles['BodyText2'],
        ))

        question_labels = [
            ("Organisation & Bottleneck", "organisation_and_bottleneck"),
            ("Data Assets", "data_assets"),
            ("Value of Improvement", "value_of_improvement"),
            ("Risk Appetite", "risk_appetite"),
            ("Technical Capability", "technical_capability"),
        ]

        for label, key in question_labels:
            if key in discovery_answers:
                value = str(discovery_answers[key])
                # Clean up enum values for display
                value = value.replace("_", " ").title() if key in ("risk_appetite", "technical_capability") else value
                story.append(Paragraph(label, styles['Label']))
                story.append(Paragraph(value, styles['FieldValue']))

    # ── Next Steps with DataVita ──
    story.append(Spacer(1, 30))
    story.append(Paragraph("Next Steps", styles['SectionHeading']))

    cta_data = [[Paragraph(
        "To explore any of these opportunities on DataVita's world-class infrastructure:<br/><br/>"
        '<b><a href="https://datavita.co.uk/contact" color="#2E86AB">datavita.co.uk/contact</a></b>'
        "<br/><br/>DataVita AI Solutions Team",
        styles['CTA'],
    )]]
    cta_table = Table(cta_data, colWidths=[frame_width - 40])
    cta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1.5, PRIMARY),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(cta_table)

    # ── Build the PDF ──
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Generate a unique, non-guessable filename
    filename = f"brief_{uuid.uuid4().hex[:12]}.pdf"

    logger.info(f"PDF generated: {filename} ({len(pdf_bytes)} bytes)")
    return filename, pdf_bytes


def save_pdf(filename: str, pdf_bytes: bytes, output_dir: str = "static/briefs") -> Path:
    """
    Save a generated PDF to disk.

    Returns the full path to the saved file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / filename
    file_path.write_bytes(pdf_bytes)

    logger.info(f"PDF saved to: {file_path}")
    return file_path
