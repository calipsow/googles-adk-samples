# Copyright 2025 Google LLC
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

"""Deployment script for Health Claim Adjudication Agent"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import vertexai
from absl import app, flags
from dotenv import load_dotenv
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

from claim_adjudication_agent.agent import root_agent

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP bucket (staging).")
flags.DEFINE_string("resource_id", None, "ReasoningEngine resource ID.")

flags.DEFINE_bool("list", False, "List all agents.")
flags.DEFINE_bool("create", False, "Creates a new agent on Reasoning Engine.")
flags.DEFINE_bool("delete", False, "Deletes an existing agent.")
flags.mark_bool_flags_as_mutual_exclusive(["create", "delete"])


def create() -> None:
    """Creates a reasoning engine for the Health Claim Adjudication workflow."""
    adk_app = AdkApp(agent=root_agent, enable_tracing=True)

    remote_agent = agent_engines.create(
        adk_app,
        display_name=root_agent.name,
        requirements=[
            "google-adk>=1.31.1",
            "google-cloud-aiplatform[agent-engines]>=1.148.1",
            "google-genai>=1.73.1",
            "pydantic>=2.12.5",
            "python-dotenv>=1.2.2",
            "absl-py>=2.1.0",
            "pandas>=2.2.3,<3.0.0",
            "google-cloud-logging>=3.15.0",
        ],
        extra_packages=["./claim_adjudication_agent"],
    )
    print(f"Created remote agent: {remote_agent.resource_name}")


def delete(resource_id: str) -> None:
    """Deletes the specified reasoning engine."""
    remote_agent = agent_engines.get(resource_id)
    remote_agent.delete(force=True)
    print(f"Deleted remote agent: {resource_id}")


def list_agents() -> None:
    """Lists all reasoning engines in the project/location."""
    remote_agents = agent_engines.list()
    template = """
{agent.name} ("{agent.display_name}")
- Create time: {agent.create_time}
- Update time: {agent.update_time}
"""
    remote_agents_string = "\n".join(
        template.format(agent=agent) for agent in remote_agents
    )
    print(f"All remote agents:\n{remote_agents_string}")


def main(argv: list[str]) -> None:
    del argv  # unused
    load_dotenv()

    # Priority: Flag -> Env -> None
    project_id = FLAGS.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = (
        FLAGS.location or os.getenv("GOOGLE_CLOUD_LOCATION") or "us-east1"
    )
    # Using the existing bucket from .env
    bucket = FLAGS.bucket or os.getenv("AE_DEPLOYMENT_BUCKET")

    print(f"PROJECT: {project_id}")
    print(f"LOCATION: {location}")
    print(f"STAGING BUCKET: {bucket}")

    if not project_id:
        print(
            "Error: Missing GOOGLE_CLOUD_PROJECT. Use --project_id or set in .env"
        )
        return
    if not bucket:
        print(
            "Error: Missing CLAIM_DOCUMENTS_BUCKET. Use --bucket or set in .env"
        )
        return

    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=f"gs://{bucket}",
    )

    if FLAGS.list:
        list_agents()
    elif FLAGS.create:
        create()
    elif FLAGS.delete:
        if not FLAGS.resource_id:
            print("Error: --resource_id is required for delete")
            return
        delete(FLAGS.resource_id)
    else:
        print(
            "Please specify an action: --create, --list, or --delete --resource_id=ID"
        )


if __name__ == "__main__":
    app.run(main)
