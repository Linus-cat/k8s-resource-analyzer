from typing import List, Dict, Optional
from datetime import datetime

from app.models import NamespaceUsage, ProjectUsage, Quota
from app.storage import Storage


class Calculator:
    def __init__(self, storage: Storage):
        self.storage = storage

    def aggregate_by_project(
        self, project_data: List[tuple[str, List[NamespaceUsage]]]
    ) -> Dict[str, ProjectUsage]:
        result = {}

        for project_name, namespaces in project_data:
            total_cpu = sum(ns.cpu_usage for ns in namespaces)
            total_memory = sum(ns.memory_usage for ns in namespaces)

            result[project_name] = ProjectUsage(
                project_name=project_name,
                cpu_usage=total_cpu,
                memory_usage=total_memory
            )

        return result

    def calculate_rates(
        self, project_usages: Dict[str, ProjectUsage]
    ) -> Dict[str, ProjectUsage]:
        for project_name, usage in project_usages.items():
            quota = self.storage.get_quota_by_project(project_name)

            if quota:
                if quota.cpu_quota > 0:
                    usage.cpu_rate = min((usage.cpu_usage / quota.cpu_quota) * 100, 100.0)
                else:
                    usage.cpu_rate = 0.0

                if quota.memory_quota > 0:
                    usage.memory_rate = min((usage.memory_usage / quota.memory_quota) * 100, 100.0)
                else:
                    usage.memory_rate = 0.0

                usage.cloud_id = quota.cloud_id
            else:
                usage.cpu_rate = None
                usage.memory_rate = None
                usage.cloud_id = None

        return project_usages

    def process_report(
        self, project_data: List[tuple[str, List[NamespaceUsage]]]
    ) -> List[ProjectUsage]:
        aggregated = self.aggregate_by_project(project_data)
        with_rates = self.calculate_rates(aggregated)
        return list(with_rates.values())

    def format_date(self, date_str: str) -> str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
