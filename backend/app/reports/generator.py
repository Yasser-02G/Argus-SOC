import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

ACCENT = colors.HexColor("#0FA37A")
CRITICAL = colors.HexColor("#D63754")
WARNING = colors.HexColor("#B9760D")
INFO = colors.HexColor("#2F6FE0")
GREY = colors.HexColor("#5B6472")
LIGHT = colors.HexColor("#F1F3F6")

SEV_COLOR = {"critical": CRITICAL, "warning": WARNING, "info": INFO}
SEV_LABEL = {"critical": "Critique", "warning": "Attention", "info": "Info"}


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("ArgusTitle", parent=styles["Title"], textColor=colors.HexColor("#101826"), fontSize=22, spaceAfter=4))
    styles.add(ParagraphStyle("ArgusSubtitle", parent=styles["Normal"], textColor=GREY, fontSize=11, spaceAfter=18))
    styles.add(ParagraphStyle("ArgusH2", parent=styles["Heading2"], textColor=colors.HexColor("#101826"), fontSize=14, spaceBefore=14, spaceAfter=8))
    styles.add(ParagraphStyle("ArgusBody", parent=styles["Normal"], fontSize=9.5, leading=13))
    return styles


def _kpi_table(stats: dict, styles) -> Table:
    sev = {s["severity"]: s["count"] for s in stats["severity_counts"]}
    data = [
        ["Total événements", "Critiques", "Attention", "Info"],
        [
            str(stats["total_events_today"]),
            str(sev.get("critical", 0)),
            str(sev.get("warning", 0)),
            str(sev.get("info", 0)),
        ],
    ]
    t = Table(data, colWidths=[42 * mm] * 4)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("TEXTCOLOR", (0, 0), (-1, 0), GREY),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, 1), 16),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 1), (1, 1), CRITICAL),
        ("TEXTCOLOR", (2, 1), (2, 1), WARNING),
        ("TEXTCOLOR", (3, 1), (3, 1), INFO),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 1), (-1, 1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E5EA")),
    ]))
    return t


def _categories_table(stats: dict, styles) -> Table:
    rows = [["Catégorie", "Événements"]]
    for c in stats["top_categories"][:8]:
        rows.append([c["category"], str(c["count"])])
    if len(rows) == 1:
        rows.append(["—", "0"])
    t = Table(rows, colWidths=[100 * mm, 40 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E5EA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ]))
    return t


def _logs_table(logs: list[dict], styles) -> Table:
    header = ["Heure", "Source", "Sévérité", "Message"]
    rows = [header]
    for l in logs[:20]:
        ts = l["timestamp"]
        if isinstance(ts, datetime):
            ts = ts.strftime("%d/%m %H:%M")
        else:
            ts = str(ts)[:16].replace("T", " ")
        rows.append([
            ts, l["source_type"], SEV_LABEL.get(l["severity"], l["severity"]),
            Paragraph((l.get("message") or l.get("event_type") or "—")[:110], styles["ArgusBody"]),
        ])
    if len(rows) == 1:
        rows.append(["—", "—", "—", Paragraph("Aucun événement critique sur la période.", styles["ArgusBody"])])

    t = Table(rows, colWidths=[22 * mm, 25 * mm, 22 * mm, 91 * mm], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#101826")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E5EA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, row in enumerate(rows[1:], start=1):
        sev_color = SEV_COLOR.get(
            {v: k for k, v in SEV_LABEL.items()}.get(row[2], ""), GREY,
        )
        style.append(("TEXTCOLOR", (2, i), (2, i), sev_color))
        style.append(("FONTNAME", (2, i), (2, i), "Helvetica-Bold"))
    t.setStyle(TableStyle(style))
    return t


def _devices_table(devices: list[dict], styles) -> Table:
    rows = [["Équipement", "Statut", "Logs (période)"]]
    for d in devices[:15]:
        rows.append([d.get("name") or d.get("ip"), "En ligne" if d.get("status") == "online" else "Dégradé", str(d.get("logs_count", 0))])
    if len(rows) == 1:
        rows.append(["—", "—", "0"])
    t = Table(rows, colWidths=[80 * mm, 30 * mm, 30 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E5EA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ]))
    return t


def build_report_pdf(
    period_label: str,
    period_start: datetime,
    period_end: datetime,
    stats: dict,
    critical_logs: list[dict],
    devices: list[dict],
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
    )
    styles = _styles()
    story = []

    story.append(Paragraph("ARGUS — Rapport de sécurité", styles["ArgusTitle"]))
    story.append(Paragraph(
        f"{period_label} · {period_start.strftime('%d/%m/%Y %H:%M')} → {period_end.strftime('%d/%m/%Y %H:%M')} (UTC)",
        styles["ArgusSubtitle"],
    ))

    story.append(Paragraph("Vue d'ensemble", styles["ArgusH2"]))
    story.append(_kpi_table(stats, styles))

    story.append(Paragraph("Top catégories", styles["ArgusH2"]))
    story.append(_categories_table(stats, styles))

    story.append(Paragraph("Événements critiques", styles["ArgusH2"]))
    story.append(_logs_table(critical_logs, styles))

    story.append(PageBreak())
    story.append(Paragraph("Équipements surveillés", styles["ArgusH2"]))
    story.append(_devices_table(devices, styles))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"Généré automatiquement par ARGUS le {datetime.utcnow().strftime('%d/%m/%Y à %H:%M UTC')}.",
        styles["ArgusSubtitle"],
    ))

    doc.build(story)
    return buf.getvalue()
