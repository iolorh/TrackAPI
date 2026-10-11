FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "main:app", "--workers", "2", "--worker-class", "uvicorn_worker.UvicornWorker", "--bind", "0.0.0.0:8000"]