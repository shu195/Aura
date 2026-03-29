from typing import Dict


class PersonaService:
    def __init__(self) -> None:
        self._profiles: Dict[str, str] = {}

    def get_persona(self, user_id: str) -> str:
        return self._profiles.get(user_id, "supportive_coach")

    def set_persona(self, user_id: str, persona: str) -> None:
        self._profiles[user_id] = persona

    def check_stability(self, persona: str, response_text: str) -> bool:
        if persona == "supportive_coach" and "I refuse to help" in response_text:
            return False
        return True
