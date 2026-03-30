from fastapi.testclient import TestClient

from app.api.deps import get_lookup_validation_service, get_reference_ingestion_service
from app.main import app
from shared.contracts.reference import LookupValidationResponse, ReferenceIngestionResult


class FakeIngestionService:
    async def ingest_excel(self, file_bytes: bytes, reference_type: str, mode: str):
        assert len(file_bytes) > 0
        return ReferenceIngestionResult(
            request_id="fb50ceb3-f6b6-4495-80de-798766615d67",
            reference_type=reference_type,
            mode=mode,
            processed_rows=2,
            inserted_rows=2,
            updated_rows=0,
            invalid_rows=0,
        )

    async def reindex_reference_type(self, reference_type: str):
        return ReferenceIngestionResult(
            request_id="5ac87ad8-78c6-4a65-b9fc-b6fefa5f1b07",
            reference_type=reference_type,
            mode="reindex",
            processed_rows=2,
            inserted_rows=0,
            updated_rows=2,
            invalid_rows=0,
        )


class FakeValidationService:
    async def validate(self, reference_type: str, value: str):
        return LookupValidationResponse(
            reference_type=reference_type,
            value=value,
            mapped_value="Mumbai",
            similarity=0.95,
        )


def test_upload_endpoint():
    app.dependency_overrides[get_reference_ingestion_service] = lambda: FakeIngestionService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/references/upload",
        files={
            "file": (
                "master.xlsx",
                b"binaryexcel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"reference_type": "location", "mode": "reload"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reference_type"] == "location"
    assert payload["mode"] == "reload"

    app.dependency_overrides.clear()


def test_validate_endpoint():
    app.dependency_overrides[get_lookup_validation_service] = lambda: FakeValidationService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/references/validate",
        json={"reference_type": "location", "value": "mumabi"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mapped_value"] == "Mumbai"
    assert payload["similarity"] == 0.95

    app.dependency_overrides.clear()
