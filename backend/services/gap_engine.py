"""
AI Competency Gap Engine
------------------------
Calculates competency gaps by comparing required levels for the user's role
against assessed competency levels. Ranks priority gaps based on:
1. Level Gap size (required_level - assessed_level)
2. Role Importance Weighting (Critical = 1.5, High = 1.2, Medium = 1.0)
3. Assessment Score Performance ((100 - current_score) / 100)
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models import User, RoleCompetency, CompetencyScore, Competency

IMPORTANCE_WEIGHTS = {
    "Critical": 1.5,
    "High": 1.25,
    "Medium": 1.0,
    "Low": 0.8
}

def classify_score(score: float) -> str:
    """
    Classify score into official tiers:
    0-49 = High Gap
    50-69 = Moderate Gap
    70-84 = Good
    85-100 = Strong
    """
    if score < 50:
        return "High Gap"
    elif score < 70:
        return "Moderate Gap"
    elif score < 85:
        return "Good"
    else:
        return "Strong"

def score_to_level(score: float) -> int:
    """
    Map score percentage to competency level 1-5.
    Level 1 (Beginner): 0-35%
    Level 2 (Basic): 36-55%
    Level 3 (Intermediate): 56-74%
    Level 4 (Advanced): 75-89%
    Level 5 (Expert): 90-100%
    """
    if score < 36:
        return 1
    elif score < 56:
        return 2
    elif score < 75:
        return 3
    elif score < 90:
        return 4
    else:
        return 5

class GapEngine:
    def compute_user_gaps(self, db: Session, user: User) -> Dict[str, Any]:
        """
        Computes all competency gaps, priority rankings, and summary statistics.
        """
        # Fetch user's role requirements
        role_reqs = db.query(RoleCompetency).filter(RoleCompetency.role_id == user.role_id).all()
        role_req_map = {rc.competency_id: rc for rc in role_reqs}

        # Fetch all user competency scores
        user_scores = db.query(CompetencyScore).filter(CompetencyScore.user_id == user.id).all()
        user_score_map = {sc.competency_id: sc for sc in user_scores}

        # Fetch all competencies
        competencies = db.query(Competency).all()

        gap_items: List[Dict[str, Any]] = []
        total_score = 0.0
        scored_count = 0

        for comp in competencies:
            req = role_req_map.get(comp.id)
            required_level = req.required_level if req else 3
            importance = req.importance if req else "Medium"
            importance_weight = IMPORTANCE_WEIGHTS.get(importance, 1.0)

            score_record = user_score_map.get(comp.id)
            if score_record:
                current_score = score_record.current_score
                baseline_score = score_record.baseline_score
                score_delta = round(current_score - baseline_score, 1)
                assessed_level = score_to_level(current_score)
            else:
                # Default baseline
                current_score = 50.0
                baseline_score = 50.0
                score_delta = 0.0
                assessed_level = 2

            total_score += current_score
            scored_count += 1

            level_gap = max(0, required_level - assessed_level)
            gap_category = classify_score(current_score)

            # Priority formula:
            # High level gap + High importance + Lower score -> High Priority
            performance_deficit = (100.0 - current_score) / 100.0
            priority_score = (level_gap * 2.5 * importance_weight) + (performance_deficit * 2.0 * importance_weight)

            gap_items.append({
                "competency_id": comp.id,
                "competency_name": comp.name,
                "domain": comp.domain,
                "required_level": required_level,
                "assessed_level": assessed_level,
                "level_gap": level_gap,
                "baseline_score": round(baseline_score, 1),
                "current_score": round(current_score, 1),
                "score_delta": score_delta,
                "gap_category": gap_category,
                "importance": importance,
                "priority_score": round(priority_score, 2),
                "rank": 0 # Will be assigned below
            })

        # Sort by priority score descending
        gap_items.sort(key=lambda x: x["priority_score"], reverse=True)
        for idx, item in enumerate(gap_items):
            item["rank"] = idx + 1

        overall_avg = round(total_score / scored_count, 1) if scored_count > 0 else 50.0

        high_gaps = sum(1 for g in gap_items if g["gap_category"] == "High Gap")
        mod_gaps = sum(1 for g in gap_items if g["gap_category"] == "Moderate Gap")
        good_count = sum(1 for g in gap_items if g["gap_category"] == "Good")
        strong_count = sum(1 for g in gap_items if g["gap_category"] == "Strong")

        return {
            "user_id": user.id,
            "user_name": user.name,
            "role_name": user.role.name if user.role else "Statistical Officer",
            "overall_competency_score": overall_avg,
            "high_gaps_count": high_gaps,
            "moderate_gaps_count": mod_gaps,
            "good_count": good_count,
            "strong_count": strong_count,
            "ranked_gaps": gap_items
        }

gap_engine = GapEngine()
