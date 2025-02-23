import json

from metrics_pb2 import ServerMetrics, MetricsRequest
import flatbuffers
from flatbuffers_schema.MetricsRequest import MetricsRequestStart, MetricsRequestAddMetrics, MetricsRequestEnd, MetricsRequestStartMetricsVector
from flatbuffers_schema.ServerMetrics import ServerMetricsStart, ServerMetricsAddServerId, ServerMetricsAddCpuUsage, \
    ServerMetricsAddMemoryUsage, ServerMetricsAddDiskUsage, ServerMetricsAddTimestamp, ServerMetricsEnd


def serialize_json(metrics):
    return json.dumps(metrics)


def serialize_protobuf(metrics):
    request = MetricsRequest()  # Создаем пустой объект MetricsRequest, который будет содержать массив метрик.
    for m in metrics:
        metric = request.metrics.add()  # Добавляем новый объект ServerMetrics в список request.metrics. add() создает новый элемент и возвращает его для заполнения.
        metric.server_id = m["server_id"]
        metric.cpu_usage = m["cpu_usage"]
        metric.memory_usage = m["memory_usage"]
        metric.disk_usage = m["disk_usage"]
        metric.timestamp = m["timestamp"]
    return request


def serialize_flatbuffers(metrics):
    builder = flatbuffers.Builder(1024)  # Создаем объект Builder — инструмент для построения FlatBuffers-буфера. 1024 — начальный размер буфера в байтах, который будет увеличиваться при необходимости.
    metric_offsets = []
    for m in metrics:
        # Создаем строковый offset для server_id, записывая строку в буфер. CreateString возвращает смещение (offset) на начало строки в буфере.
        server_id = builder.CreateString(m["server_id"])
        timestamp = builder.CreateString(m["timestamp"])
        # Начинаем построение объекта ServerMetrics в буфере. ServerMetricsStart подготавливает таблицу для объекта ServerMetrics, выделяя место для указателей на поля.
        ServerMetricsStart(builder)
        # Добавляем server_id в таблицу ServerMetrics через его offset.
        ServerMetricsAddServerId(builder, server_id)
        # Добавляем cpu_usage как float напрямую (без offset, так как примитивный тип).
        ServerMetricsAddCpuUsage(builder, m["cpu_usage"])
        ServerMetricsAddMemoryUsage(builder, m["memory_usage"])
        ServerMetricsAddDiskUsage(builder, m["disk_usage"])
        ServerMetricsAddTimestamp(builder, timestamp)
        # Завершаем объект ServerMetrics и получаем его offset в буфере.
        metric_offsets.append(ServerMetricsEnd(builder))

    MetricsRequestStartMetricsVector(builder, len(metrics))  # Начинаем создание вектора (массива) metrics в MetricsRequest. Указываем количество элементов (len(metrics)), чтобы зарезервировать место.
    # Добавляем offsets объектов ServerMetrics в вектор в обратном порядке. PrependUOffsetTRelative добавляет смещение в начало вектора (FlatBuffers строит буфер с конца).
    for offset in reversed(metric_offsets):
        builder.PrependUOffsetTRelative(offset)
    metrics_array = builder.EndVector(len(metrics))  # Завершаем вектор и получаем его offset.

    MetricsRequestStart(builder)  # Начинаем построение корневого объекта MetricsRequest.
    MetricsRequestAddMetrics(builder, metrics_array)  # Добавляем вектор metrics в MetricsRequest через его offset.
    request = MetricsRequestEnd(builder)  # Завершаем MetricsRequest и получаем его offset.
    builder.Finish(request) # Завершаем весь буфер, указывая, что request — корневой объект.
    return builder.Output() # Получаем итоговую байтовую строку (буфер FlatBuffers) для передачи или сохранения.
