import time
import logging
from datetime import datetime, timedelta
from threading import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, storage, report_cache):
        self.storage = storage
        self.report_cache = report_cache
        self.running = False
        self.thread = None

    def start(self):
        """启动定时任务"""
        if self.running:
            return
        self.running = True
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Scheduler started")

    def stop(self):
        """停止定时任务"""
        self.running = False
        logger.info("Scheduler stopped")

    def _run(self):
        """定时任务主循环"""
        while self.running:
            try:
                self._sync_namespace_quotas()
                self._sync_prometheus_usage()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            
            time.sleep(3600)

    def _sync_namespace_quotas(self):
        """每天同步命名空间配额"""
        now = datetime.now()
        if now.hour != 2:
            return
        
        logger.info("Running daily namespace quota sync...")
        
        from app.k8s_client import sync_namespace_quota_from_k8s
        
        configs = self.storage.get_all_k8s_configs()
        for config in configs:
            try:
                sync_namespace_quota_from_k8s(config.kubeconfig, config.name, self.storage)
                logger.info(f"Synced namespace quotas for cluster: {config.name}")
            except Exception as e:
                logger.error(f"Failed to sync namespace quotas for {config.name}: {e}")

    def _sync_prometheus_usage(self):
        """每天同步 Prometheus 使用量"""
        now = datetime.now()
        if now.hour != 3:
            return
        
        logger.info("Running daily Prometheus usage sync...")
        
        from app.prometheus_client import sync_prometheus_usage
        
        prom_configs = self.storage.get_all_prometheus_configs()
        if not prom_configs:
            return
        
        prom_url = prom_configs[0].url
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        try:
            sync_prometheus_usage(prom_url, yesterday, self.report_cache)
            logger.info(f"Synced Prometheus usage for {yesterday}")
        except Exception as e:
            logger.error(f"Failed to sync Prometheus usage: {e}")


scheduler = None


def init_scheduler(storage, report_cache):
    """初始化调度器"""
    global scheduler
    scheduler = Scheduler(storage, report_cache)
    return scheduler
