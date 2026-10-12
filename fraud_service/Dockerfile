FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose default port (Railway overrides via $PORT at runtime)
EXPOSE 8006

# Command to run FastAPI with Uvicorn (uses Railway's dynamic $PORT, defaults to 8006 locally)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8006}"]