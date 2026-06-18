#!/bin/bash
# AegisOps Demo Deploy Script
# INTENTIONALLY VULNERABLE: Contains command injection flaw (CWE-78) for remediation tests.

ENV_NAME=$1

# VULNERABLE: Passing arguments directly to eval/command execution without check/sanitization
eval "echo 'Deploying application to environment: '$ENV_NAME"

# Secure alternative should sanitize parameters or reject special characters
# if [[ ! "$ENV_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
#   echo "Invalid environment name!"
#   exit 1
# fi
