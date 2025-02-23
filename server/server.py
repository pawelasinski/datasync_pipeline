import logging
import signal
from concurrent import futures  # Для создания пула потоков, используемого gRPC-сервером.

import grpc

from metrics_pb2 import MetricsResponse
from metrics_pb2_grpc import MetricsServiceServicer, add_MetricsServiceServicer_to_server
from storage import save_metrics
from deserialize_perfomance import measure_deserialize_performance

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(module)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/app/results/logs/server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

server = None  # Глобальная переменная для gRPC-сервера.


# Устанавливаем обработчик сигналов.
def shutdown(signum, frame):
    global server
    if server:
        logger.info("Shutting down server...")
        server.stop(0)
        logger.info("Server stopped.")


# Определяем класс MetricsService, наследующийся от MetricsServiceServicer.
# Этот класс реализует методы, описанные в сервисе MetricsService в metrics.proto.
class MetricsService(MetricsServiceServicer):

    # Реализуем метод SendMetrics, объявленный как rpc SendMetrics в proto-файле.
    # request — это объект MetricsRequest с массивом метрик, context — контекст gRPC для управления вызовом.
    def SendMetrics(self, request, context):
        logger.info(f"Received {len(request.metrics)} metrics.")
        try:
            save_metrics(request.metrics)
            measure_deserialize_performance(request.metrics)
            logger.info("Metrics processed successfully.")
            return MetricsResponse(message="Data received and processed.")
        except Exception as e:
            logger.error(f"Failed to process metrics: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)  # Устанавливаем код ошибки gRPC как INTERNAL (500 в HTTP), сигнализируя о внутренней проблеме.
            context.set_details(str(e))  # Устанавливаем детали ошибки для клиента (строка с описанием исключения).
            return MetricsResponse(message="Error processing data.")


def serve():
    global server
    logger.info("Starting gRPC server on port 50051.")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))  # Создаем gRPC-сервер с пулом потоков (максимум 10 потоков для параллельной обработки запросов). Иначе None, и сервер будет работать в однопоточном режиме.

    add_MetricsServiceServicer_to_server(MetricsService(), server)  # Регистрируем реализацию сервиса MetricsService на сервере.

    server.add_insecure_port('[::]:50051')  # Привязываем сервер к порту 50051, используя небезопасное соединение (без TLS/SSL) (удобно для локальной разработки, но небезопасно для продакшена), '[::]' означает, что сервер слушает все доступные интерфейсы.
    # server.add_secure_port('[::]:50051', grpc.ssl_server_credentials([...])) # Безопасное соединение (TLS/SSL).
    # server.add_insecure_port('[::]:50052')  # Любой другой свободный порт.
    # server.add_insecure_port('127.0.0.1:50051')  # Только локальные соединения.
    # server.add_insecure_port('unix:/tmp/grpc.sock')  # Юникс-сокеты (альтернатива TCP-соединениям).

    # Устанавливаем обработчики сигналов для корректного завершения.
    signal.signal(signal.SIGINT, shutdown)  # Ctrl+C.
    signal.signal(signal.SIGTERM, shutdown)  # Завершение процесса.

    server.start()  # Запускаем сервер для приема запросов.

    logger.info("Server started. Press Ctrl+C to stop.")

    server.wait_for_termination()  # Блокируем выполнение программы, ожидая завершения работы gRPC-сервера (чтобы сервер продолжал работать до прерывания (например, Ctrl+C). Без него сервер может завершиться сразу после старта.
    # server.wait_for_termination(timeout=60)  # Если сервер не остановился, выполнение кода продолжится после 60 секунд ожидания. Если нужно периодически проверять состояние сервера и в сценариях, где сервер не должен работать бесконечно.


if __name__ == "__main__":
    serve()
