from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.database import get_db
from backend.models import Assessment, Question, AssessmentAttempt, User
from backend.schemas import (
    DiagnosticQuestionResponse, QuestionOption,
    DiagnosticSubmitRequest, DiagnosticResultResponse
)
from backend.routes.auth import get_current_user
from backend.services.assessment_service import assessment_service

router = APIRouter(prefix="/api/assessment", tags=["Diagnostic Assessments"])

@router.post("/start")
def start_diagnostic_assessment(
    assessment_id: int = 1,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Retrieves all diagnostic questions for an assessment.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        # Pick first available assessment
        assessment = db.query(Assessment).first()
        if not assessment:
            raise HTTPException(status_code=404, detail="No diagnostic assessments configured")

    questions = db.query(Question).filter(Question.assessment_id == assessment.id).all()
    
    formatted_questions = []
    for q in questions:
        formatted_questions.append({
            "id": q.id,
            "competency_id": q.competency_id,
            "competency_name": q.competency.name if q.competency else "Statistics Core",
            "question_text": q.question_text,
            "options": [
                {"id": "A", "text": q.option_a},
                {"id": "B", "text": q.option_b},
                {"id": "C", "text": q.option_c},
                {"id": "D", "text": q.option_d},
            ],
            "difficulty": q.difficulty,
            "source_reference": q.source_reference
        })

    return {
        "assessment_id": assessment.id,
        "title": assessment.title,
        "duration_minutes": assessment.duration_minutes,
        "total_questions": len(formatted_questions),
        "questions": formatted_questions
    }

@router.post("/submit", response_model=DiagnosticResultResponse)
def submit_diagnostic_assessment(
    req: DiagnosticSubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Evaluates submitted answers, updates user competency scores,
    and returns comprehensive diagnostic report.
    """
    answers_dict = [a.dict() for a in req.answers]
    result = assessment_service.evaluate_diagnostic(db, user, req.assessment_id, answers_dict)
    return result

@router.get("/results/{attempt_id}")
def get_assessment_results(
    attempt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    attempt = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.id == attempt_id,
        AssessmentAttempt.user_id == user.id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")

    answers = attempt.answers
    comp_breakdown: Dict[str, Dict[str, int]] = {}
    for a in answers:
        comp_name = a.question.competency.name if a.question and a.question.competency else "Core"
        if comp_name not in comp_breakdown:
            comp_breakdown[comp_name] = {"total": 0, "correct": 0}
        comp_breakdown[comp_name]["total"] += 1
        if a.is_correct:
            comp_breakdown[comp_name]["correct"] += 1

    return {
        "attempt_id": attempt.id,
        "assessment_title": attempt.assessment.title if attempt.assessment else "Diagnostic Assessment",
        "score_percentage": attempt.score_percentage,
        "total_questions": attempt.total_questions,
        "correct_count": attempt.correct_count,
        "competency_scores": {k: round(v["correct"] / v["total"] * 100.0, 1) for k, v in comp_breakdown.items()},
        "completed_at": attempt.completed_at
    }
