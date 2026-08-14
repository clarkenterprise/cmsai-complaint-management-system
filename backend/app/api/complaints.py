import os
import tempfile
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.complaint import ComplaintModel
from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from app.agents.graph import complaint_graph
from app.agents.nodes import (
    assess_risk,
    edit_complaint,
    check_completeness,
    generate_capa,
)
from app.schemas.edit import EditComplaintRequest
from app.services.document_service import extract_text_from_pdf


router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


class ComplaintAnalyzeRequest(BaseModel):
    message: str
@router.get("")
def get_complaints(
    db: Session = Depends(get_db),
):
    complaints = (
        db.query(ComplaintModel)
        .order_by(ComplaintModel.id.desc())
        .all()
    )

    return [
        {
            "id": complaint.id,
            "customer_name": complaint.customer_name,
            "customer_email": complaint.customer_email,
            "product_name": complaint.product_name,
            "product_strength": complaint.product_strength,
            "batch_number": complaint.batch_number,
            "manufacturing_date": complaint.manufacturing_date,
            "expiry_date": complaint.expiry_date,
            "quantity_affected": complaint.quantity_affected,
            "complaint_type": complaint.complaint_type,
            "complaint_date": complaint.complaint_date,
            "complaint_description": complaint.complaint_description,
            "severity": complaint.severity,
            "priority": complaint.priority,
            "risk_level": complaint.risk_level,
            "reasoning": complaint.reasoning,
            "recommended_action": complaint.recommended_action,
            "recommendations": complaint.recommendations,
            "created_at": complaint.created_at,
            "updated_at": complaint.updated_at,
        }
        for complaint in complaints
    ]
@router.get("/{complaint_id}/analysis")
def get_complaint_analysis(
    complaint_id: int,
    db: Session = Depends(get_db),
):
    # Find the existing complaint
    complaint_record = (
        db.query(ComplaintModel)
        .filter(ComplaintModel.id == complaint_id)
        .first()
    )

    if not complaint_record:
        return {
            "complaint": None,
            "risk_assessment": None,
            "completeness": None,
            "duplicate": None,
            "capa": None,
            "error": "Complaint not found",
        }

    # Convert database record into the same structure
    # used by the AI pipeline.
    complaint = {
        "complaint_source": complaint_record.complaint_source,
        "customer_name": complaint_record.customer_name,
        "customer_email": complaint_record.customer_email,
        "product_name": complaint_record.product_name,
        "product_strength": complaint_record.product_strength,
        "batch_number": complaint_record.batch_number,
        "manufacturing_date": complaint_record.manufacturing_date,
        "expiry_date": complaint_record.expiry_date,
        "quantity_affected": complaint_record.quantity_affected,
        "complaint_type": complaint_record.complaint_type,
        "complaint_date": complaint_record.complaint_date,
        "complaint_description": complaint_record.complaint_description,
    }

    # Use the stored risk assessment.
    risk = {
        "severity": complaint_record.severity,
        "priority": complaint_record.priority,
        "risk_level": complaint_record.risk_level,
        "reasoning": complaint_record.reasoning,
        "recommended_action": complaint_record.recommended_action,
    }

    # Convert stored recommendations back to a list.
    recommendations = complaint_record.recommendations

    if recommendations:
        try:
            recommendations = eval(
                recommendations,
                {"__builtins__": {}},
                {},
            )
        except Exception:
            recommendations = [recommendations]
    else:
        recommendations = []

    if not isinstance(recommendations, list):
        recommendations = [str(recommendations)]

    risk["recommendations"] = recommendations

    # -----------------------------
    # Completeness
    # -----------------------------

    completeness_state = check_completeness({
        "complaint": complaint
    })

    completeness = completeness_state.get(
        "completeness"
    )

    # -----------------------------
    # Duplicate detection
    # -----------------------------

    query = db.query(ComplaintModel).filter(
        ComplaintModel.id != complaint_record.id
    )

    if complaint_record.product_name:
        query = query.filter(
            ComplaintModel.product_name.ilike(
                complaint_record.product_name
            )
        )

    if complaint_record.batch_number:
        query = query.filter(
            ComplaintModel.batch_number.ilike(
                complaint_record.batch_number
            )
        )

    if complaint_record.complaint_type:
        query = query.filter(
            ComplaintModel.complaint_type.ilike(
                complaint_record.complaint_type
            )
        )

    duplicate_record = (
        query
        .order_by(ComplaintModel.id.desc())
        .first()
    )

    if duplicate_record:
        duplicate = {
            "is_duplicate": True,
            "complaint_id": duplicate_record.id,
            "customer_name": duplicate_record.customer_name,
            "product_name": duplicate_record.product_name,
            "batch_number": duplicate_record.batch_number,
            "complaint_type": duplicate_record.complaint_type,
            "reason": (
                "A complaint with the same product, "
                "batch number, and complaint type "
                "already exists."
            ),
        }
    else:
        duplicate = {
            "is_duplicate": False,
            "complaint_id": None,
            "customer_name": None,
            "product_name": None,
            "batch_number": None,
            "complaint_type": None,
            "reason": (
                "No matching previous complaint found."
            ),
        }

    # -----------------------------
    # CAPA
    # -----------------------------

    capa_state = generate_capa({
        "complaint": complaint,
        "risk_assessment": risk,
    })

    capa = capa_state.get("capa")

    return {
        "complaint": complaint,
        "risk_assessment": risk,
        "completeness": completeness,
        "duplicate": duplicate,
        "capa": capa,
        "complaint_id": complaint_record.id,
        "error": capa_state.get("error"),
    }
def find_duplicate_complaint(
    db: Session,
    complaint: dict,
):
    product_name = complaint.get("product_name")
    batch_number = complaint.get("batch_number")
    complaint_type = complaint.get("complaint_type")

    if not product_name and not batch_number:
        return None

    query = db.query(ComplaintModel)

    if product_name:
        query = query.filter(
            ComplaintModel.product_name.ilike(product_name)
        )

    if batch_number:
        query = query.filter(
            ComplaintModel.batch_number.ilike(batch_number)
        )

    if complaint_type:
        query = query.filter(
            ComplaintModel.complaint_type.ilike(complaint_type)
        )

    return (
        query
        .order_by(ComplaintModel.id.desc())
        .first()
    )

@router.post("/analyze")
def analyze_complaint(
    request: ComplaintAnalyzeRequest,
    db: Session = Depends(get_db),
):
    result = complaint_graph.invoke({
        "raw_input": request.message
    })

    if result.get("error"):
        return {
            "complaint": result.get("complaint"),
            "risk_assessment": result.get("risk_assessment"),
            "error": result.get("error"),
            "capa": result.get("capa"),
        }

    complaint = result.get("complaint") or {}
    risk = result.get("risk_assessment") or {}
    duplicate = find_duplicate_complaint(
    db,
    complaint,
)

    db_complaint = ComplaintModel(
        complaint_source=complaint.get("complaint_source"),
        customer_name=complaint.get("customer_name"),
        customer_email=complaint.get("customer_email"),
        product_name=complaint.get("product_name"),
        product_strength=complaint.get("product_strength"),
        batch_number=complaint.get("batch_number"),
        manufacturing_date=(
            str(complaint.get("manufacturing_date"))
            if complaint.get("manufacturing_date")
            else None
        ),
        expiry_date=(
            str(complaint.get("expiry_date"))
            if complaint.get("expiry_date")
            else None
        ),
        quantity_affected=complaint.get("quantity_affected"),
        complaint_type=complaint.get("complaint_type"),
        complaint_date=(
            str(complaint.get("complaint_date"))
            if complaint.get("complaint_date")
            else None
        ),
        complaint_description=complaint.get(
            "complaint_description"
        ),
        severity=risk.get("severity"),
        priority=risk.get("priority"),
        risk_level=risk.get("risk_level"),
        reasoning=risk.get("reasoning"),
        recommended_action=risk.get(
            "recommended_action"
        ),
        recommendations=str(
            risk.get("recommendations")
        ) if risk.get("recommendations") else None,
    )

    db.add(db_complaint)
    db.commit()
    db.refresh(db_complaint)

    return {
    "complaint": complaint,
    "risk_assessment": risk,
    "completeness": result.get("completeness"),
    "duplicate": (
        {
            "is_duplicate": True,
            "complaint_id": duplicate.id,
            "customer_name": duplicate.customer_name,
            "product_name": duplicate.product_name,
            "batch_number": duplicate.batch_number,
            "complaint_type": duplicate.complaint_type,
            "reason": (
                "A complaint with the same product, "
                "batch number, and complaint type already exists."
            ),
        }
        if duplicate
        else {
            "is_duplicate": False,
            "complaint_id": None,
            "customer_name": None,
            "product_name": None,
            "batch_number": None,
            "complaint_type": None,
            "reason": "No matching previous complaint found.",
        }
    ),
    "complaint_id": db_complaint.id,
    "capa": result.get("capa"),
    "error": None,
}

@router.post("/edit")
def edit_existing_complaint(
    request: EditComplaintRequest,
    db: Session = Depends(get_db),
):
    state = {
        "raw_input": request.update,
        "complaint": request.current_complaint.model_dump(),
        "is_edit": True,
    }

    updated_state = edit_complaint(state)

    if updated_state.get("error"):
        return {
            "complaint": updated_state.get("complaint"),
            "risk_assessment": None,
            "completeness": None,
            "error": updated_state.get("error"),
        }

    final_state = assess_risk(updated_state)

    complaint = final_state.get("complaint") or {}
    risk = final_state.get("risk_assessment") or {}

    # Find the existing complaint.
    # For now we match using the current complaint's
    # batch number and customer name.
    db_complaint = (
        db.query(ComplaintModel)
        .filter(
            ComplaintModel.batch_number
            == request.current_complaint.batch_number,
            ComplaintModel.customer_name
            == request.current_complaint.customer_name,
        )
        .order_by(ComplaintModel.id.desc())
        .first()
    )

    if db_complaint:
        db_complaint.complaint_source = complaint.get(
            "complaint_source"
        )
        db_complaint.customer_name = complaint.get(
            "customer_name"
        )
        db_complaint.customer_email = complaint.get(
            "customer_email"
        )
        db_complaint.product_name = complaint.get(
            "product_name"
        )
        db_complaint.product_strength = complaint.get(
            "product_strength"
        )
        db_complaint.batch_number = complaint.get(
            "batch_number"
        )

        db_complaint.manufacturing_date = (
            str(complaint.get("manufacturing_date"))
            if complaint.get("manufacturing_date")
            else None
        )

        db_complaint.expiry_date = (
            str(complaint.get("expiry_date"))
            if complaint.get("expiry_date")
            else None
        )

        db_complaint.quantity_affected = complaint.get(
            "quantity_affected"
        )

        db_complaint.complaint_type = complaint.get(
            "complaint_type"
        )

        db_complaint.complaint_date = (
            str(complaint.get("complaint_date"))
            if complaint.get("complaint_date")
            else None
        )

        db_complaint.complaint_description = complaint.get(
            "complaint_description"
        )

        db_complaint.severity = risk.get("severity")
        db_complaint.priority = risk.get("priority")
        db_complaint.risk_level = risk.get("risk_level")
        db_complaint.reasoning = risk.get("reasoning")
        db_complaint.recommended_action = risk.get(
            "recommended_action"
        )

        db_complaint.recommendations = (
            str(risk.get("recommendations"))
            if risk.get("recommendations")
            else None
        )

        db.commit()
        db.refresh(db_complaint)

    return {
        "complaint": complaint,
        "risk_assessment": risk,
        "complaint_id": (
            db_complaint.id if db_complaint else None
        ),
        "error": final_state.get("error"),
    }

@router.post("/extract-document")
async def extract_complaint_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        return {
            "complaint": None,
            "risk_assessment": None,
            "completeness": None,
            "duplicate": None,
            "capa": None,
            "error": "Only PDF files are supported",
        }

    contents = await file.read()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf",
    ) as temp_file:
        temp_file.write(contents)
        temp_path = temp_file.name

    try:
        # 1. Extract text from PDF
        extracted_text = extract_text_from_pdf(temp_path)

        # 2. Run the complete LangGraph pipeline
        result = complaint_graph.invoke({
            "raw_input": extracted_text
        })

        if result.get("error"):
            return {
                "filename": file.filename,
                "extracted_text": extracted_text,
                "complaint": result.get("complaint"),
                "risk_assessment": result.get("risk_assessment"),
                "completeness": result.get("completeness"),
                "duplicate": None,
                "capa": result.get("capa"),
                "error": result.get("error"),
            }

        complaint = result.get("complaint") or {}
        risk = result.get("risk_assessment") or {}

        # 3. Check for duplicate BEFORE saving
        duplicate = find_duplicate_complaint(
            db,
            complaint,
        )

        # 4. Save complaint to PostgreSQL
        db_complaint = ComplaintModel(
            complaint_source=complaint.get(
                "complaint_source"
            ),
            customer_name=complaint.get(
                "customer_name"
            ),
            customer_email=complaint.get(
                "customer_email"
            ),
            product_name=complaint.get(
                "product_name"
            ),
            product_strength=complaint.get(
                "product_strength"
            ),
            batch_number=complaint.get(
                "batch_number"
            ),
            manufacturing_date=(
                str(complaint.get("manufacturing_date"))
                if complaint.get("manufacturing_date")
                else None
            ),
            expiry_date=(
                str(complaint.get("expiry_date"))
                if complaint.get("expiry_date")
                else None
            ),
            quantity_affected=complaint.get(
                "quantity_affected"
            ),
            complaint_type=complaint.get(
                "complaint_type"
            ),
            complaint_date=(
                str(complaint.get("complaint_date"))
                if complaint.get("complaint_date")
                else None
            ),
            complaint_description=complaint.get(
                "complaint_description"
            ),
            severity=risk.get("severity"),
            priority=risk.get("priority"),
            risk_level=risk.get("risk_level"),
            reasoning=risk.get("reasoning"),
            recommended_action=risk.get(
                "recommended_action"
            ),
            recommendations=(
                str(risk.get("recommendations"))
                if risk.get("recommendations")
                else None
            ),
        )

        db.add(db_complaint)
        db.commit()
        db.refresh(db_complaint)

        # 5. Return the COMPLETE AI result
        return {
            "filename": file.filename,
            "extracted_text": extracted_text,
            "complaint": complaint,
            "risk_assessment": risk,
            "completeness": result.get(
                "completeness"
            ),
            "duplicate": (
                {
                    "is_duplicate": True,
                    "complaint_id": duplicate.id,
                    "customer_name": duplicate.customer_name,
                    "product_name": duplicate.product_name,
                    "batch_number": duplicate.batch_number,
                    "complaint_type": duplicate.complaint_type,
                    "reason": (
                        "A complaint with the same "
                        "product, batch number, and "
                        "complaint type already exists."
                    ),
                }
                if duplicate
                else {
                    "is_duplicate": False,
                    "complaint_id": None,
                    "customer_name": None,
                    "product_name": None,
                    "batch_number": None,
                    "complaint_type": None,
                    "reason": (
                        "No matching previous "
                        "complaint found."
                    ),
                }
            ),
            "complaint_id": db_complaint.id,
            "capa": result.get("capa"),
            "error": None,
        }

    finally:
        os.unlink(temp_path)