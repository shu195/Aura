import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Aura Companion API"
    app_version: str = "0.1.0"
    default_persona: str = "supportive_coach"
    default_retention_days: int = 30
    database_path: str = os.getenv("AURA_DATABASE_PATH", "data/aura.db")
    jwt_secret: str = os.getenv("AURA_JWT_SECRET", "dev-jwt-secret-change-me")
    jwt_algorithm: str = os.getenv("AURA_JWT_ALGORITHM", "HS256")
    jwt_exp_minutes: int = int(os.getenv("AURA_JWT_EXP_MINUTES", "60"))
    nim_api_key: str = os.getenv("NVIDIA_NIM_API_KEY", os.getenv("NIM_API_KEY", ""))
    nim_base_url: str = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    nim_model: str = os.getenv("NVIDIA_NIM_MODEL", "qwen/qwen3.5-122b-a10b")
    nim_timeout_seconds: int = int(os.getenv("NVIDIA_NIM_TIMEOUT_SECONDS", "45"))
    nim_embed_model: str = os.getenv("NVIDIA_NIM_EMBED_MODEL", "nvidia/nv-embedqa-e5-v5")
    rag_top_k: int = int(os.getenv("AURA_RAG_TOP_K", "4"))
    rag_embedding_dim: int = int(os.getenv("AURA_RAG_EMBEDDING_DIM", "256"))


settings = Settings()
