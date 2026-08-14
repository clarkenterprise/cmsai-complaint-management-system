from typing import TypedDict


class ComplaintState(TypedDict, total=False):
    raw_input: str

    complaint: dict
    risk_assessment: dict
    completeness: dict
    capa: dict

    missing_fields: list[str]

    is_edit: bool

    error: str | None