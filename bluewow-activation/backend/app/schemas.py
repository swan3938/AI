from pydantic import BaseModel
from typing import Optional, List

class RosterRow(BaseModel):
    employee_id: str
    name: Optional[str] = None
    company: Optional[str] = None
    subject: Optional[str] = None

class ActivationRow(BaseModel):
    employee_id: str
    first_login_at: str
    platform: Optional[str] = None
    subject: Optional[str] = None

class MatchedRecord(BaseModel):
    employee_id: str
    name: Optional[str] = None
    company: Optional[str] = None
    subject: Optional[str] = None
    first_login_at: Optional[str] = None

class OverviewMetrics(BaseModel):
    total: int
    activated: int
    activation_rate: float

class MonthlyMetricsItem(BaseModel):
    month: str
    activated: int
    activation_rate: float

class SubjectMetricsItem(BaseModel):
    subject: str
    count: int
    rate: Optional[float] = None
    month: Optional[str] = None
