import os
import re
from typing import Literal

import httpx

Strategy = Literal[
    "cognitive_restructuring",
    "behavioral_activation",
    "mindfulness",
    "emotional_support",
    "self_monitoring",
    "therapeutic_alliance",
    "general",
]


class InferenceService:
    def __init__(
        self,
        provider: str = "nvidia_nim",
        nim_api_key: str | None = None,
        nim_base_url: str | None = None,
        nim_model: str | None = None,
        timeout_seconds: int = 45,
    ) -> None:
        self.provider = provider
        self.nim_api_key = (
            nim_api_key
            if nim_api_key is not None
            else os.getenv("NVIDIA_NIM_API_KEY", os.getenv("NIM_API_KEY", ""))
        ).strip()
        self.nim_base_url = (
            nim_base_url if nim_base_url is not None else os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        ).rstrip("/")
        self.nim_model = nim_model if nim_model is not None else os.getenv("NVIDIA_NIM_MODEL", "qwen/qwen3.5-122b-a10b")
        self.timeout_seconds = timeout_seconds

    def choose_strategy(self, user_text: str) -> Strategy:
        text = user_text.lower()
        if "anxious" in text or "stress" in text:
            return "mindfulness"
        if "avoid" in text or "stuck" in text:
            return "behavioral_activation"
        if "always" in text or "never" in text:
            return "cognitive_restructuring"
        if "track" in text or "score" in text:
            return "self_monitoring"
        if "alone" in text or "lonely" in text:
            return "emotional_support"
        return "general"

    def generate(self, strategy: Strategy, user_text: str, memory_summary: str) -> str:
        if self._can_use_nim():
            try:
                return self._generate_nim(strategy, user_text, memory_summary)
            except Exception:
                # Fall back to local stub to preserve chat availability when provider is down.
                return self._generate_stub(strategy, user_text, memory_summary)

        return self._generate_stub(strategy, user_text, memory_summary)

    def _can_use_nim(self) -> bool:
        return self.provider == "nvidia_nim" and bool(self.nim_api_key)

    def _generate_stub(self, strategy: Strategy, user_text: str, memory_summary: str) -> str:
        lead = {
            "cognitive_restructuring": "Let us test that thought with evidence.",
            "behavioral_activation": "Let us pick one small action you can do in 10 minutes.",
            "mindfulness": "Let us slow down with one grounding breath cycle.",
            "emotional_support": "You are not alone in this, and your feelings make sense.",
            "self_monitoring": "Let us log a quick baseline so we can track change.",
            "therapeutic_alliance": "I am here with you and we can work through this together.",
            "general": "Here is a practical next step based on what you shared.",
        }[strategy]
        clean_user_text = user_text.strip()[:300]
        if memory_summary and memory_summary != "No prior context.":
            return f"{lead} Based on your recent context, start with this: {clean_user_text}"
        return f"{lead} Start with this: {clean_user_text}"

    def _generate_nim(self, strategy: Strategy, user_text: str, memory_summary: str) -> str:
        style_directive = self._style_directive(user_text, memory_summary)
        system_prompt = (
            "You are Aura, a practical conversational assistant. "
            "Adapt your communication style to the user's latest preference and tone. "
            "Do not force therapy framing unless user asks for it. "
            "Stay honest, concise, and non-manipulative. "
            f"Current strategy signal: {strategy}. "
            f"Style directive: {style_directive}"
        )

        user_prompt = (
            f"Recent context: {memory_summary}\n"
            f"User message: {user_text}\n"
            "Respond directly to the message in the requested style. "
            "Only propose a next step if it naturally fits."
        )

        payload = {
            "model": self.nim_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.5,
            "max_tokens": 220,
        }

        headers = {
            "Authorization": f"Bearer {self.nim_api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.nim_base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])
        if not choices:
            raise ValueError("NVIDIA NIM returned no choices")

        message = choices[0].get("message", {})
        content = (message.get("content") or "").strip()
        if not content:
            raise ValueError("NVIDIA NIM returned empty content")
        return content

    def _style_directive(self, user_text: str, memory_summary: str) -> str:
        text = f"{memory_summary} {user_text}".lower()

        if re.search(r"\b(normal|straight|direct|no fluff|brief|short)\b", text):
            return "Use direct plain language, 2-4 sentences, no coaching script tone."

        if re.search(r"\b(step by step|plan|checklist)\b", text):
            return "Use a clear structured style with short numbered actions."

        if re.search(r"\b(anxious|panic|overwhelmed|stressed)\b", text):
            return "Use calm tone and short grounding-first guidance, then practical action."

        return "Match user tone naturally and keep responses concise and useful."
