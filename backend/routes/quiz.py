from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.database import get_db
from backend.models import Document, GeneratedQuestion, QuizAttempt, User, Competency
from backend.schemas import (
    GenerateQuizRequest, GeneratedMCQItem,
    QuizStartResponse, QuizSubmitRequest, QuizEvaluationResponse
)
from backend.routes.auth import get_current_user
from backend.services.ai_service import ai_service
from backend.services.assessment_service import assessment_service

router = APIRouter(prefix="/api", tags=["AI MCQ Generator & Quiz Engine"])

@router.post("/documents/{document_id}/generate-quiz", response_model=List[GeneratedMCQItem])
def generate_quiz_from_document(
    document_id: int,
    req: GenerateQuizRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Triggers AI / RAG pipeline to generate MCQs strictly grounded in the document.
    Outputs source pages, source excerpts, explanations, and review flags.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    questions = ai_service.generate_grounded_mcqs(
        db=db,
        document=doc,
        num_questions=req.num_questions,
        difficulty=req.difficulty,
        competency_id=req.competency_id
    )

    results = []
    for q in questions:
        results.append(GeneratedMCQItem(
            id=q.id,
            question_text=q.question_text,
            options={
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d
            },
            correct_option=q.correct_option,
            explanation=q.explanation,
            difficulty=q.difficulty,
            competency_name=q.competency.name if q.competency else "Official Statistics",
            source_document=doc.filename,
            source_page=q.source_page,
            source_snippet=q.source_snippet,
            grounding_score=q.grounding_score,
            needs_review=q.needs_review
        ))
    return results

@router.get("/documents/{document_id}/generated-questions", response_model=List[GeneratedMCQItem])
def get_generated_questions_for_doc(
    document_id: int,
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    questions = db.query(GeneratedQuestion).filter(GeneratedQuestion.document_id == document_id).all()
    results = []
    for q in questions:
        results.append(GeneratedMCQItem(
            id=q.id,
            question_text=q.question_text,
            options={
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d
            },
            correct_option=q.correct_option,
            explanation=q.explanation,
            difficulty=q.difficulty,
            competency_name=q.competency.name if q.competency else "Official Statistics",
            source_document=doc.filename,
            source_page=q.source_page,
            source_snippet=q.source_snippet,
            grounding_score=q.grounding_score,
            needs_review=q.needs_review
        ))
    return results

@router.post("/quiz/start", response_model=QuizStartResponse)
def start_quiz_session(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Initializes an interactive quiz session from generated MCQs.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    questions = db.query(GeneratedQuestion).filter(GeneratedQuestion.document_id == document_id).all()
    if not questions:
        # Generate automatically on the fly if none exist
        questions = ai_service.generate_grounded_mcqs(db, doc, num_questions=5, difficulty="Mixed")

    formatted = []
    for q in questions:
        formatted.append({
            "id": q.id,
            "question_text": q.question_text,
            "options": [
                {"id": "A", "text": q.option_a},
                {"id": "B", "text": q.option_b},
                {"id": "C", "text": q.option_c},
                {"id": "D", "text": q.option_d}
            ],
            "difficulty": q.difficulty,
            "competency_name": q.competency.name if q.competency else "Official Statistics",
            "source_page": q.source_page
        })

    return QuizStartResponse(
        quiz_session_id=f"quiz-sess-{doc.id}-{int(user.id)}",
        document_id=doc.id,
        document_title=doc.filename,
        questions=formatted,
        duration_minutes=15
    )

@router.post("/quiz/submit", response_model=QuizEvaluationResponse)
def submit_quiz_session(
    req: QuizSubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Submits quiz responses, computes score, adapts difficulty,
    and updates competency scores (Closing the Learning Loop).
    """
    answers_dict = [a.dict() for a in req.answers]
    doc_id = req.document_id or 1
    eval_result = assessment_service.evaluate_quiz(db, user, doc_id, answers_dict)
    return eval_result

@router.get("/quiz/results/{attempt_id}")
def get_quiz_attempt_results(
    attempt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")

    return {
        "attempt_id": attempt.id,
        "score_percentage": attempt.score_percentage,
        "total_questions": attempt.total_questions,
        "correct_count": attempt.correct_count,
        "adaptive_difficulty_reached": attempt.adaptive_difficulty_reached,
        "weak_topics": attempt.weak_topics.split(",") if attempt.weak_topics else [],
        "completed_at": attempt.completed_at
    }
