from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.consent import router as consent_router
from app.api.routes.conversation import router as conversation_router
from app.api.routes.health import router as health_router
from app.api.routes.memory import router as memory_router
from app.api.routes.observability import router as observability_router
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Persistent AI companion backend with safety, consent, and memory primitives.",
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(conversation_router)
app.include_router(memory_router)
app.include_router(consent_router)
app.include_router(observability_router)
