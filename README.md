# StatSkill AI

**AI-Enabled Learning & Competency Development Platform for India's Official Statistical System**  
*(Ministry of Statistics and Programme Implementation - MoSPI / National Statistical Systems Training Academy - NSSTA / iGOT Karmayogi Integration)*

---

## 📌 Project Overview

**StatSkill AI** is a production-grade competency intelligence and personalized capacity-building platform architected specifically for India's statistical cadre (Indian Statistical Service, Subordinate Statistical Services, NSSO field investigators, and statistical supervisors).

Unlike traditional static learning management systems (LMS) or isolated quiz generators, StatSkill AI demonstrates a **complete closed-loop competency development lifecycle**:

$$\text{Diagnose} \longrightarrow \text{Identify Gap} \longrightarrow \text{Recommend Learning} \longrightarrow \text{Learn} \longrightarrow \text{Generate Assessment} \longrightarrow \text{Measure Growth} \longrightarrow \text{Update Competency} \longrightarrow \text{Recommend Next}$$

---

## 🏛️ Key Architectural Principles

1. **Working Production-Quality MVP**:
   - Backend built with **FastAPI**, **SQLAlchemy ORM**, **SQLite**, and document parsing (`pypdf`, `python-docx`, `python-pptx`).
   - Frontend built with **Modern Vanilla ES6+ SPA** and a Government of India / MoSPI / iGOT Karmayogi design system.
2. **Strict iGOT Karmayogi Adapter Boundaries**:
   - Includes a dedicated `iGOTIntegrationService` adhering to DoPT / Karmayogi Bharat schemas.
   - Operates in `adapter_mock` mode out-of-the-box, clearly separating mock course data from future authorized official API integration.
3. **Document-Grounded RAG Engine**:
   - Generates MCQs strictly grounded in uploaded training manuals (PDF, DOCX, PPTX, TXT) with **exact page references, verbatim excerpts, explanations, and review flags**.
   - Built-in heuristic RAG engine works **100% offline**, with pluggable support for Google Gemini, OpenAI, and Ollama.
4. **Official Competency Framework**:
   - 16 core competencies with 5-level proficiency descriptors (Level 1: Beginner to Level 5: Expert).
   - 5 roles with benchmark level requirements and criticality weights.

---

## 👥 Seeded Demo Personas

The platform includes a quick **one-click persona switcher** in the top navigation bar:

| Persona | Role | Department | Baseline Focus / Gaps |
|---|---|---|---|
| **Ramesh Kumar** | Statistical Officer | NSSO Field Operations | **Sampling Methods: 42% (High Gap)**<br>**Data Visualization: 35% (High Gap)**<br>**Statistical Analysis: 61% (Moderate Gap)**<br>**Data Quality: 82% (Good)** |
| **Dr. Priya Sharma** | Training Administrator | NSSTA Academy | Access to **MoSPI-wide Executive Analytics**, department radars, and gap severity rankings |
| **Prof. Arvind Swaminathan** | Subject Matter Expert | ISI / MoSPI Advisory | Authoritative validator for question banks, sampling frameworks, and grounded MCQs |

---

## 🔄 The Closed-Loop Demonstration Journey

1. **Login as Ramesh Kumar** (Statistical Officer).
2. **View Competency Dashboard**:
   - See baseline scores: *Sampling Methods (42%)*, *Data Visualization (35%)*, *Statistical Analysis (61%)*, *Data Quality (82%)*.
   - View visual competency heatmap across all 16 domains.
3. **Identify Gaps**:
   - AI highlights Sampling Methods and Data Visualization as **Priority High Gaps** requiring Level 4 benchmark attainment.
4. **Personalized iGOT Recommendations**:
   - Inspect courses with transparent **"Why am I seeing this recommendation?"** rationale.
5. **Document Ingestion**:
   - View *MoSPI Sampling Methodology Manual* in the Document Hub, parsed into chunks with extracted statistical topics.
6. **Generate Grounded MCQs**:
   - Open **AI Assessment Generator** to generate 10 MCQs with page citations and excerpts.
7. **Take Interactive Quiz**:
   - Complete the quiz with live timer and adaptive feedback.
8. **Measure Growth**:
   - See your score update in real-time (e.g., *Sampling Methods rises from 42% to 78%, yielding a **+36 percentage point** gain*).
9. **Switch to Admin Persona**:
   - Log in as Dr. Priya Sharma and examine MoSPI organizational analytics, department distributions, and training effectiveness.

---

## 🚀 Quick Start & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Web browser (Chrome, Edge, Firefox)

### 1. Clone & Setup Directory
```bash
git clone <repository_url>
cd statskill-ai
```

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Initialize & Seed Database
```bash
python -m backend.seed_data
```

### 4. Run the Platform
```bash
python main.py
```
The server will launch at: **http://127.0.0.1:8000**  
Interactive Swagger API documentation: **http://127.0.0.1:8000/api/docs**

---

## 🗄️ Database Architecture (16 Relational Tables)

- `users`: Statistical personnel profiles, employee IDs, roles, departments.
- `roles`: Statistical designations (Statistical Officer, Data Analyst, etc.).
- `competencies`: 16 official statistical competencies with Level 1-5 descriptors.
- `role_competencies`: Benchmark requirements (Level 1-5) & criticality (Critical, High, Medium).
- `assessments`: Diagnostic and certification test configurations.
- `questions`: Question bank with options, correct keys, and explanations.
- `assessment_attempts`: Officer attempt records and score percentages.
- `assessment_answers`: Individual question answers with time spent.
- `documents`: Uploaded manuals (PDF, DOCX, PPTX, TXT) and parsing status.
- `document_chunks`: Overlapping text chunks with page numbers and section headers.
- `generated_questions`: Document-grounded MCQs with source page citations and excerpts.
- `courses`: iGOT Karmayogi catalog metadata and target levels.
- `course_recommendations`: Ranked recommendations with AI explainability justifications.
- `learning_progress`: Course completion tracking and hours spent.
- `competency_scores`: Persistent competency scores with baseline, current, and delta tracking.
- `quiz_attempts`: Grounded quiz sessions with adaptive difficulty evaluations.

---

## 📡 REST API Summary

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Authenticate user or demo persona |
| `POST` | `/api/auth/switch-demo` | Seamlessly toggle between Learner, Admin, and SME personas |
| `GET` | `/api/auth/users/me` | Fetch active user profile and role details |
| `GET` | `/api/competencies` | Retrieve the 16-competency framework |
| `GET` | `/api/roles` | Retrieve roles and required competency level mappings |
| `GET` | `/api/competency/gaps` | Compute assessed vs required competency gaps |
| `POST` | `/api/assessment/start` | Start diagnostic assessment |
| `POST` | `/api/assessment/submit` | Submit diagnostic and receive classified gap report |
| `GET` | `/api/recommendations` | Get personalized iGOT course recommendations with rationale |
| `POST` | `/api/documents/upload` | Upload PDF/DOCX/PPTX/TXT document to processing pipeline |
| `GET` | `/api/documents` | List uploaded training documents with statuses & topics |
| `GET` | `/api/documents/{id}/chunks` | Inspect document chunks with page & section metadata |
| `POST` | `/api/documents/{id}/generate-quiz` | Generate grounded MCQs with source page citations |
| `POST` | `/api/quiz/start` | Initialize interactive quiz session |
| `POST` | `/api/quiz/submit` | Submit quiz and update competency scores in real time |
| `GET` | `/api/dashboard/learner` | Fetch learner metrics, heatmaps, and before/after deltas |
| `GET` | `/api/dashboard/admin` | Fetch MoSPI organizational analytics and department radars |

---

## 🔒 Security & Best Practices

- Input sanitization and file extension validation (`.pdf`, `.docx`, `.pptx`, `.txt`).
- File size capped at 25MB with secure disk storage.
- Zero API keys exposed in frontend code; all AI dispatch happens securely on the backend.
- Separation of operational modes (`adapter_mock` vs `live_authorized`).

---

## 📜 Compliance & Disclaimers

> **Disclaimer**: StatSkill AI includes an iGOT-compatible integration adapter (`iGOTIntegrationService`). Seeded course data follows the official schema for demonstration. The system is ready to connect to live authorized Karmayogi Bharat REST/OAuth2 endpoints when official agency credentials are provided.
