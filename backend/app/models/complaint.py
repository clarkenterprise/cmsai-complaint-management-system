from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class ComplaintModel(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    complaint_source = Column(String(100))
    customer_name = Column(String(255))
    customer_email = Column(String(255))

    product_name = Column(String(255))
    product_strength = Column(String(255))
    batch_number = Column(String(255))

    manufacturing_date = Column(String(50))
    expiry_date = Column(String(50))

    quantity_affected = Column(String(100))

    complaint_type = Column(String(255))
    complaint_date = Column(String(50))
    complaint_description = Column(Text)

    severity = Column(String(100))
    priority = Column(String(100))
    risk_level = Column(String(100))

    reasoning = Column(Text)
    recommended_action = Column(Text)
    recommendations = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )