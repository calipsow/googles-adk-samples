#!/bin/bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# --- COMMON CONFIGURATION ---

# Get the directory where the script is located
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Source the .env file located one level up
if [ -f "$SCRIPT_DIR/../.env" ]; then
    source "$SCRIPT_DIR/../.env"
else
    echo "Error: .env file not found at $SCRIPT_DIR/../.env"
    exit 1
fi

# -- Project and App Details --
export PROJECT_ID
export PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
export LOCATION="${GOOGLE_CLOUD_LOCATION}"
export STAGING_BUCKET="gs://${STAGING_BUCKET}"
export GEMINI_ENTERPRISE_APP_ID="${PROJECT_ID}-ge"
export REASONING_ENGINE_LOCATION="${LOCATION}"
export GCS_BUCKET_NAME
export MODEL_NAME
export GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT

# -- Agent Details --
export AGENT_DISPLAY_NAME="Brand Aligner Agent"
export AGENT_DESCRIPTION="Searches for and evaluates visual assets (images/videos) against brand guidelines to ensure compliance and stylistic alignment."
export AGENT_TOOL_DESCRIPTION="Use whenever a user uploads files or asks to check visual assets against brand guidelines, including scenarios where the user needs to search for or retrieve existing assets and guidelines from their workspace to perform the evaluation."

# -- For a fresh deployment to Agent Engine, leave the REASONING_ENGINE_ID empty, otherwise use the ID of the last deployment from .agent_engine_resource.json. --
export REASONING_ENGINE_ID=""

# -- Agent Engine Details --
export ADK_DEPLOYMENT_ID="projects/${PROJECT_NUMBER}/locations/${REASONING_ENGINE_LOCATION}/reasoningEngines/${REASONING_ENGINE_ID}"

# -- Gemini Enterprise Authorization Details (Optional: only if your agent needs OAuth 2.0) --
# -- Leave any of OAUTH_CLIENT_ID or OAUTH_CLIENT_SECRET in .env empty to skip authorization resource creation --
export AUTH_ID
export OAUTH_CLIENT_ID
export OAUTH_CLIENT_SECRET
export OAUTH_TOKEN_URI
export OAUTH_AUTH_URI_BASE
export OAUTH_AUTH_URI
