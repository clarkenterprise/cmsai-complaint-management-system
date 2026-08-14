from fastapi import FastAPI

from fastapi import File, UploadFile

from fastapi.middleware.cors import CORSMiddleware

import os

import tempfile

from app.services.document_service import extract_text_from_pdf

from app.agents.graph import complaint_graph

from app.schemas.complaint import Complaint

from app.schemas.risk import RiskAssessment

from app.services.groq_service import ask_groq

from app.agents.nodes import assess_risk, edit_complaint

from app.schemas.edit import EditComplaintRequest

from app.api.complaints import router as complaints_router
from app.database import engine, Base
from app.models.complaint import ComplaintModel


app = FastAPI(title="AIVOA Complaint Management System")
Base.metadata.create_all(bind=engine)

app.add_middleware(
   CORSMiddleware,

    allow_origins=[

        "http://localhost:5173",

        "http://localhost:5174",

        "http://localhost:5175",

        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5181",

        "http://127.0.0.1:5173",

        "http://127.0.0.1:5174",

        "http://127.0.0.1:5175",

        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5181",

    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)

app.include_router(complaints_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "AIVOA backend is running"
    }


@app.post("/test/complaint")
def test_complaint(complaint: Complaint):
    return {
        "complaint": complaint.model_dump()
    }


@app.post("/test/risk")
def test_risk(risk: RiskAssessment):
    return {
        "risk_assessment": risk.model_dump()
    }
@app.post("/test/ai")

def test_ai(prompt: str):

    response = ask_groq(prompt)

    return {

        "response": response

    }
@app.post("/test/langgraph")
def test_langgraph(prompt: str):
    result = complaint_graph.invoke({
        "raw_input": prompt
    })

    return result
@app.post("/test/edit")
def test_edit(request: EditComplaintRequest):
    state = {
        "raw_input": request.update,
        "complaint": request.current_complaint.model_dump(),
        "is_edit": True,
    }

    updated_state = edit_complaint(state)

    if updated_state.get("error"):
        return updated_state

    final_state = assess_risk(updated_state)

    return final_state
@app.post("/test/extract-document")
async def extract_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return {
            "error": "Only PDF files are supported"
        }

    contents = await file.read()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ) as temp_file:

        temp_file.write(contents)
        temp_path = temp_file.name

    try:
        extracted_text = extract_text_from_pdf(temp_path)

        state = {
            "raw_input": extracted_text
        }

        result = complaint_graph.invoke(state)

        return {
            "filename": file.filename,
            "extracted_text": extracted_text,
            "complaint": result.get("complaint"),
            "risk_assessment": result.get("risk_assessment"),
            "error": result.get("error")
        }

    finally:
        os.unlink(temp_path)