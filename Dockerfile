FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY websocket.py .
COPY templates/ templates/
EXPOSE 8765 5001
CMD ["python", "websocket.py"]