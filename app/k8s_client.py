import base64
import json
import yaml
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models import K8sNamespace, SyncResult, NamespaceQuota


class K8sClient:
    def __init__(self, kubeconfig: str, cluster_name: str = ""):
        self.kubeconfig = kubeconfig
        self.cluster_name = cluster_name
        self.config = self._parse_kubeconfig(kubeconfig)
        self.base_url = None
        self.token = None
        self.ca_cert = None
        self._setup_connection()

    def _parse_kubeconfig(self, kubeconfig_str: str) -> Dict[str, Any]:
        try:
            return yaml.safe_load(kubeconfig_str)
        except:
            try:
                decoded = base64.b64decode(kubeconfig_str).decode('utf-8')
                return yaml.safe_load(decoded)
            except:
                return {}

    def _setup_connection(self):
        if not self.config:
            return

        for ctx_name, context in self.config.get('contexts', []):
            if context.get('context', {}).get('cluster'):
                cluster = self.config.get('clusters', [])
                for c in cluster:
                    if c.get('name') == context['context']['cluster']:
                        server = c.get('cluster', {}).get('server', '')
                        self.base_url = server.rstrip('/')
                        self.ca_cert = c.get('cluster', {}).get('certificate-authority-data', '')
                        break

                user = context.get('context', {}).get('user', '')
                users = self.config.get('users', [])
                for u in users:
                    if u.get('name') == user:
                        self.token = u.get('user', {}).get('token', '')
                        if not self.token:
                            token_file = u.get('user', {}).get('tokenFile', '')
                            if token_file:
                                try:
                                    with open(token_file, 'r') as f:
                                        self.token = f.read().strip()
                                except:
                                    pass
                        break

    def _request(self, path: str, method: str = 'GET') -> Optional[Dict]:
        if not self.base_url:
            return None

        try:
            import urllib.request
            import urllib.error

            url = f"{self.base_url}{path}"
            req = urllib.request.Request(url, method=method)

            if self.token:
                req.add_header('Authorization', f'Bearer {self.token}')

            if self.ca_cert:
                try:
                    ca_data = base64.b64decode(self.ca_cert).decode('utf-8')
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False) as ca_file:
                        ca_file.write(ca_data)
                        ca_path = ca_file.name
                except:
                    ca_path = None
            else:
                ca_path = None

            ctx = None
            if ca_path:
                import ssl
                ctx = ssl.create_default_context(cafile=ca_path)
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, context=ctx) as resp:
                data = resp.read().decode('utf-8')
                return json.loads(data) if data else {}

        except Exception as e:
            print(f"K8s API error: {e}")
            return None

    def get_namespaces(self) -> List[K8sNamespace]:
        result = self._request('/api/v1/namespaces')
        if not result:
            return []

        namespaces = []
        for item in result.get('items', []):
            name = item.get('metadata', {}).get('name', '')
            if name and not name.startswith('kube-'):
                quota = self.get_resource_quota(name)
                namespaces.append(K8sNamespace(
                    name=name,
                    cpu_quota=quota.get('cpu'),
                    memory_quota=quota.get('memory')
                ))

        return namespaces

    def get_projectquotas(self) -> List[Dict]:
        result = self._request('/apis/auth.alauda.io/v1/projectquotas')
        if not result:
            return []
        
        items = []
        for item in result.get('items', []):
            metadata = item.get('metadata', {})
            spec = item.get('spec', {})
            status = item.get('status', {})
            
            hard = spec.get('hard', {})
            used = status.get('used', {})
            
            if not hard or (not hard.get('limits.cpu') and not hard.get('requests.cpu') and not hard.get('limits.memory') and not hard.get('requests.memory')):
                continue
            
            project_name = metadata.get('labels', {}).get('cpaas.io/project', metadata.get('name', ''))
            
            cpu_str = hard.get('limits.cpu', hard.get('requests.cpu', '0'))
            mem_str = hard.get('limits.memory', hard.get('requests.memory', '0'))
            
            cpu = self._parse_cpu(cpu_str)
            memory = self._parse_memory(mem_str)
            
            items.append({
                'name': project_name,
                'cloud_id': project_name,
                'cpu_quota': cpu,
                'memory_quota': memory,
                'cpu_used': self._parse_cpu(used.get('limits.cpu', used.get('requests.cpu', '0'))),
                'memory_used': self._parse_memory(used.get('limits.memory', used.get('requests.memory', '0')))
            })
        
        return items

    def _parse_cpu(self, cpu_str: str) -> float:
        if not cpu_str or cpu_str == '0':
            return 0.0
        try:
            if cpu_str.endswith('m'):
                return float(cpu_str[:-1]) / 1000
            return float(cpu_str)
        except:
            return 0.0

    def _parse_memory(self, mem_str: str) -> float:
        if not mem_str or mem_str == '0':
            return 0.0
        try:
            if mem_str.endswith('Ki'):
                return float(mem_str[:-2]) / 1024 / 1024
            elif mem_str.endswith('Mi'):
                return float(mem_str[:-2]) / 1024
            elif mem_str.endswith('Gi'):
                return float(mem_str[:-2])
            elif mem_str.endswith('Ti'):
                return float(mem_str[:-2]) * 1024
            elif mem_str.endswith('K'):
                return float(mem_str[:-1]) / 1000 / 1024
            elif mem_str.endswith('M'):
                return float(mem_str[:-1]) / 1000
            elif mem_str.endswith('G'):
                return float(mem_str[:-1])
            else:
                return float(mem_str) / 1024 / 1024 / 1024
        except:
            return 0.0

    def get_resource_quota(self, namespace: str) -> Dict[str, float]:
        result = self._request(f'/api/v1/namespaces/{namespace}/resourcequota')
        if not result:
            return {'cpu': 0, 'memory': 0}

        cpu = 0.0
        memory = 0.0

        for item in result.get('items', []):
            limits = item.get('status', {}).get('hard', {})
            cpu_str = limits.get('limits.cpu', limits.get('requests.cpu', '0'))
            mem_str = limits.get('limits.memory', limits.get('requests.memory', '0'))

            cpu = self._parse_cpu(cpu_str)
            memory = self._parse_memory(mem_str)

        return {'cpu': cpu, 'memory': memory}

    def get_namespace_with_project(self, namespace: str) -> Optional[Dict]:
        """获取命名空间信息，包含项目名称"""
        result = self._request(f'/api/v1/namespaces/{namespace}')
        if not result:
            return None
        
        labels = result.get('metadata', {}).get('labels', {})
        annotations = result.get('metadata', {}).get('annotations', {})
        project_name = labels.get('cpaas.io/project', '')
        
        return {
            'name': namespace,
            'project_name': project_name,
            'labels': labels,
            'annotations': annotations
        }

    def get_resource_quota_limits(self, namespace: str) -> Optional[Dict]:
        """获取命名空间 limits 配额"""
        result = self._request(f'/api/v1/namespaces/{namespace}/resourcequota')
        if not result or not result.get('items'):
            return None
        
        item = result['items'][0]
        hard = item.get('status', {}).get('hard', {})
        used = item.get('status', {}).get('used', {})
        
        return {
            'cpu_limit': self._parse_cpu(hard.get('limits.cpu', '0')),
            'memory_limit': self._parse_memory(hard.get('limits.memory', '0')),
            'cpu_used': self._parse_cpu(used.get('limits.cpu', '0')),
            'memory_used': self._parse_memory(used.get('limits.memory', '0')),
            'pods_limit': self._parse_quantity(hard.get('pods', '0')),
            'pods_used': self._parse_quantity(used.get('pods', '0')),
            'storage_limit': self._parse_storage(hard.get('requests.storage', '0')),
            'storage_used': self._parse_storage(used.get('requests.storage', '0')),
        }

    def _parse_quantity(self, qty: str) -> int:
        """解析 Kubernetes quantity (如 1k, 2m)"""
        if not qty or qty == '0':
            return 0
        try:
            if qty.endswith('k'):
                return int(float(qty[:-1]) * 1000)
            elif qty.endswith('m'):
                return int(float(qty[:-1]) / 1000)
            elif qty.endswith('Ki'):
                return int(float(qty[:-2]) * 1024)
            elif qty.endswith('Mi'):
                return int(float(qty[:-2]))
            elif qty.endswith('Gi'):
                return int(float(qty[:-2]) * 1024)
            elif qty.endswith('Ti'):
                return int(float(qty[:-2]) * 1024 * 1024)
            elif qty.endswith('K'):
                return int(float(qty[:-1]) * 1000)
            elif qty.endswith('M'):
                return int(float(qty[:-1]) * 1000 * 1000)
            elif qty.endswith('G'):
                return int(float(qty[:-1]) * 1000 * 1000 * 1000)
            else:
                return int(float(qty))
        except:
            return 0

    def _parse_storage(self, storage_str: str) -> float:
        """解析存储字符串，返回 Gi"""
        if not storage_str or storage_str == '0':
            return 0.0
        try:
            if storage_str.endswith('Ki'):
                return float(storage_str[:-2]) / 1024 / 1024
            elif storage_str.endswith('Mi'):
                return float(storage_str[:-2]) / 1024
            elif storage_str.endswith('Gi'):
                return float(storage_str[:-2])
            elif storage_str.endswith('Ti'):
                return float(storage_str[:-2]) * 1024
            elif storage_str.endswith('K'):
                return float(storage_str[:-1]) / 1000 / 1024
            elif storage_str.endswith('M'):
                return float(storage_str[:-1]) / 1000
            elif storage_str.endswith('G'):
                return float(storage_str[:-1])
            else:
                return float(storage_str) / 1024 / 1024 / 1024
        except:
            return 0.0

    def get_all_namespace_quotas(self) -> List[NamespaceQuota]:
        """获取所有命名空间配额"""
        result = self._request('/api/v1/namespaces')
        if not result:
            return []
        
        quotas = []
        for ns in result.get('items', []):
            name = ns.get('metadata', {}).get('name', '')
            if not name or name.startswith('kube-'):
                continue
            
            labels = ns.get('metadata', {}).get('labels', {})
            project_name = labels.get('cpaas.io/project', '')
            
            quota_info = self.get_resource_quota_limits(name)
            if not quota_info:
                continue
            
            quotas.append(NamespaceQuota(
                cluster_name=self.cluster_name,
                namespace=name,
                project_name=project_name,
                cpu_limit=quota_info['cpu_limit'],
                memory_limit=quota_info['memory_limit'],
                cpu_used=quota_info['cpu_used'],
                memory_used=quota_info['memory_used'],
                pods_limit=quota_info['pods_limit'],
                pods_used=quota_info['pods_used'],
                storage_limit=quota_info['storage_limit'],
                storage_used=quota_info['storage_used'],
            ))
        
        return quotas

    def get_workload_replicas(self, namespace: str) -> Dict[str, int]:
        """获取 namespace 下所有 workload 的期望副本数"""
        replicas = {}
        
        try:
            result = self._request(f'/apis/apps/v1/namespaces/{namespace}/deployments')
            if result:
                for deploy in result.get('items', []):
                    name = deploy.get('metadata', {}).get('name', '')
                    spec_replicas = deploy.get('spec', {}).get('replicas', 0)
                    if name:
                        replicas[f'deploy/{name}'] = spec_replicas
        except:
            pass
        
        try:
            result = self._request(f'/apis/apps/v1/namespaces/{namespace}/statefulsets')
            if result:
                for ss in result.get('items', []):
                    name = ss.get('metadata', {}).get('name', '')
                    spec_replicas = ss.get('spec', {}).get('replicas', 0)
                    if name:
                        replicas[f'ss/{name}'] = spec_replicas
        except:
            pass
        
        return replicas

    def get_namespace_list(self) -> List[str]:
        """获取命名空间列表"""
        result = self._request('/api/v1/namespaces')
        if not result:
            return []
        
        namespaces = []
        for ns in result.get('items', []):
            name = ns.get('metadata', {}).get('name', '')
            if name and not name.startswith('kube-'):
                namespaces.append(name)
        
        return namespaces


def sync_k8s_quotas(kubeconfig: str, storage, use_projectquota: bool = True) -> SyncResult:
    client = K8sClient(kubeconfig)
    
    imported = 0
    updated = 0
    errors = []
    
    if use_projectquota:
        projectquotas = client.get_projectquotas()
        
        for pq in projectquotas:
            if not pq.get('cpu_quota') or not pq.get('memory_quota'):
                continue
                
            from app.models import Quota
            quota = Quota(
                cloud_id=pq.get('cloud_id', ''),
                project_name=pq.get('name', ''),
                cpu_quota=pq.get('cpu_quota', 0),
                memory_quota=pq.get('memory_quota', 0)
            )
            
            if quota.cloud_id:
                existing = storage.get_quota(quota.cloud_id)
                if existing:
                    storage.update_quota(quota.cloud_id, quota)
                    updated += 1
                else:
                    storage.add_quota(quota)
                    imported += 1
    else:
        namespaces = client.get_namespaces()

        for ns in namespaces:
            if not ns.cpu_quota or not ns.memory_quota:
                continue

            from app.models import Quota
            quota = Quota(
                cloud_id=f"k8s-{ns.name}",
                project_name=ns.name,
                cpu_quota=ns.cpu_quota,
                memory_quota=ns.memory_quota
            )

            existing = storage.get_quota(f"k8s-{ns.name}")
            if existing:
                storage.update_quota(f"k8s-{ns.name}", quota)
                updated += 1
            else:
                storage.add_quota(quota)
                imported += 1

    return SyncResult(
        success=True,
        imported=imported,
        updated=updated,
        errors=errors
    )


def sync_namespace_quota_from_k8s(kubeconfig: str, cluster_name: str, storage) -> SyncResult:
    """从 K8s 同步命名空间配额"""
    client = K8sClient(kubeconfig, cluster_name)
    
    imported = 0
    updated = 0
    errors = []
    
    quotas = client.get_all_namespace_quotas()
    
    for quota in quotas:
        key = f"{cluster_name}__{quota.namespace}"
        existing = storage.get_namespace_quota(cluster_name, quota.namespace)
        
        if existing:
            storage.save_namespace_quota(quota)
            updated += 1
        else:
            storage.save_namespace_quota(quota)
            imported += 1
    
    return SyncResult(
        success=True,
        imported=imported,
        updated=updated,
        errors=errors
    )


def refresh_namespace_quota_used(kubeconfig: str, cluster_name: str, storage) -> SyncResult:
    """刷新命名空间配额的 used 量"""
    client = K8sClient(kubeconfig, cluster_name)
    
    updated = 0
    errors = []
    
    all_quotas = storage.get_all_namespace_quotas()
    cluster_quotas = [q for q in all_quotas if q.cluster_name == cluster_name]
    
    for quota in cluster_quotas:
        quota_info = client.get_resource_quota_limits(quota.namespace)
        if quota_info:
            quota.cpu_used = quota_info['cpu_used']
            quota.memory_used = quota_info['memory_used']
            quota.pods_used = quota_info['pods_used']
            quota.storage_used = quota_info['storage_used']
            storage.save_namespace_quota(quota)
            updated += 1
    
    return SyncResult(
        success=True,
        imported=0,
        updated=updated,
        errors=errors
    )
