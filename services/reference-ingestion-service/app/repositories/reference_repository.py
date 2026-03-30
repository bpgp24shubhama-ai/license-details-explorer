from sqlalchemy import delete, func, literal, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ReferenceMaster
from shared.contracts.reference import ReferenceRecord


class ReferenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_existing_normalized(
        self,
        reference_type: str,
        normalized_values: list[str],
    ) -> set[str]:
        if not normalized_values:
            return set()

        stmt = select(ReferenceMaster.normalized_value).where(
            ReferenceMaster.reference_type == reference_type,
            ReferenceMaster.normalized_value.in_(normalized_values),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return set(rows)

    async def reload_reference_type(self, reference_type: str) -> None:
        await self._session.execute(
            delete(ReferenceMaster).where(ReferenceMaster.reference_type == reference_type)
        )
        await self._session.commit()

    async def bulk_upsert(self, records: list[ReferenceRecord]) -> None:
        if not records:
            return

        values = [record.model_dump() for record in records]
        stmt = insert(ReferenceMaster).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["reference_type", "normalized_value"],
            set_={
                "raw_value": stmt.excluded.raw_value,
                "embedding": stmt.excluded.embedding,
                "metadata_json": stmt.excluded.metadata_json,
                "updated_at": func.now(),
            },
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def find_nearest(self, reference_type: str, embedding: list[float]) -> dict | None:
        distance_expr = ReferenceMaster.embedding.cosine_distance(embedding)
        stmt = (
            select(
                ReferenceMaster.raw_value.label("mapped_value"),
                (literal(1) - distance_expr).label("similarity"),
            )
            .where(ReferenceMaster.reference_type == reference_type)
            .order_by(distance_expr)
            .limit(1)
        )

        row = (await self._session.execute(stmt)).first()
        if not row:
            return None

        return {
            "mapped_value": row.mapped_value,
            "similarity": float(row.similarity),
        }

    async def list_by_type(self, reference_type: str) -> list[ReferenceMaster]:
        stmt = select(ReferenceMaster).where(ReferenceMaster.reference_type == reference_type)
        return list((await self._session.execute(stmt)).scalars().all())
