"""AI agent service – uses OpenAI function calling to guide the extraction workflow."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from models.schemas import AgentMessage, ExtractionJob, ExtractionSchema, SchemaField

logger = logging.getLogger(__name__)

# Maximum characters of raw document text sent to the model per file.
# GPT-4o has a 128 k-token context; 12 000 characters ≈ 3 000 tokens,
# leaving ample room for the system prompt, schema spec, and the response.
MAX_EXTRACTION_TEXT_LENGTH = 12_000

# ---------------------------------------------------------------------------
# Tool definitions exposed to the model
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "set_schema",
            "description": (
                "Define or update the extraction schema – the list of fields "
                "that should be extracted from the uploaded documents."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {
                                    "type": "string",
                                    "enum": ["string", "number", "boolean", "date", "list"],
                                },
                                "description": {"type": "string"},
                                "required": {"type": "boolean"},
                            },
                            "required": ["name", "type"],
                        },
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Extra extraction instructions sent to the model.",
                    },
                },
                "required": ["fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extract_data",
            "description": (
                "Trigger (re-)extraction of structured data from all uploaded "
                "documents using the current (or a newly supplied) schema."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "instructions": {
                        "type": "string",
                        "description": "Additional extraction instructions.",
                    }
                },
            },
        },
    },
]

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an intelligent data extraction assistant built into the AI Data Extractor application.

Your job is to help the user:
1. Upload and parse documents (PDFs, images, Word docs, spreadsheets, etc.)
2. Define an extraction schema – the structured fields they want to pull from the documents
3. Extract data from the documents according to the schema
4. Review and clean the extracted data in the interactive table
5. Export the results as JSON, JSONL, CSV, XLSX, or TSV

Guidelines:
- Ask clarifying questions before defining a schema if the user's intent is unclear.
- When suggesting a schema, use descriptive field names and pick the most appropriate type.
- After extraction, summarise what was found and suggest improvements.
- Be concise but thorough.
- If the user uploads documents, encourage them to describe the data they want to extract.
"""

# ---------------------------------------------------------------------------
# Core chat function
# ---------------------------------------------------------------------------


def _get_client():
    """Return an OpenAI client, raising a clear error if the key is missing."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package is not installed") from exc

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("your_"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please add it to your .env file."
        )
    return OpenAI(api_key=api_key)


def chat(
    messages: list[AgentMessage],
    job: ExtractionJob | None = None,
) -> dict[str, Any]:
    """Send messages to the AI agent and return the response.

    Returns a dict with:
      - message: AgentMessage
      - tool_calls: list of raw tool call dicts (if any)
      - updated_schema: ExtractionSchema | None
      - updated_records: list[dict] | None
    """
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    client = _get_client()

    # Build the message list for the API
    api_messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Inject current job context
    if job:
        context_parts: list[str] = []
        if job.files:
            file_names = [f.filename for f in job.files]
            context_parts.append(f"Uploaded files: {', '.join(file_names)}")
        if job.extraction_schema.fields:
            field_summary = ", ".join(
                f"{f.name} ({f.type})" for f in job.extraction_schema.fields
            )
            context_parts.append(f"Current schema: {field_summary}")
        if job.records:
            context_parts.append(f"Extracted records: {len(job.records)} rows")
        if context_parts:
            api_messages.append(
                {
                    "role": "system",
                    "content": "Current job context:\n" + "\n".join(context_parts),
                }
            )

    for msg in messages:
        api_messages.append({"role": msg.role, "content": msg.content})

    response = client.chat.completions.create(
        model=model,
        messages=api_messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.2,
    )

    choice = response.choices[0]
    assistant_msg = choice.message

    result: dict[str, Any] = {
        "message": AgentMessage(
            role="assistant",
            content=assistant_msg.content or "",
        ),
        "tool_calls": [],
        "updated_schema": None,
        "updated_records": None,
    }

    if assistant_msg.tool_calls:
        for tc in assistant_msg.tool_calls:
            result["tool_calls"].append(
                {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
            )

            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            if tc.function.name == "set_schema":
                fields = [SchemaField(**f) for f in args.get("fields", [])]
                result["updated_schema"] = ExtractionSchema(
                    fields=fields,
                    instructions=args.get("instructions", ""),
                )

    return result


# ---------------------------------------------------------------------------
# AI-powered extraction helper
# ---------------------------------------------------------------------------

def extract_with_ai(
    raw_text: str,
    schema: ExtractionSchema,
    filename: str = "",
) -> list[dict[str, Any]]:
    """Use the AI to extract structured records from raw_text according to schema.

    Returns a list of dicts (one per record found in the document).
    """
    if not schema.fields:
        return []

    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    client = _get_client()

    field_spec = "\n".join(
        f'- {f.name} ({f.type}): {f.description or "no description"}'
        for f in schema.fields
    )

    extra = f"\nAdditional instructions: {schema.instructions}" if schema.instructions else ""

    system = (
        "You are a precise data extraction engine. "
        "Extract structured records from the provided text and return them as a JSON array. "
        "Each element of the array is one record (one row). "
        "Only output valid JSON – no markdown, no explanation."
    )

    user = (
        f"Document: {filename}\n\n"
        f"Fields to extract:\n{field_spec}{extra}\n\n"
        f"Text:\n{raw_text[:MAX_EXTRACTION_TEXT_LENGTH]}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("AI returned invalid JSON for %s", filename)
        return []

    # The model may return {"records": [...]} or directly [...]
    if isinstance(parsed, list):
        return parsed
    for key in ("records", "data", "results", "items"):
        if key in parsed and isinstance(parsed[key], list):
            return parsed[key]

    logger.warning("Unexpected AI response shape for %s: %s", filename, list(parsed.keys()))
    return []
