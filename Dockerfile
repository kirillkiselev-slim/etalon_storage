FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV REDIS_URL=redis://redis:6379
ENV PYTHONPATH="/app"

CMD ["python3", "app/main.py"]
