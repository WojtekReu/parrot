from typing import Any

from sqlalchemy import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select


async def model_join_to_set(
    session: AsyncSession,
    relation_model: Any,
    source_id_name: str,
    source_id: int,
    target_id_name: str,
    target_ids: set[int],
) -> None:
    for target_id in target_ids:
        result = await session.execute(
            select(relation_model)
            .where(getattr(relation_model, source_id_name) == source_id)
            .where(getattr(relation_model, target_id_name) == target_id)
        )
        if not result.first():
            relation_model_attrs = {
                source_id_name: source_id,
                target_id_name: target_id,
            }
            relation_object = relation_model(**relation_model_attrs)
            session.add(relation_object)
    await session.commit()


async def model_separate_list(
    session: AsyncSession,
    relation_model: Any,
    source_id_name: str,
    source_id: int,
    target_id_name: str,
    target_ids: set[int],
) -> Result:
    query = (
        delete(relation_model)
        .where(getattr(relation_model, source_id_name) == source_id)
        .filter(getattr(relation_model, target_id_name).in_(target_ids))
    )
    return await session.execute(query)
