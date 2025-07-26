"""
应用监控和指标收集
"""
import time
import psutil
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: float
    value: float
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, max_points: int = 1000):
        self.max_points = max_points
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        
    def record_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """记录计数器指标"""
        key = self._make_key(name, labels)
        self.counters[key] += value
        
    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """记录仪表盘指标"""
        key = self._make_key(name, labels)
        self.gauges[key] = value
        
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """记录直方图指标"""
        key = self._make_key(name, labels)
        point = MetricPoint(timestamp=time.time(), value=value, labels=labels or {})
        self.metrics[key].append(point)
        
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """生成指标键"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                name: {
                    "count": len(points),
                    "latest": points[-1].value if points else 0,
                    "avg": sum(p.value for p in points) / len(points) if points else 0,
                    "min": min(p.value for p in points) if points else 0,
                    "max": max(p.value for p in points) if points else 0,
                }
                for name, points in self.metrics.items()
            }
        }


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.start_time = time.time()
        
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录HTTP请求指标"""
        labels = {
            "method": method,
            "endpoint": endpoint,
            "status_code": str(status_code)
        }
        
        self.metrics.record_counter("http_requests_total", 1, labels)
        self.metrics.record_histogram("http_request_duration_seconds", duration, labels)
        
    def record_model_usage(self, provider: str, model: str, tokens: int, duration: float):
        """记录模型使用指标"""
        labels = {
            "provider": provider,
            "model": model
        }
        
        self.metrics.record_counter("model_requests_total", 1, labels)
        self.metrics.record_histogram("model_request_duration_seconds", duration, labels)
        self.metrics.record_histogram("model_tokens_used", tokens, labels)
        
    def record_error(self, error_type: str, component: str):
        """记录错误指标"""
        labels = {
            "error_type": error_type,
            "component": component
        }
        
        self.metrics.record_counter("errors_total", 1, labels)
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics.record_gauge("system_cpu_usage_percent", cpu_percent)
        
        # 内存使用
        memory = psutil.virtual_memory()
        self.metrics.record_gauge("system_memory_usage_percent", memory.percent)
        self.metrics.record_gauge("system_memory_used_bytes", memory.used)
        self.metrics.record_gauge("system_memory_available_bytes", memory.available)
        
        # 磁盘使用
        disk = psutil.disk_usage('/')
        self.metrics.record_gauge("system_disk_usage_percent", (disk.used / disk.total) * 100)
        self.metrics.record_gauge("system_disk_used_bytes", disk.used)
        self.metrics.record_gauge("system_disk_free_bytes", disk.free)
        
        # 应用运行时间
        uptime = time.time() - self.start_time
        self.metrics.record_gauge("app_uptime_seconds", uptime)
        
        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "percent": memory.percent,
                "used": memory.used,
                "available": memory.available,
                "total": memory.total
            },
            "disk": {
                "percent": (disk.used / disk.total) * 100,
                "used": disk.used,
                "free": disk.free,
                "total": disk.total
            },
            "uptime": uptime
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        system_metrics = self.get_system_metrics()
        
        # 健康检查阈值
        cpu_threshold = 80.0
        memory_threshold = 85.0
        disk_threshold = 90.0
        
        health_checks = {
            "cpu": {
                "status": "healthy" if system_metrics["cpu_percent"] < cpu_threshold else "warning",
                "value": system_metrics["cpu_percent"],
                "threshold": cpu_threshold
            },
            "memory": {
                "status": "healthy" if system_metrics["memory"]["percent"] < memory_threshold else "warning",
                "value": system_metrics["memory"]["percent"],
                "threshold": memory_threshold
            },
            "disk": {
                "status": "healthy" if system_metrics["disk"]["percent"] < disk_threshold else "warning",
                "value": system_metrics["disk"]["percent"],
                "threshold": disk_threshold
            }
        }
        
        # 整体健康状态
        overall_status = "healthy"
        if any(check["status"] == "warning" for check in health_checks.values()):
            overall_status = "warning"
        
        return {
            "status": overall_status,
            "checks": health_checks,
            "uptime": system_metrics["uptime"],
            "timestamp": time.time()
        }
    
    def export_metrics(self) -> Dict[str, Any]:
        """导出所有指标"""
        return {
            "metrics": self.metrics.get_metrics_summary(),
            "system": self.get_system_metrics(),
            "health": self.get_health_status(),
            "timestamp": time.time()
        }


# 全局监控实例
monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """获取监控实例"""
    return monitor