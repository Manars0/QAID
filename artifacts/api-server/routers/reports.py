"""
Report generation routes: Excel and PDF.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io

from services import analyzer
from services.report_generator import generate_excel_report, generate_pdf_report

router = APIRouter()


@router.get("/analysis/{session_id}/report/excel")
async def download_excel_report(session_id: str):
    """Generate and download an Excel report for the analysis session."""
    session = analyzer.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = session["result"]
    df = session["df"]

    excel_bytes = generate_excel_report(result, df)

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="QAID_Report_{session_id}.xlsx"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get("/analysis/{session_id}/report/pdf")
async def download_pdf_report(session_id: str):
    """Generate and download a PDF report for the analysis session."""
    session = analyzer.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = session["result"]

    pdf_bytes = generate_pdf_report(result)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="QAID_Report_{session_id}.pdf"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
