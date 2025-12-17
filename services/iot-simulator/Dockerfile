# Use a slim image to keep size down (Best Practice)
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first (Docker Layer Caching strategy)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ .

# Command to run the application
CMD ["python", "-u", "main.py"] 
# (-u forces unbuffered output so you see logs immediately)