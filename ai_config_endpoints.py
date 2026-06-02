"""
AI Configuration Endpoints
Handles AI provider configuration and API key management.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import json
from pathlib import Path

router = APIRouter(prefix="/ai-config", tags=["AI Configuration"])

CONFIG_FILE = Path(os.path.dirname(__file__)) / ".ai_config.json"


class AIConfigRequest(BaseModel):
    provider: str
    apiKey: str
    model: str
    baseUrl: str = ""


class AIConfigResponse(BaseModel):
    provider: str
    model: str
    baseUrl: str = ""
    isAvailable: bool


@router.get("/current")
async def get_current_config():
    """Get current AI configuration."""
    if not CONFIG_FILE.exists():
        return {
            "provider": None,
            "model": None,
            "baseUrl": None,
            "isAvailable": False
        }
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        return {
            "provider": config.get("provider"),
            "model": config.get("model"),
            "baseUrl": config.get("baseUrl", ""),
            "isAvailable": bool(config.get("apiKey")) or config.get("provider") == "local"
        }
    except Exception as e:
        print(f"Error reading config: {str(e)}")
        return {
            "provider": None,
            "model": None,
            "baseUrl": None,
            "isAvailable": False
        }


@router.post("/save")
async def save_config(config: AIConfigRequest):
    """Save AI configuration."""
    try:
        # Store config (in production, use secure secrets management)
        config_data = {
            "provider": config.provider,
            "model": config.model,
            "baseUrl": config.baseUrl,
            "apiKey": config.apiKey if config.provider != "local" else ""
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Set environment variables for immediate use
        if config.provider == "openai":
            os.environ["OPENAI_API_KEY"] = config.apiKey
            os.environ["OPENAI_MODEL"] = config.model
        elif config.provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = config.apiKey
            os.environ["ANTHROPIC_MODEL"] = config.model
        elif config.provider == "google_gemini":
            os.environ["GEMINI_API_KEY"] = config.apiKey
            os.environ["GEMINI_MODEL"] = config.model
        elif config.provider == "local":
            os.environ["LOCAL_AI_ENABLED"] = "true"
            os.environ["LOCAL_AI_URL"] = config.baseUrl or "http://localhost:11434"
            os.environ["LOCAL_AI_MODEL"] = config.model or "llama3"
        
        return {
            "success": True,
            "message": f"Configuration saved for {config.provider}",
            "provider": config.provider,
            "model": config.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")


@router.post("/reset")
async def reset_config():
    """Reset to default/mock configuration."""
    try:
        # Remove config file
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        
        # Clear environment variables
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
                    "LOCAL_AI_ENABLED", "LOCAL_AI_URL", "LOCAL_AI_MODEL"]:
            if key in os.environ:
                del os.environ[key]
        
        return {
            "success": True,
            "message": "Configuration reset to defaults"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset configuration: {str(e)}")
