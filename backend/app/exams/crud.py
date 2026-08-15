from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.core.database as db
from app.core.models import (
    Exam,
    ExamSection,
    Question,
    QuestionOption,
    School,
    Teacher,
    User,
    generate_exam_code,
)
from app.exams.schemas import (
    ExamCreateRequest,
    ExamResponse,
    ExamUpdateRequest,
)

EXAM_OPTIONS = [
    selectinload(Exam.teacher).selectinload(Teacher.user),
    selectinload(Exam.teacher).selectinload(Teacher.school),
    selectinload(Exam.sections),
    selectinload(Exam.questions).selectinload(Question.options),
]


async def create_exam(
    exam_data: ExamCreateRequest, teacher_id: str, session: AsyncSession | None = None
) -> ExamResponse:
    questions_list = []
    if exam_data.questions:
        for q in exam_data.questions:
            options = []
            if q.options:
                options = [
                    QuestionOption(
                        text=o.text,
                        optionNumber=o.optionNumber,
                        isCorrect=o.isCorrect,
                        imageUrl=o.imageUrl,
                    )
                    for o in q.options
                ]

            question = Question(
                text=q.text,
                marks=q.marks,
                questionNumber=q.questionNumber,
                questionType=q.questionType,
                imageUrl=q.imageUrl,
                wordLimit=q.wordLimit,
                explanation=q.explanation,
                section=q.section,
                options=options,
            )
            questions_list.append(question)

    data = {
        "name": exam_data.name,
        "description": exam_data.description,
        "scheduledAt": exam_data.scheduledAt,
        "duration": exam_data.duration,
        "maxMarks": exam_data.maxMarks,
        "instructions": exam_data.instructions,
        "isPublished": exam_data.isPublished,
        "isPublic": exam_data.isPublic,
        "isResultsReleased": exam_data.isResultsReleased,
        "negativeMarking": exam_data.negativeMarking,
        "negativeMarks": exam_data.negativeMarks,
        "type": exam_data.type,
        "teacherId": teacher_id,
        "questions": questions_list,
        "examCode": exam_data.examCode if exam_data.examCode else generate_exam_code(),
    }

    if exam_data.subject:
        data["subject"] = exam_data.subject

    async def _do_create(s: AsyncSession):
        exam = Exam(**data)
        s.add(exam)
        await s.commit()
        await s.refresh(exam)

        stmt = select(Exam).where(Exam.id == exam.id).options(*EXAM_OPTIONS)
        created = (await s.execute(stmt)).scalar_one()
        return ExamResponse.model_validate(created)

    if session:
        return await _do_create(session)
    async with db.get_session() as s:
        return await _do_create(s)


async def get_exam_by_id(
    exam_id: str, session: AsyncSession | None = None
) -> ExamResponse | None:

    async def _do_get(s: AsyncSession):
        stmt = select(Exam).where(Exam.id == exam_id).options(*EXAM_OPTIONS)
        exam = (await s.execute(stmt)).scalar_one_or_none()
        return ExamResponse.model_validate(exam) if exam else None

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def get_exams_by_teacher(
    teacher_id: str, session: AsyncSession | None = None
) -> list[ExamResponse]:

    async def _do_get(s: AsyncSession):
        stmt = select(Exam).where(Exam.teacherId == teacher_id).options(*EXAM_OPTIONS)
        exams = (await s.execute(stmt)).scalars().all()
        return [ExamResponse.model_validate(e) for e in exams]

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def get_published_exams(
    name=None,
    exam_type=None,
    teacher_name=None,
    school_name=None,
    subject=None,
    school_id=None,
    code=None,
    session: AsyncSession | None = None,
):
    async def _do_get(s: AsyncSession):
        stmt = select(Exam).where(Exam.isPublished == True).options(*EXAM_OPTIONS)  # noqa: E712

        if code:
            stmt = stmt.where(Exam.examCode.ilike(f"%{code.strip()}%"))
        elif name:
            stmt = stmt.where(
                (Exam.name.ilike(f"%{name}%")) | (Exam.examCode.ilike(f"%{name}%"))
            )
        if exam_type:
            stmt = stmt.where(Exam.type == exam_type)
        if subject:
            stmt = stmt.where(Exam.subject == subject)

        if teacher_name or school_name or school_id:
            stmt = stmt.join(Exam.teacher)
            if teacher_name:
                stmt = stmt.join(Teacher.user).where(
                    User.name.ilike(f"%{teacher_name}%")
                )
            if school_name:
                stmt = stmt.join(Teacher.school).where(
                    School.name.ilike(f"%{school_name}%")
                )
            if school_id:
                stmt = stmt.where(Teacher.schoolId == school_id)

        exams = (await s.execute(stmt)).scalars().unique().all()
        return [ExamResponse.model_validate(e) for e in exams]

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def get_published_exams_for_student(
    student_id: str,
    school_id: str,
    name=None,
    exam_type=None,
    subject=None,
    code=None,
    session: AsyncSession | None = None,
) -> list[dict]:

    async def _do_get(s: AsyncSession):
        stmt = (
            select(Exam)
            .join(Exam.teacher)
            .where(Exam.isPublished == True, Teacher.schoolId == school_id)  # noqa: E712
            .options(
                *EXAM_OPTIONS,
                selectinload(Exam.studentExams),
            )
        )

        if code:
            stmt = stmt.where(Exam.examCode.ilike(f"%{code.strip()}%"))
        elif name:
            stmt = stmt.where(
                (Exam.name.ilike(f"%{name}%")) | (Exam.examCode.ilike(f"%{name}%"))
            )
        if exam_type:
            stmt = stmt.where(Exam.type == exam_type)
        if subject:
            stmt = stmt.where(Exam.subject == subject)

        exams = (await s.execute(stmt)).scalars().unique().all()

        results = []
        for e in exams:
            e_resp = ExamResponse.model_validate(e)
            e_dict = e_resp.model_dump()

            # Find matching studentExam for student_id
            student_exams = [
                se for se in (e.studentExams or []) if se.studentId == student_id
            ]
            if student_exams:
                st_status = student_exams[0].status
                e_dict["studentStatus"] = (
                    st_status.value if hasattr(st_status, "value") else str(st_status)
                )
                e_dict["attemptId"] = student_exams[0].id
            else:
                e_dict["studentStatus"] = "NOT_ATTEMPTED"
                e_dict["attemptId"] = None

            results.append(e_dict)

        return results

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def update_exam(
    exam_id: str, update_data: ExamUpdateRequest, session: AsyncSession | None = None
) -> ExamResponse | None:
    update_dict = update_data.model_dump(exclude_unset=True, exclude={"questions"})

    async def _do_update(s: AsyncSession):
        stmt = select(Exam).where(Exam.id == exam_id).options(*EXAM_OPTIONS)
        exam = (await s.execute(stmt)).scalar_one_or_none()
        if not exam:
            return None

        for k, v in update_dict.items():
            setattr(exam, k, v)

        await s.commit()

        res_stmt = select(Exam).where(Exam.id == exam_id).options(*EXAM_OPTIONS)
        updated = (await s.execute(res_stmt)).scalar_one_or_none()
        return ExamResponse.model_validate(updated) if updated else None

    if session:
        return await _do_update(session)
    async with db.get_session() as s:
        return await _do_update(s)


async def release_results(
    exam_id: str, session: AsyncSession | None = None
) -> ExamResponse | None:
    async def _do_release(s: AsyncSession):
        stmt = select(Exam).where(Exam.id == exam_id).options(*EXAM_OPTIONS)
        exam = (await s.execute(stmt)).scalar_one_or_none()
        if not exam:
            return None

        exam.isResultsReleased = True
        await s.commit()

        res_stmt = select(Exam).where(Exam.id == exam_id).options(*EXAM_OPTIONS)
        updated = (await s.execute(res_stmt)).scalar_one_or_none()
        return ExamResponse.model_validate(updated) if updated else None

    if session:
        return await _do_release(session)
    async with db.get_session() as s:
        return await _do_release(s)
