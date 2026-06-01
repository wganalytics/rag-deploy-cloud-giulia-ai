# Base image
FROM python:3.12-slim

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements from root (passed during build)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy common lib
COPY INFRA/lib /app/INFRA/lib

# Expose ports (FastAPI 8000, Streamlit 8501)
EXPOSE 8000
EXPOSE 8501

# Entry point will be defined in docker-compose per project
CMD ["bash"]
