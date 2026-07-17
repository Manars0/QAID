"""
Generate downloadable reports: Excel and PDF.
"""
import io
from datetime import datetime
import pandas as pd
from models.schemas import AnalysisResult


# ─── Brand palette ────────────────────────────────────────────────────────────
BRAND_TEAL     = "#0F766E"
BRAND_TEAL_LT  = "#0F9D94"
BRAND_DARK     = "#111827"
BRAND_BG       = "#F8FAFC"
BRAND_WHITE    = "#FFFFFF"
BRAND_BORDER   = "#E2E8F0"
BRAND_SUCCESS  = "#10B981"
BRAND_WARNING  = "#F59E0B"
BRAND_DANGER   = "#EF4444"
BRAND_ORANGE   = "#F97316"

RISK_COLORS_HEX = {
    "LOW":      BRAND_SUCCESS,
    "MEDIUM":   BRAND_WARNING,
    "HIGH":     BRAND_ORANGE,
    "CRITICAL": BRAND_DANGER,
}

def _compliance_label(status: str, score: float) -> str:
    """Map backend compliance status → human-readable label."""
    if status == "COMPLIANT":
        return "Compliant"
    if status == "WARNING" or (status == "NON_COMPLIANT" and score >= 97):
        return "Needs Review"
    if status == "NON_COMPLIANT" and score >= 90:
        return "Potential Issue"
    return "High Risk"

def _compliance_color_hex(status: str, score: float) -> str:
    label = _compliance_label(status, score)
    return {
        "Compliant":        BRAND_SUCCESS,
        "Needs Review":     BRAND_WARNING,
        "Potential Issue":  BRAND_ORANGE,
        "High Risk":        BRAND_DANGER,
    }.get(label, BRAND_WARNING)


def generate_excel_report(result: AnalysisResult, df: pd.DataFrame) -> bytes:
    """Generate a comprehensive Excel report with QAID teal branding."""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        # ── Formats ────────────────────────────────────────────────────────
        title_fmt       = workbook.add_format({"bold": True, "font_size": 14, "font_color": BRAND_TEAL,   "bg_color": "#F0FDFA"})
        header_fmt      = workbook.add_format({"bold": True, "bg_color": BRAND_TEAL,  "font_color": BRAND_WHITE, "border": 1})
        kpi_label_fmt   = workbook.add_format({"bold": True, "font_size": 11, "bg_color": "#F0FDFA"})
        kpi_value_fmt   = workbook.add_format({"bold": True, "font_size": 14, "font_color": BRAND_TEAL})
        critical_fmt    = workbook.add_format({"bg_color": "#FEF2F2", "font_color": "#DC2626"})
        high_fmt        = workbook.add_format({"bg_color": "#FFF7ED", "font_color": "#C2410C"})
        medium_fmt      = workbook.add_format({"bg_color": "#FEFCE8", "font_color": "#A16207"})
        low_fmt         = workbook.add_format({"bg_color": "#F0FDF4", "font_color": "#15803D"})
        compliant_fmt   = workbook.add_format({"bg_color": "#F0FDF4", "font_color": "#15803D"})
        review_fmt      = workbook.add_format({"bg_color": "#FEFCE8", "font_color": "#A16207"})
        issue_fmt       = workbook.add_format({"bg_color": "#FFF7ED", "font_color": "#C2410C"})
        risk_fmt        = workbook.add_format({"bg_color": "#FEF2F2", "font_color": "#DC2626"})
        num_fmt         = workbook.add_format({"num_format": "#,##0.00"})

        def get_risk_fmt(level):
            return {"CRITICAL": critical_fmt, "HIGH": high_fmt, "MEDIUM": medium_fmt}.get(level, low_fmt)

        def get_compliance_fmt(status, score):
            label = _compliance_label(status, score)
            return {
                "Compliant":        compliant_fmt,
                "Needs Review":     review_fmt,
                "Potential Issue":  issue_fmt,
                "High Risk":        risk_fmt,
            }.get(label, review_fmt)

        # ── Sheet 1: Executive Summary ──────────────────────────────────────
        ws = workbook.add_worksheet("Executive Summary")
        ws.set_column("A:A", 30)
        ws.set_column("B:B", 25)
        ws.set_column("C:C", 50)

        ws.write("A1", "QAID — AI Financial Risk & Compliance Report", title_fmt)
        ws.write("A2", f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        ws.write("A3", f"File Analyzed: {result.file_name}")
        ws.write("A4", f"Session ID: {result.session_id}")
        ws.write("A5", f"Total Entries Analyzed: {result.total_entries_analyzed:,}")

        ws.write("A7", "KEY PERFORMANCE INDICATORS", title_fmt)
        row = 8
        kpis = [
            ("Overall Risk Score", f"{result.kpi_summary.overall_risk_score:.1f} / 100"),
            ("Risk Level", result.kpi_summary.risk_level),
            ("Total Journal Entries", f"{result.kpi_summary.total_entries:,}"),
            ("Flagged Accounts", f"{result.kpi_summary.flagged_accounts:,}"),
            ("Suspicious Transactions", f"{result.kpi_summary.suspicious_transactions:,}"),
            ("IFRS Compliance %", f"{result.kpi_summary.compliance_percentage:.1f}%"),
        ]
        for label, value in kpis:
            ws.write(row, 0, label, kpi_label_fmt)
            ws.write(row, 1, value, kpi_value_fmt)
            row += 1

        row += 1
        ws.write(row, 0, "AI EXECUTIVE SUMMARY", title_fmt)
        row += 1
        ws.write(row, 0, result.ai_summary)
        ws.set_row(row, 60)

        row += 2
        ws.write(row, 0, "RECOMMENDATIONS", title_fmt)
        row += 1
        for rec in result.recommendations:
            ws.write(row, 0, f"• {rec}")
            row += 1

        # ── Sheet 2: Risk Distribution ──────────────────────────────────────
        risk_data = [{"Risk Level": r.level, "Count": r.count, "Percentage": r.percentage / 100} for r in result.risk_distribution]
        risk_df = pd.DataFrame(risk_data)
        risk_df.to_excel(writer, sheet_name="Risk Distribution", index=False)
        ws2 = writer.sheets["Risk Distribution"]
        ws2.set_column("A:A", 15)
        ws2.set_column("B:C", 15)

        # ── Sheet 3: High Risk Entries ──────────────────────────────────────
        if result.high_risk_entries:
            entries_data = [
                {
                    "Entry ID": e.entry_id,
                    "Account": e.account,
                    "Account Name": e.account_name or "",
                    "Date": e.date,
                    "Amount": e.amount,
                    "Debit": e.debit,
                    "Credit": e.credit,
                    "Risk Score": e.risk_score,
                    "Fraud Probability": e.fraud_probability,
                    "Risk Level": e.risk_level,
                    "ML Score": e.ml_score,
                    "Rule Score": e.rule_score,
                    "Triggered Rules": "; ".join(e.triggered_rules),
                    "User": e.user or "",
                }
                for e in result.high_risk_entries
            ]
            entries_df = pd.DataFrame(entries_data)
            entries_df.to_excel(writer, sheet_name="High Risk Entries", index=False)
            ws3 = writer.sheets["High Risk Entries"]
            ws3.set_column("A:A", 12)
            ws3.set_column("B:C", 12)
            ws3.set_column("D:D", 12)
            ws3.set_column("E:G", 14)
            ws3.set_column("H:L", 14)
            ws3.set_column("M:M", 50)
            for i, entry in enumerate(result.high_risk_entries, start=1):
                ws3.set_row(i, None, get_risk_fmt(entry.risk_level))

        # ── Sheet 4: High Risk Accounts ─────────────────────────────────────
        if result.high_risk_accounts:
            accts_data = [
                {
                    "Account Code": a.account_code,
                    "Account Name": a.account_name,
                    "Total Entries": a.total_entries,
                    "Avg Risk Score": a.avg_risk_score,
                    "Risk Level": a.risk_level,
                    "Total Amount": a.total_amount,
                    "Max Single Amount": a.max_single_amount,
                }
                for a in result.high_risk_accounts
            ]
            accts_df = pd.DataFrame(accts_data)
            accts_df.to_excel(writer, sheet_name="High Risk Accounts", index=False)
            ws4 = writer.sheets["High Risk Accounts"]
            ws4.set_column("A:B", 20)
            ws4.set_column("C:G", 18)

        # ── Sheet 5: IFRS Compliance ────────────────────────────────────────
        compliance_data = [
            {
                "IFRS Standard": c.standard,
                "Requirement": c.requirement,
                "Status": _compliance_label(c.status, c.score),
                "Score (%)": c.score,
                "Details": c.details,
            }
            for c in result.compliance_items
        ]
        comp_df = pd.DataFrame(compliance_data)
        comp_df.to_excel(writer, sheet_name="IFRS Compliance", index=False)
        ws5 = writer.sheets["IFRS Compliance"]
        ws5.set_column("A:A", 15)
        ws5.set_column("B:B", 50)
        ws5.set_column("C:C", 18)
        ws5.set_column("D:D", 12)
        ws5.set_column("E:E", 60)
        for i, item in enumerate(result.compliance_items, start=1):
            ws5.set_row(i, None, get_compliance_fmt(item.status, item.score))

        # ── Sheet 6: Fraud Indicators ───────────────────────────────────────
        fi_data = [
            {"Indicator": f.name, "Severity": f.severity, "Count": f.count, "Description": f.description}
            for f in result.fraud_indicators
        ]
        fi_df = pd.DataFrame(fi_data)
        fi_df.to_excel(writer, sheet_name="Fraud Indicators", index=False)
        ws6 = writer.sheets["Fraud Indicators"]
        ws6.set_column("A:A", 30)
        ws6.set_column("B:B", 12)
        ws6.set_column("C:C", 10)
        ws6.set_column("D:D", 60)

        # ── Sheet 7: Validation Issues ──────────────────────────────────────
        if result.validation_issues:
            val_data = [
                {"Type": v.type, "Severity": v.severity, "Count": v.count, "Description": v.description}
                for v in result.validation_issues
            ]
            val_df = pd.DataFrame(val_data)
            val_df.to_excel(writer, sheet_name="Validation Issues", index=False)
            ws7 = writer.sheets["Validation Issues"]
            ws7.set_column("A:A", 25)
            ws7.set_column("B:B", 12)
            ws7.set_column("C:C", 10)
            ws7.set_column("D:D", 60)

    return output.getvalue()


def generate_pdf_report(result: AnalysisResult) -> bytes:
    """Generate a PDF executive report with QAID teal branding."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4,
        rightMargin=22 * mm, leftMargin=22 * mm,
        topMargin=22 * mm, bottomMargin=22 * mm,
    )

    styles = getSampleStyleSheet()

    # ── Colours ───────────────────────────────────────────────────────────
    c_teal    = colors.HexColor(BRAND_TEAL)
    c_teal_lt = colors.HexColor(BRAND_TEAL_LT)
    c_dark    = colors.HexColor(BRAND_DARK)
    c_bg      = colors.HexColor(BRAND_BG)
    c_border  = colors.HexColor(BRAND_BORDER)
    c_success = colors.HexColor(BRAND_SUCCESS)
    c_warning = colors.HexColor(BRAND_WARNING)
    c_danger  = colors.HexColor(BRAND_DANGER)
    c_orange  = colors.HexColor(BRAND_ORANGE)

    risk_colors_rl = {
        "LOW":      c_success,
        "MEDIUM":   c_warning,
        "HIGH":     c_orange,
        "CRITICAL": c_danger,
    }

    compliance_colors_rl = {
        "Compliant":       c_success,
        "Needs Review":    c_warning,
        "Potential Issue": c_orange,
        "High Risk":       c_danger,
    }

    # ── Typography ────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "qaid_title", parent=styles["Title"],
        fontSize=22, textColor=c_dark,
        alignment=TA_CENTER, spaceAfter=2,
    )
    brand_style = ParagraphStyle(
        "qaid_brand", parent=styles["Normal"],
        fontSize=13, textColor=c_teal,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "qaid_subtitle", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#64748B"),
        alignment=TA_CENTER,
    )
    h2_style = ParagraphStyle(
        "qaid_h2", parent=styles["Heading2"],
        fontSize=12, textColor=c_teal,
        fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "qaid_body", parent=styles["Normal"],
        fontSize=9, leading=14, textColor=c_dark,
    )
    small_style = ParagraphStyle(
        "qaid_small", parent=styles["Normal"],
        fontSize=8, leading=12, textColor=colors.HexColor("#64748B"),
    )
    footer_style = ParagraphStyle(
        "qaid_footer", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#94A3B8"),
        alignment=TA_CENTER,
    )

    story = []
    page_w = A4[0] - 44 * mm  # usable width

    # ── Header block ──────────────────────────────────────────────────────
    story.append(Paragraph("QAID · قيد", brand_style))
    story.append(Spacer(1, 1 * mm))
    story.append(Paragraph("Financial Risk & IFRS Compliance Report", title_style))
    story.append(Spacer(1, 1 * mm))
    story.append(Paragraph(
        f"Session: {result.session_id} &nbsp;|&nbsp; File: {result.file_name}",
        subtitle_style,
    ))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        subtitle_style,
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(width="100%", thickness=2, color=c_teal, spaceAfter=6))

    # ── KPI summary table ─────────────────────────────────────────────────
    kpi = result.kpi_summary
    risk_color = risk_colors_rl.get(kpi.risk_level, c_success)
    story.append(Paragraph("Executive KPIs", h2_style))

    kpi_data = [
        ["Metric", "Value"],
        ["Overall Risk Score", f"{kpi.overall_risk_score:.1f} / 100"],
        ["Risk Level", kpi.risk_level],
        ["Entries Analyzed", f"{kpi.total_entries:,}"],
        ["Flagged Accounts", f"{kpi.flagged_accounts:,}"],
        ["Suspicious Transactions", f"{kpi.suspicious_transactions:,}"],
        ["IFRS Compliance Rate", f"{kpi.compliance_percentage:.1f}%"],
    ]
    kpi_table = Table(kpi_data, colWidths=[page_w * 0.55, page_w * 0.45])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), c_teal),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F0FDFA"), colors.white]),
        ("GRID",         (0, 0), (-1, -1), 0.4, c_border),
        ("ALIGN",        (1, 0), (1, -1), "CENTER"),
        ("FONTNAME",     (0, 2), (0, 2), "Helvetica-Bold"),
        ("TEXTCOLOR",    (1, 2), (1, 2), risk_color),
        ("FONTNAME",     (1, 2), (1, 2), "Helvetica-Bold"),
        ("FONTSIZE",     (1, 2), (1, 2), 11),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 5 * mm))

    # ── AI Summary ────────────────────────────────────────────────────────
    story.append(Paragraph("AI Executive Summary", h2_style))
    story.append(Paragraph(result.ai_summary, body_style))
    story.append(Spacer(1, 5 * mm))

    # ── Recommended Actions ───────────────────────────────────────────────
    if result.recommendations:
        story.append(Paragraph("Recommended Actions", h2_style))
        for i, rec in enumerate(result.recommendations, 1):
            story.append(Paragraph(f"{i}.&nbsp;&nbsp;{rec}", body_style))
            story.append(Spacer(1, 1 * mm))
        story.append(Spacer(1, 3 * mm))

    # ── Fraud Indicators ──────────────────────────────────────────────────
    if result.fraud_indicators:
        story.append(Paragraph("Fraud Indicators Detected", h2_style))
        fi_data = [["Indicator", "Severity", "Count"]]
        for fi in result.fraud_indicators:
            fi_data.append([fi.name, fi.severity, str(fi.count)])
        fi_table = Table(fi_data, colWidths=[page_w * 0.58, page_w * 0.22, page_w * 0.20])
        fi_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), c_teal),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 8),
            ("GRID",         (0, 0), (-1, -1), 0.4, c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFBEB"), colors.white]),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ]))
        story.append(fi_table)
        story.append(Spacer(1, 5 * mm))

    # ── IFRS Compliance ───────────────────────────────────────────────────
    story.append(Paragraph("IFRS Compliance Summary", h2_style))
    comp_data = [["Standard", "Status", "Score", "Details"]]
    for c in result.compliance_items:
        label = _compliance_label(c.status, c.score)
        comp_data.append([c.standard, label, f"{c.score:.1f}%", c.requirement[:80] + "…" if len(c.requirement) > 80 else c.requirement])

    comp_table = Table(
        comp_data,
        colWidths=[page_w * 0.13, page_w * 0.18, page_w * 0.11, page_w * 0.58],
    )
    # Build row-level colour commands
    row_styles = [
        ("BACKGROUND",   (0, 0), (-1, 0), c_teal),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("GRID",         (0, 0), (-1, -1), 0.4, c_border),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
    ]
    for row_i, item in enumerate(result.compliance_items, start=1):
        label = _compliance_label(item.status, item.score)
        txt_color = compliance_colors_rl.get(label, c_warning)
        row_styles.append(("TEXTCOLOR", (1, row_i), (1, row_i), txt_color))
        row_styles.append(("FONTNAME",  (1, row_i), (1, row_i), "Helvetica-Bold"))
        bg = colors.HexColor("#F0FDF4") if label == "Compliant" else colors.HexColor("#FFFBEB") if label == "Needs Review" else colors.HexColor("#FFF7ED") if label == "Potential Issue" else colors.HexColor("#FEF2F2")
        row_styles.append(("BACKGROUND", (0, row_i), (-1, row_i), bg))

    comp_table.setStyle(TableStyle(row_styles))
    story.append(comp_table)
    story.append(Spacer(1, 5 * mm))

    # ── High-risk accounts (top 10) ────────────────────────────────────────
    if result.high_risk_accounts:
        story.append(Paragraph("Top Risk Accounts", h2_style))
        top_accts = sorted(result.high_risk_accounts, key=lambda x: x.avg_risk_score, reverse=True)[:10]
        acct_data = [["Account Code", "Account Name", "Avg Risk", "Level", "Total Amount"]]
        for a in top_accts:
            acct_data.append([
                a.account_code,
                (a.account_name or "")[:28],
                f"{a.avg_risk_score:.1f}",
                a.risk_level,
                f"${a.total_amount:,.0f}",
            ])
        acct_table = Table(
            acct_data,
            colWidths=[page_w*0.17, page_w*0.28, page_w*0.13, page_w*0.14, page_w*0.28],
        )
        acct_styles = [
            ("BACKGROUND",   (0, 0), (-1, 0), c_teal),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 8),
            ("GRID",         (0, 0), (-1, -1), 0.4, c_border),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.HexColor(BRAND_BG), colors.white]),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ]
        for row_i, a in enumerate(top_accts, start=1):
            acct_styles.append(("TEXTCOLOR", (3, row_i), (3, row_i), risk_colors_rl.get(a.risk_level, c_success)))
            acct_styles.append(("FONTNAME",  (3, row_i), (3, row_i), "Helvetica-Bold"))
        acct_table.setStyle(TableStyle(acct_styles))
        story.append(acct_table)
        story.append(Spacer(1, 5 * mm))

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=c_border))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "Generated by <b>QAID · قيد</b> — AI-powered Financial Risk & IFRS Compliance Platform.",
        footer_style,
    ))

    doc.build(story)
    return output.getvalue()
