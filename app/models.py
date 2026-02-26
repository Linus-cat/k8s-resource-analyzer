from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class Quota(BaseModel):
    cloud_id: str
    project_name: str
    cpu_quota: float
    memory_quota: float


class QuotaUpdate(BaseModel):
    project_name: Optional[str] = None
    cpu_quota: Optional[float] = None
    memory_quota: Optional[float] = None


class NamespaceUsage(BaseModel):
    namespace: str
    cpu_usage: float
    memory_usage: float


class ProjectUsage(BaseModel):
    project_name: str
    cloud_id: Optional[str] = None
    cpu_usage: float
    memory_usage: float
    cpu_rate: Optional[float] = None
    memory_rate: Optional[float] = None


class DailyReportData(BaseModel):
    date: str
    project_usages: List[ProjectUsage]


class ReportFile(BaseModel):
    filename: str
    date: str
    record_count: int


class ExportRequest(BaseModel):
    dates: List[str]


class ImportResult(BaseModel):
    success: bool
    imported: int
    updated: int
    errors: List[str] = []
