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


class K8sConfig(BaseModel):
    id: str
    name: str
    kubeconfig: str
    use_projectquota: bool = True


class K8sConfigCreate(BaseModel):
    name: str
    kubeconfig: str
    use_projectquota: bool = True


class PrometheusConfig(BaseModel):
    id: str
    name: str
    url: str
    cluster_name: str
    use_accurate_sync: bool = False


class PrometheusConfigCreate(BaseModel):
    name: str
    url: str
    cluster_name: str
    use_accurate_sync: bool = False


class NamespaceQuota(BaseModel):
    cluster_name: str
    namespace: str
    project_name: str = ""
    cpu_limit: float = 0
    memory_limit: float = 0
    cpu_used: float = 0
    memory_used: float = 0
    pods_limit: int = 0
    pods_used: int = 0
    storage_limit: float = 0
    storage_used: float = 0


class SyncResult(BaseModel):
    success: bool
    imported: int = 0
    updated: int = 0
    errors: List[str] = []


class NamespaceUsageDetail(BaseModel):
    namespace: str
    project_name: str = ""
    cpu_usage: float = 0
    memory_usage: float = 0
    cpu_limit: float = 0
    memory_limit: float = 0
    cpu_rate: float = 0
    memory_rate: float = 0
    pod_count: int = 0
    workload_replicas: Dict[str, int] = {}


class K8sNamespace(BaseModel):
    name: str
    cpu_quota: float = 0
    memory_quota: float = 0
