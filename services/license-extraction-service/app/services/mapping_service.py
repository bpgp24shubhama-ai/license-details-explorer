from app.core.config import LicenseExtractionSettings
from app.providers.llm.base import EmbeddingProvider
from app.repositories.reference_repository import ReferenceRepository


class MappingService:
    def __init__(
        self,
        settings: LicenseExtractionSettings,
        reference_repository: ReferenceRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._settings = settings
        self._reference_repository = reference_repository
        self._embedding_provider = embedding_provider

    async def map_value(self, reference_type: str, value: str | None) -> tuple[str | None, float | None]:
        if not value or not value.strip():
            return None, None

        embedding = (await self._embedding_provider.embed_texts([value]))[0]
        candidate = await self._reference_repository.find_nearest(reference_type, embedding)
        if not candidate:
            return None, None

        similarity = float(candidate["similarity"])
        if similarity < self._settings.similarity_threshold:
            return None, similarity

        return str(candidate["mapped_value"]), similarity
