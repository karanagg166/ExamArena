import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(UTC)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


# ── ENUMS ──────────────────────────────────────────────────────
class Role(enum.StrEnum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ADMIN = "ADMIN"
    PRINCIPAL = "PRINCIPAL"


class Subject(enum.StrEnum):
    MATHS = "MATHS"
    SCIENCE = "SCIENCE"
    HISTORY = "HISTORY"
    LITERATURE = "LITERATURE"
    ART = "ART"
    MUSIC = "MUSIC"
    PHYSICAL_EDUCATION = "PHYSICAL_EDUCATION"


class ExamType(enum.StrEnum):
    MIDTERM = "MIDTERM"
    FINAL = "FINAL"
    QUIZ = "QUIZ"
    ASSIGNMENT = "ASSIGNMENT"
    MOCK = "MOCK"


class Qualification(enum.StrEnum):
    BACHELORS = "BACHELORS"
    MASTERS = "MASTERS"
    PHD = "PHD"
    OTHER = "OTHER"
    BACHELORS_WITH_HONORS = "BACHELORS_WITH_HONORS"


class QuestionType(enum.StrEnum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    MULTIPLE_SELECT = "MULTIPLE_SELECT"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    ESSAY = "ESSAY"


class SchoolType(enum.StrEnum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    CHARTER = "CHARTER"
    INTERNATIONAL = "INTERNATIONAL"


class StudentExamStatus(enum.StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    GRADED = "GRADED"
    EXPIRED = "EXPIRED"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"


class GradingStatus(enum.StrEnum):
    PENDING = "PENDING"
    AUTO_GRADED = "AUTO_GRADED"
    MANUALLY_GRADED = "MANUALLY_GRADED"


class Correctness(enum.StrEnum):
    FULLY_CORRECT = "FULLY_CORRECT"
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT"
    INCORRECT = "INCORRECT"


class JoinRequestStatus(enum.StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ── MODELS ─────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "User"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    phoneNo: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[Role] = mapped_column(
        SQLEnum(Role, native_enum=False), default=Role.STUDENT, nullable=False
    )
    dateOfBirth: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    city: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    pincode: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    school: Mapped[list["School"]] = relationship(
        "School", back_populates="user", cascade="all, delete-orphan"
    )
    student: Mapped["Student | None"] = relationship(
        "Student", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    teacher: Mapped["Teacher | None"] = relationship(
        "Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    joinRequests: Mapped[list["ClassJoinRequest"]] = relationship(
        "ClassJoinRequest", back_populates="user", cascade="all, delete-orphan"
    )


class Student(Base):
    __tablename__ = "Student"
    __table_args__ = (
        UniqueConstraint("classId", "rollNo", name="student_classid_rollno_key"),
        Index("student_classid_idx", "classId"),
        Index("student_userid_idx", "userId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    userId: Mapped[str] = mapped_column(
        String,
        ForeignKey("User.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    rollNo: Mapped[str] = mapped_column(String, nullable=False)
    parentName: Mapped[str | None] = mapped_column(String, nullable=True)
    parentEmail: Mapped[str | None] = mapped_column(String, nullable=True)
    fatherName: Mapped[str | None] = mapped_column(String, nullable=True)
    fatherEmail: Mapped[str | None] = mapped_column(String, nullable=True)
    fatherPhoneNo: Mapped[str | None] = mapped_column(String, nullable=True)
    motherName: Mapped[str | None] = mapped_column(String, nullable=True)
    motherEmail: Mapped[str | None] = mapped_column(String, nullable=True)
    motherPhoneNo: Mapped[str | None] = mapped_column(String, nullable=True)
    guardianName: Mapped[str | None] = mapped_column(String, nullable=True)
    guardianRelation: Mapped[str | None] = mapped_column(String, nullable=True)
    guardianEmail: Mapped[str | None] = mapped_column(String, nullable=True)
    guardianPhoneNo: Mapped[str | None] = mapped_column(String, nullable=True)
    dateOfAdmission: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    classId: Mapped[str] = mapped_column(
        String,
        ForeignKey("SchoolClass.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schoolId: Mapped[str] = mapped_column(
        String, ForeignKey("School.id", ondelete="CASCADE"), nullable=False
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="student")
    schoolClass: Mapped["SchoolClass"] = relationship(
        "SchoolClass", back_populates="students"
    )
    school: Mapped["School"] = relationship("School", back_populates="students")
    studentExams: Mapped[list["StudentExam"]] = relationship(
        "StudentExam", back_populates="student", cascade="all, delete-orphan"
    )

    @property
    def className(self) -> str | None:
        return self.schoolClass.name if self.schoolClass else None

    @property
    def schoolName(self) -> str | None:
        return self.school.name if self.school else None


class Teacher(Base):
    __tablename__ = "Teacher"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    userId: Mapped[str] = mapped_column(
        String,
        ForeignKey("User.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    qualification: Mapped[str] = mapped_column(String, default="[]", nullable=False)
    experience: Mapped[int] = mapped_column(Integer, nullable=False)
    department: Mapped[str] = mapped_column(String, nullable=False)
    subjects: Mapped[str] = mapped_column(String, default="[]", nullable=False)
    schoolId: Mapped[str | None] = mapped_column(
        String, ForeignKey("School.id"), nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="teacher")
    school: Mapped["School | None"] = relationship("School", back_populates="teachers")
    exams: Mapped[list["Exam"]] = relationship(
        "Exam", back_populates="teacher", cascade="all, delete-orphan"
    )
    principal: Mapped["Principal | None"] = relationship(
        "Principal",
        back_populates="teacher",
        uselist=False,
        cascade="all, delete-orphan",
    )
    teaches: Mapped[list["TeacherClass"]] = relationship(
        "TeacherClass", back_populates="teacher", cascade="all, delete-orphan"
    )


class TeacherClass(Base):
    __tablename__ = "TeacherClass"
    __table_args__ = (
        UniqueConstraint(
            "teacherId", "classId", name="teacherclass_teacherid_classid_key"
        ),
        Index("teacherclass_teacherid_idx", "teacherId"),
        Index("teacherclass_classid_idx", "classId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    teacherId: Mapped[str] = mapped_column(
        String, ForeignKey("Teacher.id", ondelete="CASCADE"), nullable=False
    )
    classId: Mapped[str] = mapped_column(
        String, ForeignKey("SchoolClass.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[Subject] = mapped_column(
        SQLEnum(Subject, native_enum=False), nullable=False
    )

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="teaches")
    schoolClass: Mapped["SchoolClass"] = relationship(
        "SchoolClass", back_populates="teachers"
    )


class SchoolClass(Base):
    __tablename__ = "SchoolClass"
    __table_args__ = (
        UniqueConstraint(
            "schoolId", "year", "section", name="schoolclass_schoolid_year_section_key"
        ),
        Index("schoolclass_schoolid_idx", "schoolId"),
        Index("schoolclass_teacherid_idx", "teacherId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[str] = mapped_column(String, nullable=False)
    section: Mapped[str] = mapped_column(String, default="A", nullable=False)
    schoolId: Mapped[str] = mapped_column(
        String, ForeignKey("School.id", ondelete="CASCADE"), nullable=False
    )
    teacherId: Mapped[str | None] = mapped_column(String, nullable=True)
    joinCode: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    nextRollNo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    school: Mapped["School"] = relationship("School", back_populates="classes")
    students: Mapped[list["Student"]] = relationship(
        "Student", back_populates="schoolClass", cascade="all, delete-orphan"
    )
    teachers: Mapped[list["TeacherClass"]] = relationship(
        "TeacherClass", back_populates="schoolClass", cascade="all, delete-orphan"
    )
    joinRequests: Mapped[list["ClassJoinRequest"]] = relationship(
        "ClassJoinRequest", back_populates="schoolClass", cascade="all, delete-orphan"
    )


class ClassJoinRequest(Base):
    __tablename__ = "ClassJoinRequest"
    __table_args__ = (
        UniqueConstraint(
            "studentUserId",
            "classId",
            name="classjoinrequest_studentuserid_classid_key",
        ),
        Index("classjoinrequest_classid_idx", "classId"),
        Index("classjoinrequest_studentuserid_idx", "studentUserId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    studentUserId: Mapped[str] = mapped_column(
        String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False
    )
    classId: Mapped[str] = mapped_column(
        String, ForeignKey("SchoolClass.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[JoinRequestStatus] = mapped_column(
        SQLEnum(JoinRequestStatus, name="JoinRequestStatus"),
        default=JoinRequestStatus.PENDING,
        nullable=False,
    )
    requestedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    decidedAt: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decidedBy: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="joinRequests")
    schoolClass: Mapped["SchoolClass"] = relationship(
        "SchoolClass", back_populates="joinRequests"
    )


class TeacherClassJoinRequest(Base):
    __tablename__ = "TeacherClassJoinRequest"
    __table_args__ = (
        UniqueConstraint(
            "teacherId",
            "classId",
            name="teacherclassjoinrequest_teacherid_classid_key",
        ),
        Index("teacherclassjoinrequest_classid_idx", "classId"),
        Index("teacherclassjoinrequest_teacherid_idx", "teacherId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    teacherId: Mapped[str] = mapped_column(
        String, ForeignKey("Teacher.id", ondelete="CASCADE"), nullable=False
    )
    classId: Mapped[str] = mapped_column(
        String, ForeignKey("SchoolClass.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[Subject | None] = mapped_column(
        SQLEnum(Subject, native_enum=False), nullable=True
    )
    status: Mapped[JoinRequestStatus] = mapped_column(
        SQLEnum(JoinRequestStatus, native_enum=False),
        default=JoinRequestStatus.PENDING,
        nullable=False,
    )
    requestedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    decidedAt: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decidedBy: Mapped[str | None] = mapped_column(String, nullable=True)

    teacher: Mapped["Teacher"] = relationship("Teacher")
    schoolClass: Mapped["SchoolClass"] = relationship("SchoolClass")


class TeacherSchoolJoinRequest(Base):
    __tablename__ = "TeacherSchoolJoinRequest"
    __table_args__ = (
        UniqueConstraint(
            "teacherId",
            "schoolId",
            name="teacherschooljoinrequest_teacherid_schoolid_key",
        ),
        Index("teacherschooljoinrequest_schoolid_idx", "schoolId"),
        Index("teacherschooljoinrequest_teacherid_idx", "teacherId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    teacherId: Mapped[str] = mapped_column(
        String, ForeignKey("Teacher.id", ondelete="CASCADE"), nullable=False
    )
    schoolId: Mapped[str] = mapped_column(
        String, ForeignKey("School.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[JoinRequestStatus] = mapped_column(
        SQLEnum(JoinRequestStatus, native_enum=False),
        default=JoinRequestStatus.PENDING,
        nullable=False,
    )
    requestedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    decidedAt: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decidedBy: Mapped[str | None] = mapped_column(String, nullable=True)

    teacher: Mapped["Teacher"] = relationship("Teacher")
    school: Mapped["School"] = relationship("School")


class Principal(Base):
    __tablename__ = "Principal"
    __table_args__ = (
        Index("principal_schoolid_idx", "schoolId"),
        Index("principal_teacherid_idx", "teacherId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    experience: Mapped[int] = mapped_column(Integer, nullable=False)
    schoolId: Mapped[str | None] = mapped_column(
        String, ForeignKey("School.id", ondelete="CASCADE"), nullable=True
    )
    teacherId: Mapped[str] = mapped_column(
        String,
        ForeignKey("Teacher.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    school: Mapped["School | None"] = relationship(
        "School", back_populates="principals"
    )
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="principal")


class School(Base):
    __tablename__ = "School"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    createdBy: Mapped[str] = mapped_column(
        String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False
    )
    address: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    pincode: Mapped[str] = mapped_column(String, nullable=False)
    schoolCode: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    type: Mapped[SchoolType] = mapped_column(
        SQLEnum(SchoolType, native_enum=False),
        default=SchoolType.PUBLIC,
        nullable=False,
    )
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    phoneNo: Mapped[str | None] = mapped_column(String, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="school")
    principals: Mapped[list["Principal"]] = relationship(
        "Principal", back_populates="school", cascade="all, delete-orphan"
    )
    classes: Mapped[list["SchoolClass"]] = relationship(
        "SchoolClass", back_populates="school", cascade="all, delete-orphan"
    )
    students: Mapped[list["Student"]] = relationship(
        "Student", back_populates="school", cascade="all, delete-orphan"
    )
    teachers: Mapped[list["Teacher"]] = relationship("Teacher", back_populates="school")


def generate_exam_code() -> str:
    import secrets
    import string

    chars = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(chars) for _ in range(6))
    return f"EXM-{code}"


class Exam(Base):
    __tablename__ = "Exam"
    __table_args__ = (
        Index("exam_teacherid_idx", "teacherId"),
        Index("exam_examcode_idx", "examCode"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    examCode: Mapped[str] = mapped_column(
        String, default=generate_exam_code, nullable=False
    )
    accessPassword: Mapped[str | None] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    scheduledAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    maxMarks: Mapped[int] = mapped_column(Integer, nullable=False)
    instructions: Mapped[str | None] = mapped_column(String, nullable=True)
    isPublished: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    isPublic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    isResultsReleased: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    negativeMarking: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    negativeMarks: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    subject: Mapped[Subject | None] = mapped_column(
        SQLEnum(Subject, native_enum=False), nullable=True
    )
    type: Mapped[ExamType] = mapped_column(
        SQLEnum(ExamType, native_enum=False), nullable=False
    )
    teacherId: Mapped[str] = mapped_column(
        String, ForeignKey("Teacher.id", ondelete="CASCADE"), nullable=False
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="exams")
    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="exam", cascade="all, delete-orphan"
    )
    studentExams: Mapped[list["StudentExam"]] = relationship(
        "StudentExam", back_populates="exam", cascade="all, delete-orphan"
    )
    sections: Mapped[list["ExamSection"]] = relationship(
        "ExamSection", back_populates="exam", cascade="all, delete-orphan"
    )


class ExamSection(Base):
    __tablename__ = "ExamSection"
    __table_args__ = (
        UniqueConstraint("examId", "name", name="examsection_examid_name_key"),
        UniqueConstraint(
            "examId", "sortOrder", name="examsection_examid_sortorder_key"
        ),
        Index("examsection_examid_idx", "examId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(
        String, nullable=False
    )  # "Section A", "Section B", etc.
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    questionType: Mapped[QuestionType] = mapped_column(
        SQLEnum(QuestionType, native_enum=False), nullable=False
    )
    marksPerQuestion: Mapped[int] = mapped_column(Integer, nullable=False)
    durationMinutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    negativeMarking: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    negativeMarks: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sortOrder: Mapped[int] = mapped_column(Integer, nullable=False)  # A=1, B=2, etc.
    examId: Mapped[str] = mapped_column(
        String, ForeignKey("Exam.id", ondelete="CASCADE"), nullable=False
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    exam: Mapped["Exam"] = relationship("Exam", back_populates="sections")
    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="examSection", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "Question"
    __table_args__ = (
        UniqueConstraint(
            "examId",
            "questionNumber",
            "section",
            name="question_examid_questionnumber_section_key",
        ),
        Index("question_examid_idx", "examId"),
        Index("question_sectionid_idx", "sectionId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    questionNumber: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    section: Mapped[str] = mapped_column(String, default="General", nullable=False)
    marks: Mapped[int] = mapped_column(Integer, nullable=False)
    imageUrl: Mapped[str | None] = mapped_column(String, nullable=True)
    wordLimit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    explanation: Mapped[str | None] = mapped_column(String, nullable=True)
    questionType: Mapped[QuestionType] = mapped_column(
        SQLEnum(QuestionType, native_enum=False),
        default=QuestionType.MULTIPLE_CHOICE,
        nullable=False,
    )
    examId: Mapped[str] = mapped_column(
        String, ForeignKey("Exam.id", ondelete="CASCADE"), nullable=False
    )
    sectionId: Mapped[str | None] = mapped_column(
        String, ForeignKey("ExamSection.id", ondelete="CASCADE"), nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    exam: Mapped["Exam"] = relationship("Exam", back_populates="questions")
    examSection: Mapped["ExamSection | None"] = relationship(
        "ExamSection", back_populates="questions"
    )
    options: Mapped[list["QuestionOption"]] = relationship(
        "QuestionOption", back_populates="question", cascade="all, delete-orphan"
    )
    answers: Mapped[list["StudentExamAnswer"]] = relationship(
        "StudentExamAnswer", back_populates="question", cascade="all, delete-orphan"
    )


class QuestionOption(Base):
    __tablename__ = "QuestionOption"
    __table_args__ = (
        UniqueConstraint(
            "questionId",
            "optionNumber",
            name="questionoption_questionid_optionnumber_key",
        ),
        Index("questionoption_questionid_idx", "questionId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    optionNumber: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    questionId: Mapped[str] = mapped_column(
        String, ForeignKey("Question.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(String, nullable=False)
    isCorrect: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    imageUrl: Mapped[str | None] = mapped_column(String, nullable=True)

    question: Mapped["Question"] = relationship("Question", back_populates="options")
    selectedBy: Mapped[list["SelectedOption"]] = relationship(
        "SelectedOption", back_populates="option", cascade="all, delete-orphan"
    )


class StudentExam(Base):
    __tablename__ = "StudentExam"
    __table_args__ = (
        UniqueConstraint(
            "studentId", "examId", name="studentexam_studentid_examid_key"
        ),
        Index("studentexam_studentid_idx", "studentId"),
        Index("studentexam_examid_idx", "examId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    studentId: Mapped[str] = mapped_column(
        String, ForeignKey("Student.id", ondelete="CASCADE"), nullable=False
    )
    examId: Mapped[str] = mapped_column(
        String, ForeignKey("Exam.id", ondelete="CASCADE"), nullable=False
    )
    marksObtained: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    startedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    submittedAt: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    status: Mapped[StudentExamStatus] = mapped_column(
        SQLEnum(StudentExamStatus, native_enum=False),
        default=StudentExamStatus.IN_PROGRESS,
        nullable=False,
    )

    exam: Mapped["Exam"] = relationship("Exam", back_populates="studentExams")
    student: Mapped["Student"] = relationship("Student", back_populates="studentExams")
    answers: Mapped[list["StudentExamAnswer"]] = relationship(
        "StudentExamAnswer", back_populates="studentExam", cascade="all, delete-orphan"
    )


class StudentExamAnswer(Base):
    __tablename__ = "StudentExamAnswer"
    __table_args__ = (
        UniqueConstraint(
            "studentExamId",
            "questionId",
            name="studentexamanswer_studentexamid_questionid_key",
        ),
        Index("studentexamanswer_studentexamid_idx", "studentExamId"),
        Index("studentexamanswer_questionid_idx", "questionId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    studentExamId: Mapped[str] = mapped_column(
        String, ForeignKey("StudentExam.id", ondelete="CASCADE"), nullable=False
    )
    questionId: Mapped[str] = mapped_column(
        String, ForeignKey("Question.id", ondelete="CASCADE"), nullable=False
    )
    questionType: Mapped[QuestionType] = mapped_column(
        SQLEnum(QuestionType, native_enum=False), nullable=False
    )
    textAnswer: Mapped[str | None] = mapped_column(String, nullable=True)
    marksAwarded: Mapped[float | None] = mapped_column(
        Float, default=0.0, nullable=True
    )
    feedback: Mapped[str | None] = mapped_column(String, nullable=True)
    isCorrect: Mapped[Correctness | None] = mapped_column(
        SQLEnum(Correctness, native_enum=False), nullable=True
    )
    gradingStatus: Mapped[GradingStatus] = mapped_column(
        SQLEnum(GradingStatus, native_enum=False),
        default=GradingStatus.PENDING,
        nullable=False,
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    selectedOptions: Mapped[list["SelectedOption"]] = relationship(
        "SelectedOption",
        back_populates="studentExamAnswer",
        cascade="all, delete-orphan",
    )
    question: Mapped["Question"] = relationship("Question", back_populates="answers")
    studentExam: Mapped["StudentExam"] = relationship(
        "StudentExam", back_populates="answers"
    )


class SelectedOption(Base):
    __tablename__ = "SelectedOption"
    __table_args__ = (
        UniqueConstraint(
            "studentExamAnswerId",
            "optionId",
            name="selectedoption_studentexamanswerid_optionid_key",
        ),
        Index("selectedoption_studentexamanswerid_idx", "studentExamAnswerId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    studentExamAnswerId: Mapped[str] = mapped_column(
        String, ForeignKey("StudentExamAnswer.id", ondelete="CASCADE"), nullable=False
    )
    optionId: Mapped[str] = mapped_column(
        String, ForeignKey("QuestionOption.id", ondelete="CASCADE"), nullable=False
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    option: Mapped["QuestionOption"] = relationship(
        "QuestionOption", back_populates="selectedBy"
    )
    studentExamAnswer: Mapped["StudentExamAnswer"] = relationship(
        "StudentExamAnswer", back_populates="selectedOptions"
    )


class Notification(Base):
    __tablename__ = "Notification"
    __table_args__ = (Index("notification_userid_idx", "userId"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    userId: Mapped[str] = mapped_column(
        String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False
    )
    message: Mapped[str] = mapped_column(String, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="notifications")
