FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY docs ./docs
COPY templates ./templates
COPY .env.example ./.env.example

CMD ["python", "-m", "backend.main", "--help"]
