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

"""Test deployment of Supply Chain AI Agent to Agent Engine."""

import asyncio
import os

import vertexai
from absl import app, flags
from dotenv import load_dotenv
from google.adk.sessions import VertexAiSessionService
from vertexai import agent_engines

FLAGS = flags.FLAGS

flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP bucket.")
flags.DEFINE_string(
    "resource_id",
    None,
    "ReasoningEngine resource ID (returned after deploying the agent)",
)
flags.DEFINE_string("user_id", None, "User ID (can be any string).")
flags.mark_flag_as_required("resource_id")
flags.mark_flag_as_required("user_id")


def validate_env(
    project_id: str | None, location: str | None, bucket: str | None
) -> bool:
    """Validates required environment variables."""
    if not project_id:
        print("Missing required environment variable: GOOGLE_CLOUD_PROJECT")
        return False
    elif not location:
        print("Missing required environment variable: GOOGLE_CLOUD_LOCATION")
        return False
    elif not bucket:
        print(
            "Missing required environment variable: GOOGLE_CLOUD_STORAGE_BUCKET"
        )
        return False
    return True


def run_chat_loop(agent, session, user_id: str) -> None:
    """Runs the interactive chat loop."""
    print(f"Created session for user ID: {user_id}")
    print("Type 'quit' to exit.")
    while True:
        user_input = input("Input: ")
        if user_input == "quit":
            break

        for event in agent.stream_query(
            user_id=user_id, session_id=session.id, message=user_input
        ):
            if "content" in event:
                if "parts" in event["content"]:
                    parts = event["content"]["parts"]
                    for part in parts:
                        if "text" in part:
                            text_part = part["text"]
                            print(f"Response: {text_part}")


def main(argv: list[str]) -> None:  # pylint: disable=unused-argument
    """Main execution function."""
    load_dotenv()

    # Prioritize flags, fallback to env vars
    project_id = (
        FLAGS.project_id
        if FLAGS.project_id
        else os.getenv("GOOGLE_CLOUD_PROJECT")
    )
    location = (
        FLAGS.location if FLAGS.location else os.getenv("GOOGLE_CLOUD_LOCATION")
    )
    bucket = (
        FLAGS.bucket
        if FLAGS.bucket
        else os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
    )

    if not validate_env(project_id, location, bucket):
        return

    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=f"gs://{bucket}",
    )

    session_service = VertexAiSessionService(project_id, location)  # type: ignore
    session = asyncio.run(
        session_service.create_session(
            app_name=FLAGS.resource_id, user_id=FLAGS.user_id
        )
    )

    agent = agent_engines.get(FLAGS.resource_id)
    print(f"Found agent with resource ID: {FLAGS.resource_id}")

    run_chat_loop(agent, session, FLAGS.user_id)

    asyncio.run(
        session_service.delete_session(
            app_name=FLAGS.resource_id,
            user_id=FLAGS.user_id,
            session_id=session.id,
        )
    )
    print(f"Deleted session for user ID: {FLAGS.user_id}")


if __name__ == "__main__":
    app.run(main)
