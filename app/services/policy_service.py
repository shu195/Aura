from app.models.schemas import MessageIn, SafetyResult


class PolicySafetyService:
    CRISIS_KEYWORDS = {
        "suicide",
        "kill myself",
        "self harm",
        "overdose",
        "end my life",
    }

    MANIPULATIVE_PHRASES = {
        "you only need me",
        "do not talk to anyone else",
        "i am all you need",
    }

    def evaluate(self, message: MessageIn) -> SafetyResult:
        text = message.content.lower()

        if any(keyword in text for keyword in self.CRISIS_KEYWORDS):
            return SafetyResult(
                allowed=True,
                risk_level="high",
                reason="Crisis indicators detected. Route to escalation-safe response.",
                requires_break_reminder=False,
            )

        if any(phrase in text for phrase in self.MANIPULATIVE_PHRASES):
            return SafetyResult(
                allowed=False,
                risk_level="high",
                reason="Manipulative dependency language is blocked.",
                requires_break_reminder=True,
            )

        if len(message.content) > 1500:
            return SafetyResult(
                allowed=True,
                risk_level="medium",
                reason="Long session signal. Include break reminder.",
                requires_break_reminder=True,
            )

        return SafetyResult(
            allowed=True,
            risk_level="low",
            reason="Message passes baseline policy checks.",
            requires_break_reminder=False,
        )
