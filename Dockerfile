# Full-stack production image: React UI + FastAPI + live AI pipeline (localhost parity)
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# Same-origin deploy — API calls use /api like localhost Vite proxy
RUN npm run build

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-production.txt .
RUN pip install --no-cache-dir -r requirements-production.txt \
    && python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

COPY . .
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN mkdir -p data/videos data/crops data/plates data/vehicle_crops data/frames data/demo static/crops

ENV SERVE_FRONTEND=true
ENV RENDER_DEMO_MODE=false
ENV ENABLE_LIVE_PIPELINE=true
ENV MAX_CONCURRENT_STREAMS=4
ENV PIPELINE_STARTUP_DELAY_SEC=8
ENV DATABASE_URL=sqlite+aiosqlite:///./data/sentinel.db

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
