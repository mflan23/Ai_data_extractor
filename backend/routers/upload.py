"""Upload router – handles multipart file uploads."""
from __future__ import annotations

import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from models.schemas import ExtractionJob, FileStatus, JobStatus, UploadedFile
from services.parser_service import SUPPORTED_EXTENSIONS, parse_file
from state import jobs

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("", summary="Upload one or more files and create an extraction job")
async def upload_files(files: list[UploadFile] = File(...)):
    job_id = str(uuid.uuid4())
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    uploaded: list[UploadedFile] = []

    for uf in files:
        suffix = Path(uf.filename or "").suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=415,
                detail=(
                    f"Unsupported file type '{suffix}'. "
                    f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
                ),
            )

        data = await uf.read()
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File '{uf.filename}' exceeds the 50 MB limit.",
            )

        file_id = str(uuid.uuid4())
        dest = job_dir / f"{file_id}{suffix}"
        async with aiofiles.open(dest, "wb") as f:
            await f.write(data)

        # Parse immediately (sync – fast for small files; use background task for large ones)
        try:
            raw_text = parse_file(uf.filename or "", data)
            status = FileStatus.DONE
            error = ""
        except (ValueError, IOError, RuntimeError, UnicodeDecodeError) as exc:
            raw_text = ""
            status = FileStatus.ERROR
            error = str(exc)

        uploaded.append(
            UploadedFile(
                file_id=file_id,
                filename=uf.filename or dest.name,
                content_type=uf.content_type or "application/octet-stream",
                size=len(data),
                status=status,
                raw_text=raw_text,
                error=error,
            )
        )

    job = ExtractionJob(job_id=job_id, status=JobStatus.CREATED, files=uploaded)
    jobs[job_id] = job

    return JSONResponse(
        status_code=201,
        content={
            "job_id": job_id,
            "files": [
                {
                    "file_id": f.file_id,
                    "filename": f.filename,
                    "size": f.size,
                    "status": f.status,
                }
                for f in uploaded
            ],
        },
    )
