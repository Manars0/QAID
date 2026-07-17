"""
Analysis routes: file upload, demo, entries, entry detail.
"""
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import List

from models.schemas import AnalysisResult, RiskEntry, EntryDetail
from services.file_processor import process_uploaded_file
from services.demo_data import DEMO_DATA_NOT_CONFIGURED
from services import analyzer

router = APIRouter()

# Demo files are loaded from backend/demo_data/ at the workspace root
_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DEMO_DATA_DIR = _WORKSPACE_ROOT / "backend" / "demo_data"

SUPPORTED_EXTENSIONS = {".xlsx", ".csv", ".zip"}


@router.post("/upload", response_model=AnalysisResult)
async def upload_file(file: UploadFile = File(...)):
    """Upload an ERP file (Excel, CSV, or ZIP) and run full analysis."""
    content = await file.read()
    filename = file.filename or "upload"

    try:
        df, file_label, fraud_labels = process_uploaded_file(content, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(df) == 0:
        raise HTTPException(status_code=400, detail="No data found in uploaded file")

    result = analyzer.run_analysis(df, file_label, fraud_labels=fraud_labels)
    return result


@router.post("/demo", response_model=AnalysisResult)
async def load_demo():
    """Load and analyze the demo file from backend/demo_data/."""
    demo_file: Path | None = None
    if DEMO_DATA_DIR.is_dir():
        for path in sorted(DEMO_DATA_DIR.iterdir()):
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                demo_file = path
                break

    if demo_file is None:
        raise HTTPException(status_code=503, detail=DEMO_DATA_NOT_CONFIGURED)

    content = demo_file.read_bytes()
    try:
        df, file_label, fraud_labels = process_uploaded_file(content, demo_file.name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if len(df) == 0:
        raise HTTPException(status_code=422, detail="Demo file contains no data")

    result = analyzer.run_analysis(df, file_label, fraud_labels=fraud_labels)
    return result


@router.get("/analysis/{session_id}/entries", response_model=List[RiskEntry])
async def get_analysis_entries(
    session_id: str,
    limit: int = Query(200, ge=1, le=5000),
    minRisk: float = Query(0, ge=0, le=100),
):
    """Get journal entries for a session, sorted by risk score descending."""
    entries = analyzer.get_entries_for_session(session_id, limit=limit, min_risk=minRisk)
    if entries is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return entries


@router.get("/analysis/{session_id}/entry/{entry_id}", response_model=EntryDetail)
async def get_entry_detail(session_id: str, entry_id: str):
    """Get detailed breakdown for a specific journal entry."""
    detail = analyzer.get_entry_detail_for_session(session_id, entry_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Entry or session not found")
    return detail
