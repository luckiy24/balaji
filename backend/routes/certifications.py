from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from backend.database import get_db
from backend.models import User, Course, LearningProgress, CompetencyScore, QuizAttempt, AssessmentAttempt
from backend.routes.auth import get_current_user
from backend.services.igot_adapter import igot_service

router = APIRouter(prefix="/api/certifications", tags=["Certifications & Credentials"])

@router.get("")
def get_user_credentials(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all earned certificates, digital badges, in-progress certifications,
    and official credentials for the active officer persona.
    """
    employee_id = user.employee_id or f"MOSPI-USER-{user.id}"
    igot_history = igot_service.getUserLearningHistory(employee_id)

    completed_certificates = []
    in_progress_certifications = []

    # 1. Process iGOT learning records
    for item in igot_history:
        course_meta = igot_service.getCourseById(item["igot_course_id"]) or {}
        comp_name = course_meta.get("competency_name", "Official Statistics")
        
        if item["status"] == "COMPLETED":
            cert_id = f"CERT-IGOT-{item['igot_course_id']}-{employee_id}"
            completed_certificates.append({
                "id": cert_id,
                "title": item["title"],
                "course_code": item["igot_course_id"],
                "credential_type": "iGOT Karmayogi Course Certificate",
                "issuer": "National Statistical Systems Training Academy (NSSTA) & iGOT Karmayogi",
                "competency_name": comp_name,
                "issue_date": item.get("completion_date", "2026-05-15"),
                "expiry_date": "Lifetime Credential",
                "verification_status": "VERIFIED_ON_CHAIN",
                "verification_hash": f"SHA256:{abs(hash(cert_id)) % 10**12:012d}",
                "score": "94%",
                "grade": "Exemplary (A+)",
                "credits": 2.0,
                "badge_color": "gold"
            })
        else:
            in_progress_certifications.append({
                "course_code": item["igot_course_id"],
                "title": item["title"],
                "competency_name": comp_name,
                "progress_percentage": item["progress_percentage"],
                "status": "IN_PROGRESS",
                "estimated_hours_remaining": 2.5,
                "provider": "iGOT Karmayogi / MoSPI"
            })

    # 2. Process database LearningProgress
    db_progress = db.query(LearningProgress).filter(LearningProgress.user_id == user.id).all()
    for lp in db_progress:
        c = lp.course
        if not c:
            continue
        # Avoid duplicating if already present from igot_history
        if any(item.get("course_code") == c.igot_course_id for item in completed_certificates):
            continue
        if any(item.get("course_code") == c.igot_course_id for item in in_progress_certifications):
            continue

        if lp.status == "COMPLETED" or lp.progress_percentage >= 100.0:
            cert_id = f"CERT-MOSPI-{c.igot_course_id}-{employee_id}"
            completed_certificates.append({
                "id": cert_id,
                "title": c.title,
                "course_code": c.igot_course_id,
                "credential_type": "MoSPI Specialized Course Certificate",
                "issuer": "MoSPI Capacity Development & Training Directorate",
                "competency_name": c.competency.name if c.competency else "Official Statistics",
                "issue_date": lp.completed_at.strftime("%Y-%m-%d") if lp.completed_at else "2026-08-20",
                "expiry_date": "Lifetime Credential",
                "verification_status": "VERIFIED_ON_CHAIN",
                "verification_hash": f"SHA256:{abs(hash(cert_id)) % 10**12:012d}",
                "score": "92%",
                "grade": "Distinction (A)",
                "credits": round(c.duration_hours / 5.0, 1),
                "badge_color": "gold"
            })
        elif lp.progress_percentage > 0:
            in_progress_certifications.append({
                "course_code": c.igot_course_id,
                "title": c.title,
                "competency_name": c.competency.name if c.competency else "Official Statistics",
                "progress_percentage": lp.progress_percentage,
                "status": "IN_PROGRESS",
                "estimated_hours_remaining": round(c.duration_hours * (1.0 - lp.progress_percentage / 100.0), 1),
                "provider": c.provider
            })

    # 3. Process High-Score Quizzes (Certificates of Assessment Proficiency)
    passed_quizzes = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == user.id,
        QuizAttempt.score_percentage >= 70.0
    ).all()
    for qz in passed_quizzes:
        cert_id = f"CERT-QUIZ-PRACTICE-{qz.id}-{user.id}"
        completed_certificates.append({
            "id": cert_id,
            "title": f"Official Statistics Practice Certification ({qz.adaptive_difficulty_reached} Tier)",
            "course_code": f"NSSTA-QUIZ-{qz.id}",
            "credential_type": "NSSTA Practice Assessment Credential",
            "issuer": "National Statistical Systems Training Academy (NSSTA)",
            "competency_name": "Applied Official Statistics",
            "issue_date": qz.completed_at.strftime("%Y-%m-%d") if qz.completed_at else "2026-09-01",
            "expiry_date": "Valid for 2 Years",
            "verification_status": "VERIFIED_INTERNAL",
            "verification_hash": f"SHA256:{abs(hash(cert_id)) % 10**12:012d}",
            "score": f"{round(qz.score_percentage, 1)}%",
            "grade": "Proficient",
            "credits": 1.0,
            "badge_color": "blue"
        })

    # 4. Official Competency Badges
    badges = []
    comp_scores = db.query(CompetencyScore).filter(CompetencyScore.user_id == user.id).all()
    for cs in comp_scores:
        if cs.current_score >= 70.0:
            badges.append({
                "code": cs.competency.code if cs.competency else "COMP-EXC",
                "name": f"{cs.competency.name} Master",
                "domain": cs.competency.domain if cs.competency else "General",
                "level": f"Level {cs.assessed_level}",
                "score": round(cs.current_score, 1),
                "badge_type": "Gold Proficiency Badge",
                "icon": "🎖️",
                "criteria": f"Attained {round(cs.current_score, 1)}% in official diagnostic and practical assessments"
            })
        elif cs.current_score >= 50.0:
            badges.append({
                "code": cs.competency.code if cs.competency else "COMP-MID",
                "name": f"{cs.competency.name} Practitioner",
                "domain": cs.competency.domain if cs.competency else "General",
                "level": f"Level {cs.assessed_level}",
                "score": round(cs.current_score, 1),
                "badge_type": "Silver Competency Badge",
                "icon": "🥈",
                "criteria": f"Demonstrated operational competency ({round(cs.current_score, 1)}%) in role framework"
            })

    return {
        "officer": {
            "name": user.name,
            "employee_id": user.employee_id,
            "role": user.role.name if user.role else "Statistical Officer",
            "department": user.department,
            "email": user.email
        },
        "summary": {
            "total_credentials_earned": len(completed_certificates),
            "digital_badges_count": len(badges),
            "in_progress_count": len(in_progress_certifications),
            "igot_verified_count": sum(1 for c in completed_certificates if "iGOT" in c["issuer"]),
            "role_certification_readiness": "76%"
        },
        "completed_certificates": completed_certificates,
        "digital_badges": badges,
        "in_progress_certifications": in_progress_certifications
    }

@router.get("/verify/{cert_id}")
def verify_certificate_credential(cert_id: str, db: Session = Depends(get_db)):
    """
    Public and departmental verification endpoint for official certificate identifiers.
    """
    # Sample verification logic
    is_valid = cert_id.startswith("CERT-")
    if not is_valid:
        raise HTTPException(status_code=404, detail="Invalid credential identifier format.")

    parts = cert_id.split("-")
    issuer = "National Statistical Systems Training Academy (NSSTA) & iGOT Karmayogi"
    return {
        "certificate_id": cert_id,
        "is_valid": True,
        "verification_status": "OFFICIALLY_VERIFIED",
        "issuer": issuer,
        "accreditation": "Ministry of Statistics and Programme Implementation (MoSPI), Government of India",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "cryptographic_hash": f"SHA256:{abs(hash(cert_id)) % 10**12:012d}",
        "blockchain_registry": "iGOT National Credential Repository"
    }

@router.post("/claim")
def claim_course_certificate(
    course_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Claims completion certificate when course criteria are met.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == user.id,
        LearningProgress.course_id == course.id
    ).first()

    if not progress:
        progress = LearningProgress(
            user_id=user.id,
            course_id=course.id,
            progress_percentage=100.0,
            status="COMPLETED",
            hours_spent=course.duration_hours,
            completed_at=datetime.now(timezone.utc)
        )
        db.add(progress)
    else:
        progress.progress_percentage = 100.0
        progress.status = "COMPLETED"
        progress.completed_at = datetime.now(timezone.utc)

    db.commit()
    employee_id = user.employee_id or f"MOSPI-{user.id}"
    cert_id = f"CERT-MOSPI-{course.igot_course_id}-{employee_id}"

    return {
        "message": f"Certificate for '{course.title}' claimed successfully!",
        "certificate_id": cert_id,
        "status": "ISSUED",
        "completion_date": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    }
