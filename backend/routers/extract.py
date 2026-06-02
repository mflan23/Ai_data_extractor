"""Extract router – runs AI-powered structured extraction on an existing job."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.schemas import ExtractRequest, ExtractResponse, JobStatus
from services.ai_service import extract_with_ai
from state import jobs

router = APIRouter(prefix="/api/jobs", tags=["extract"])


@router.get("/{job_id}", summary="Get job details and extracted records")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post(
    "/{job_id}/extract",
    response_model=ExtractResponse,
    summary="Run extraction on all parsed files",
)
def extract(job_id: str, body: ExtractRequest | None = None):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Optionally update the schema from the request body
    if body and body.extraction_schema:
        job.extraction_schema = body.extraction_schema

    if not job.extraction_schema.fields:
        raise HTTPException(
            status_code=422,
            detail="No schema defined. Please set a schema before extracting.",
        )

    job.status = JobStatus.EXTRACTING
    all_records: list[dict] = []

    for file in job.files:
        if not file.raw_text:
            continue
        try:
            records = extract_with_ai(
                raw_text=file.raw_text,
                schema=job.extraction_schema,
                filename=file.filename,
            )
            all_records.extend(records)
        except Exception as exc:  # noqa: BLE001
            file.error = str(exc)

    job.records = all_records
    job.status = JobStatus.DONE

    return ExtractResponse(
        job_id=job_id,
        records=all_records,
        total=len(all_records),
    )


@router.put("/{job_id}/schema", summary="Update the extraction schema for a job")
def update_schema(job_id: str, schema: dict):
    from models.schemas import ExtractionSchema, SchemaField

    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    fields = [SchemaField(**f) for f in schema.get("fields", [])]
    job.extraction_schema = ExtractionSchema(
        fields=fields,
        instructions=schema.get("instructions", ""),
    )
    return {"job_id": job_id, "extraction_schema": job.extraction_schema}


@router.patch("/{job_id}/records", summary="Update extracted records (manual edits)")
def update_records(job_id: str, records: list[dict]):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.records = records
    return {"job_id": job_id, "total": len(records)}
