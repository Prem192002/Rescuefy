# Use the official Python 3.10 image from Docker Hub
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install system dependencies and Python dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files to the container
COPY . .

# Expose the port your Flask app runs on (default 5000)
EXPOSE 5000

# Command to run your application
CMD ["python3", "app.py"]
