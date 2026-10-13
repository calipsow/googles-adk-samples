#!/bin/bash

# Determine project root (directory where this script's parent is, if script is in deployment/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
REGION="us-central1"
DISPLAY_NAME="Global KYC Agent"
PROJECT_ID=""
ENV_FILE=""

# Function to show usage
usage() {
    echo "Usage: $0 --project PROJECT_ID [options]"
    echo "Options:"
    echo "  -p, --project PROJECT_ID    Google Cloud Project ID (Required)"
    echo "  -r, --region REGION          Google Cloud Region (Default: us-central1)"
    echo "  -n, --name NAME              Display name for the agent (Default: Global KYC Agent)"
    echo "  -e, --env-file FILE          Path to .env file"
    echo "  -h, --help                   Show this help message"
    exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -p|--project) PROJECT_ID="$2"; shift ;;
        -r|--region) REGION="$2"; shift ;;
        -n|--name) DISPLAY_NAME="$2"; shift ;;
        -e|--env-file) ENV_FILE="$2"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter: $1"; usage ;;
    esac
    shift
done

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Project ID is required."
    usage
fi

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Determine ADK command
ADK_CMD="adk"
if [ -f ".venv/bin/adk" ]; then
    ADK_CMD=".venv/bin/adk"
fi

echo "Deploying Global KYC Agent to Project: $PROJECT_ID in Region: $REGION"

# Build command array
DEPLOY_CMD=("$ADK_CMD" "deploy" "agent_engine" "global_kyc_agent" \
    "--project" "$PROJECT_ID" \
    "--region" "$REGION" \
    "--display_name" "$DISPLAY_NAME")

if [ -n "$ENV_FILE" ]; then
    DEPLOY_CMD+=("--env_file" "$ENV_FILE")
fi

# Run command
"${DEPLOY_CMD[@]}"
