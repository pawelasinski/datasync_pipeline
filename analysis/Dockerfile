FROM python:3.9-slim

WORKDIR /app

RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install --no-cache-dir -r requirements.txt

COPY analysis/ .

RUN mkdir -p /app/results/logs

CMD ["python", "analyze.py"]
