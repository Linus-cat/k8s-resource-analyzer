import urllib.request
import urllib.parse
import json
import re
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta

from app.models import NamespaceUsage, SyncResult, NamespaceUsageDetail


class PrometheusClient:
    ROLLING_UPDATE_TOLERANCE = 1.5

    def __init__(self, url: str):
        self.url = url.rstrip('/')

    def _query(self, query: str, time: Optional[int] = None) -> Optional[Dict]:
        try:
            params = {'query': query}
            if time:
                params['time'] = str(time)

            url = f"{self.url}/api/v1/query?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url)

            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode('utf-8'))

        except Exception as e:
            print(f"Prometheus query error: {e}")
            return None

    def _query_range(self, query: str, start: int, end: int, step: str = '1h') -> Optional[Dict]:
        try:
            params = {
                'query': query,
                'start': str(start),
                'end': str(end),
                'step': step
            }

            url = f"{self.url}/api/v1/query_range?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url)

            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode('utf-8'))

        except Exception as e:
            print(f"Prometheus query_range error: {e}")
            return None

    def get_namespace_usage(self, date: str = None) -> List[NamespaceUsage]:
        if date:
            try:
                dt = datetime.strptime(date, '%Y-%m-%d')
                timestamp = int(dt.timestamp())
            except:
                timestamp = None
        else:
            timestamp = None

        cpu_query = '''
            sum by (namespace) (
                max by (pod) (
                    max_over_time(
                        (irate(container_cpu_usage_seconds_total{namespace!="", container!="", container!="POD"}[5m]))[1d:]
                    )
                )
            )
        '''
        
        mem_query = '''
            sum by (namespace) (
                max by (pod) (
                    max_over_time(
                        container_memory_usage_bytes{namespace!="", container!="", container!="POD"}[1d]
                    )
                )
            )
        '''

        cpu_result = self._query(cpu_query, timestamp)
        mem_result = self._query(mem_query, timestamp)

        cpu_data = {}
        if cpu_result and cpu_result.get('status') == 'success':
            for item in cpu_result.get('data', {}).get('result', []):
                ns = item.get('metric', {}).get('namespace', '')
                val = float(item.get('value', [0, 0])[1])
                cpu_data[ns] = val

        mem_data = {}
        if mem_result and mem_result.get('status') == 'success':
            for item in mem_result.get('data', {}).get('result', []):
                ns = item.get('metric', {}).get('namespace', '')
                val = float(item.get('value', [0, 0])[1])
                mem_data[ns] = val / (1024 * 1024 * 1024)

        namespaces = set(cpu_data.keys()) | set(mem_data.keys())
        results = []

        for ns in namespaces:
            results.append(NamespaceUsage(
                namespace=ns,
                cpu_usage=cpu_data.get(ns, 0),
                memory_usage=mem_data.get(ns, 0)
            ))

        return results

    def _extract_workload_name(self, pod_name: str) -> str:
        """从 pod name 提取 workload name (去掉随机后缀)"""
        parts = pod_name.split('-')
        if len(parts) >= 2:
            if parts[-1].isdigit():
                return '-'.join(parts[:-1])
        return pod_name

    def _get_pod_peaks_by_workload(self, namespace: str, workload_replicas: Dict[str, int]) -> Dict[str, List[float]]:
        """获取每个 workload 下所有 Pod 的 CPU 峰值"""
        cpu_query = f'''
            max by (pod) (
                max_over_time(
                    (irate(container_cpu_usage_seconds_total{{namespace="{namespace}", container!="", container!="POD"}}[5m]))[1d:]
                )
            )
        '''
        mem_query = f'''
            max by (pod) (
                max_over_time(
                    container_memory_usage_bytes{{namespace="{namespace}", container!="", container!="POD"}}[1d]
                )
            )
        '''
        
        cpu_result = self._query(cpu_query)
        mem_result = self._query(mem_query)
        
        pod_cpu_peaks = {}
        pod_mem_peaks = {}
        
        if cpu_result and cpu_result.get('status') == 'success':
            for item in cpu_result.get('data', {}).get('result', []):
                pod = item.get('metric', {}).get('pod', '')
                if pod:
                    val = float(item.get('value', [0, 0])[1])
                    pod_cpu_peaks[pod] = val
        
        if mem_result and mem_result.get('status') == 'success':
            for item in mem_result.get('data', {}).get('result', []):
                pod = item.get('metric', {}).get('pod', '')
                if pod:
                    val = float(item.get('value', [0, 0])[1]) / (1024 * 1024 * 1024)
                    pod_mem_peaks[pod] = val
        
        workload_pods = {}
        for pod in pod_cpu_peaks.keys():
            workload = self._extract_workload_name(pod)
            if workload not in workload_pods:
                workload_pods[workload] = {'pods': [], 'cpu': [], 'mem': []}
            workload_pods[workload]['pods'].append(pod)
            workload_pods[workload]['cpu'].append(pod_cpu_peaks.get(pod, 0))
            workload_pods[workload]['mem'].append(pod_mem_peaks.get(pod, 0))
        
        return workload_pods

    def _aggregate_by_replicas(self, workload_pods: Dict, workload_replicas: Dict[str, int]) -> Tuple[float, float]:
        """根据副本数聚合资源使用量"""
        total_cpu = 0.0
        total_mem = 0.0
        
        for workload, data in workload_pods.items():
            cpu_values = sorted(data['cpu'], reverse=True)
            mem_values = sorted(data['mem'], reverse=True)
            
            pod_count = len(cpu_values)
            expected_replicas = workload_replicas.get(workload, 0)
            
            if expected_replicas == 0:
                expected_replicas = pod_count
            
            max_allowed = int(expected_replicas * self.ROLLING_UPDATE_TOLERANCE)
            
            if pod_count > max_allowed:
                cpu_values = cpu_values[:max_allowed]
                mem_values = mem_values[:max_allowed]
            
            total_cpu += sum(cpu_values)
            total_mem += sum(mem_values)
        
        return total_cpu, total_mem

    def get_namespace_usage_accurate(self, namespace: str, workload_replicas: Dict[str, int]) -> NamespaceUsageDetail:
        """获取命名空间的精确使用量（基于副本数去重）"""
        workload_pods = self._get_pod_peaks_by_workload(namespace, workload_replicas)
        cpu_usage, mem_usage = self._aggregate_by_replicas(workload_pods, workload_replicas)
        
        return NamespaceUsageDetail(
            namespace=namespace,
            project_name="",
            cpu_usage=cpu_usage,
            memory_usage=mem_usage
        )

    def get_all_namespaces_usage_accurate(self, namespaces: List[str], k8s_client) -> List[NamespaceUsageDetail]:
        """获取所有命名空间的精确使用量"""
        results = []
        
        for namespace in namespaces:
            workload_replicas = k8s_client.get_workload_replicas(namespace)
            usage = self.get_namespace_usage_accurate(namespace, workload_replicas)
            
            ns_info = k8s_client.get_namespace_with_project(namespace)
            if ns_info:
                usage.project_name = ns_info.get('project_name', '')
            
            results.append(usage)
        
        return results


def sync_prometheus_usage(prometheus_url: str, date: str, report_cache) -> SyncResult:
    client = PrometheusClient(prometheus_url)
    usages = client.get_namespace_usage(date)

    imported = 0
    errors = []

    for usage in usages:
        from app.models import ProjectUsage
        project_usage = ProjectUsage(
            project_name=usage.namespace,
            cpu_usage=usage.cpu_usage,
            memory_usage=usage.memory_usage
        )
        report_cache.add(date, [project_usage])
        imported += 1

    return SyncResult(
        success=True,
        imported=imported,
        updated=0,
        errors=errors
    )


def sync_prometheus_usage_accurate(prometheus_url: str, kubeconfig: str, cluster_name: str, 
                                    date: str, storage, report_cache) -> SyncResult:
    """使用精确方式同步 Prometheus 数据（基于副本数去重）"""
    from app.k8s_client import K8sClient
    
    prom_client = PrometheusClient(prometheus_url)
    k8s_client = K8sClient(kubeconfig, cluster_name)
    
    namespaces = k8s_client.get_namespace_list()
    if not namespaces:
        return SyncResult(success=False, imported=0, updated=0, errors=["No namespaces found"])
    
    usages = prom_client.get_all_namespaces_usage_accurate(namespaces, k8s_client)
    
    imported = 0
    errors = []
    
    for usage in usages:
        from app.models import ProjectUsage
        
        if not usage.project_name:
            usage.project_name = usage.namespace
        
        project_usage = ProjectUsage(
            project_name=usage.project_name,
            cloud_id=f"{cluster_name}__{usage.namespace}",
            cpu_usage=usage.cpu_usage,
            memory_usage=usage.memory_usage
        )
        report_cache.add(date, [project_usage])
        
        ns_quota = storage.get_namespace_quota(cluster_name, usage.namespace)
        if ns_quota and ns_quota.cpu_limit > 0:
            project_usage.cpu_rate = min(usage.cpu_usage / ns_quota.cpu_limit * 100, 100)
        if ns_quota and ns_quota.memory_limit > 0:
            project_usage.memory_rate = min(usage.memory_usage / ns_quota.memory_limit * 100, 100)
        
        imported += 1
    
    return SyncResult(
        success=True,
        imported=imported,
        updated=0,
        errors=errors
    )
