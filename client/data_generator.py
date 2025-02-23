import random
import datetime


def generate_metrics(count):
    metrics = []
    for i in range(count):
        metric = {
            "server_id": f"srv{i}",
            "cpu_usage": random.uniform(0, 100),
            "memory_usage": random.uniform(0, 100),
            "disk_usage": random.uniform(0, 100),
            "timestamp": datetime.datetime.now().isoformat()
        }
        metrics.append(metric)
    return metrics
