FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV DOCKER_CONTAINER=true
CMD ["python", "-u", "app.py"]
