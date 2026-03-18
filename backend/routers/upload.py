from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import json
import math

from security.rate_limiter import limiter
from session.session_store import create_session, get_session
from services.file_service import parse_file
from security.audit_logger import log_upload

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    x_session_id: Optional[str] = Header(None),
):
    limiter.check(key=f"upload:{x_session_id or 'anonymous'}", max_requests=4, window_seconds=60)
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


@router.get("/suggestions")
async def get_suggestions(
    filename: str,
    sheet: str = "Sheet1",
    x_session_id: str = Header(...),
):
    """Generate suggested prompts using the LLM based on the dataset's schema."""
    session = get_session(x_session_id)
    if session is None:
        raise HTTPException(404, "Session not found")

    file_sheets = session["files"].get(filename)
    if file_sheets is None:
        raise HTTPException(404, f"File '{filename}' not found")

    df = file_sheets.get(sheet)
    if df is None:
        raise HTTPException(404, f"Sheet '{sheet}' not found")

    import os
    import httpx

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

    col_info = []
    for col in df.columns:
        col_info.append(f"  - {col} ({df[col].dtype})")

    sample = df.head(3).to_string(index=False)

    prompt = (
        f"You are given a dataset with the following metadata:\n"
        f"- Filename: {filename}\n"
        f"- Shape: {df.shape[0]} rows x {df.shape[1]} columns\n"
        f"- Columns:\n" + "\n".join(col_info) + "\n\n"
        f"Sample rows:\n{sample}\n\n"
        f"Generate exactly 3 diverse, useful natural language prompts that a user might ask about this data. "
        f"Include a mix of: summary questions, filtering/counting, comparisons across categories, "
        f"and at least one that asks for a chart/visualization.\n\n"
        f"Return ONLY a JSON array of strings, e.g. [\"prompt1\", \"prompt2\", ...]. No other text."
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 512,
                },
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"].strip()
        # Strip markdown fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        import json as json_mod
        suggestions = json_mod.loads(content)
        if isinstance(suggestions, list):
            return {"suggestions": [s for s in suggestions if isinstance(s, str)][:3]}
    except Exception:
        pass

    # Fallback: basic deterministic suggestions
    return {"suggestions": [
        "Give me a summary of this dataset",
        f"How many rows are in this dataset?",
        f"Show the first 10 rows sorted by {df.columns[0]}",
    ]}
