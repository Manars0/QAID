"""
Generate downloadable reports: Excel and PDF.
"""
import io
from datetime import datetime
import pandas as pd
from models.schemas import AnalysisResult


def generate_excel_report(result: AnalysisResult, df: pd.DataFrame) -> bytes:
    """Generate a comprehensive Excel report."""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        # Formats
        title_fmt = workbook.add_format({"bold": True, "font_size": 14, "font_color": "#1e40af", "bg_color": "#eff6ff"})
        header_fmt = workbook.add_format({"bold": True, "bg_color": "#1e40af", "font_color": "#ffffff", "border": 1})
        kpi_label_fmt = workbook.add_format({"bold": True, "font_size": 11, "bg_color": "#f0f9ff"})
        kpi_value_fmt = workbook.add_format({"bold": True, "font_size": 14, "font_color": "#1d4ed8"})
        critical_fmt = workbook.add_format({"bg_color": "#fef2f2", "font_color": "#dc2626"})
        high_fmt = workbook.add_format({"bg_color": "#fff7ed", "font_color": "#c2410c"})
        medium_fmt = workbook.add_format({"bg_color": "#fefce8", "font_color": "#a16207"})
        low_fmt = workbook.add_format({"bg_color": "#f0fdf4", "font_color": "#15803d"})
        compliant_fmt = workbook.add_format({"bg_color": "#f0fdf4", "font_color": "#15803d"})
        noncompliant_fmt = workbook.add_format({"bg_color": "#fef2f2", "font_color": "#dc2626"})
        warning_fmt = workbook.add_format({"bg_color": "#fefce8", "font_color": "#a16207"})
        num_fmt = workbook.add_format({"num_format": "#,##0.00"})
        pct_fmt = workbook.add_format({"num_format": "0.00%"})

        def get_risk_fmt(level):
            return {"CRITICAL": critical_fmt, "HIGH": high_fmt, "MEDIUM": medium_fmt}.get(level, low_fmt)

        # === Sheet 1: Executive Summary ===
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
            ("AI Confidence", f"{result.kpi_summary.ai_confidence:.1f}%"),
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

        # === Sheet 2: Risk Distribution ===
        risk_data = [{"Risk Level": r.level, "Count": r.count, "Percentage": r.percentage / 100} for r in result.risk_distribution]
        risk_df = pd.DataFrame(risk_data)
        risk_df.to_excel(writer, sheet_name="Risk Distribution", index=False)
        ws2 = writer.sheets["Risk Distribution"]
        ws2.set_column("A:A", 15)
        ws2.set_column("B:C", 15)

        # === Sheet 3: High Risk Entries ===
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
                fmt = get_risk_fmt(entry.risk_level)
                ws3.set_row(i, None, fmt)

        # === Sheet 4: High Risk Accounts ===
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

        # === Sheet 5: IFRS Compliance ===
        compliance_data = [
            {
                "IFRS Standard": c.standard,
                "Requirement": c.requirement,
                "Status": c.status,
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
        ws5.set_column("C:C", 15)
        ws5.set_column("D:D", 12)
        ws5.set_column("E:E", 60)
        for i, item in enumerate(result.compliance_items, start=1):
            fmt = compliant_fmt if item.status == "COMPLIANT" else (noncompliant_fmt if item.status == "NON_COMPLIANT" else warning_fmt)
            ws5.set_row(i, None, fmt)

        # === Sheet 6: Fraud Indicators ===
        fi_data = [
            {
                "Indicator": f.name,
                "Severity": f.severity,
                "Count": f.count,
                "Description": f.description,
            }
            for f in result.fraud_indicators
        ]
        fi_df = pd.DataFrame(fi_data)
        fi_df.to_excel(writer, sheet_name="Fraud Indicators", index=False)
        ws6 = writer.sheets["Fraud Indicators"]
        ws6.set_column("A:A", 30)
        ws6.set_column("B:B", 12)
        ws6.set_column("C:C", 10)
        ws6.set_column("D:D", 60)

        # === Sheet 7: Validation Issues ===
        if result.validation_issues:
            val_data = [
                {
                    "Type": v.type,
                    "Severity": v.severity,
                    "Count": v.count,
                    "Description": v.description,
                }
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
    """Generate a PDF executive summary report using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4,
        rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    brand_blue = colors.HexColor("#1e40af")
    brand_dark = colors.HexColor("#1e293b")
    risk_colors = {
        "LOW": colors.HexColor("#15803d"),
        "MEDIUM": colors.HexColor("#a16207"),
        "HIGH": colors.HexColor("#c2410c"),
        "CRITICAL": colors.HexColor("#dc2626"),
    }

    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=20, textColor=brand_blue, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle("subtitle", parent=styles["Normal"], fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
    h2_style = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, textColor=brand_blue)
    body_style = ParagraphStyle("body", parent=styles["Normal"], fontSize=9, leading=14)

    story = []

    # Title
    story.append(Paragraph("QAID Financial Risk & Compliance Report", title_style))
    story.append(Paragraph(f"Session: {result.session_id} | File: {result.file_name}", subtitle_style))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=brand_blue))
    story.append(Spacer(1, 5 * mm))

    # KPI Table
    story.append(Paragraph("Executive KPIs", h2_style))
    kpi = result.kpi_summary
    risk_color = risk_colors.get(kpi.risk_level, brand_dark)
    kpi_data = [
        ["Metric", "Value"],
        ["Overall Risk Score", f"{kpi.overall_risk_score:.1f} / 100"],
        ["Risk Level", kpi.risk_level],
        ["Total Entries Analyzed", f"{kpi.total_entries:,}"],
        ["Flagged Accounts", f"{kpi.flagged_accounts:,}"],
        ["Suspicious Transactions", f"{kpi.suspicious_transactions:,}"],
        ["IFRS Compliance", f"{kpi.compliance_percentage:.1f}%"],
        ["AI Confidence", f"{kpi.ai_confidence:.1f}%"],
    ]
    kpi_table = Table(kpi_data, colWidths=[90 * mm, 70 * mm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), brand_blue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("FONTNAME", (0, 2), (0, 2), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 2), (1, 2), risk_color),
        ("FONTNAME", (1, 2), (1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (1, 2), (1, 2), 12),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 5 * mm))

    # AI Summary
    story.append(Paragraph("AI Executive Summary", h2_style))
    story.append(Paragraph(result.ai_summary, body_style))
    story.append(Spacer(1, 5 * mm))

    # Fraud Indicators
    if result.fraud_indicators:
        story.append(Paragraph("Fraud Indicators Detected", h2_style))
        fi_data = [["Indicator", "Severity", "Count"]]
        for fi in result.fraud_indicators:
            fi_data.append([fi.name, fi.severity, str(fi.count)])
        fi_table = Table(fi_data, colWidths=[100 * mm, 35 * mm, 25 * mm])
        fi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), brand_blue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fff7ed"), colors.white]),
        ]))
        story.append(fi_table)
        story.append(Spacer(1, 5 * mm))

    # Compliance
    story.append(Paragraph("IFRS Compliance Summary", h2_style))
    comp_data = [["Standard", "Status", "Score"]]
    for c in result.compliance_items:
        comp_data.append([c.standard, c.status, f"{c.score:.1f}%"])
    comp_table = Table(comp_data, colWidths=[35 * mm, 50 * mm, 25 * mm])
    comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), brand_blue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0fdf4"), colors.white]),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 5 * mm))

    # Recommendations
    story.append(Paragraph("Recommendations", h2_style))
    for i, rec in enumerate(result.recommendations, 1):
        story.append(Paragraph(f"{i}. {rec}", body_style))
    story.append(Spacer(1, 3 * mm))

    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Paragraph("This report was generated by QAID — AI-powered Financial Risk & Compliance Platform.", subtitle_style))

    doc.build(story)
    return output.getvalue()
