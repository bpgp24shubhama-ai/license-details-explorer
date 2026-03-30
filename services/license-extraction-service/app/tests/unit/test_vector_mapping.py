import pytest

from app.core.config import LicenseExtractionSettings
from app.services.mapping_service import MappingService


class FakeEmbeddingProvider:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        assert len(texts) == 1
        return [[0.1] * 1536]


class FakeReferenceRepo:
    def __init__(self, similarity: float) -> None:
        self.similarity = similarity

    async def find_nearest(self, reference_type: str, embedding: list[float]):
        assert reference_type in {"license_category", "location"}
        assert len(embedding) == 1536
        return {"mapped_value": "Mumbai", "similarity": self.similarity}


@pytest.mark.asyncio
async def test_mapping_above_threshold():
    settings = LicenseExtractionSettings(SIMILARITY_THRESHOLD=0.7)
    service = MappingService(settings, FakeReferenceRepo(0.9), FakeEmbeddingProvider())

    mapped, similarity = await service.map_value("location", "mumabi")

    assert mapped == "Mumbai"
    assert similarity == 0.9


@pytest.mark.asyncio
async def test_mapping_below_threshold_returns_null_mapping():
    settings = LicenseExtractionSettings(SIMILARITY_THRESHOLD=0.95)
    service = MappingService(settings, FakeReferenceRepo(0.9), FakeEmbeddingProvider())

    mapped, similarity = await service.map_value("location", "mumabi")

    assert mapped is None
    assert similarity == 0.9
