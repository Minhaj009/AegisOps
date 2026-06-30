#!/bin/bash
# AegisOps Build & Push Script for Alibaba Cloud Container Registry (ACR)

set -e

# Configuration (Edit these or pass as environment variables)
REGION=${ALICLOUD_REGION:-"ap-southeast-1"} # Default to Singapore
NAMESPACE=${ACR_NAMESPACE:-"aegisops-registry"}
IMAGE_NAME="aegisops-sandbox"
TAG="latest"

REGISTRY="registry.${REGION}.aliyuncs.com"
FULL_IMAGE_PATH="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${TAG}"

echo "=== AegisOps ACR Deployment ==="
echo "Target Registry: ${REGISTRY}"
echo "Namespace: ${NAMESPACE}"
echo "Full Target Path: ${FULL_IMAGE_PATH}"
echo "==============================="

# Verify Docker daemon is running locally
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running or accessible. Please start Docker first."
    exit 1
fi

# Step 1: Login to Alibaba Cloud CR
echo "Step 1: Logging in to Alibaba Cloud Container Registry..."
echo "Please enter your Alibaba Cloud Container Registry login credentials."
docker login --username="" "${REGISTRY}"

# Step 2: Build the Dockerfile
echo "Step 2: Compiling secure sandbox Docker image..."
# Run build command targeting our sandbox directory
docker build -t "${IMAGE_NAME}:local" -f ../sandbox/Dockerfile ../sandbox/

# Step 3: Tag for ACR
echo "Step 3: Tagging local image for remote registry..."
docker tag "${IMAGE_NAME}:local" "${FULL_IMAGE_PATH}"

# Step 4: Push to registry
echo "Step 4: Pushing sandbox image to Alibaba Cloud Container Registry..."
docker push "${FULL_IMAGE_PATH}"

echo "=== Push to ACR Completed Successfully! ==="
echo "Image URL: ${FULL_IMAGE_PATH}"
