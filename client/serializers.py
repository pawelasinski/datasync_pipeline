import json

from metrics_pb2 import ServerMetrics, MetricsRequest
import flatbuffers
from flatbuffers_schema.MetricsRequest import MetricsRequestStart, MetricsRequestAddMetrics, MetricsRequestEnd, \
    MetricsRequestStartMetricsVector
from flatbuffers_schema.ServerMetrics import ServerMetricsStart, ServerMetricsAddServerId, ServerMetricsAddCpuUsage, \
    ServerMetricsAddMemoryUsage, ServerMetricsAddDiskUsage, ServerMetricsAddTimestamp, ServerMetricsEnd


def serialize_json(metrics):
    return json.dumps(metrics)


def serialize_protobuf(metrics):
    request = MetricsRequest()  # Create an empty MetricsRequest object that will contain an array of metrics.
    for m in metrics:
        metric = request.metrics.add()  # Add a new ServerMetrics object to the request.metrics list. `add()` creates a new element and returns it for further filling.
        metric.server_id = m["server_id"]
        metric.cpu_usage = m["cpu_usage"]
        metric.memory_usage = m["memory_usage"]
        metric.disk_usage = m["disk_usage"]
        metric.timestamp = m["timestamp"]
    return request


def serialize_flatbuffers(metrics):
    builder = flatbuffers.Builder(
        1024)  # Create a Builder object — a tool for constructing a FlatBuffers buffer. 1024 is the initial buffer size in bytes, which will grow if needed.
    metric_offsets = []
    for m in metrics:
        # Create a string offset for server_id by writing the string into the buffer. CreateString returns the offset pointing to the beginning of the string in the buffer.
        server_id = builder.CreateString(m["server_id"])
        timestamp = builder.CreateString(m["timestamp"])
        # Start building the ServerMetrics object in the buffer. ServerMetricsStart prepares a table for the ServerMetrics object, allocating space for field pointers.
        ServerMetricsStart(builder)
        # Add server_id to the ServerMetrics table using its offset.
        ServerMetricsAddServerId(builder, server_id)
        # Add cpu_usage as a float directly (without an offset, since it's a primitive type).
        ServerMetricsAddCpuUsage(builder, m["cpu_usage"])
        ServerMetricsAddMemoryUsage(builder, m["memory_usage"])
        ServerMetricsAddDiskUsage(builder, m["disk_usage"])
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
    return builder.Output()  # Retrieve the final byte string (FlatBuffers buffer) for transmission or storage.
