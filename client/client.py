import os
import logging
import time
import json

import grpc

from metrics_pb2_grpc import MetricsServiceStub
from data_generator import generate_metrics
from serializers import serialize_json, serialize_protobuf, serialize_flatbuffers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(module)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/app/results/logs/client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_metrics(metrics):
    if not metrics or not isinstance(metrics, list):
        logger.error("Generated metrics are empty or invalid.")
        raise ValueError("Metrics must be a non-empty list.")
    for m in metrics:
        if not all(k in m for k in ["server_id", "cpu_usage", "memory_usage", "disk_usage", "timestamp"]):
            logger.error(f"Invalid metric format: {m}")
            raise ValueError("Metric missing required fields.")
    logger.info("Metrics validated successfully.")
    return


def run():
    server_host = os.getenv("SERVER_HOST")
    logger.info(f"Starting client, connecting to {server_host}:50051")

    # Генерация и проверка данных.
    try:
        metrics = generate_metrics(1000)
        check_metrics(metrics)
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return

    # Сериализация.
    try:
        start = time.time()
        json_data = serialize_json(metrics)
        json_ser_time = time.time() - start
        logger.info(f"JSON serialization took {json_ser_time:.4f}s")

        start = time.time()
        proto_data = serialize_protobuf(metrics)
        proto_ser_time = time.time() - start
        logger.info(f"Protobuf serialization took {proto_ser_time:.4f}s")

        start = time.time()
        flat_data = serialize_flatbuffers(metrics)
        flat_ser_time = time.time() - start
        logger.info(f"FlatBuffers serialization took {flat_ser_time:.4f}s")

        serialize_times = {
            "json_ser_time": json_ser_time,
            "proto_ser_time": proto_ser_time,
            "flat_ser_time": flat_ser_time
        }
        base_path = os.getenv("RESULTS_PATH")
        os.makedirs(base_path, exist_ok=True)
        try:
            with open(f"{base_path}/serialize_times.json", "w") as f_serialize_times:
                json.dump(serialize_times, f_serialize_times)
            logger.info("Serialization times saved to serialize_times.json")
        except Exception as e:
            logger.error(f"Failed to save serialization times: {e}")

    except Exception as e:
        logger.error(f"Serialization failed: {e}")
        return

    # Проверка доступности сервера и отправка.
    channel = grpc.insecure_channel(f"{server_host}:50051")
    try:
        grpc.channel_ready_future(channel).result(timeout=10)  # grpc.channel_ready_future возвращает объект Future, который завершается, когда канал готов. result(timeout=10) блокирует выполнение максимум на 10 секунд, ожидая готовности сервера.
        logger.info("gRPC server is ready.")  # Если сервер ответил в течение 10 секунд.
    except grpc.FutureTimeoutError:  # Если сервер не ответил за 10 секунд, возникает исключение FutureTimeoutError.
        logger.error("gRPC server is not responding.")
        return

    with channel:
        stub = MetricsServiceStub(channel)  # Создаем объект stub — клиентский интерфейс для вызова RPC-методов сервиса MetricsService. MetricsServiceStub сгенерирован из metrics.proto и привязан к каналу.
        try:
            response = stub.SendMetrics(proto_data)  # Возвращается объект MetricsResponse с полем message.
            logger.info(f"Server response: {response.message}")
        except grpc.RpcError as e:  # Обрабатываем возможные ошибки gRPC (например, сервер не отвечает или вернул ошибку).
            logger.error(f"gRPC call failed: {e}")
            return


if __name__ == "__main__":
    run()
