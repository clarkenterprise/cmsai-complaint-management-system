import json
import re

from app.agents.state import ComplaintState
from app.services.groq_service import ask_groq

def parse_json_response(response: str) -> dict:
    response = response.strip()

    # Remove Markdown code fences if the model added them
    response = re.sub(r"^```json\s*", "", response, flags=re.IGNORECASE)
    response = re.sub(r"^```\s*", "", response)
    response = re.sub(r"\s*```$", "", response)

    return json.loads(response)

def extract_complaint(state: ComplaintState) -> ComplaintState:
    prompt = f"""
You are an AI assistant for a pharmaceutical customer complaint
management system.

Extract structured information from the customer's complaint.

USER INPUT:
{state["raw_input"]}

Return ONLY one valid JSON object.
Do not use Markdown.
Do not use ```json.
Do not add explanations.

Use exactly this structure:

{{
  "complaint_source": null,
  "customer_name": null,
  "customer_email": null,
  "product_name": null,
  "product_strength": null,
  "batch_number": null,
  "manufacturing_date": null,
  "expiry_date": null,
  "quantity_affected": null,
  "complaint_type": null,
  "complaint_date": null,
  "complaint_description": null
}}

IMPORTANT FIELD RULES:

1. complaint_source:
   Identify how the complaint was received.
   Examples: "Customer", "Email", "Phone", "Portal", "Document".
   If the text simply describes a customer reporting a complaint
   and does not specify the communication channel, use "Customer".

2. customer_name:
   Extract the name of the customer, pharmacy, distributor,
   hospital, company, or organization making the complaint.

3. product_name:
   Extract only the product name.
   Do not put strength or grade into this field.

4. product_strength:
   Extract strength, grade, specification, IP/BP, etc.

5. batch_number:
   Extract the batch or lot number exactly as provided.

6. quantity_affected:
   Preserve both the number and unit.
   Example: "48 capsules", "50 kg", "2 drums".

7. complaint_type:
   Classify the complaint.
   Examples:
   - Product Quality
   - Packaging
   - Labeling
   - Delivery
   - Documentation
   - Other

8. complaint_description:
   Write a concise description of the actual complaint.

9. Dates:
   If a date is not explicitly provided, return null.
   Never invent dates.

10. Missing information:
    Return null.
    Never invent information.

USER INPUT:
{state["raw_input"]}
"""

    response = ask_groq(prompt)

    try:
        complaint = parse_json_response(response)
    except json.JSONDecodeError:
        return {
            **state,
            "error": "AI returned invalid complaint JSON",
        }

    return {
        **state,
        "complaint": complaint,
    }

def assess_risk(state: ComplaintState) -> ComplaintState:
    complaint = state.get("complaint", {})

    prompt = f"""
You are a pharmaceutical customer complaint risk assessment assistant.

Analyze this complaint:

{json.dumps(complaint, indent=2, default=str)}

Return ONLY a single valid JSON object.

Do NOT use Markdown.
Do NOT use ```json.
Do NOT add explanations before or after the JSON.

Use exactly this structure:

{{
  "severity": "Major",
  "priority": "High",
  "risk_level": "High",
  "reasoning": "Brief explanation",
  "recommended_action": "Recommended next action",
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2"
  ]
}}

Rules:

1. severity must be one of:
   Minor, Moderate, Major, Critical

2. priority must be one of:
   Low, Medium, High, Critical

3. risk_level must be one of:
   Low, Medium, High, Critical

4. Base the assessment only on information contained in the complaint.

5. Do not invent batch information, patient information, medical outcomes,
   or other facts.

6. This is an AI recommendation for review by a qualified QA professional.
   It is not a final pharmaceutical quality decision.

Complaint:
{json.dumps(complaint, default=str)}
"""

    response = ask_groq(prompt)

    try:
        risk_assessment = parse_json_response(response)
    except json.JSONDecodeError:
        return {
            **state,
            "error": "AI returned invalid risk assessment JSON",
        }

    return {
        **state,
        "risk_assessment": risk_assessment,
    }
def edit_complaint(state: ComplaintState) -> ComplaintState:
    current_complaint = state.get("complaint", {})

    prompt = f"""
You are an AI assistant for a pharmaceutical customer complaint
management system.

An existing complaint already exists.

EXISTING COMPLAINT:
{json.dumps(current_complaint, indent=2, default=str)}

The user has provided a correction or update:

USER UPDATE:
{state["raw_input"]}

Identify ONLY the fields that the user explicitly wants to change.

Return ONLY a valid JSON object.

Do not use Markdown.
Do not use ```json.
Do not add explanations.

Use this structure:

{{
  "customer_name": null,
  "customer_email": null,
  "product_name": null,
  "product_strength": null,
  "batch_number": null,
  "manufacturing_date": null,
  "expiry_date": null,
  "quantity_affected": null,
  "complaint_type": null,
  "complaint_date": null,
  "complaint_description": null
}}

IMPORTANT:

- Only include fields that the user is changing.
- For fields that are NOT being changed, return null.
- Never modify information that the user did not request to modify.
- Never invent information.
"""

    response = ask_groq(prompt)

    try:
        updates = parse_json_response(response)
    except json.JSONDecodeError:
        return {
            **state,
            "error": "AI returned invalid edit JSON",
        }

    # Only apply fields that contain actual values.
    updated_complaint = current_complaint.copy()

    for field, value in updates.items():
        if value is not None:
            updated_complaint[field] = value

    return {
        **state,
        "complaint": updated_complaint,
        "is_edit": True,
    }

    complaint = state.get("complaint", {})

    fields = {
        "Customer Information": [
            complaint.get("customer_name"),
            complaint.get("customer_email"),
        ],
        "Product Information": [
            complaint.get("product_name"),
            complaint.get("product_strength"),
        ],
        "Batch Information": [
            complaint.get("batch_number"),
            complaint.get("manufacturing_date"),
            complaint.get("expiry_date"),
        ],
        "Complaint Details": [
            complaint.get("complaint_type"),
            complaint.get("complaint_description"),
        ],
        "Quantity Affected": [
            complaint.get("quantity_affected"),
        ],
    }

    checks = []
    completed = 0
    total = len(fields)

    for category, values in fields.items():
        is_complete = all(
            value is not None and str(value).strip() != ""
            for value in values
        )

        checks.append({
            "category": category,
            "complete": is_complete,
        })

        if is_complete:
            completed += 1

    score = round((completed / total) * 100)

    missing = [
        item["category"]
        for item in checks
        if not item["complete"]
    ]

    completeness = {
        "score": score,
        "completed": completed,
        "total": total,
        "checks": checks,
        "missing": missing,
    }

    return {
        **state,
        "completeness": completeness,
    }
def check_completeness(state: ComplaintState) -> ComplaintState:
    complaint = state.get("complaint", {})

    fields = {
        "Customer Information": [
            complaint.get("customer_name"),
            complaint.get("customer_email"),
        ],
        "Product Information": [
            complaint.get("product_name"),
            complaint.get("product_strength"),
        ],
        "Batch Information": [
            complaint.get("batch_number"),
            complaint.get("manufacturing_date"),
            complaint.get("expiry_date"),
        ],
        "Complaint Details": [
            complaint.get("complaint_type"),
            complaint.get("complaint_description"),
        ],
        "Quantity Affected": [
            complaint.get("quantity_affected"),
        ],
    }

    checks = []
    completed = 0
    total = len(fields)

    for category, values in fields.items():
        is_complete = all(
            value is not None and str(value).strip() != ""
            for value in values
        )

        checks.append({
            "category": category,
            "complete": is_complete,
        })

        if is_complete:
            completed += 1

    score = round((completed / total) * 100)

    missing = [
        item["category"]
        for item in checks
        if not item["complete"]
    ]

    completeness = {
        "score": score,
        "completed": completed,
        "total": total,
        "checks": checks,
        "missing": missing,
    }

    return {
        **state,
        "completeness": completeness,
    }
def generate_capa(state: ComplaintState) -> ComplaintState:
    complaint = state.get("complaint", {})
    risk = state.get("risk_assessment", {})

    prompt = f"""
You are a pharmaceutical Quality Assurance assistant.

Generate a practical CAPA recommendation for the following
customer complaint.

COMPLAINT:
{json.dumps(complaint, indent=2, default=str)}

RISK ASSESSMENT:
{json.dumps(risk, indent=2, default=str)}

CAPA means:
- Corrective Action: actions to address the current complaint/problem.
- Preventive Action: actions to reduce the likelihood of recurrence.

Return ONLY one valid JSON object.
Do not use Markdown.
Do not use ```json.
Do not add explanations outside the JSON.

Use exactly this structure:

{{
  "corrective_action": "Specific action to address the current issue",
  "preventive_action": "Specific action to prevent recurrence",
  "investigation_required": true,
  "priority": "High",
  "reasoning": "Brief explanation"
}}

Rules:

1. Base the recommendation only on the complaint and risk assessment.
2. Do not invent laboratory results, root causes, batch findings,
   patient outcomes, or confirmed manufacturing failures.
3. If the root cause is unknown, recommend an investigation rather
   than claiming a root cause.
4. Priority must be one of:
   Low, Medium, High, Critical
5. investigation_required must be true or false.
6. These are AI-generated recommendations for review by qualified
   pharmaceutical QA personnel. They are not final CAPA decisions.

"""

    response = ask_groq(prompt)

    try:
        capa = parse_json_response(response)
    except json.JSONDecodeError:
        return {
            **state,
            "error": "AI returned invalid CAPA JSON",
        }

    return {
        **state,
        "capa": capa,
    }