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

# Also see https://clouddocs.devsite.corp.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent

source "$(dirname "${BASH_SOURCE[0]}")/config.sh"

echo "--- PART 2: REGISTERING WITH GEMINI ENTERPRISE ---"

# --- STEP 1: PREREQUISITES - ENABLING APIS & SETTING PERMISSIONS ---

echo "--- Enabling necessary Google Cloud APIs... ---"
gcloud services enable --project="${PROJECT_ID}" \
  discoveryengine.googleapis.com \
  aiplatform.googleapis.com
echo "APIs enabled."

echo "--- Granting IAM Roles to Discovery and Reasoning Engine Service Accounts... ---"
DISCOVERY_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
REASONING_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
AI_PLATFORM_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform.iam.gserviceaccount.com"

SA_ARR=(${DISCOVERY_ENGINE_SA} ${REASONING_ENGINE_SA} ${AI_PLATFORM_SA})
for SA in "${SA_ARR[@]}"; do
    echo "Granting Vertex AI User role to ${SA}..."
    gcloud --no-user-output-enabled projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SA}" \
        --role="roles/aiplatform.user" \
        --condition="None"

    echo "Granting Storage Object User role to ${SA}..."
    gcloud --no-user-output-enabled projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SA}" \
        --role="roles/storage.objectUser" \
        --condition="None"
done
echo "IAM roles granted successfully."

# --- STEP 2: AUTHORIZE YOUR AGENT (OPTIONAL) ---
# This step creates an authorization resource in Gemini Enterprise if your agent needs OAuth 2.0

echo "--- Registering OAuth 2.0 Authorization Resource (Optional)... ---"
if [[ -n "${OAUTH_CLIENT_ID}" && -n "${OAUTH_CLIENT_SECRET}" ]]; then
    curl -X POST \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json" \
    -H "X-Goog-User-Project: ${PROJECT_ID}" \
    "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_NUMBER}/locations/global/authorizations?authorizationId=${AUTH_ID}" \
    -d @- << EOF
{
  "name": "projects/${PROJECT_NUMBER}/locations/global/authorizations/${AUTH_ID}",
  "serverSideOauth2": {
    "clientId": "${OAUTH_CLIENT_ID}",
    "clientSecret": "${OAUTH_CLIENT_SECRET}",
    "authorizationUri": "${OAUTH_AUTH_URI}",
    "tokenUri": "${OAUTH_TOKEN_URI}",
    "scopes": ["https://www.googleapis.com/auth/userinfo.email"]
  }
}
EOF
    echo "Authorization resource '${AUTH_ID}' created."
    AUTHORIZATION_CONFIG_JSON="\"authorization_config\": { \"tool_authorizations\": [ \"projects/${PROJECT_NUMBER}/locations/global/authorizations/${AUTH_ID}\" ] },"
else
    echo "Skipping authorization resource creation as OAuth details are not provided."
    AUTHORIZATION_CONFIG_JSON=""
fi


# --- STEP 3: REGISTER THE ADK AGENT WITH GEMINI ENTERPRISE ---

echo "--- Registering the ADK Agent with Gemini Enterprise... ---"
AGENT_REGISTRATION_RESPONSE=$(curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: ${PROJECT_ID}" \
"https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_NUMBER}/locations/global/collections/default_collection/engines/${GEMINI_ENTERPRISE_APP_ID}/assistants/default_assistant/agents" \
-d @- << EOF
{
  "displayName": "${AGENT_DISPLAY_NAME}",
  "description": "${AGENT_DESCRIPTION}",
  "icon": {
    "uri": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/smart_toy/default/24px.svg"
  },
  ${AUTHORIZATION_CONFIG_JSON}
  "adk_agent_definition": {
    "tool_settings": {
      "tool_description": "${AGENT_TOOL_DESCRIPTION}"
    },
    "provisioned_reasoning_engine": {
      "reasoning_engine": "${ADK_DEPLOYMENT_ID}"
    }
  }
}
EOF
)

echo "${AGENT_REGISTRATION_RESPONSE}"
echo "Agent registered successfully."

export AGENT_RESOURCE_NAME=$(echo "${AGENT_REGISTRATION_RESPONSE}" | grep -o '"name": "[^"]*' | cut -d'"' -f4)
echo "Agent Resource Name: ${AGENT_RESOURCE_NAME}"

echo "--- REGISTRATION COMPLETE ---"
