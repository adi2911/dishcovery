FROM python:3.11-slim

# Set working directory
WORKDIR /backend

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential gcc curl && \
    rm -rf /var/lib/apt/lists/*

# Install Google Cloud SDK (for gsutil)
RUN curl https://sdk.cloud.google.com | bash > /dev/null && \
    export PATH=$PATH:/root/google-cloud-sdk/bin && \
    gcloud components install gsutil

# Make gsutil available in the running container
ENV PATH="/root/google-cloud-sdk/bin:${PATH}"

# Copy dependencies and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure the data directory exists
RUN mkdir -p /backend/src/data/index_data_dishcovery

# Copy the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set environment variables
ENV PYTHONPATH="."
ENV FLASK_APP=src/app.py
EXPOSE 8080

# Run the entrypoint script
CMD ["/entrypoint.sh"]
