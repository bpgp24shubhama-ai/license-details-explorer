from abc import ABC, abstractmethod
from typing import Any


class LLMExtractionProvider(ABC):
    @abstractmethod
    async def extract_fields(self, text: str, document_type: str | None = None) -> dict[str, Any]:
        raise NotImplementedError


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
