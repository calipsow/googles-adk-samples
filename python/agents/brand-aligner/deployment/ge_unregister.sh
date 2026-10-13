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

source "$(dirname "${BASH_SOURCE[0]}")/config.sh"

echo "--- Unregistering all agents with display name: ${AGENT_DISPLAY_NAME} ... ---"

# --- List All Agents in the App and Delete Matching ---

echo "--- Listing all agents in App ID: ${GEMINI_ENTERPRISE_APP_ID}... ---"

AGENTS_JSON=$(curl -s -X GET \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: ${PROJECT_ID}" \
"https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${GEMINI_ENTERPRISE_APP_ID}/assistants/default_assistant/agents")

echo "--- Unregistering all agents with display name: ${AGENT_DISPLAY_NAME}... ---"

echo "${AGENTS_JSON}" | jq -r --arg ADN "${AGENT_DISPLAY_NAME}" '.agents[] | select(.displayName == $ADN) | .name' |

while IFS= read -r AGENT_RESOURCE_NAME; do
  if [ -z "$AGENT_RESOURCE_NAME" ]; then
    echo "No agent found with display name: ${AGENT_DISPLAY_NAME}"
    continue
  fi

  echo "--- Unregistering Agent: ${AGENT_RESOURCE_NAME}... ---"

  curl -s -X DELETE \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://discoveryengine.googleapis.com/v1alpha/${AGENT_RESOURCE_NAME}"
  echo "\nAgent ${AGENT_RESOURCE_NAME} unregistered."

done
