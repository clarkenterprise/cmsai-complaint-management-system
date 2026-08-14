from pydantic import BaseModel

from app.schemas.complaint import Complaint


class EditComplaintRequest(BaseModel):
    current_complaint: Complaint
    update: str