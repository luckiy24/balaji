from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models import Competency, Role, RoleCompetency, User
from backend.schemas import CompetencyResponse, RoleResponse, RoleCompetencyResponse, CompetencyGapReport
from backend.routes.auth import get_current_user
from backend.services.gap_engine import gap_engine

router = APIRouter(prefix="/api", tags=["Competencies & Roles"])

@router.get("/competencies", response_model=List[CompetencyResponse])
def get_all_competencies(db: Session = Depends(get_db)):
    comps = db.query(Competency).all()
    return comps

@router.get("/roles", response_model=List[RoleResponse])
def get_all_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    output = []
    for r in roles:
        rc_list = []
        for rc in r.role_competencies:
            rc_list.append(RoleCompetencyResponse(
                competency_id=rc.competency_id,
                competency_name=rc.competency.name if rc.competency else "Unknown",
                required_level=rc.required_level,
                importance=rc.importance
            ))
        output.append(RoleResponse(
            id=r.id,
            name=r.name,
            code=r.code,
            department=r.department,
            description=r.description,
            competencies=rc_list
        ))
    return output

@router.get("/competency/gaps", response_model=CompetencyGapReport)
def get_user_competency_gaps(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Computes current user's competency gaps vs required role levels,
    returning classified categories (High Gap, Moderate Gap, Good, Strong)
    and priority rank.
    """
    report = gap_engine.compute_user_gaps(db, user)
    return report
