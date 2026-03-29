from app.config import settings
from app.services.consent_service import ConsentService
from app.services.embedding_service import EmbeddingService
from app.services.inference_service import InferenceService
from app.services.memory_service import MemoryService
from app.services.observability_service import ObservabilityService
from app.services.orchestrator_service import ConversationOrchestrator
from app.services.persona_service import PersonaService
from app.services.policy_service import PolicySafetyService
from app.storage import SQLiteStore

store = SQLiteStore(settings.database_path)

embedding_service = EmbeddingService(
    api_key=settings.nim_api_key,
    base_url=settings.nim_base_url,
    model=settings.nim_embed_model,
    timeout_seconds=settings.nim_timeout_seconds,
    local_dim=settings.rag_embedding_dim,
)

memory_service = MemoryService(store, embedding_service)
consent_service = ConsentService(store)
policy_service = PolicySafetyService()
persona_service = PersonaService()
inference_service = InferenceService(
    provider="nvidia_nim",
    nim_api_key=settings.nim_api_key,
    nim_base_url=settings.nim_base_url,
    nim_model=settings.nim_model,
    timeout_seconds=settings.nim_timeout_seconds,
)
observability_service = ObservabilityService(store)

orchestrator = ConversationOrchestrator(
    memory_service=memory_service,
    consent_service=consent_service,
    policy_service=policy_service,
    persona_service=persona_service,
    inference_service=inference_service,
    observability_service=observability_service,
)
