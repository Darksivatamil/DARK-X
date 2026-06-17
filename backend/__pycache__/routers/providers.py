from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.database import get_db
from backend.models.user import User
from backend.models.provider import ApiProvider
from backend.routers.auth import get_current_user
from backend.services.ai_service import ai_service
from backend.config import Config, logger

router = APIRouter(prefix="/api/providers", tags=["providers"])

KNOWN_PROVIDERS = [
    {"type": "openai", "name": "OpenAI", "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "o1", "o3-mini"], "default_url": "https://api.openai.com/v1"},
    {"type": "google", "name": "Google Gemini", "models": ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-pro"], "default_url": "https://generativelanguage.googleapis.com/v1"},
    {"type": "anthropic", "name": "Anthropic Claude", "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-4"], "default_url": "https://api.anthropic.com/v1"},
    {"type": "groq", "name": "Groq", "models": ["mixtral-8x7b-32768", "llama2-70b-4096", "gemma2-9b-it", "llama-3.3-70b"], "default_url": "https://api.groq.com/openai/v1"},
    {"type": "together", "name": "Together AI", "models": ["mistralai/Mixtral-8x22B-Instruct-v0.1", "meta-llama/Llama-3-70b-chat-hf", "codellama/CodeLlama-34b-Instruct-hf"], "default_url": "https://api.together.xyz/v1"},
    {"type": "openrouter", "name": "OpenRouter", "models": ["openai/gpt-4", "anthropic/claude-3-opus", "google/gemini-pro", "meta-llama/llama-3-70b"], "default_url": "https://openrouter.ai/api/v1"},
    {"type": "ollama", "name": "Ollama (Local)", "models": ["llama3", "mistral", "codellama", "mixtral", "phi3"], "default_url": "http://localhost:11434/v1"},
    {"type": "custom", "name": "Custom OpenAI-Compatible", "models": ["custom"], "default_url": "http://localhost:8000/v1"},
]

@router.get("/known")
async def get_known_providers():
    return KNOWN_PROVIDERS

@router.get("/list")
async def list_providers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    providers = db.query(ApiProvider).filter(ApiProvider.user_id == current_user.id).order_by(ApiProvider.created_at.desc()).all()
    return [{
        "id": p.id, "name": p.name, "provider_type": p.provider_type,
        "model_name": p.model_name, "base_url": p.base_url,
        "is_active": p.is_active, "api_key": p.api_key[:12] + "..." if p.api_key and len(p.api_key) > 12 else "",
    } for p in providers]

@router.post("/add")
async def add_provider(data: Dict[str, Any], current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(ApiProvider).filter(
        ApiProvider.user_id == current_user.id,
        ApiProvider.name == data.get("name")
    ).first()
    if existing:
        existing.api_key = data.get("api_key", existing.api_key)
        existing.model_name = data.get("model_name", existing.model_name)
        existing.base_url = data.get("base_url", existing.base_url)
        existing.is_active = data.get("is_active", True)
        existing.provider_type = data.get("provider_type", existing.provider_type)
        db.commit()
        db.refresh(existing)
        return {"status": "updated", "id": existing.id}

    provider = ApiProvider(
        user_id=current_user.id,
        name=data.get("name", "My Provider"),
        provider_type=data.get("provider_type", "custom"),
        api_key=data.get("api_key", ""),
        model_name=data.get("model_name", "gpt-4"),
        base_url=data.get("base_url", ""),
        is_active=data.get("is_active", True),
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return {"status": "created", "id": provider.id}

@router.put("/{provider_id}")
async def update_provider(provider_id: int, data: Dict[str, Any],
                          current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    provider = db.query(ApiProvider).filter(
        ApiProvider.id == provider_id,
        ApiProvider.user_id == current_user.id
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if "name" in data: provider.name = data["name"]
    if "provider_type" in data: provider.provider_type = data["provider_type"]
    if "api_key" in data: provider.api_key = data["api_key"]
    if "model_name" in data: provider.model_name = data["model_name"]
    if "base_url" in data: provider.base_url = data["base_url"]
    if "is_active" in data: provider.is_active = data["is_active"]
    db.commit()
    db.refresh(provider)
    return {"status": "updated", "id": provider.id}

@router.delete("/{provider_id}")
async def delete_provider(provider_id: int,
                          current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    provider = db.query(ApiProvider).filter(
        ApiProvider.id == provider_id,
        ApiProvider.user_id == current_user.id
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    db.delete(provider)
    db.commit()
    return {"status": "deleted"}

@router.post("/{provider_id}/test")
async def test_provider(provider_id: int,
                        current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    provider = db.query(ApiProvider).filter(
        ApiProvider.id == provider_id,
        ApiProvider.user_id == current_user.id
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    try:
        import openai
        client = openai.OpenAI(api_key=provider.api_key, base_url=provider.base_url)
        response = client.chat.completions.create(
            model=provider.model_name,
            messages=[{"role": "user", "content": "Reply with just: OK"}],
            max_tokens=10,
            timeout=15
        )
        return {"status": "success", "response": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "error": str(e)}
