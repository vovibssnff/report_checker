from __future__ import annotations

from pydantic import BaseModel


class CommonErrorItem(BaseModel):
    rule_code: str
    count: int


class StatsResponse(BaseModel):
    total_documents: int
    passed_count: int
    failed_count: int
    warning_count: int
    pass_rate: float
    common_errors: list[CommonErrorItem]
