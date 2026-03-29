from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


ModalityType = Literal["text", "voice", "vision"]
StrategyType = Literal[
    "cognitive_restructuring",
    "behavioral_activation",
    "mindfulness",
    "emotional_support",
    "self_monitoring",
    "therapeutic_alliance",
    "general",
]


class MessageIn(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1, max_length=5000)
    modality: ModalityType = "text"
    metadata: Dict[str, str] = Field(default_factory=dict)


class ConversationRequest(BaseModel):
    user_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    message: MessageIn


class SafetyResult(BaseModel):
    allowed: bool
    risk_level: Literal["low", "medium", "high"]
    reason: str
    requires_break_reminder: bool = False


class ConversationResponse(BaseModel):
    user_id: str
    session_id: str
    strategy: StrategyType
    response_text: str
    safety: SafetyResult
    memory_hits: List[str] = Field(default_factory=list)
    persona_stable: bool
    generated_at: datetime


class MemoryRecord(BaseModel):
    user_id: str
    session_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    retention_days: int = 30
    purpose: Literal["wellness", "productivity", "operations"]
    created_at: datetime


class MemorySearchRequest(BaseModel):
    user_id: str
    query: str = Field(min_length=1, max_length=5000)


class MemorySearchResponse(BaseModel):
    user_id: str
    query: str
    hits: List[str] = Field(default_factory=list)


class ConsentUpdateRequest(BaseModel):
    user_id: str
    gpc_enabled: bool = False
    one_click_opt_out: bool = False
    voice_enabled: bool = True
    vision_enabled: bool = False


class ConsentStatusResponse(BaseModel):
    user_id: str
    gpc_enabled: bool
    one_click_opt_out: bool
    voice_enabled: bool
    vision_enabled: bool
    updated_at: datetime


class PurgeRequest(BaseModel):
    user_id: str
    reason: Literal["user_request", "retention_expired", "compliance"]


class PurgeResponse(BaseModel):
    user_id: str
    deleted_records: int
    receipt_id: str
    deleted_at: datetime


class AuditEvent(BaseModel):
    event_type: str
    user_id: Optional[str] = None
    details: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime


class TokenRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    scopes: List[str]
