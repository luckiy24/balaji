from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    organization = Column(String(150), default="Ministry of Statistics and Programme Implementation (MoSPI)")
    department = Column(String(100), default="National Sample Survey Office (NSSO)")
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    experience_years = Column(Float, default=3.5)
    avatar_url = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_sme = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    role = relationship("Role", back_populates="users")
    assessment_attempts = relationship("AssessmentAttempt", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    course_recommendations = relationship("CourseRecommendation", back_populates="user", cascade="all, delete-orphan")
    learning_progress = relationship("LearningProgress", back_populates="user", cascade="all, delete-orphan")
    competency_scores = relationship("CompetencyScore", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    department = Column(String(100), default="Statistical Cadre")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    users = relationship("User", back_populates="role")
    role_competencies = relationship("RoleCompetency", back_populates="role", cascade="all, delete-orphan")


class Competency(Base):
    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    domain = Column(String(100), default="Official Statistics Core")
    description = Column(Text, nullable=True)
    level_1_desc = Column(Text, nullable=True) # Beginner
    level_2_desc = Column(Text, nullable=True) # Basic
    level_3_desc = Column(Text, nullable=True) # Intermediate
    level_4_desc = Column(Text, nullable=True) # Advanced
    level_5_desc = Column(Text, nullable=True) # Expert
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    role_competencies = relationship("RoleCompetency", back_populates="competency")
    questions = relationship("Question", back_populates="competency")
    generated_questions = relationship("GeneratedQuestion", back_populates="competency")
    courses = relationship("Course", back_populates="competency")
    user_scores = relationship("CompetencyScore", back_populates="competency")


class RoleCompetency(Base):
    __tablename__ = "role_competencies"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    required_level = Column(Integer, default=3) # 1 to 5
    importance = Column(String(20), default="High") # Critical, High, Medium

    role = relationship("Role", back_populates="role_competencies")
    competency = relationship("Competency", back_populates="role_competencies")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    assessment_type = Column(String(50), default="DIAGNOSTIC") # DIAGNOSTIC, ADAPTIVE, ROLE_CERTIFICATION
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=30)
    total_questions = Column(Integer, default=20)
    created_at = Column(DateTime, default=utcnow)

    questions = relationship("Question", back_populates="assessment")
    attempts = relationship("AssessmentAttempt", back_populates="assessment")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_option = Column(String(5), nullable=False) # A, B, C, D
    difficulty = Column(String(20), default="Medium") # Easy, Medium, Hard
    explanation = Column(Text, nullable=False)
    source_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    assessment = relationship("Assessment", back_populates="questions")
    competency = relationship("Competency", back_populates="questions")
    answers = relationship("AssessmentAnswer", back_populates="question")


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    score_percentage = Column(Float, default=0.0)
    total_questions = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    status = Column(String(30), default="IN_PROGRESS") # IN_PROGRESS, COMPLETED
    summary_report = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="assessment_attempts")
    assessment = relationship("Assessment", back_populates="attempts")
    answers = relationship("AssessmentAnswer", back_populates="attempt", cascade="all, delete-orphan")


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("assessment_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_option = Column(String(5), nullable=True)
    is_correct = Column(Boolean, default=False)
    time_spent_seconds = Column(Integer, default=0)

    attempt = relationship("AssessmentAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False) # PDF, DOCX, PPTX, TXT
    file_size_bytes = Column(Integer, default=0)
    page_count = Column(Integer, default=1)
    extracted_topics = Column(Text, nullable=True) # JSON list or comma-separated
    processing_status = Column(String(30), default="PENDING") # PENDING, PROCESSING, READY, FAILED
    ocr_applied = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    generated_questions = relationship("GeneratedQuestion", back_populates="document", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1)
    section_title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)

    document = relationship("Document", back_populates="chunks")


class GeneratedQuestion(Base):
    __tablename__ = "generated_questions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_option = Column(String(5), nullable=False)
    difficulty = Column(String(20), default="Medium") # Easy, Medium, Hard
    explanation = Column(Text, nullable=False)
    source_page = Column(Integer, nullable=True)
    source_snippet = Column(Text, nullable=True)
    grounding_score = Column(Float, default=1.0)
    is_grounded = Column(Boolean, default=True)
    needs_review = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    document = relationship("Document", back_populates="generated_questions")
    competency = relationship("Competency", back_populates="generated_questions")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    igot_course_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    provider = Column(String(150), default="iGOT Karmayogi / NSSTA")
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    target_level = Column(Integer, default=3) # Level 1 to 5
    duration_hours = Column(Float, default=10.0)
    rating = Column(Float, default=4.8)
    thumbnail_url = Column(String(255), nullable=True)
    syllabus_summary = Column(Text, nullable=True)
    is_igot_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    competency = relationship("Competency", back_populates="courses")
    recommendations = relationship("CourseRecommendation", back_populates="course")
    learning_progress = relationship("LearningProgress", back_populates="course")


class CourseRecommendation(Base):
    __tablename__ = "course_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    priority_score = Column(Float, default=1.0) # Lower is higher priority or ranking
    rank = Column(Integer, default=1)
    reason = Column(Text, nullable=False) # "Why am I seeing this?"
    gap_level = Column(Integer, default=2) # e.g. 2 levels gap
    recommended_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="course_recommendations")
    course = relationship("Course", back_populates="recommendations")


class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    progress_percentage = Column(Float, default=0.0)
    status = Column(String(30), default="NOT_STARTED") # NOT_STARTED, IN_PROGRESS, COMPLETED
    hours_spent = Column(Float, default=0.0)
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    last_accessed = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="learning_progress")
    course = relationship("Course", back_populates="learning_progress")


class CompetencyScore(Base):
    __tablename__ = "competency_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    baseline_score = Column(Float, default=50.0) # e.g. 42.0%
    current_score = Column(Float, default=50.0) # e.g. 78.0%
    previous_score = Column(Float, default=50.0)
    assessed_level = Column(Integer, default=2) # Level 1 to 5
    gap_category = Column(String(30), default="Moderate Gap") # High Gap, Moderate Gap, Good, Strong
    last_assessed_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="competency_scores")
    competency = relationship("Competency", back_populates="user_scores")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    quiz_type = Column(String(50), default="DOCUMENT_GROUNDED") # DOCUMENT_GROUNDED, ADAPTIVE_PRACTICE
    score_percentage = Column(Float, default=0.0)
    total_questions = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    time_taken_seconds = Column(Integer, default=0)
    adaptive_difficulty_reached = Column(String(20), default="Medium")
    performance_summary = Column(Text, nullable=True) # JSON of competency/difficulty breakdown
    weak_topics = Column(Text, nullable=True) # Comma-separated or JSON list
    completed_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="quiz_attempts")
    document = relationship("Document", back_populates="quiz_attempts")
