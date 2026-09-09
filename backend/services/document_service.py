"""
Document Processing Pipeline
----------------------------
Extracts text from PDF, DOCX, PPTX, and TXT files.
Applies text normalization, chunking with sliding windows and page tracking,
and extracts key statistical topics/entities.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Statistical domain keywords for topic extraction
STATISTICAL_TOPICS_DICTIONARY = [
    "Sampling Methods", "Simple Random Sampling", "Stratified Sampling", "Cluster Sampling",
    "Multi-Stage Sampling", "Systematic Sampling", "Sampling Frame", "Sampling Error",
    "Non-Sampling Error", "Finite Population Correction", "Data Quality", "Imputation",
    "Outlier Detection", "Validation Rules", "Data Governance", "National Accounts",
    "Consumer Price Index (CPI)", "Index of Industrial Production (IIP)", "Descriptive Statistics",
    "Inferential Statistics", "Hypothesis Testing", "Time Series Analysis", "Seasonal Adjustment",
    "Questionnaire Design", "Survey Methodology", "Data Privacy", "Digital Personal Data Protection",
    "Python", "R Programming", "Statistical Ethics", "CAPI", "CATI", "NSSO Rounds"
]

class DocumentService:
    def __init__(self):
        pass

    def extract_text(self, file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """
        Extracts text from the file page-by-page.
        Returns a list of dicts: [{"page": 1, "text": "..."}, ...]
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_type = file_type.upper().replace(".", "")
        pages_content: List[Dict[str, Any]] = []

        if file_type == "PDF":
            pages_content = self._extract_pdf(path)
        elif file_type in ("DOCX", "DOC"):
            pages_content = self._extract_docx(path)
        elif file_type in ("PPTX", "PPT"):
            pages_content = self._extract_pptx(path)
        elif file_type == "TXT":
            pages_content = self._extract_txt(path)
        else:
            raise ValueError(f"Unsupported file format: {file_type}")

        # If empty (such as a scanned document with no raw text layer), provide an OCR-ready fallback notice
        if not pages_content or not any(p["text"].strip() for p in pages_content):
            pages_content = [{
                "page": 1,
                "text": "[OCR Notice: Scanned document detected. Optical Character Recognition placeholder activated for official MoSPI image scan processing.]"
            }]

        return pages_content

    def _extract_pdf(self, path: Path) -> List[Dict[str, Any]]:
        results = []
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                results.append({"page": idx + 1, "text": text.strip()})
        except Exception as e:
            logger.error(f"Error reading PDF {path}: {e}")
            results.append({"page": 1, "text": f"Error parsing PDF: {str(e)}"})
        return results

    def _extract_docx(self, path: Path) -> List[Dict[str, Any]]:
        results = []
        try:
            import docx
            doc = docx.Document(str(path))
            full_text = []
            for p in doc.paragraphs:
                if p.text.strip():
                    full_text.append(p.text.strip())
            
            # Approximate pages by every 400 words
            text = "\n\n".join(full_text)
            words = text.split()
            page_size = 400
            if not words:
                return [{"page": 1, "text": ""}]
            
            for i in range(0, len(words), page_size):
                page_num = (i // page_size) + 1
                page_text = " ".join(words[i:i + page_size])
                results.append({"page": page_num, "text": page_text})
        except Exception as e:
            logger.error(f"Error reading DOCX {path}: {e}")
            results.append({"page": 1, "text": f"Error parsing DOCX: {str(e)}"})
        return results

    def _extract_pptx(self, path: Path) -> List[Dict[str, Any]]:
        results = []
        try:
            from pptx import Presentation
            prs = Presentation(str(path))
            for idx, slide in enumerate(prs.slides):
                slide_texts = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_texts.append(shape.text.strip())
                results.append({"page": idx + 1, "text": "\n".join(slide_texts)})
        except Exception as e:
            logger.error(f"Error reading PPTX {path}: {e}")
            results.append({"page": 1, "text": f"Error parsing PPTX: {str(e)}"})
        return results

    def _extract_txt(self, path: Path) -> List[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Divide into simulated sections/pages if large
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            if not paragraphs:
                return [{"page": 1, "text": content.strip()}]
            
            # Group ~3 paragraphs per page
            results = []
            chunk_paras = 3
            for i in range(0, len(paragraphs), chunk_paras):
                page_num = (i // chunk_paras) + 1
                page_text = "\n\n".join(paragraphs[i:i + chunk_paras])
                results.append({"page": page_num, "text": page_text})
            return results
        except Exception as e:
            logger.error(f"Error reading TXT {path}: {e}")
            return [{"page": 1, "text": f"Error reading text file: {str(e)}"}]

    def chunk_document(self, pages_content: List[Dict[str, Any]], chunk_size_words: int = 250, overlap_words: int = 40) -> List[Dict[str, Any]]:
        """
        Splits pages into overlapping chunks with page and section tracking.
        """
        chunks = []
        chunk_idx = 1

        for item in pages_content:
            page_num = item["page"]
            text = item["text"]
            if not text.strip():
                continue

            # Identify probable section headers (lines ending without punctuation or uppercase)
            lines = text.split("\n")
            section_title = "General Content"
            for line in lines[:3]:
                if line.strip() and len(line.strip()) < 80 and not line.strip().endswith("."):
                    section_title = line.strip()
                    break

            words = text.split()
            if len(words) <= chunk_size_words:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "page_number": page_num,
                    "section_title": section_title,
                    "content": text.strip(),
                    "token_count": int(len(words) * 1.3)
                })
                chunk_idx += 1
            else:
                i = 0
                while i < len(words):
                    sub_words = words[i:i + chunk_size_words]
                    chunk_text = " ".join(sub_words)
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "page_number": page_num,
                        "section_title": section_title,
                        "content": chunk_text.strip(),
                        "token_count": int(len(sub_words) * 1.3)
                    })
                    chunk_idx += 1
                    i += (chunk_size_words - overlap_words)

        return chunks

    def extract_topics(self, full_text: str) -> List[str]:
        """
        Extracts high-relevance official statistical topics from text.
        """
        found_topics = []
        text_lower = full_text.lower()

        for topic in STATISTICAL_TOPICS_DICTIONARY:
            if topic.lower() in text_lower:
                found_topics.append(topic)

        # Fallback to key capitalized phrases if few found
        if len(found_topics) < 3:
            capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', full_text)
            for cap in capitalized:
                if len(cap) > 6 and cap not in found_topics:
                    found_topics.append(cap)
                if len(found_topics) >= 5:
                    break

        return found_topics[:7] if found_topics else ["Official Statistics", "General Methodology"]

document_service = DocumentService()
