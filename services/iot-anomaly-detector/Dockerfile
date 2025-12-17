# We need a slightly bigger image for Scikit-Learn
FROM python:3.9-slim

WORKDIR /app

# Install build tools for numpy/scikit (sometimes needed on slim images)
RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

# We run with -u for unbuffered logs
CMD ["python", "-u", "main.py"]