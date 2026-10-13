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

import json
import os
import sys

import vertexai
from dotenv import load_dotenv
from vertexai import agent_engines

# Add the project root to sys.path to allow importing brand_aligner_agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from brand_aligner_agent.agent import root_agent

load_dotenv(override=True)
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
GCS_BUCKET = os.getenv("GCS_BUCKET_NAME")
STAGING_BUCKET = os.getenv("STAGING_BUCKET")

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=f"gs://{STAGING_BUCKET}",
)

adk_app = agent_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

if os.path.exists(".agent_engine_resource.json"):
    with open(".agent_engine_resource.json") as f:
        app_resource_data = json.load(f)
        existing_resource_name = app_resource_data.get("resource_name")
else:
    existing_resource_name = None

common_args = {
    "agent_engine": adk_app,
    "extra_packages": [
        "brand_aligner_agent/__init__.py",
        "brand_aligner_agent/agent.py",
        "brand_aligner_agent/auth.py",
        "brand_aligner_agent/models.py",
        "brand_aligner_agent/services.py",
        "brand_aligner_agent/tools.py",
        "brand_aligner_agent/utils.py",
    ],
    "requirements": [
        "cloudpickle>=3.1.2",
        "fastapi>=0.136.1",
        "google-adk==1.31.1",
        "google-api-python-client>=2.194.0",
        "google-auth>=2.49.2",
        "google-auth-oauthlib>=1.3.1",
        "google-cloud-aiplatform[adk,agent-engines,evaluation]>=1.148.0,<2.0.0",
        "google-cloud-storage==3.10.1",
        "google-genai>=1.73.0",
        "matplotlib>=3.10.9",
        "numpy>=2.4.4",
        "pandas>=3.0.2",
        "pydantic==2.13.3",
    ],
    "env_vars": {
        "PROJECT_ID": PROJECT_ID,
        "LOCATION": LOCATION,
        "GOOGLE_GENAI_USE_VERTEXAI": os.getenv(
            "GOOGLE_GENAI_USE_VERTEXAI", "true"
        ),
        "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": os.getenv(
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "true"
        ),
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": os.getenv(
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "true"
        ),
        "GCS_BUCKET_NAME": GCS_BUCKET,
        "MODEL_NAME": os.getenv("MODEL_NAME", "gemini-2.5-flash"),
        "AUTH_ID": os.getenv("AUTH_ID"),
        "OAUTH_TOKEN_URI": os.getenv("OAUTH_TOKEN_URI"),
        "OAUTH_AUTH_URI_BASE": os.getenv("OAUTH_AUTH_URI_BASE"),
        "OAUTH_CLIENT_ID": os.getenv("OAUTH_CLIENT_ID"),
        "OAUTH_CLIENT_SECRET": os.getenv("OAUTH_CLIENT_SECRET"),
        "MODE": "production",
    },
    "gcs_dir_name": "build-dev",
    "display_name": "Brand Aligner Agent",
    "description": "Searches for and evaluates visual assets (images/videos) against brand guidelines to ensure compliance and stylistic alignment.",
}

if existing_resource_name:
    print(f"Updating existing Agent Engine resource: {existing_resource_name}")
    remote_app = agent_engines.update(
        resource_name=existing_resource_name,
        **common_args,
    )
else:
    print("Creating new Agent Engine resource")
    remote_app = agent_engines.create(
        **common_args,
    )

print("Deployment finished!")

app_resource_data = {"resource_name": remote_app.resource_name}
with open(".agent_engine_resource.json", "w") as f:
    json.dump(app_resource_data, f, indent=2)

print(f"Resource Name: {remote_app.resource_name}")
