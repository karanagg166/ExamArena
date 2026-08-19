"""Exams, sections, questions, and option bank seeding module for ExamArena."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Exam,
    ExamSection,
    Question,
    QuestionOption,
    Teacher,
    User,
    generate_exam_code,
)
from seeds.data import EXAMS_FIXTURES


async def seed_exams(
    session: AsyncSession, teachers_map: dict[str, tuple[User, Teacher]]
) -> dict[str, Exam]:
    """Seed comprehensive exams with sections, questions, and option banks."""
    print("\n📝 Creating Exams, Question Banks, and Sections...", flush=True)
    created_exams = {}

    for e_cfg in EXAMS_FIXTURES:
        t_prof = teachers_map[e_cfg["teacherKey"]][1]
        e_stmt = select(Exam).where(Exam.name == e_cfg["name"])
        exam = (await session.execute(e_stmt)).scalar_one_or_none()

        if not exam:
            exam = Exam(
                name=e_cfg["name"],
                description=e_cfg["description"],
                scheduledAt=e_cfg["scheduledAt"],
                duration=e_cfg["duration"],
                maxMarks=e_cfg["maxMarks"],
                instructions=e_cfg["instructions"],
                isPublished=e_cfg["isPublished"],
                isPublic=e_cfg["isPublic"],
                isResultsReleased=e_cfg["isResultsReleased"],
                accessPassword=e_cfg.get("accessPassword"),
                subject=e_cfg["subject"],
                type=e_cfg["type"],
                teacherId=t_prof.id,
                examCode=generate_exam_code(),
            )
            session.add(exam)
            await session.commit()
            await session.refresh(exam)
            print(
                f"  [+] Created Exam: {exam.name} (Code: {exam.examCode})", flush=True
            )

            sections_map = {}
            for s_data in e_cfg.get("sections", []):
                sec_obj = ExamSection(
                    examId=exam.id,
                    name=s_data["name"],
                    description=s_data["description"],
                    questionType=s_data["questionType"],
                    marksPerQuestion=s_data["marksPerQuestion"],
                    sortOrder=s_data["sortOrder"],
                )
                session.add(sec_obj)
                await session.commit()
                await session.refresh(sec_obj)
                sections_map[s_data["name"]] = sec_obj

            for q_data in e_cfg.get("questions", []):
                sec_obj = sections_map.get(q_data["section"])
                q_obj = Question(
                    examId=exam.id,
                    sectionId=sec_obj.id if sec_obj else None,
                    section=q_data["section"],
                    questionNumber=q_data["qNum"],
                    text=q_data["text"],
                    questionType=q_data["type"],
                    marks=q_data["marks"],
                    explanation=q_data["explanation"],
                    wordLimit=q_data.get("wordLimit"),
                )
                session.add(q_obj)
                await session.commit()
                await session.refresh(q_obj)

                for opt_idx, (opt_text, is_corr) in enumerate(
                    q_data.get("options", []), start=1
                ):
                    session.add(
                        QuestionOption(
                            questionId=q_obj.id,
                            optionNumber=opt_idx,
                            text=opt_text,
                            isCorrect=is_corr,
                        )
                    )
            await session.commit()

        created_exams[e_cfg["key"]] = exam

    return created_exams
