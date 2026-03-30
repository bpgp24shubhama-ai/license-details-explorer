from app.core.config import ReferenceIngestionSettings
from app.providers.llm.base import EmbeddingProvider
from app.repositories.reference_repository import ReferenceRepository
from shared.contracts.reference import LookupValidationResponse
from shared.exceptions.app_exceptions import AppException


class LookupValidationService:
    def __init__(
        self,
        settings: ReferenceIngestionSettings,
        embedding_provider: EmbeddingProvider,
        reference_repository: ReferenceRepository,
    ) -> None:
        self._settings = settings
        self._embedding_provider = embedding_provider
        self._reference_repository = reference_repository

    @staticmethod
    def normalize_value(value: str) -> str:
        return " ".join(value.strip().lower().split())

    async def validate(self, reference_type: str, value: str) -> LookupValidationResponse:
        if not value.strip():
            raise AppException(
                status_code=422,
                code="empty_value",
                detail="Validation value cannot be empty",
            )

        normalized = self.normalize_value(value)
        embedding = (await self._embedding_provider.embed_texts([normalized]))[0]
        candidate = await self._reference_repository.find_nearest(reference_type, embedding)

        if not candidate:
            return LookupValidationResponse(
                reference_type=reference_type,
                value=value,
                mapped_value=None,
                similarity=None,
            )

        similarity = float(candidate["similarity"])
        mapped_value = (
            str(candidate["mapped_value"])
            if similarity >= self._settings.similarity_threshold
            else None
        )

        return LookupValidationResponse(
            reference_type=reference_type,
            value=value,
            mapped_value=mapped_value,
            similarity=similarity,
        )
