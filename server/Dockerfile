FROM python:3.9-slim

WORKDIR /app

RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install --no-cache-dir -r requirements.txt

# Устанавливаем flatc (компилятор FlatBuffers).
RUN apt-get update && apt-get install -y flatbuffers-compiler

# Копируем схемы и компилируем их.
RUN mkdir ./proto/ ./flatbuffers_schema/
COPY proto/ ./proto/
COPY flatbuffers_schema/ ./flatbuffers_schema/
RUN python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/metrics.proto
RUN flatc --python flatbuffers_schema/metrics.fbs

COPY server/ .

RUN mkdir -p /app/results/logs

CMD ["python", "server.py"]
