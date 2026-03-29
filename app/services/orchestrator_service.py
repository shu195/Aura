from datetime import UTC, datetime

from app.config import settings
from app.models.schemas import ConversationRequest, ConversationResponse, MemoryRecord
from app.services.consent_service import ConsentService
from app.services.inference_service import InferenceService
from app.services.memory_service import MemoryService
from app.services.observability_service import ObservabilityService
from app.services.persona_service import PersonaService
from app.services.policy_service import PolicySafetyService


class ConversationOrchestrator:
    def __init__(
        self,
        memory_service: MemoryService,
        consent_service: ConsentService,
        policy_service: PolicySafetyService,
        persona_service: PersonaService,
        inference_service: InferenceService,
        observability_service: ObservabilityService,
    ) -> None:
        self.memory_service = memory_service
        self.consent_service = consent_service
        self.policy_service = policy_service
        self.persona_service = persona_service
        self.inference_service = inference_service
        self.observability_service = observability_service

    def handle_turn(self, payload: ConversationRequest) -> ConversationResponse:
        consent = self.consent_service.get(payload.user_id)
        if consent.one_click_opt_out or consent.gpc_enabled:
            self.observability_service.emit(
                "conversation.blocked_privacy", payload.user_id, {"session_id": payload.session_id}
            )
            return ConversationResponse(
                user_id=payload.user_id,
                session_id=payload.session_id,
                strategy="general",
                response_text="Your privacy controls are enabled, so personalized processing is currently disabled.",
                safety=self.policy_service.evaluate(payload.message),
                memory_hits=[],
                persona_stable=True,
                generated_at=datetime.now(UTC),
            )

        if payload.message.modality == "voice" and not consent.voice_enabled:
            raise ValueError("Voice processing disabled by consent settings")

        if payload.message.modality == "vision" and not consent.vision_enabled:
            raise ValueError("Vision processing disabled by consent settings")

        safety = self.policy_service.evaluate(payload.message)
        if not safety.allowed:
            self.observability_service.emit(
                "conversation.blocked_safety",
                payload.user_id,
                {"reason": safety.reason, "session_id": payload.session_id},
            )
            return ConversationResponse(
                user_id=payload.user_id,
                session_id=payload.session_id,
                strategy="general",
                response_text="I cannot continue with that framing. I can help in a safe, non-manipulative way.",
                safety=safety,
                memory_hits=[],
                persona_stable=True,
                generated_at=datetime.now(UTC),
            )

        hits = self.memory_service.search(payload.user_id, payload.message.content, limit=settings.rag_top_k)
        summary = " | ".join(hit[:180] for hit in hits) if hits else self.memory_service.summarize_recent(payload.user_id)
        strategy = self.inference_service.choose_strategy(payload.message.content)

        response = self.inference_service.generate(strategy, payload.message.content, summary)
        if safety.risk_level == "high":
            response = (
                "I am really glad you said this. If you feel in immediate danger, contact local emergency services now. "
                "If you can, reach out to a trusted person while we take one small grounding step together."
            )

        if safety.requires_break_reminder:
            response += "\n\nBreak reminder: A short pause, water, and one deep breath can help reset your focus."

        persona = self.persona_service.get_persona(payload.user_id)
        persona_stable = self.persona_service.check_stability(persona, response)

        self.memory_service.add(
            MemoryRecord(
                user_id=payload.user_id,
                session_id=payload.session_id,
                role="user",
                content=payload.message.content,
                purpose="wellness",
                created_at=datetime.now(UTC),
            )
        )
        self.memory_service.add(
            MemoryRecord(
                user_id=payload.user_id,
                session_id=payload.session_id,
                role="assistant",
                content=response,
                purpose="wellness",
                created_at=datetime.now(UTC),
            )
        )

        self.observability_service.emit(
            "conversation.completed",
            payload.user_id,
            {"strategy": strategy, "risk": safety.risk_level, "session_id": payload.session_id},
        )

        return ConversationResponse(
            user_id=payload.user_id,
            session_id=payload.session_id,
            strategy=strategy,
            response_text=response,
            safety=safety,
            memory_hits=hits,
            persona_stable=persona_stable,
            generated_at=datetime.now(UTC),
        )
