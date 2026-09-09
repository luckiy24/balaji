from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime

# Auth & User schemas
class UserBase(BaseModel):
    name: str
    email: str
    employee_id: str
    organization: str
    department: str
    role_id: int
    experience_years: float
    is_admin: bool = False
    is_sme: bool = False

class UserResponse(UserBase):
    id: int
    role_name: Optional[str] = None
    role_code: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DemoLoginRequest(BaseModel):
    user_id: int

class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = "demo123"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Competency & Role Schemas
class CompetencyResponse(BaseModel):
    id: int
    name: str
    code: str
    domain: str
    description: Optional[str] = None
    level_1_desc: Optional[str] = None
    level_2_desc: Optional[str] = None
    level_3_desc: Optional[str] = None
    level_4_desc: Optional[str] = None
    level_5_desc: Optional[str] = None

    class Config:
        from_attributes = True

class RoleCompetencyResponse(BaseModel):
    competency_id: int
    competency_name: str
    required_level: int
    importance: str

class RoleResponse(BaseModel):
    id: int
    name: str
    code: str
    department: str
    description: Optional[str] = None
    competencies: List[RoleCompetencyResponse] = []

    class Config:
        from_attributes = True

# Competency Gap Schema
class CompetencyGapItem(BaseModel):
    competency_id: int
    competency_name: str
    domain: str
    required_level: int
    assessed_level: int
    level_gap: int # required - assessed
    baseline_score: float
    current_score: float
    score_delta: float
    gap_category: str # High Gap, Moderate Gap, Good, Strong
    importance: str
    priority_score: float # Computed priority for ranking
    rank: int

class CompetencyGapReport(BaseModel):
    user_id: int
    user_name: str
    role_name: str
    overall_competency_score: float
    high_gaps_count: int
    moderate_gaps_count: int
    good_count: int
    strong_count: int
    ranked_gaps: List[CompetencyGapItem]

# Diagnostic Assessment Schemas
class QuestionOption(BaseModel):
    id: str # A, B, C, D
    text: str

class DiagnosticQuestionResponse(BaseModel):
    id: int
    competency_id: int
    competency_name: str
    question_text: str
    options: List[QuestionOption]
    difficulty: str
    source_reference: Optional[str] = None

class DiagnosticSubmitItem(BaseModel):
    question_id: int
    selected_option: str
    time_spent_seconds: int = 0

class DiagnosticSubmitRequest(BaseModel):
    assessment_id: int
    answers: List[DiagnosticSubmitItem]

class DiagnosticResultResponse(BaseModel):
    attempt_id: int
    overall_score: float
    total_questions: int
    correct_count: int
    competency_scores: Dict[str, float]
    gap_classifications: Dict[str, str]
    priority_gaps: List[str]
    strong_areas: List[str]
    improvement_plan: List[str]

# Course & Recommendation Schemas
class CourseResponse(BaseModel):
    id: int
    igot_course_id: str
    title: str
    provider: str
    competency_id: int
    competency_name: str
    target_level: int
    duration_hours: float
    rating: float
    thumbnail_url: Optional[str] = None
    syllabus_summary: Optional[str] = None
    is_igot_verified: bool

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    recommendation_id: int
    course: CourseResponse
    priority_rank: int
    reason: str
    gap_level_addressed: int
    progress_percentage: float = 0.0
    status: str = "NOT_STARTED"

# Document & MCQ Generator Schemas
class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size_bytes: int
    page_count: int
    extracted_topics: List[str]
    processing_status: str
    ocr_applied: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True

class DocumentChunkResponse(BaseModel):
    chunk_index: int
    page_number: int
    section_title: Optional[str] = None
    content: str
    token_count: int

class GenerateQuizRequest(BaseModel):
    document_id: int
    num_questions: int = 5
    difficulty: str = "Mixed" # Easy, Medium, Hard, Mixed
    competency_id: Optional[int] = None

class GeneratedMCQItem(BaseModel):
    id: int
    question_text: str
    options: Dict[str, str] # {"A": ..., "B": ..., "C": ..., "D": ...}
    correct_option: str
    explanation: str
    difficulty: str
    competency_name: str
    source_document: str
    source_page: Optional[int] = None
    source_snippet: Optional[str] = None
    grounding_score: float
    needs_review: bool

# Interactive Quiz Session Schemas
class QuizStartResponse(BaseModel):
    quiz_session_id: str
    document_id: Optional[int]
    document_title: Optional[str]
    questions: List[Dict[str, Any]]
    duration_minutes: int = 15

class QuizAnswerSubmit(BaseModel):
    question_id: int
    selected_option: str
    time_spent: int = 0

class QuizSubmitRequest(BaseModel):
    document_id: Optional[int] = None
    answers: List[QuizAnswerSubmit]

class QuizEvaluationResponse(BaseModel):
    quiz_attempt_id: int
    overall_score: float
    total_questions: int
    correct_count: int
    competency_performance: Dict[str, float]
    difficulty_performance: Dict[str, float]
    strong_areas: List[str]
    weak_areas: List[str]
    updated_competency_scores: Dict[str, Dict[str, Any]] # e.g. {"Sampling Methods": {"before": 42.0, "after": 78.0, "delta": +36.0}}
    adaptive_recommendation: str
    questions_detail: List[Dict[str, Any]]

# Dashboards
class LearnerDashboardResponse(BaseModel):
    user: UserResponse
    overall_competency_score: float
    recent_improvement: float
    competency_scores: List[Dict[str, Any]]
    priority_gaps: List[CompetencyGapItem]
    recommended_courses: List[RecommendationResponse]
    recent_quizzes: List[Dict[str, Any]]
    completed_courses_count: int

class AdminDashboardResponse(BaseModel):
    total_learners: int
    average_competency: float
    top_competency_gaps: List[Dict[str, Any]]
    department_comparison: List[Dict[str, Any]]
    role_competency_matrix: List[Dict[str, Any]]
    course_completion_stats: Dict[str, Any]
    training_effectiveness: Dict[str, Any]
