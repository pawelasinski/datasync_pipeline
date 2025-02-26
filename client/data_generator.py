import random
import datetime
from typing import Union


def generate_metrics(count: int) -> list[dict[str, Union[str, float]]]:
    """Generate a list of synthetic server metrics.

    Args:
        count: The number of metric entries to generate.

    Returns:
        A list of dictionaries, where each dictionary represents a metric
        with server ID, CPU usage, memory usage, disk usage, and timestamp.

    """
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
