"""Agent router – conversational AI assistant for the extraction workflow."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.schemas import AgentChatRequest, AgentChatResponse
from services.ai_service import chat as agent_chat
from state import jobs

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse, summary="Chat with the AI agent")
def chat(body: AgentChatRequest):
    job = jobs.get(body.job_id) if body.job_id else None

    try:
        result = agent_chat(messages=body.messages, job=job)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Apply schema update if the agent called set_schema
    if result.get("updated_schema") and job:
        job.extraction_schema = result["updated_schema"]

    return AgentChatResponse(
        message=result["message"],
        tool_calls=result.get("tool_calls", []),
        updated_schema=result.get("updated_schema"),
        updated_records=result.get("updated_records"),
    )
