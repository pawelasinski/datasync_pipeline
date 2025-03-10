import os
import json
import logging

import matplotlib.pyplot as plt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(module)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/results/logs/analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_files_exist(results_path: str) -> None:
    """Check if required result files exist in the specified directory.

    Args:
        results_path: The directory path where result files are located.

    Raises:
        FileNotFoundError: If any required file is missing.
    
    """
    required_files = [
        "metrics.json",
        "metrics.proto.bin",
        "serialize_times.json",
        "deserialize_times.json"
    ]
    for f in required_files:
        if not os.path.exists(f"{results_path}/{f}"):
            logger.error("File %s not found.", f)
            raise FileNotFoundError(f"Required files {f} are missing.")
    logger.info("All required files found.")
    return


def plot_results(
        sizes: list[int],
        serialize_times: list[int],
        deserialize_times: list[int]
) -> None:
    """Generate and save plots comparing file sizes and performance metrics.

    Args:
        sizes: List of file sizes in bytes for JSON, Protobuf, and FlatBuffers.
        serialize_times: List of serialization times for each format.
        deserialize_times: List of deserialization times for each format.

    Raises:
        Exception: If an error occurs during plot generation.

    """
    formats = ["JSON", "Protobuf", "FlatBuffers"]
    try:
        plt.bar(formats, sizes)  # Build a bar chart to compare file sizes.
        plt.title("File Size Comparison")  # Set the chart title to "File Size Comparison".
        plt.xlabel("Format")  # Label for the X-axis.
        plt.ylabel("Size (bytes)")
        plt.savefig("/app/results/size_comparison.png")  # Save the chart to /app/results/size_comparison.png.
        plt.close()

        plt.figure(figsize=(10, 6))  # Set the figure size to 10x6 inches.
        plt.plot(formats, serialize_times,
                 label="Serialization")  # Create a line plot to compare serialization times. `plt.plot` draws a line connecting points (formats, serialize_times), `label` specifies the name for the legend.
        plt.plot(formats, deserialize_times, label="Deserialization")
        plt.title("Performance Comparison")
        plt.legend()  # Add a legend to indicate which line represents serialization and deserialization.
        plt.savefig("/app/results/performance_comparison.png")
        plt.close()
        logger.info("Graphs generated successfully.")
    except Exception as e:
        logger.error("Failed to generate graphs: %s", e)
        raise


def run() -> None:
    """Run the analysis process to generate comparison plots.

    Raises:
        Exception: If an error occurs during the analysis process.
        
    """
    results_path = os.getenv("RESULTS_PATH")
    logger.info("Starting analysis.")

    try:
        check_files_exist(results_path)

        sizes = [
            os.path.getsize(f"{results_path}/metrics.json"),
            os.path.getsize(f"{results_path}/metrics.proto.bin"),
            os.path.getsize(f"{results_path}/metrics.flatbuf")
        ]

        with open(f"{results_path}/serialize_times.json", "r") as f_serialize_times:
            serialize_data = json.load(f_serialize_times)
        serialize_times = [
            serialize_data["json_ser_time"],
            serialize_data["proto_ser_time"],
            serialize_data["flat_ser_time"]
        ]

        with open(f"{results_path}/deserialize_times.json", "r") as f_deserialize_times:
            deserialize_data = json.load(f_deserialize_times)
        deserialize_times = [
            deserialize_data["json_deser_time"],
            deserialize_data["proto_deser_time"],
            deserialize_data["flat_deser_time"]
        ]

        plot_results(sizes, serialize_times, deserialize_times)
    except Exception as e:
        logger.error("Analysis failed: %s", e)


if __name__ == "__main__":
    run()
