import os
import json
import logging

import matplotlib.pyplot as plt

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(module)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/app/results/logs/analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_files_exist(base_path):
    required_files = ["metrics.json", "metrics.proto.bin", "serialize_times.json", "deserialize_times.json"]
    for f in required_files:
        if not os.path.exists(f"{base_path}/{f}"):
            logger.error(f"File {f} not found.")
            raise FileNotFoundError(f"Required files {f} are missing.")
    logger.info("All required files found.")
    return

def plot_results(sizes, serialize_times, deserialize_times):
    formats = ["JSON", "Protobuf", "FlatBuffers"]
    try:
        plt.bar(formats, sizes)  # Строим столбчатую диаграмму для сравнения размеров файлов.
        plt.title("File Size Comparison")  # Устанавливаем заголовок графика "File Size Comparison".
        plt.xlabel("Format")  # Подпись оси X.
        plt.ylabel("Size (bytes)")
        plt.savefig("/app/results/size_comparison.png")  # Сохраняем график в файл /app/results/size_comparison.png.
        plt.close()

        plt.figure(figsize=(10, 6))  # Устанавливаем размер 10x6 дюймов.
        plt.plot(formats, serialize_times, label="Serialization")  # Строим линейный график для сравнения времени сериализации. plt.plot рисует линию, соединяя точки (formats, serialize_times), label задает имя линии для легенды.
        plt.plot(formats, deserialize_times, label="Deserialization")
        plt.title("Performance Comparison")
        plt.legend()  # Добавляем легенду, чтобы показать, какая линия, что обозначает (Serialization или Deserialization).
        plt.savefig("/app/results/performance_comparison.png")
        plt.close()
        logger.info("Graphs generated successfully.")
    except Exception as e:
        logger.error(f"Failed to generate graphs: {e}")
        raise

def run():
    base_path = os.getenv("RESULTS_PATH")
    logger.info("Starting analysis.")

    try:
        check_files_exist(base_path)

        sizes = [
            os.path.getsize(f"{base_path}/metrics.json"),
            os.path.getsize(f"{base_path}/metrics.proto.bin"),
            os.path.getsize(f"{base_path}/metrics.flatbuf")
        ]

        with open(f"{base_path}/serialize_times.json", "r") as f_serialize_times:
            serialize_data = json.load(f_serialize_times)
        serialize_times = [
            serialize_data["json_ser_time"],
            serialize_data["proto_ser_time"],
            serialize_data["flat_ser_time"]
        ]

        with open(f"{base_path}/deserialize_times.json", "r") as f_deserialize_times:
            deserialize_data = json.load(f_deserialize_times)
        deserialize_times = [
            deserialize_data["json_deser_time"],
            deserialize_data["proto_deser_time"],
            deserialize_data["flat_deser_time"]
        ]

        plot_results(sizes, serialize_times, deserialize_times)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")

if __name__ == "__main__":
    run()
