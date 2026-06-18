# AegisOps isolated security sandbox Dockerfile
FROM python:3.10-slim-bullseye

# System setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Establish security boundaries
# Create a non-privileged user 'sandbox_user'
RUN groupadd -g 10001 sandbox_group && \
    useradd -u 10001 -g sandbox_group -m -s /bin/bash sandbox_user

# Set up sandbox operational directory
WORKDIR /workspace
RUN chown -R sandbox_user:sandbox_group /workspace

# Run as non-root user for security isolation
USER sandbox_user

# Set default command to interactive shell or testing entrypoint
CMD ["/bin/bash"]
