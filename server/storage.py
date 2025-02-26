import os
import json
import logging

import flatbuffers
from metrics_pb2 import MetricsRequest, ServerMetrics
from flatbuffers_schema.MetricsRequest import MetricsRequestStart, MetricsRequestAddMetrics, MetricsRequestEnd, \
    MetricsRequestStartMetricsVector
from flatbuffers_schema.ServerMetrics import ServerMetricsStart, ServerMetricsAddServerId, ServerMetricsAddCpuUsage, \
    ServerMetricsAddMemoryUsage, ServerMetricsAddDiskUsage, ServerMetricsAddTimestamp, ServerMetricsEnd

logger = logging.getLogger(__name__)


def save_metrics(metrics: list) -> None:
    """Save metrics in JSON, Protobuf, and FlatBuffers formats to files.

    Args:
        metrics: List of ServerMetrics objects to save.

    Raises:
        ValueError: If RESULTS_PATH environment variable is not set.
        OSError: If directory creation fails.
        Exception: If saving to any format (JSON, Protobuf, FlatBuffers) fails.

    """
    results_path = os.getenv("RESULTS_PATH")
    if not results_path:
        logger.error("RESULTS_PATH environment variable is not set.")
        raise ValueError("RESULTS_PATH is not defined.")

    try:
        os.makedirs(results_path, exist_ok=True)
    except OSError as e:
        logger.error("Failed to create directory %s: %s", results_path, e)
        raise

    if not metrics:
        logger.warning("No metrics to save.")
        return

    # JSON serialization
    json_data = [
        {"server_id": m.server_id, "cpu_usage": m.cpu_usage, "memory_usage": m.memory_usage, "disk_usage": m.disk_usage,
         "timestamp": m.timestamp} for m in metrics]
    try:
        with open(f"{results_path}/metrics.json", "w") as f_json:
            json.dump(json_data, f_json)
        logger.info("Saved %d metrics to %s/metrics.json", len(json_data), results_path)
    except Exception as e:
        logger.error("Failed to save JSON: %s", e)
        raise

    # Protobuf serialization
    try:
        request = MetricsRequest()
        request.metrics.extend(metrics)
        with open(f"{results_path}/metrics.proto.bin", "wb") as f_proto:
            f_proto.write(
                request.SerializeToString())  # Serialize to binary format (bytes). SerializeToString() converts the msg object into a byte sequence according to the Protobuf schema.
        logger.info("Saved %d metrics to %s/metrics.proto.bin", len(metrics), results_path)
    except Exception as e:
        logger.error("Failed to save Protobuf: %s", e)
        raise

    # FlatBuffers serialization
    try:
        builder = flatbuffers.Builder(
            1024)  # Create a Builder object — a tool for constructing a FlatBuffers buffer. 1024 is the initial buffer size in bytes, which will grow if needed.
        metric_offsets = []
        for m in metrics:
            # Create a string offset for server_id by writing the string into the buffer. CreateString returns the offset pointing to the beginning of the string in the buffer.
            server_id = builder.CreateString(m.server_id)
            timestamp = builder.CreateString(m.timestamp)
            # Start building the ServerMetrics object in the buffer. ServerMetricsStart prepares a table for the ServerMetrics object, allocating space for field pointers.
            ServerMetricsStart(builder)
            # Add server_id to the ServerMetrics table using its offset.
            ServerMetricsAddServerId(builder, server_id)
            # Add cpu_usage as a float directly (without an offset, since it's a primitive type).
            ServerMetricsAddCpuUsage(builder, m.cpu_usage)
            ServerMetricsAddMemoryUsage(builder, m.memory_usage)
            ServerMetricsAddDiskUsage(builder, m.disk_usage)
            ServerMetricsAddTimestamp(builder, timestamp)
            # Finalize the ServerMetrics object and get its offset in the buffer.
            metric_offsets.append(ServerMetricsEnd(builder))

        MetricsRequestStartMetricsVector(
            builder,
            len(metrics))  # Start creating the metrics vector (array) in MetricsRequest. Specify the number of elements (len(metrics)) to reserve space.
        # Add offsets of ServerMetrics objects to the vector in reverse order. PrependUOffsetTRelative adds offsets at the beginning of the vector (FlatBuffers builds the buffer from the end).
        for offset in reversed(metric_offsets):
            builder.PrependUOffsetTRelative(offset)
        metrics_array = builder.EndVector(len(metrics))  # Finalize the vector and get its offset.

        MetricsRequestStart(builder)  # Start building the root MetricsRequest object.
        MetricsRequestAddMetrics(builder, metrics_array)  # Add the metrics vector to MetricsRequest using its offset.
        request = MetricsRequestEnd(builder)  # Finalize MetricsRequest and get its offset.
        builder.Finish(request)  # Finalize the entire buffer, specifying that request is the root object.
        flat_data = builder.Output()  # Retrieve the final byte string (FlatBuffers buffer) for transmission or storage.

        with open(f"{results_path}/metrics.flatbuf", "wb") as f_flat:
            f_flat.write(flat_data)
        logger.info("Saved %d metrics to %s/metrics.flatbuf", len(metrics), results_path)
    except Exception as e:
        logger.error("Failed to save FlatBuffers: %s", e)
        raise
