FROM python:3.9

# Set working directory
WORKDIR /app

# Copy FastAPI app files
COPY /app /app

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set the default FastAPI command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
