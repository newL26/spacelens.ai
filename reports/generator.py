"""
PDF report generator using ReportLab.

Produces a single-page intelligence report containing:
  - SpaceLens AI header / branding
  - Satellite image thumbnail
  - Prediction summary (class, confidence, top-3)
  - IBM Granite AI narrative
  - Probability table
  - Footer with timestamp and user
"""
import io
import os
import textwrap
import logging
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    Image as RLImage,
    KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# ── Colour palette (mirrors CSS vars) ─────────────────────────────────────────
C_BG        = colors.HexColor("#030712")
C_SURFACE   = colors.HexColor("#0d1117")
C_SURFACE2  = colors.HexColor("#161b22")
C_CYAN      = colors.HexColor("#38bdf8")
C_VIOLET    = colors.HexColor("#818cf8")
C_ACCENT    = colors.HexColor("#a78bfa")
C_SUCCESS   = colors.HexColor("#4ade80")
C_WARNING   = colors.HexColor("#fbbf24")
C_DANGER    = colors.HexColor("#f87171")
C_TEXT      = colors.HexColor("#e2e8f0")
C_MUTED     = colors.HexColor("#8b98a9")
C_BORDER    = colors.HexColor("#1e2d3d")
C_WHITE     = colors.white


def _confidence_colour(confidence: float) -> colors.HexColor:
    if confidence >= 75:
        return C_SUCCESS
    if confidence >= 45:
        return C_WARNING
    return C_DANGER


def _wrap(text: str, width: int = 90) -> str:
    """Soft-wrap long text for Paragraph cells."""
    lines = []
    for paragraph in text.split("\n"):
        if len(paragraph) > width:
            lines.extend(textwrap.wrap(paragraph, width))
        else:
            lines.append(paragraph)
    return "<br/>".join(lines)


def generate_prediction_report(prediction) -> bytes:
    """
    Build and return a PDF report for the given Prediction instance.

    Args:
        prediction: prediction.models.Prediction instance

    Returns:
        bytes — PDF content ready for an HttpResponse.
    """
    buffer = io.BytesIO()
    page_w, page_h = A4
    margin = 18 * mm

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title=f"SpaceLens AI — {prediction.predicted_class} Report",
        author="SpaceLens AI",
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Helper styles ──────────────────────────────────────────────────────────
    def style(name, **kwargs) -> ParagraphStyle:
        base = styles.get(name, styles["Normal"])
        # Merge defaults with caller overrides to avoid duplicate kwargs.
        style_kwargs = {"textColor": C_TEXT, **kwargs}
        return ParagraphStyle(
            f"custom_{id(kwargs)}",
            parent=base,
            **style_kwargs,
        )

    h1 = style("Heading1", fontSize=22, textColor=C_CYAN,   spaceAfter=2,  leading=26)
    h2 = style("Heading2", fontSize=13, textColor=C_TEXT,   spaceAfter=4,  leading=17)
    h3 = style("Heading3", fontSize=10, textColor=C_MUTED,  spaceAfter=2,  leading=13)
    body_st = style("Normal", fontSize=9, textColor=C_TEXT,  leading=14, spaceAfter=3)
    muted_st = style("Normal", fontSize=8, textColor=C_MUTED, leading=12)
    label_st = style("Normal", fontSize=7.5, textColor=C_MUTED,
                     fontName="Helvetica-Bold", leading=11, spaceAfter=1)

    # ─────────────────────────────────────────────────────────────────────────
    # HEADER BLOCK
    # ─────────────────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("SpaceLens<font color='#818cf8'>AI</font>", h1),
        Paragraph(
            f"<font color='#8b98a9' size='8'>INTELLIGENCE REPORT</font><br/>"
            f"<font color='#8b98a9' size='7'>"
            f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC</font>",
            style("Normal", alignment=TA_CENTER, textColor=C_MUTED, fontSize=8, leading=12),
        ),
        Paragraph(
            f"<font color='#8b98a9' size='7'>User: {prediction.user.username}<br/>"
            f"Report ID: #{prediction.pk:05d}</font>",
            style("Normal", alignment=2, textColor=C_MUTED, fontSize=7.5, leading=12),
        ),
    ]]
    header_table = Table(header_data, colWidths=[60 * mm, None, 55 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND",  (0, 0), (-1, -1), C_SURFACE),
        ("ROWPADDING",  (0, 0), (-1, -1), 8),
        ("LINEBELOW",   (0, 0), (-1, 0), 0.5, C_CYAN),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6 * mm))

    # ─────────────────────────────────────────────────────────────────────────
    # IMAGE + TOP PREDICTION (side by side)
    # ─────────────────────────────────────────────────────────────────────────
    content_width = page_w - 2 * margin
    img_col_w = 70 * mm
    info_col_w = content_width - img_col_w - 6 * mm

    img_cell = _build_image_cell(prediction, img_col_w, styles)
    conf_colour = _confidence_colour(prediction.confidence)

    top3_rows = "".join(
        f"<font color='#8b98a9' size='8'>{cls}</font>"
        f"<font color='#38bdf8' size='8'> {prob:.1f}%</font><br/>"
        for cls, prob in prediction.top3
    )

    info_paras = [
        Paragraph("<font color='#8b98a9' size='7'>PREDICTED CLASS</font>", label_st),
        Paragraph(
            f"<font size='18' color='#38bdf8'><b>{prediction.predicted_class}</b></font>",
            style("Normal", fontSize=18, textColor=C_CYAN, leading=22, spaceAfter=4),
        ),
        Paragraph("<font color='#8b98a9' size='7'>CONFIDENCE SCORE</font>", label_st),
        Paragraph(
            f"<font size='20' color='{conf_colour.hexval()}'>"
            f"<b>{prediction.confidence:.1f}%</b></font>",
            style("Normal", fontSize=20, textColor=conf_colour, leading=24, spaceAfter=6),
        ),
        Paragraph("<font color='#8b98a9' size='7'>TOP 3 CANDIDATES</font>", label_st),
        Paragraph(top3_rows, style("Normal", fontSize=8, leading=13, textColor=C_TEXT)),
        Spacer(1, 3 * mm),
        Paragraph(
            f"<font color='#8b98a9' size='7'>ANALYSED ON</font><br/>"
            f"<font size='8'>{prediction.created_at.strftime('%B %d, %Y at %H:%M UTC')}</font>",
            muted_st,
        ),
    ]

    side_data = [[img_cell, info_paras]]
    side_table = Table(side_data, colWidths=[img_col_w, info_col_w])
    side_table.setStyle(TableStyle([
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (1, 0), (1, 0), 8),
        ("RIGHTPADDING", (0, 0), (0, 0), 4),
        ("BACKGROUND", (0, 0), (-1, -1), C_SURFACE2),
        ("ROWPADDING", (0, 0), (-1, -1), 10),
        ("BOX",        (0, 0), (-1, -1), 0.5, C_BORDER),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(side_table)
    story.append(Spacer(1, 6 * mm))

    # ─────────────────────────────────────────────────────────────────────────
    # IBM GRANITE AI REPORT
    # ─────────────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4))

    story.append(KeepTogether([
        Paragraph(
            "<font color='#818cf8'>■</font>  IBM Granite — AI Intelligence Report",
            h2,
        ),
        Paragraph(
            "Generated by IBM watsonx.ai Granite LLM based on model prediction results.",
            muted_st,
        ),
        Spacer(1, 3 * mm),
    ]))

    if prediction.granite_response:
        granite_text = prediction.granite_response.strip()
        # Split by double newline to preserve paragraph structure
        for block in granite_text.split("\n\n"):
            block = block.strip()
            if block:
                story.append(Paragraph(_wrap(block.replace("\n", " ")), body_st))
                story.append(Spacer(1, 2 * mm))
    else:
        story.append(Paragraph(
            "<i>Granite response not available for this prediction.</i>",
            muted_st,
        ))

    story.append(Spacer(1, 5 * mm))

    # ─────────────────────────────────────────────────────────────────────────
    # PROBABILITY TABLE
    # ─────────────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4))
    story.append(Paragraph(
        "<font color='#38bdf8'>■</font>  Full Probability Distribution",
        h2,
    ))
    story.append(Spacer(1, 2 * mm))

    sorted_probs = sorted(
        prediction.probabilities.items(), key=lambda x: x[1], reverse=True
    )
    prob_data = [["Land-Cover Class", "Confidence (%)", "Rank"]]
    for rank, (cls, prob) in enumerate(sorted_probs, start=1):
        row_colour = C_SURFACE if rank % 2 == 0 else C_SURFACE2
        prob_data.append([cls, f"{prob:.2f} %", f"#{rank}"])

    prob_table = Table(
        prob_data,
        colWidths=[content_width * 0.55, content_width * 0.28, content_width * 0.17],
    )
    prob_table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",  (0, 0), (-1, 0), C_BG),
        ("TEXTCOLOR",   (0, 0), (-1, 0), C_MUTED),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("LINEBELOW",   (0, 0), (-1, 0), 0.5, C_BORDER),
        # Data rows
        ("FONTSIZE",    (0, 1), (-1, -1), 8.5),
        ("TEXTCOLOR",   (0, 1), (0, -1),  C_TEXT),
        ("TEXTCOLOR",   (1, 1), (1, -1),  C_CYAN),
        ("TEXTCOLOR",   (2, 1), (2, -1),  C_MUTED),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_SURFACE2, C_SURFACE]),
        ("ROWPADDING",  (0, 0), (-1, -1), 5),
        ("GRID",        (0, 0), (-1, -1), 0.3, C_BORDER),
        # Highlight top row
        ("TEXTCOLOR",   (0, 1), (0, 1),  C_CYAN),
        ("FONTNAME",    (0, 1), (-1, 1), "Helvetica-Bold"),
    ]))
    story.append(prob_table)

    # ─────────────────────────────────────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "<font color='#4a5568' size='7'>"
        "SpaceLens AI · Powered by IBM watsonx.ai Granite &amp; TensorFlow · "
        "This report is AI-generated and intended for informational purposes only."
        "</font>",
        style("Normal", alignment=TA_CENTER, fontSize=7, textColor=C_MUTED),
    ))

    doc.build(story)
    return buffer.getvalue()


def _build_image_cell(prediction, width_pts: float, styles) -> list:
    """Return a list of flowables for the satellite image cell."""
    cell = []
    try:
        if prediction.image and os.path.exists(prediction.image.path):
            img = RLImage(prediction.image.path, width=width_pts, height=width_pts)
            cell.append(img)
        else:
            raise FileNotFoundError("Image not found on disk.")
    except Exception as exc:
        logger.warning("Could not embed image in PDF: %s", exc)
        cell.append(Paragraph(
            "<font color='#4a5568' size='8'>[Image unavailable]</font>",
            ParagraphStyle("ph", parent=styles["Normal"], textColor=C_MUTED, fontSize=8),
        ))
    cell.append(Spacer(1, 2 * mm))
    cell.append(Paragraph(
        f"<font color='#8b98a9' size='7'>{os.path.basename(prediction.image.name)}</font>",
        ParagraphStyle("fn", parent=styles["Normal"], textColor=C_MUTED,
                       fontSize=7, leading=9, alignment=TA_CENTER),
    ))
    return cell
