from datetime import date
from typing import Optional

from pydantic import BaseModel


class Complaint(BaseModel):
    complaint_source: Optional[str] = None

    customer_name: Optional[str] = None
    customer_email: Optional[str] = None

    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None

    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None

    quantity_affected: Optional[str] = None

    complaint_type: Optional[str] = None
    complaint_date: Optional[date] = None
    complaint_description: Optional[str] = None

    severity: Optional[str] = None
    priority: Optional[str] = None