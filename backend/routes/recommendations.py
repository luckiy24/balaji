from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models import User, Course, LearningProgress
from backend.schemas import RecommendationResponse, CourseResponse
from backend.routes.auth import get_current_user
from backend.services.recommendation_engine import recommendation_engine

router = APIRouter(prefix="/api", tags=["Recommendations & Course Catalogue"])

@router.get("/recommendations", response_model=List[RecommendationResponse])
def get_personalized_recommendations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns personalized iGOT Karmayogi course recommendations tailored
    to closing the user's priority competency gaps.
    """
    recs = recommendation_engine.generate_recommendations(db, user)
    return recs

@router.get("/courses", response_model=List[CourseResponse])
def get_all_courses(
    search: Optional[str] = None,
    competency_name: Optional[str] = None,
    provider: Optional[str] = None,
    target_level: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Returns all courses in the iGOT-compatible course catalogue with search and filter options.
    """
    query = db.query(Course)
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            Course.title.ilike(search_fmt) | 
            Course.syllabus_summary.ilike(search_fmt) |
            Course.provider.ilike(search_fmt)
        )
    if competency_name:
        query = query.join(Course.competency).filter(Course.competency.has(name=competency_name))
    if provider:
        query = query.filter(Course.provider.ilike(f"%{provider.strip()}%"))
    if target_level:
        query = query.filter(Course.target_level == target_level)

    courses = query.order_by(Course.rating.desc(), Course.title.asc()).all()
    results = []
    for c in courses:
        results.append(CourseResponse(
            id=c.id,
            igot_course_id=c.igot_course_id,
            title=c.title,
            provider=c.provider,
            competency_id=c.competency_id,
            competency_name=c.competency.name if c.competency else "Official Statistics",
            target_level=c.target_level,
            duration_hours=c.duration_hours,
            rating=c.rating,
            thumbnail_url=c.thumbnail_url,
            syllabus_summary=c.syllabus_summary,
            is_igot_verified=c.is_igot_verified
        ))
    return results

@router.post("/courses/{course_id}/enroll")
def enroll_in_course(
    course_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enrolls the current user in an iGOT course or advances progress.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found in catalogue")

    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == user.id,
        LearningProgress.course_id == course.id
    ).first()

    if not progress:
        progress = LearningProgress(
            user_id=user.id,
            course_id=course.id,
            progress_percentage=25.0,
            status="IN_PROGRESS",
            hours_spent=1.5
        )
        db.add(progress)
    else:
        new_pct = min(100.0, progress.progress_percentage + 25.0)
        progress.progress_percentage = new_pct
        progress.status = "COMPLETED" if new_pct >= 100.0 else "IN_PROGRESS"
        progress.hours_spent += 2.0

    db.commit()
    return {
        "message": f"Successfully enrolled in {course.title}",
        "course_id": course.id,
        "progress_percentage": progress.progress_percentage,
        "status": progress.status
    }

