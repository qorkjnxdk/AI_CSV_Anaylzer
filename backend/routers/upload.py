from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import json
import math

from session.session_store import create_session, get_session
from services.file_service import parse_file
from security.audit_logger import log_upload

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    x_session_id: Optional[str] = Header(None),
):
    # Create or retrieve session
    if x_session_id:
        session = get_session(x_session_id)
        if session is None:
            session_id = create_session()
            session = get_session(session_id)
        else:
            session_id = x_session_id
    else:
        session_id = create_session()
        session = get_session(session_id)

    results = []

    for upload_file in files:
        file_bytes = await upload_file.read()

        try:
            sheets = parse_file(file_bytes, upload_file.filename or "unknown")
        except ValueError as e:
            results.append({
                "filename": upload_file.filename,
                "success": False,
                "error": str(e),
            })
            continue

        session["files"][upload_file.filename] = sheets

        sheet_info = []
        for sheet_name, df in sheets.items():
            log_upload(session_id, upload_file.filename or "unknown", len(df))
            sheet_info.append({
                "sheet_name": sheet_name,
                "rows": len(df),
                "columns": df.columns.tolist(),
            })

        results.append({
            "filename": upload_file.filename,
            "success": True,
            "sheets": sheet_info,
        })

    return {"session_id": session_id, "files": results}


@router.get("/preview")
async def preview(
    filename: str,
    sheet: str = "Sheet1",
    n: int = 10,
    x_session_id: str = Header(...),
):
    session = get_session(x_session_id)
    if session is None:
        raise HTTPException(404, "Session not found")

    file_sheets = session["files"].get(filename)
    if file_sheets is None:
        raise HTTPException(404, f"File '{filename}' not found in session")

    df = file_sheets.get(sheet)
    if df is None:
        raise HTTPException(404, f"Sheet '{sheet}' not found in file '{filename}'")

    n = min(max(1, n), 500)
    rows = df.head(n).values.tolist()

    def sanitize(val):
        if val is None:
            return None
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
        return val

    clean_rows = [[sanitize(cell) for cell in row] for row in rows]

    return {
        "filename": filename,
        "sheet": sheet,
        "columns": df.columns.tolist(),
        "rows": clean_rows,
        "total_rows": len(df),
    }


@router.get("/files")
async def list_files(x_session_id: str = Header(...)):
    session = get_session(x_session_id)
    if session is None:
        raise HTTPException(404, "Session not found")

    result = []
    for filename, sheets in session["files"].items():
        result.append({
            "filename": filename,
            "sheets": list(sheets.keys()),
        })
    return {"files": result}
