FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000 5514/udp 5514/tcp

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
