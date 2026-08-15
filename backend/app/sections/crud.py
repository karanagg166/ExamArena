from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.database as db
from app.core.models import ExamSection
from app.sections.schemas import (
    SectionCreateRequest,
    SectionResponse,
    SectionUpdateRequest,
)


def _sort_order_from_name(name: str) -> int:
    """Derive sort order from section name. 'Section A' -> 1, 'Section B' -> 2, etc."""
    return ord(name[-1]) - ord("A") + 1


async def create_section(
    section_data: SectionCreateRequest, session: AsyncSession | None = None
) -> SectionResponse:
    sort_order = _sort_order_from_name(section_data.name)

    async def _do_create(s: AsyncSession):
        section = ExamSection(
            name=section_data.name,
            description=section_data.description,
            questionType=section_data.questionType,
            marksPerQuestion=section_data.marksPerQuestion,
            sortOrder=sort_order,
            examId=section_data.examId,
        )
        s.add(section)
        await s.commit()
        await s.refresh(section)
        return SectionResponse.model_validate(section)

    if session:
        return await _do_create(session)
    async with db.get_session() as s:
        return await _do_create(s)


async def get_sections_by_exam(
    exam_id: str, session: AsyncSession | None = None
) -> list[SectionResponse]:

    async def _do_get(s: AsyncSession):
        stmt = (
            select(ExamSection)
            .where(ExamSection.examId == exam_id)
            .order_by(ExamSection.sortOrder)
        )
        sections = (await s.execute(stmt)).scalars().all()
        return [SectionResponse.model_validate(sec) for sec in sections]

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def get_section_by_id(
    section_id: str, session: AsyncSession | None = None
) -> SectionResponse | None:

    async def _do_get(s: AsyncSession):
        stmt = select(ExamSection).where(ExamSection.id == section_id)
        section = (await s.execute(stmt)).scalar_one_or_none()
        return SectionResponse.model_validate(section) if section else None

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def update_section(
    section_id: str,
    update_data: SectionUpdateRequest,
    session: AsyncSession | None = None,
) -> SectionResponse | None:
    update_dict = update_data.model_dump(exclude_unset=True)

    async def _do_update(s: AsyncSession):
        stmt = select(ExamSection).where(ExamSection.id == section_id)
        section = (await s.execute(stmt)).scalar_one_or_none()
        if not section:
            return None

        for k, v in update_dict.items():
            setattr(section, k, v)

        await s.commit()
        await s.refresh(section)
        return SectionResponse.model_validate(section)

    if session:
        return await _do_update(session)
    async with db.get_session() as s:
        return await _do_update(s)


async def delete_section(
    section_id: str, session: AsyncSession | None = None
) -> SectionResponse | None:

    async def _do_delete(s: AsyncSession):
        stmt = select(ExamSection).where(ExamSection.id == section_id)
        section = (await s.execute(stmt)).scalar_one_or_none()
        if not section:
            return None
        res = SectionResponse.model_validate(section)
        await s.delete(section)
        await s.commit()
        return res

    if session:
        return await _do_delete(session)
    async with db.get_session() as s:
        return await _do_delete(s)
