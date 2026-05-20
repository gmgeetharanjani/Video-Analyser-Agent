# Sample Agent Dockerfile

FROM docker-hub.common.cdn.repositories.cloud.sap/python:3.13

# Artifactory credentials as build arguments
ARG ARTIFACTORY_USER
ARG ARTIFACTORY_TOKEN

# Artifactory configuration
ENV ARTIFACTORY_URL="https://common.repositories.cloud.sap/artifactory/api/pypi/application-foundation-sdk-python"
ENV ARTIFACTORY_USER=${ARTIFACTORY_USER}
ENV ARTIFACTORY_TOKEN=${ARTIFACTORY_TOKEN}

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install git (required for some dependencies), curl (for health checks), and Python dependencies
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    mkdir -p /root/.pip && \
    printf "[global]\n\
index-url = https://%s:%s@common.repositories.cloud.sap/artifactory/api/pypi/application-foundation-sdk-python/simple\n\
extra-index-url = https://pypi.org/simple\n" \
    "$ARTIFACTORY_USER" "$ARTIFACTORY_TOKEN" > /root/.pip/pip.conf && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.pip

# Copy the application code
COPY app/ ./app/

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose the port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/.well-known/agent.json || exit 1

# Run the application
CMD ["python", "app/main.py", "--host", "0.0.0.0", "--port", "5000"]