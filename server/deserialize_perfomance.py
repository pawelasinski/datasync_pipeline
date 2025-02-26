import time
import os
import json
import logging

from metrics_pb2 import MetricsRequest as ProtoMetricsRequest
from flatbuffers_schema.MetricsRequest import MetricsRequest as FlatMetricsRequest

logger = logging.getLogger(__name__)


def measure_deserialize_performance(metrics: list) -> None:
    """Measure and log the deserialization performance of metrics in JSON, Protobuf, and FlatBuffers formats.

    This function reads serialized metrics from files, measures the time taken to deserialize them,
    logs the results, and saves the deserialization times to a JSON file.

    Args:
        metrics: List of metrics (used only for logging the count; format not enforced here).

    """
    results_path = os.getenv("RESULTS_PATH")

    json_path = f"{results_path}/metrics.json"
    proto_path = f"{results_path}/metrics.proto.bin"
    flat_path = f"{results_path}/metrics.flatbuf"
    if not (os.path.exists(json_path) and os.path.exists(proto_path) and os.path.exists(flat_path)):
        logger.error("Metrics files not found for performance measurement.")
        return

    # Measure JSON deserialization time.
    start_time = time.time()
    with open(json_path, "r") as f_json:
        json_data = json.load(f_json)
    json_deser_time = time.time() - start_time
    json_size = os.path.getsize(json_path)
    logger.info("JSON deserialization took %.4f seconds, size: %d bytes.", json_deser_time, json_size)

    # Measure Protobuf deserialization time.
    start_time = time.time()
    proto_data = ProtoMetricsRequest()  # Create an empty MetricsRequest object for deserialization.
    with open(proto_path, "rb") as f_proto:
        proto_data.ParseFromString(f_proto.read())
    proto_deser_time = time.time() - start_time
    proto_size = os.path.getsize(proto_path)
    logger.info("Protobuf deserialization took %.4f seconds, size: %d bytes.", proto_deser_time, proto_size)

    # Measure FlatBuffers deserialization time.
    start_time = time.time()
    with open(f"{results_path}/metrics.flatbuf", "rb") as f_flat:
        flat_data = FlatMetricsRequest.GetRootAsMetricsRequest(f_flat.read(), 0)
    flat_deser_time = time.time() - start_time
    flat_size = os.path.getsize(proto_path)
    logger.info("FlatBuffers deserialization took %.4f seconds, size: %d bytes.", flat_deser_time, flat_size)

    deserialize_times = {
        "json_deser_time": json_deser_time,
        "proto_deser_time": proto_deser_time,
        "flat_deser_time": flat_deser_time
    }

    with open(f"{results_path}/deserialize_times.json", "w") as f_deserialize_times:
        json.dump(deserialize_times, f_deserialize_times)

    logger.info("Processed %d metrics in performance measurement.", len(metrics))
