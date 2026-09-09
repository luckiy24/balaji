from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models import User, Role
from backend.schemas import UserResponse, LoginRequest, DemoLoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication & Profile"])

# In-memory session tracking for active demo user if no JWT provided
_CURRENT_USER_ID = 1

def get_current_user(db: Session = Depends(get_db)) -> User:
    global _CURRENT_USER_ID
    user = db.query(User).filter(User.id == _CURRENT_USER_ID).first()
    if not user:
        # Fallback to first user
        user = db.query(User).first()
        if not user:
            raise HTTPException(status_code=404, detail="No users found in database")
        _CURRENT_USER_ID = user.id
    return user

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # Default to user 1 for demo resilience
        user = db.query(User).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    global _CURRENT_USER_ID
    _CURRENT_USER_ID = user.id

    u_resp = UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        employee_id=user.employee_id,
        organization=user.organization,
        department=user.department,
        role_id=user.role_id,
        role_name=user.role.name if user.role else "Statistical Officer",
        role_code=user.role.code if user.role else "STAT_OFFICER",
        experience_years=user.experience_years,
        avatar_url=user.avatar_url,
        is_admin=user.is_admin,
        is_sme=user.is_sme,
        created_at=user.created_at
    )
    return TokenResponse(
        access_token=f"demo-token-user-{user.id}",
        token_type="bearer",
        user=u_resp
    )

@router.post("/switch-demo", response_model=UserResponse)
def switch_demo_user(req: DemoLoginRequest, db: Session = Depends(get_db)):
    """
    Switch active persona seamlessly between Learner, Admin, and SME.
    """
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Demo persona not found")
    
    global _CURRENT_USER_ID
    _CURRENT_USER_ID = user.id

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        employee_id=user.employee_id,
        organization=user.organization,
        department=user.department,
        role_id=user.role_id,
        role_name=user.role.name if user.role else "Statistical Officer",
        role_code=user.role.code if user.role else "STAT_OFFICER",
        experience_years=user.experience_years,
        avatar_url=user.avatar_url,
        is_admin=user.is_admin,
        is_sme=user.is_sme,
        created_at=user.created_at
    )

@router.get("/users/me", response_model=UserResponse)
def get_user_profile(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        employee_id=user.employee_id,
        organization=user.organization,
        department=user.department,
        role_id=user.role_id,
        role_name=user.role.name if user.role else "Statistical Officer",
        role_code=user.role.code if user.role else "STAT_OFFICER",
        experience_years=user.experience_years,
        avatar_url=user.avatar_url,
        is_admin=user.is_admin,
        is_sme=user.is_sme,
        created_at=user.created_at
    )

@router.get("/users/all", response_model=List[UserResponse])
def get_all_demo_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    results = []
    for u in users:
        results.append(UserResponse(
            id=u.id,
            name=u.name,
            email=u.email,
            employee_id=u.employee_id,
            organization=u.organization,
            department=u.department,
            role_id=u.role_id,
            role_name=u.role.name if u.role else "",
            role_code=u.role.code if u.role else "",
            experience_years=u.experience_years,
            avatar_url=u.avatar_url,
            is_admin=u.is_admin,
            is_sme=u.is_sme,
            created_at=u.created_at
        ))
    return results
