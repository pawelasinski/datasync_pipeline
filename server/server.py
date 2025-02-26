import logging
import signal
from concurrent import futures  # For creating a thread pool used by the gRPC server.

import grpc

from metrics_pb2 import MetricsResponse, MetricsRequest
from metrics_pb2_grpc import MetricsServiceServicer, add_MetricsServiceServicer_to_server
from storage import save_metrics
from deserialize_perfomance import measure_deserialize_performance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(module)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/results/logs/server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Define the MetricsService class, inheriting from MetricsServiceServicer.
# This class implements the methods defined in the MetricsService service in metrics.proto.
class MetricsService(MetricsServiceServicer):
    """Implementation of the MetricsService gRPC service.

    This class defines the behavior of the SendMetrics RPC method as specified in metrics.proto.

    """

    def SendMetrics(
            self,
            request: MetricsRequest,
            context: grpc.ServicerContext
    ) -> MetricsResponse:
        """Process incoming metrics and save them, measuring deserialization performance.

        Args:
            request: A Protobuf MetricsRequest object containing an array of metrics.
            context: The gRPC context for managing the RPC call.

        Returns:
            A Protobuf response object with a success or error message.

        """
        logger.info("Received %d metrics.", len(request.metrics))
        try:
            save_metrics(request.metrics)
            measure_deserialize_performance(request.metrics)
            logger.info("Metrics processed successfully.")
            return MetricsResponse(message="Data received and processed.")
        except Exception as e:
            logger.error("Failed to process metrics: %s", e)
            context.set_code(
                grpc.StatusCode.INTERNAL)  # Set the gRPC error code as INTERNAL (equivalent to HTTP 500), indicating an internal server issue.
            context.set_details(
                str(e))  # Provide error details for the client (a string containing the exception description).
            return MetricsResponse(message="Error processing data.")


def serve() -> None:
    """Start and run the gRPC server to handle incoming metrics requests.

    Sets up a gRPC server on port 50051 with a thread pool, registers the MetricsService,
    and listens for incoming connections until interrupted (e.g., via SIGINT or SIGTERM).

    """
    logger.info("Starting gRPC server on port 50051.")
    server = grpc.server(futures.ThreadPoolExecutor(
        10))  # Create a gRPC server with a thread pool (maximum 10 threads for parallel request handling). If None, the server runs in single-threaded mode.
    logger.info("Server initialized: %s", server)

    add_MetricsServiceServicer_to_server(MetricsService(),
                                         server)  # Register the MetricsService implementation on the server.

    server.add_insecure_port(
        "[::]:50051")  # Bind the server to port 50051 using an insecure connection (no TLS/SSL). This is convenient for local development but not secure for production. "[::]" means the server listens on all available interfaces.
    # server.add_secure_port("[::]:50051", grpc.ssl_server_credentials([...]))  # Secure connection (TLS/SSL).
    # server.add_insecure_port("[::]:50052")  # Any other available port.
    # server.add_insecure_port("127.0.0.1:50051")  # Local connections only.
    # server.add_insecure_port("unix:/tmp/grpc.sock")  # Unix sockets (alternative to TCP connections).

    server.start()  # Start the server to accept requests.
    logger.info("Server started. Press Ctrl+C to stop.")

    server.wait_for_termination()  # Block program execution, waiting for the gRPC server to terminate (ensures the server keeps running until interrupted, e.g., with Ctrl+C). Without this, the server might exit immediately after starting.
    # server.wait_for_termination(timeout=60)  # If the server does not stop, execution will continue after 60 seconds of waiting. Useful for periodic server status checks or scenarios where the server should not run indefinitely.


if __name__ == "__main__":
    serve()
