FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY poller.py .
COPY venus_api.py .

# Create logs directory
RUN mkdir -p /app/logs

# Run poller
CMD ["python", "-u", "poller.py"]
