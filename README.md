# CMSAI — AI-Powered Complaint Management System
CMSAI is an AI-assisted pharmaceutical complaint management system designed to help QA teams capture, analyze, validate, and manage customer complaints efficiently.
The system combines a React frontend, FastAPI backend, PostgreSQL database, and an AI-powered LangGraph pipeline to transform unstructured complaint text and PDF documents into structured complaint records and actionable QA insights.
## Features
- AI-powered complaint information extraction
- Customer, product, batch, and quantity extraction
- Complaint classification
- Pharmaceutical complaint risk assessment
- Severity, priority, and risk-level classification
- Complaint completeness validation
- Duplicate complaint detection
- AI-generated CAPA recommendations
- PDF complaint document extraction
- Natural-language complaint editing
- Complaint history
- PostgreSQL persistence
- AI Copilot interface
- Re-analysis of existing complaints
## AI Analysis Pipeline
```text
Customer Complaint / PDF
          │
          ▼
   Complaint Extraction
          │
          ▼
     Risk Assessment
          │
          ├───────────────┐
          ▼               ▼
   Completeness      Duplicate Check
          │               │
          └───────┬───────┘
                  ▼
           CAPA Recommendation
                  │
                  ▼
             PostgreSQL
                  │
                  ▼
              React UI

System Architecture

┌─────────────────────────────┐
│        React Frontend       │
│                             │
│  Complaint Form             │
│  AI Copilot                 │
│  Risk Assessment            │
│  Completeness               │
│  Duplicate Detection        │
│  CAPA                       │
│  Complaint History          │
└──────────────┬──────────────┘
               │ REST API
               ▼
┌─────────────────────────────┐
│       FastAPI Backend       │
│                             │
│  Complaint APIs             │
│  PDF Processing             │
│  Database Integration       │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       LangGraph / AI        │
│                             │
│  Extraction                 │
│  Risk Assessment            │
│  Completeness               │
│  CAPA Generation            │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│        PostgreSQL           │
│                             │
│  Complaint Records          │
│  Risk Information           │
└─────────────────────────────┘

Technology Stack

Frontend

* React
* Vite
* Redux Toolkit
* Axios
* CSS

Backend

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL
* Pydantic

AI / Machine Learning

* LangGraph
* Groq API
* LLM-based structured extraction
* AI-assisted risk assessment
* AI-generated CAPA recommendations

Document Processing

* PDF text extraction
* Structured AI extraction from uploaded complaint documents

API Endpoints

Method	Endpoint	Purpose
GET	/api/complaints	Retrieve complaint history
GET	/api/complaints/{id}/analysis	Retrieve complete analysis for an existing complaint
POST	/api/complaints/analyze	Analyze a new complaint
POST	/api/complaints/edit	Edit an existing complaint
POST	/api/complaints/extract-document	Extract and analyze a PDF complaint

Example Complaint

Input

A pharmacist reports that 18 bottles of Amoxicillin 500 mg capsules from batch AMX-2026-031 contain capsules with cracked shells.

Processing

CMSAI extracts the complaint information and performs:

* Complaint classification
* Risk assessment
* Completeness validation
* Duplicate detection
* CAPA recommendation

Project Structure

cmsai-complaint-management-system/
│
├── backend/
│   └── app/
│       ├── agents/
│       ├── api/
│       ├── models/
│       ├── schemas/
│       └── services/
│
├── frontend/
│   └── src/
│       ├── services/
│       ├── store/
│       ├── assets/
│       ├── App.jsx
│       └── index.css
│
├── .gitignore
└── README.md

Running Locally

Backend

cd backend
python -m venv .venv
source .venv/bin/activate

Install the Python dependencies required by the project.

Create a .env file containing your local configuration, including:

DATABASE_URL=your_postgresql_connection_string
GROQ_API_KEY=your_groq_api_key

Start the backend:

uvicorn app.main:app --reload

Frontend

Open another terminal:

cd frontend
npm install
npm run dev

The frontend will normally be available at:

http://localhost:5173

Security

Sensitive configuration is kept outside version control.

The repository excludes:

* .env files
* Python virtual environments
* node_modules
* Local database backups
* API credentials

AI Safety

CMSAI provides AI-assisted recommendations intended to support qualified pharmaceutical QA personnel.

Risk assessments, investigations, and CAPA recommendations should be reviewed and approved by appropriate QA professionals before being used for real-world quality decisions.

Project Status

Functional prototype / portfolio project

The current system supports end-to-end complaint intake, AI analysis, PDF extraction, validation, duplicate detection, CAPA generation, complaint editing, complaint history, and PostgreSQL persistence.

Future Improvements

* Authentication and role-based access control
* QA approval workflow
* Complaint status tracking
* Audit trail
* Analytics dashboard
* Email notification system
* Production deployment
* Automated evaluation of AI outputs
* Embedding-based duplicate similarity detection

