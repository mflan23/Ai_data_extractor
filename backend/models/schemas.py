"""Pydantic models / schemas for the AI Data Extractor API."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schema / field definitions
# ---------------------------------------------------------------------------

class FieldType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    LIST = "list"


class SchemaField(BaseModel):
    name: str = Field(..., description="Column name")
    type: FieldType = Field(FieldType.STRING, description="Data type")
    description: str = Field("", description="Optional field description")
    required: bool = Field(False, description="Whether this field is required")


class ExtractionSchema(BaseModel):
    fields: list[SchemaField] = Field(default_factory=list)
    instructions: str = Field(
        "",
        description="Additional extraction instructions for the AI",
    )


# ---------------------------------------------------------------------------
# Job / file models
# ---------------------------------------------------------------------------

class FileStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class UploadedFile(BaseModel):
    file_id: str
    filename: str
    content_type: str
    size: int
    status: FileStatus = FileStatus.PENDING
    raw_text: str = ""
    error: str = ""


class JobStatus(str, Enum):
    CREATED = "created"
    EXTRACTING = "extracting"
    DONE = "done"
    ERROR = "error"


class ExtractionJob(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.CREATED
    files: list[UploadedFile] = Field(default_factory=list)
    extraction_schema: ExtractionSchema = Field(default_factory=ExtractionSchema)
    records: list[dict[str, Any]] = Field(default_factory=list)
    error: str = ""


# ---------------------------------------------------------------------------
# Request / response bodies
# ---------------------------------------------------------------------------

class ExtractRequest(BaseModel):
    extraction_schema: ExtractionSchema | None = None


class ExtractResponse(BaseModel):
    job_id: str
    records: list[dict[str, Any]]
    total: int


class AgentMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class AgentChatRequest(BaseModel):
    job_id: str | None = None
    messages: list[AgentMessage]


class AgentChatResponse(BaseModel):
    message: AgentMessage
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    updated_schema: ExtractionSchema | None = None
    updated_records: list[dict[str, Any]] | None = None
