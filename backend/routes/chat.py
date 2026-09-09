from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel
from backend.database import get_db
from backend.models import User
from backend.routes.auth import get_current_user
from backend.services.ai_service import ai_service

router = APIRouter(prefix="/api/chat", tags=["AI Doubt Solver & Chatbot"])

# In-memory per-user chat session history
USER_CHAT_SESSIONS: Dict[int, List[Dict[str, Any]]] = {}

class ChatRequest(BaseModel):
    message: str
    document_id: Optional[int] = None
    competency_id: Optional[int] = None

class CitationItem(BaseModel):
    source: str
    section: Optional[str] = None
    page: Optional[int] = None
    snippet: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    citations: List[Dict[str, Any]] = []
    suggested_questions: List[str] = []
    topic: Optional[str] = "Official Statistics"
    timestamp: str

@router.post("/ask", response_model=ChatResponse)
def ask_doubt(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a statistical question or study doubt to the AI Doubt Solver.
    Returns grounded answers with citations and pedagogical explanations.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Question message cannot be empty.")

    result = ai_service.clarify_doubt(
        db=db,
        query=req.message.strip(),
        document_id=req.document_id,
        competency_id=req.competency_id,
        user=user
    )

    now_iso = datetime.now(timezone.utc).isoformat()

    # Store in user session history
    user_id = user.id
    if user_id not in USER_CHAT_SESSIONS:
        USER_CHAT_SESSIONS[user_id] = []

    USER_CHAT_SESSIONS[user_id].append({
        "sender": "user",
        "text": req.message.strip(),
        "timestamp": now_iso
    })
    USER_CHAT_SESSIONS[user_id].append({
        "sender": "assistant",
        "text": result.get("reply", ""),
        "citations": result.get("citations", []),
        "suggested_questions": result.get("suggested_questions", []),
        "topic": result.get("topic", "Official Statistics"),
        "timestamp": now_iso
    })

    # Keep last 30 messages
    if len(USER_CHAT_SESSIONS[user_id]) > 30:
        USER_CHAT_SESSIONS[user_id] = USER_CHAT_SESSIONS[user_id][-30:]

    return ChatResponse(
        reply=result.get("reply", "No answer generated."),
        citations=result.get("citations", []),
        suggested_questions=result.get("suggested_questions", []),
        topic=result.get("topic", "Official Statistics"),
        timestamp=now_iso
    )

@router.get("/suggestions")
def get_chat_suggestions():
    """
    Returns curated quick doubt prompts organized by statistical domain.
    """
    return {
        "categories": [
            {
                "domain": "Survey & Sampling",
                "icon": "📐",
                "prompts": [
                    "What is the difference between Stratified and Cluster Sampling?",
                    "What is Design Effect (Deff) and how is it calculated?",
                    "Explain Neyman Optimum Allocation in Stratified Sampling",
                    "What are the main sources of Non-Sampling Errors?"
                ]
            },
            {
                "domain": "Economic Statistics",
                "icon": "🛒",
                "prompts": [
                    "How does MoSPI compile the Consumer Price Index (CPI)?",
                    "What is the difference between Laspeyres and Paasche index numbers?",
                    "How is Gross Value Added (GVA) calculated in National Accounts?"
                ]
            },
            {
                "domain": "Data Quality & Governance",
                "icon": "🛡️",
                "prompts": [
                    "What methods does MoSPI use for statistical imputation?",
                    "What does the Collection of Statistics Act say about confidentiality?",
                    "What are the 10 UN Fundamental Principles of Official Statistics?"
                ]
            }
        ]
    }

@router.get("/history")
def get_chat_history(user: User = Depends(get_current_user)):
    """
    Retrieves the conversation history for the current officer session.
    """
    return USER_CHAT_SESSIONS.get(user.id, [])

@router.delete("/history")
def clear_chat_history(user: User = Depends(get_current_user)):
    """
    Clears the current officer's active chat session.
    """
    USER_CHAT_SESSIONS[user.id] = []
    return {"message": "Chat history cleared successfully"}
