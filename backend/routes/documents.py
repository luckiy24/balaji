import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models import Document, DocumentChunk, User
from backend.schemas import DocumentResponse, DocumentChunkResponse
from backend.config import settings
from backend.routes.auth import get_current_user
from backend.services.document_service import document_service

router = APIRouter(prefix="/api/documents", tags=["Document Processing Pipeline"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accepts PDF, DOCX, PPTX, or TXT document,
    extracts text, generates chunks, extracts statistical topics, and stores metadata.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed formats: PDF, DOCX, PPTX, TXT."
        )

    # Save uploaded file
    target_path = settings.UPLOAD_DIR / f"{user.id}_{int(os.times().elapsed)}_{file.filename}"
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = target_path.stat().st_size
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB")

    # Document DB record
    clean_type = ext.replace(".", "").upper()
    doc = Document(
        user_id=user.id,
        filename=file.filename,
        stored_path=str(target_path),
        file_type=clean_type,
        file_size_bytes=file_size,
        processing_status="PROCESSING"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        # Extract text pages
        pages_content = document_service.extract_text(str(target_path), clean_type)
        doc.page_count = len(pages_content)

        # Chunk document
        chunks_data = document_service.chunk_document(pages_content)
        for c in chunks_data:
            chunk_rec = DocumentChunk(
                document_id=doc.id,
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                section_title=c["section_title"],
                content=c["content"],
                token_count=c["token_count"]
            )
            db.add(chunk_rec)

        # Extract topics
        full_text = " ".join([p["text"] for p in pages_content])
        topics = document_service.extract_topics(full_text)
        doc.extracted_topics = ",".join(topics)
        doc.processing_status = "READY"
        db.commit()
        db.refresh(doc)

    except Exception as e:
        doc.processing_status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Document parsing error: {str(e)}")

    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size_bytes=doc.file_size_bytes,
        page_count=doc.page_count,
        extracted_topics=doc.extracted_topics.split(",") if doc.extracted_topics else [],
        processing_status=doc.processing_status,
        ocr_applied=doc.ocr_applied,
        uploaded_at=doc.uploaded_at
    )

@router.get("", response_model=List[DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    results = []
    for d in docs:
        results.append(DocumentResponse(
            id=d.id,
            filename=d.filename,
            file_type=d.file_type,
            file_size_bytes=d.file_size_bytes,
            page_count=d.page_count,
            extracted_topics=d.extracted_topics.split(",") if d.extracted_topics else [],
            processing_status=d.processing_status,
            ocr_applied=d.ocr_applied,
            uploaded_at=d.uploaded_at
        ))
    return results

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_by_id(document_id: int, db: Session = Depends(get_db)):
    d = db.query(Document).filter(Document.id == document_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        id=d.id,
        filename=d.filename,
        file_type=d.file_type,
        file_size_bytes=d.file_size_bytes,
        page_count=d.page_count,
        extracted_topics=d.extracted_topics.split(",") if d.extracted_topics else [],
        processing_status=d.processing_status,
        ocr_applied=d.ocr_applied,
        uploaded_at=d.uploaded_at
    )

@router.get("/{document_id}/chunks", response_model=List[DocumentChunkResponse])
def get_document_chunks(document_id: int, db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
    return chunks
