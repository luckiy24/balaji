"""
Personalized Learning Recommendation Engine with AI Explainability
-------------------------------------------------------------------
Matches user competency gaps, assessed levels, and role criticality to
iGOT Karmayogi catalog courses, generating transparent "Why am I seeing this?"
justifications for every recommendation.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models import User, Course, CourseRecommendation, LearningProgress
from backend.services.gap_engine import gap_engine
from backend.services.igot_adapter import igot_service

class RecommendationEngine:
    def generate_recommendations(self, db: Session, user: User) -> List[Dict[str, Any]]:
        """
        Calculates ranked recommendations based on current user gaps,
        ensuring explainability for each suggestion.
        """
        gap_report = gap_engine.compute_user_gaps(db, user)
        ranked_gaps = gap_report["ranked_gaps"]
        gap_by_comp_id = {g["competency_id"]: g for g in ranked_gaps}

        # Check existing learning progress
        progress_records = db.query(LearningProgress).filter(LearningProgress.user_id == user.id).all()
        completed_course_ids = {p.course_id for p in progress_records if p.status == "COMPLETED"}
        progress_map = {p.course_id: p for p in progress_records}

        # Fetch available courses in DB
        courses = db.query(Course).all()

        recommendations: List[Dict[str, Any]] = []

        for course in courses:
            if course.id in completed_course_ids:
                continue

            gap_info = gap_by_comp_id.get(course.competency_id)
            if not gap_info:
                continue

            # Check if this course addresses a meaningful gap
            level_gap = gap_info["level_gap"]
            current_score = gap_info["current_score"]
            required_level = gap_info["required_level"]
            comp_name = gap_info["competency_name"]

            # AI Explainability generator
            if level_gap > 0 or current_score < 70:
                reason = (
                    f"You scored {current_score}% in {comp_name}, while your role requires Level {required_level} "
                    f"({gap_info['importance']} Priority). This course provides targeted training to close the "
                    f"{level_gap}-level competency gap."
                )
            elif current_score < 85:
                reason = (
                    f"You have a solid foundation in {comp_name} ({current_score}%), but this advanced iGOT module "
                    f"will elevate your competency toward Level {required_level} mastery."
                )
            else:
                reason = (
                    f"Recommended as a continuous professional refresher in {comp_name} to maintain your strong proficiency."
                )

            # Prioritization weight
            priority_score = gap_info["priority_score"]
            # Target level proximity bonus
            if course.target_level <= required_level:
                priority_score += 1.0

            p_rec = progress_map.get(course.id)
            progress_val = p_rec.progress_percentage if p_rec else 0.0
            status_val = p_rec.status if p_rec else "NOT_STARTED"

            recommendations.append({
                "course": course,
                "priority_score": round(priority_score, 2),
                "reason": reason,
                "gap_level_addressed": level_gap,
                "progress_percentage": progress_val,
                "status": status_val
            })

        # Sort recommendations by priority score descending
        recommendations.sort(key=lambda x: x["priority_score"], reverse=True)

        results = []
        for idx, rec in enumerate(recommendations):
            course_obj = rec["course"]
            results.append({
                "recommendation_id": idx + 1,
                "priority_rank": idx + 1,
                "reason": rec["reason"],
                "gap_level_addressed": rec["gap_level_addressed"],
                "progress_percentage": rec["progress_percentage"],
                "status": rec["status"],
                "course": {
                    "id": course_obj.id,
                    "igot_course_id": course_obj.igot_course_id,
                    "title": course_obj.title,
                    "provider": course_obj.provider,
                    "competency_id": course_obj.competency_id,
                    "competency_name": course_obj.competency.name if course_obj.competency else "Statistics",
                    "target_level": course_obj.target_level,
                    "duration_hours": course_obj.duration_hours,
                    "rating": course_obj.rating,
                    "thumbnail_url": course_obj.thumbnail_url,
                    "syllabus_summary": course_obj.syllabus_summary,
                    "is_igot_verified": course_obj.is_igot_verified
                }
            })

        return results

recommendation_engine = RecommendationEngine()
