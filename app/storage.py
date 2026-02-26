import json
import os
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from app.models import Quota, ProjectUsage, K8sConfig, PrometheusConfig, NamespaceQuota


class Storage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.quotas_file = self.data_dir / "quotas.json"
        self._init_quotas_file()

    def _init_quotas_file(self):
        if not self.quotas_file.exists():
            self._save_quotas({})

    def _load_quotas(self) -> Dict[str, Quota]:
        with open(self.quotas_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {k: Quota(**v) for k, v in data.items()}

    def _save_quotas(self, quotas: Dict[str, Quota]):
        with open(self.quotas_file, "w", encoding="utf-8") as f:
            json.dump({k: v.model_dump() for k, v in quotas.items()}, f, ensure_ascii=False, indent=2)

    def get_all_quotas(self) -> List[Quota]:
        quotas = self._load_quotas()
        return list(quotas.values())

    def get_quota(self, cloud_id: str) -> Optional[Quota]:
        quotas = self._load_quotas()
        return quotas.get(cloud_id)

    def get_quota_by_project(self, project_name: str) -> Optional[Quota]:
        quotas = self._load_quotas()
        for quota in quotas.values():
            if quota.project_name == project_name:
                return quota
        return None

    def add_quota(self, quota: Quota) -> bool:
        quotas = self._load_quotas()
        if quota.cloud_id in quotas:
            return False
        quotas[quota.cloud_id] = quota
        self._save_quotas(quotas)
        return True

    def update_quota(self, cloud_id: str, quota: Quota) -> bool:
        quotas = self._load_quotas()
        if cloud_id not in quotas:
            return False
        quotas[cloud_id] = quota
        self._save_quotas(quotas)
        return True

    def delete_quota(self, cloud_id: str) -> bool:
        quotas = self._load_quotas()
        if cloud_id not in quotas:
            return False
        del quotas[cloud_id]
        self._save_quotas(quotas)
        return True

    def import_quotas(self, quotas: List[Quota]) -> tuple[int, int]:
        existing = self._load_quotas()
        imported = 0
        updated = 0
        for quota in quotas:
            if quota.cloud_id in existing:
                existing[quota.cloud_id] = quota
                updated += 1
            else:
                existing[quota.cloud_id] = quota
                imported += 1
        self._save_quotas(existing)
        return imported, updated


class ReportStorage:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_report(self, filename: str, content: bytes) -> str:
        filepath = self.upload_dir / filename
        filepath.write_bytes(content)
        return str(filepath)

    def get_report(self, filename: str) -> Optional[bytes]:
        filepath = self.upload_dir / filename
        if filepath.exists():
            return filepath.read_bytes()
        return None

    def list_reports(self) -> List[str]:
        return [f.name for f in self.upload_dir.glob("Day_report_*")]

    def delete_report(self, filename: str) -> bool:
        filepath = self.upload_dir / filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False


class MemoryReportCache:
    def __init__(self):
        self._cache: Dict[str, List[ProjectUsage]] = {}

    def set(self, date: str, usages: List[ProjectUsage]):
        self._cache[date] = usages

    def add(self, date: str, usages: List[ProjectUsage]):
        existing = self._cache.get(date, [])
        existing_dict = {u.project_name: u for u in existing}
        
        for usage in usages:
            if usage.project_name in existing_dict:
                existing_dict[usage.project_name].cpu_usage += usage.cpu_usage
                existing_dict[usage.project_name].memory_usage += usage.memory_usage
            else:
                existing_dict[usage.project_name] = usage
        
        self._cache[date] = list(existing_dict.values())

    def get(self, date: str) -> Optional[List[ProjectUsage]]:
        return self._cache.get(date)

    def get_dates(self) -> List[str]:
        return sorted(self._cache.keys())

    def clear(self):
        self._cache.clear()


class K8sConfigStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.configs_file = self.data_dir / "k8s_configs.json"
        self._init_file()

    def _init_file(self):
        if not self.configs_file.exists():
            self._save_configs({})

    def _load_configs(self) -> Dict[str, K8sConfig]:
        with open(self.configs_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {k: K8sConfig(**v) for k, v in data.items()}

    def _save_configs(self, configs: Dict[str, K8sConfig]):
        with open(self.configs_file, "w", encoding="utf-8") as f:
            json.dump({k: v.model_dump() for k, v in configs.items()}, f, ensure_ascii=False, indent=2)

    def get_all(self) -> List[K8sConfig]:
        return list(self._load_configs().values())

    def get(self, id: str) -> Optional[K8sConfig]:
        return self._load_configs().get(id)

    def add(self, config: K8sConfig) -> bool:
        configs = self._load_configs()
        if config.id in configs:
            return False
        configs[config.id] = config
        self._save_configs(configs)
        return True

    def update(self, id: str, config: K8sConfig) -> bool:
        configs = self._load_configs()
        if id not in configs:
            return False
        configs[id] = config
        self._save_configs(configs)
        return True

    def delete(self, id: str) -> bool:
        configs = self._load_configs()
        if id not in configs:
            return False
        del configs[id]
        self._save_configs(configs)
        return True


class PrometheusConfigStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.configs_file = self.data_dir / "prometheus_configs.json"
        self._init_file()

    def _init_file(self):
        if not self.configs_file.exists():
            self._save_configs({})

    def _load_configs(self) -> Dict[str, PrometheusConfig]:
        with open(self.configs_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {k: PrometheusConfig(**v) for k, v in data.items()}

    def _save_configs(self, configs: Dict[str, PrometheusConfig]):
        with open(self.configs_file, "w", encoding="utf-8") as f:
            json.dump({k: v.model_dump() for k, v in configs.items()}, f, ensure_ascii=False, indent=2)

    def get_all(self) -> List[PrometheusConfig]:
        return list(self._load_configs().values())

    def get(self, id: str) -> Optional[PrometheusConfig]:
        return self._load_configs().get(id)

    def add(self, config: PrometheusConfig) -> bool:
        configs = self._load_configs()
        if config.id in configs:
            return False
        configs[config.id] = config
        self._save_configs(configs)
        return True

    def update(self, id: str, config: PrometheusConfig) -> bool:
        configs = self._load_configs()
        if id not in configs:
            return False
        configs[id] = config
        self._save_configs(configs)
        return True

    def delete(self, id: str) -> bool:
        configs = self._load_configs()
        if id not in configs:
            return False
        del configs[id]
        self._save_configs(configs)
        return True


class NamespaceQuotaStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.quotas_file = self.data_dir / "namespace_quotas.json"
        self._init_file()

    def _init_file(self):
        if not self.quotas_file.exists():
            self._save_quotas({})

    def _load_quotas(self) -> Dict[str, NamespaceQuota]:
        with open(self.quotas_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {k: NamespaceQuota(**v) for k, v in data.items()}

    def _save_quotas(self, quotas: Dict[str, NamespaceQuota]):
        with open(self.quotas_file, "w", encoding="utf-8") as f:
            json.dump({k: v.model_dump() for k, v in quotas.items()}, f, ensure_ascii=False, indent=2)

    def get_all(self) -> List[NamespaceQuota]:
        return list(self._load_quotas().values())

    def get(self, cluster_name: str, namespace: str) -> Optional[NamespaceQuota]:
        key = f"{cluster_name}__{namespace}"
        return self._load_quotas().get(key)

    def save(self, quota: NamespaceQuota):
        quotas = self._load_quotas()
        key = f"{quota.cluster_name}__{quota.namespace}"
        quotas[key] = quota
        self._save_quotas(quotas)

    def get_by_cluster(self, cluster_name: str) -> List[NamespaceQuota]:
        all_quotas = self._load_quotas()
        return [q for q in all_quotas.values() if q.cluster_name == cluster_name]

    def delete(self, cluster_name: str, namespace: str) -> bool:
        key = f"{cluster_name}__{namespace}"
        quotas = self._load_quotas()
        if key not in quotas:
            return False
        del quotas[key]
        self._save_quotas(quotas)
        return True
