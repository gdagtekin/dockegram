FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ENABLE_MONITORING=False
ENV MONITORING_INTERVAL=300

CMD ["python", "dockegram.py"]