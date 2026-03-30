from typing import Any

from sqlalchemy import literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ReferenceMaster


class ReferenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_nearest(self, reference_type: str, embedding: list[float]) -> dict[str, Any] | None:
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
