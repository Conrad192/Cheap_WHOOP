# ============================================================================
# REPORTS - PDF export and professional reporting
# ============================================================================
# Generate downloadable monthly reports
# ============================================================================

import pandas as pd
from datetime import datetime, timedelta
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_monthly_report_data(history_df, user_profile):
    """
    Generate data for monthly report.

    Args:
        history_df: DataFrame with historical data
        user_profile: User profile dictionary

    Returns:
        Dictionary with report data
    """
    # Get last 30 days
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    month_data = history_df[history_df["date"] >= thirty_days_ago]

    if len(month_data) < 7:
        return None

    report_data = {
        "generated_date": datetime.now().strftime("%Y-%m-%d"),
        "period": f"{thirty_days_ago} to {datetime.now().date()}",
        "user": {
            "age": user_profile.get("age", "N/A"),
            "weight_kg": user_profile.get("weight_kg", "N/A"),
            "height_cm": user_profile.get("height_cm", "N/A")
        },
        "summary": {
            "days_tracked": len(month_data),
            "avg_recovery": round(month_data["recovery"].mean(), 1),
            "avg_strain": round(month_data["strain"].mean(), 1),
            "avg_hrv": round(month_data["hrv"].mean(), 1),
            "avg_rhr": round(month_data["rhr"].mean(), 1),
            "total_steps": int(month_data["steps"].sum()),
            "avg_steps": int(month_data["steps"].mean())
        },
        "best_day": {
            "date": str(month_data.loc[month_data["recovery"].idxmax(), "date"]),
            "recovery": int(month_data["recovery"].max())
        },
        "worst_day": {
            "date": str(month_data.loc[month_data["recovery"].idxmin(), "date"]),
            "recovery": int(month_data["recovery"].min())
        },
        "trends": {
            "recovery_trend": "improving" if month_data["recovery"].diff().mean() > 0 else "stable/declining",
            "hrv_trend": "improving" if month_data["hrv"].diff().mean() > 0 else "stable/declining"
        }
    }

    return report_data


def generate_pdf_report(history_df, user_profile, output_path="data/monthly_report.pdf"):
    """
    Generate a professional PDF report.

    Args:
        history_df: DataFrame with historical data
        user_profile: User profile dictionary
        output_path: Where to save the PDF

    Returns:
        Success status and file path
    """
    if not REPORTLAB_AVAILABLE:
        return {
            "success": False,
            "error": "reportlab not installed. Run: pip install reportlab",
            "path": None
        }

    report_data = generate_monthly_report_data(history_df, user_profile)

    if not report_data:
        return {
            "success": False,
            "error": "Not enough data (need 7+ days)",
            "path": None
        }

    # Create PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2E86AB')
    )

    # Title
    title = Paragraph("Cheap WHOOP - Monthly Performance Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))

    # Report info
    info_text = f"""
    <b>Report Period:</b> {report_data['period']}<br/>
    <b>Generated:</b> {report_data['generated_date']}<br/>
    <b>Days Tracked:</b> {report_data['summary']['days_tracked']}
    """
    elements.append(Paragraph(info_text, styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    # Summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Average Recovery', f"{report_data['summary']['avg_recovery']}%"],
        ['Average Strain', f"{report_data['summary']['avg_strain']}/21"],
        ['Average HRV', f"{report_data['summary']['avg_hrv']} ms"],
        ['Average RHR', f"{report_data['summary']['avg_rhr']} BPM"],
        ['Total Steps', f"{report_data['summary']['total_steps']:,}"],
        ['Average Steps/Day', f"{report_data['summary']['avg_steps']:,}"]
    ]

    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Best and worst days
    highlights_text = f"""
    <b>Best Day:</b> {report_data['best_day']['date']} (Recovery: {report_data['best_day']['recovery']}%)<br/>
    <b>Worst Day:</b> {report_data['worst_day']['date']} (Recovery: {report_data['worst_day']['recovery']}%)
    """
    elements.append(Paragraph(highlights_text, styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    # Trends
    trends_text = f"""
    <b>Trends:</b><br/>
    • Recovery: {report_data['trends']['recovery_trend']}<br/>
    • HRV: {report_data['trends']['hrv_trend']}
    """
    elements.append(Paragraph(trends_text, styles['Normal']))

    # Build PDF
    doc.build(elements)

    return {
        "success": True,
        "error": None,
        "path": output_path
    }


def export_csv(history_df, output_path="data/history_export.csv"):
    """
    Export history to CSV for external analysis.

    Args:
        history_df: DataFrame with historical data
        output_path: Where to save the CSV

    Returns:
        Success status and file path
    """
    try:
        history_df.to_csv(output_path, index=False)
        return {
            "success": True,
            "path": output_path,
            "rows": len(history_df)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
