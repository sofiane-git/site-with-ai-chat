import urllib.request

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])


class ProvidersHealth(BaseModel):
    ollama: bool
    azure: bool


@router.get("")
def health_check() -> dict:
    return {"status": "ok"}


@router.get("/providers", response_model=ProvidersHealth)
def providers_health() -> ProvidersHealth:
    from app.routes.chat import agent_azure
    try:
        urllib.request.urlopen(settings.ollama_base_url.get_secret_value(), timeout=2)
        ollama_ok = True
    except Exception:
        ollama_ok = False
    return ProvidersHealth(ollama=ollama_ok, azure=agent_azure is not None)
