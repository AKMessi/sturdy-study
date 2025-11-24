# Use Python 3.11 Slim (Smaller base image)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# We add build-essential to help compile some python packages if needed
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first.
# This creates a "cached layer" with the small version.
# When the next step runs, it sees PyTorch is already installed and skips the 2GB download.
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install the rest
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose the port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]