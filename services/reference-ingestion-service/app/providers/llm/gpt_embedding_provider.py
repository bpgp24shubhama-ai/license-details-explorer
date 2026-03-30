import hashlib
import random

import httpx

from app.core.config import ReferenceIngestionSettings
from app.providers.llm.base import EmbeddingProvider
from app.utils.retry import run_with_retry


class GPTEmbeddingProvider(EmbeddingProvider):
    VECTOR_SIZE = 1536

    def __init__(self, settings: ReferenceIngestionSettings) -> None:
        self._settings = settings

    @classmethod
    def _deterministic_embedding(cls, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], byteorder="big", signed=False)
        rng = random.Random(seed)
        return [rng.uniform(-1.0, 1.0) for _ in range(cls.VECTOR_SIZE)]

    async def _remote_embed(self, texts: list[str]) -> list[list[float]]:
        payload = {
            "model": self._settings.embedding_model,
            "input": texts,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        async def _call() -> list[list[float]]:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
                response = await client.post(
                    f"{self._settings.openai_base_url}/embeddings",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                ordered = sorted(data["data"], key=lambda item: item["index"])
                return [item["embedding"] for item in ordered]

        return await run_with_retry(
            _call,
            attempts=self._settings.external_api_retry_count,
            base_seconds=self._settings.external_api_retry_backoff_seconds,
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if not self._settings.openai_api_key:
            return [self._deterministic_embedding(text) for text in texts]

        return await self._remote_embed(texts)
