import os
import json
import logging

import flatbuffers
from metrics_pb2 import MetricsRequest
from flatbuffers_schema.MetricsRequest import MetricsRequestStart, MetricsRequestAddMetrics, MetricsRequestEnd, MetricsRequestStartMetricsVector
from flatbuffers_schema.ServerMetrics import ServerMetricsStart, ServerMetricsAddServerId, ServerMetricsAddCpuUsage, \
    ServerMetricsAddMemoryUsage, ServerMetricsAddDiskUsage, ServerMetricsAddTimestamp, ServerMetricsEnd

logger = logging.getLogger(__name__)


def save_metrics(metrics):
    base_path = os.getenv("RESULTS_PATH")
    if not base_path:
        logger.error("RESULTS_PATH environment variable is not set.")
        raise ValueError("RESULTS_PATH is not defined.")

    try:
        os.makedirs(base_path, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create directory {base_path}: {e}")
        raise

    if not metrics:
        logger.warning("No metrics to save.")
        return

    json_data = [
        {"server_id": m.server_id, "cpu_usage": m.cpu_usage, "memory_usage": m.memory_usage, "disk_usage": m.disk_usage,
         "timestamp": m.timestamp} for m in metrics]
    try:
        with open(f"{base_path}/metrics.json", "w") as f_json:
            json.dump(json_data, f_json)
        logger.info(f"Saved {len(json_data)} metrics to {base_path}/metrics.json")
    except Exception as e:
        logger.error(f"Failed to save JSON: {e}")
        raise

    try:
        request = MetricsRequest()
        request.metrics.extend(metrics)
        with open(f"{base_path}/metrics.proto.bin", "wb") as f_proto:
            f_proto.write(request.SerializeToString())  # Сериализация в бинарный формат (bytes) (SerializeToString() преобразует объект msg в последовательность байтов согласно схеме Protobuf).
        logger.info(f"Saved {len(metrics)} metrics to {base_path}/metrics.proto.bin")
    except Exception as e:
        logger.error(f"Failed to save Protobuf: {e}")
        raise

    try:
        builder = flatbuffers.Builder(1024)  # Создаем объект Builder — инструмент для построения FlatBuffers-буфера. 1024 — начальный размер буфера в байтах, который будет увеличиваться при необходимости.
        metric_offsets = []
        for m in metrics:
            # Создаем строковый offset для server_id, записывая строку в буфер. CreateString возвращает смещение (offset) на начало строки в буфере.
            server_id = builder.CreateString(m.server_id)
            timestamp = builder.CreateString(m.timestamp)
            # Начинаем построение объекта ServerMetrics в буфере. ServerMetricsStart подготавливает таблицу для объекта ServerMetrics, выделяя место для указателей на поля.
            ServerMetricsStart(builder)
            # Добавляем server_id в таблицу ServerMetrics через его offset.
            ServerMetricsAddServerId(builder, server_id)
            # Добавляем cpu_usage как float напрямую (без offset, так как примитивный тип).
            ServerMetricsAddCpuUsage(builder, m.cpu_usage)
            ServerMetricsAddMemoryUsage(builder, m.memory_usage)
            ServerMetricsAddDiskUsage(builder, m.disk_usage)
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
        builder.Finish(request)  # Завершаем весь буфер, указывая, что request — корневой объект.
        flat_data = builder.Output()  # Получаем итоговую байтовую строку (буфер FlatBuffers) для передачи или сохранения.

        with open(f"{base_path}/metrics.flatbuf", "wb") as f_flat:
            f_flat.write(flat_data)
        logger.info(f"Saved {len(metrics)} metrics to {base_path}/metrics.flatbuf")
    except Exception as e:
        logger.error(f"Failed to save FlatBuffers: {e}")
        raise
