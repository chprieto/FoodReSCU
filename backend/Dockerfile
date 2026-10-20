# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install dependencies and code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app .

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]