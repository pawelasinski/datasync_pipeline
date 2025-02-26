import os
import logging
import time
import json
from typing import Union

import grpc

from metrics_pb2_grpc import MetricsServiceStub
from data_generator import generate_metrics
from serializers import serialize_json, serialize_protobuf, serialize_flatbuffers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(module)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/results/logs/client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_metrics(metrics: list[dict[str, Union[str, float]]]) -> None:
    """Validate the structure and content of generated metrics.

    Args:
        metrics: List of metrics to validate.

    Raises:
        ValueError: If metrics are empty, not a list, or missing required fields.

    """
    if not metrics or not isinstance(metrics, list):
        logger.error("Generated metrics are empty or invalid.")
        raise ValueError("Metrics must be a non-empty list.")
    for m in metrics:
        if not all(k in m for k in ["server_id", "cpu_usage", "memory_usage", "disk_usage", "timestamp"]):
            logger.error("Invalid metric format: %s", m)
            raise ValueError("Metric missing required fields.")
    logger.info("Metrics validated successfully.")
    return


def run() -> None:
    """Execute the client process: generate metrics, serialize them, and send to the gRPC server.

    This function handles metric generation, serialization timing, saving results, and communication
    with a gRPC server.

    Raises:
        Exception: If any step (metric generation, serialization, or gRPC communication) fails.

    """
    server_host = os.getenv("SERVER_HOST")
    logger.info("Starting client, connecting to %s:50051", server_host)

    # Data generation and validation.
    try:
        metrics = generate_metrics(1000)
        check_metrics(metrics)
    except Exception as e:
        logger.error("Failed to generate metrics: %s", e)
        return

    # Serialization
    try:
        start = time.time()
        json_data = serialize_json(metrics)
        json_ser_time = time.time() - start
        logger.info("JSON serialization took %.4f seconds.", json_ser_time)

        start = time.time()
        proto_data = serialize_protobuf(metrics)
        proto_ser_time = time.time() - start
        logger.info("Protobuf serialization took %.4f seconds.", proto_ser_time)

        start = time.time()
        flat_data = serialize_flatbuffers(metrics)
        flat_ser_time = time.time() - start
        logger.info("FlatBuffers serialization took %.4f seconds.", flat_ser_time)

        serialize_times = {
            "json_ser_time": json_ser_time,
            "proto_ser_time": proto_ser_time,
            "flat_ser_time": flat_ser_time
        }

        results_path = os.getenv("RESULTS_PATH")
        os.makedirs(results_path, exist_ok=True)
        try:
            with open(f"{results_path}/serialize_times.json", "w") as f_serialize_times:
                json.dump(serialize_times, f_serialize_times)
            logger.info("Serialization times saved to serialize_times.json")
        except Exception as e:
            logger.error("Failed to save serialization times: %s", e)
    except Exception as e:
        logger.error("Serialization failed: %s", e)
        return

    # Server availability check and data transmission.
    channel = grpc.insecure_channel(f"{server_host}:50051")
    try:
        grpc.channel_ready_future(channel).result(
            timeout=10)  # `grpc.channel_ready_future` returns a Future object that completes when the channel is ready. `result(timeout=10)` blocks execution for up to 10 seconds, waiting for the server to be ready.
        logger.info("gRPC server is ready.")  # If the server responds within 10 seconds.
    except grpc.FutureTimeoutError:  # If the server does not respond within 10 seconds, a FutureTimeoutError exception is raised.
        logger.error("gRPC server is not responding.")
        return

    with channel:
        stub = MetricsServiceStub(
            channel)  # Create a stub object — a client interface for calling RPC methods of the MetricsService. MetricsServiceStub is generated from metrics.proto and bound to the channel.
        try:
            response = stub.SendMetrics(proto_data)  # Returns a MetricsResponse object with a message field.
            logger.info("Server response: %s", response.message)
        except grpc.RpcError as e:  # Handle possible gRPC errors (e.g., server not responding or returning an error).
            logger.error("gRPC call failed: %s", e)
            return


if __name__ == "__main__":
    run()
