import hashlib
import math
import re
from datetime import UTC, datetime

import httpx


class EmbeddingService:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: int,
        local_dim: int = 256,
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.local_dim = local_dim

    def embed(self, text: str) -> list[float]:
        clean = text.strip()
        if not clean:
            return [0.0] * self.local_dim

        if self.api_key:
            try:
                return self._embed_nim(clean)
            except Exception:
                return self._embed_local(clean)

        return self._embed_local(clean)

    def _embed_nim(self, text: str) -> list[float]:
        payload = {
            "model": self.model,
            "input": text,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/embeddings", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        embedding = data.get("data", [{}])[0].get("embedding")
        if not isinstance(embedding, list) or not embedding:
            raise ValueError("NIM embeddings response missing vector")

        return [float(v) for v in embedding]

    def _embed_local(self, text: str) -> list[float]:
        vec = [0.0] * self.local_dim
        tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        if not tokens:
            return vec

        for token in tokens:
            idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.local_dim
            vec[idx] += 1.0

        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return vec
        return [v / norm for v in vec]
