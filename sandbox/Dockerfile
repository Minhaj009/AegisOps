# AegisOps secure sandbox Dockerfile
FROM python:3.10-slim

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install testing frameworks and libraries
RUN pip install --no-cache-dir pytest pydantic

# Create non-root execution user 'aegisrun'
RUN groupadd -g 10001 aegisrun && \
    useradd -u 10001 -g aegisrun -m -s /bin/bash aegisrun

# Establish workspace directory and verify ownership permissions
WORKDIR /app
RUN mkdir -p /app && chown -R aegisrun:aegisrun /app

# Switch to non-privileged user to maintain strict containment boundaries
USER aegisrun

# Default entrypoint
CMD ["/bin/bash"]
