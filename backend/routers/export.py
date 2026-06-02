"""Export router – converts extracted records to downloadable files."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from services.export_service import EXPORT_FORMATS, export
from state import jobs

router = APIRouter(prefix="/api/jobs", tags=["export"])


@router.get(
    "/{job_id}/export/{fmt}",
    summary="Download extracted records in the specified format",
)
def export_records(job_id: str, fmt: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.records:
        raise HTTPException(status_code=422, detail="No records to export. Run extraction first.")

    if fmt.lower() not in EXPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{fmt}'. Supported: {', '.join(EXPORT_FORMATS)}",
        )

    try:
        data, media_type, filename = export(job.records, fmt)
    except (ImportError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
