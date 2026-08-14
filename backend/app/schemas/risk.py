from typing import List

from pydantic import BaseModel


class RiskAssessment(BaseModel):
    severity: str | None = None
    priority: str | None = None
    risk_level: str | None = None
    reasoning: str | None = None
    recommended_action: str | None = None
    recommendations: List[str] = []