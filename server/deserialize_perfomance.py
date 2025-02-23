import time
import os
import json
import logging

from metrics_pb2 import MetricsRequest as ProtoMetricsRequest
from flatbuffers_schema.MetricsRequest import MetricsRequest as FlatMetricsRequest

logger = logging.getLogger(__name__)


def measure_deserialize_performance(metrics):
    base_path = os.getenv("RESULTS_PATH")

    json_path = f"{base_path}/metrics.json"
    proto_path = f"{base_path}/metrics.proto.bin"
    flat_path = f"{base_path}/metrics.flatbuf"
    if not (os.path.exists(json_path) and os.path.exists(proto_path) and os.path.exists(flat_path)):
        logger.error("Metrics files not found for performance measurement.")
        return

    # Замеряем время десериализации JSON.
    start_time = time.time()
    with open(json_path, "r") as f_json:
        json_data = json.load(f_json)
    json_deser_time = time.time() - start_time
    json_size = os.path.getsize(json_path)
    logger.info(f"JSON deserialization took {json_deser_time:.4f} seconds, size: {json_size} bytes.")

    # Замеряем время десериализации Protobuf.
    start_time = time.time()
    proto_data = ProtoMetricsRequest()  # Создаем пустой объект MetricsRequest для десериализации.
    with open(proto_path, "rb") as f_proto:
        proto_data.ParseFromString(f_proto.read())
    proto_deser_time = time.time() - start_time
    proto_size = os.path.getsize(proto_path)
    logger.info(f"Protobuf deserialization took {proto_deser_time:.4f} seconds, size: {proto_size} bytes.")

    # Замеряем время десериализации FlatBuffers.
    start_time = time.time()
    with open(f"{base_path}/metrics.flatbuf", "rb") as f_flat:
        flat_data = FlatMetricsRequest.GetRootAsMetricsRequest(f_flat.read(), 0)
    flat_deser_time = time.time() - start_time
    flat_size = os.path.getsize(proto_path)
    logger.info(f"FlatBuffers deserialization took {flat_deser_time:.4f} seconds, size: {flat_size} bytes.")

    deserialize_times = {"json_deser_time": json_deser_time,
                         "proto_deser_time": proto_deser_time,
                         "flat_deser_time": flat_deser_time}
    with open(f"{base_path}/deserialize_times.json", "w") as f_deserialize_times:
        json.dump(deserialize_times, f_deserialize_times)

    logger.info(f"Processed {len(metrics)} metrics in performance measurement.")
