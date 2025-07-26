# Multi-stage build for Socially application

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ .

# Build the frontend
RUN npm run build

# Stage 2: Final backend image with frontend static files
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    libsndfile1-dev \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend static files
COPY --from=frontend-builder /app/frontend/dist ./backend/fe/dist

# Create directory for models (if needed)
RUN mkdir -p /app/backend/models/emotion

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
