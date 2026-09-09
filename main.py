import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings, BASE_DIR
from backend.database import engine, Base
from backend.seed_data import seed_database

# Import routers
from backend.routes.auth import router as auth_router
from backend.routes.competencies import router as comp_router
from backend.routes.assessments import router as assess_router
from backend.routes.recommendations import router as rec_router
from backend.routes.documents import router as doc_router
from backend.routes.quiz import router as quiz_router
from backend.routes.admin import router as admin_router
from backend.routes.chat import router as chat_router
from backend.routes.certifications import router as cert_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Enable CORS for local dev / testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router)
app.include_router(comp_router)
app.include_router(assess_router)
app.include_router(rec_router)
app.include_router(doc_router)
app.include_router(quiz_router)
app.include_router(admin_router)
app.include_router(chat_router)
app.include_router(cert_router)

# Ensure database tables and initial seed
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    try:
        seed_database()
    except Exception as e:
        print(f"Startup seed notice: {e}")

# Mount static frontend and uploads
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR = settings.UPLOAD_DIR
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({
        "app": settings.APP_NAME,
        "status": "online",
        "api_docs": "/api/docs",
        "notice": "Frontend index.html is being mounted."
    })

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ai_provider": settings.AI_PROVIDER,
        "igot_mode": settings.IGOT_MODE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
