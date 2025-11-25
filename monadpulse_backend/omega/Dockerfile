FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Omega Engine code
COPY . .

# Expose API port
EXPOSE 8001

# Run Omega Engine directly
CMD ["python", "main.py"]
