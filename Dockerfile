# Use an official lightweight Python base image
FROM python:3.10-slim

# Install system dependencies needed by PyMuPDF or others
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy code and models
COPY main.py ./
COPY heading_classifier.pkl ./
COPY helper/ ./helper  

# Ensure input/output folders exist in image (won’t override mounted volumes)
RUN mkdir -p /app/input /app/output

# Entrypoint
CMD ["python", "main.py"]
