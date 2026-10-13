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

"""Test deployment of Health Claim Adjudication Agent to Vertex AI Agent Engine."""

import os

import vertexai
from absl import app, flags
from dotenv import load_dotenv
from vertexai import agent_engines

FLAGS = flags.FLAGS

flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string(
    "resource_id",
    None,
    "ReasoningEngine resource ID (returned after deployment).",
)
flags.DEFINE_string("user_id", None, "User ID for the session.")
flags.mark_flag_as_required("resource_id")
flags.mark_flag_as_required("user_id")


def main(argv: list[str]) -> None:
    del argv  # unused
    load_dotenv()

    # Priority: Flag -> Env -> None
    project_id = FLAGS.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = (
        FLAGS.location or os.getenv("GOOGLE_CLOUD_LOCATION") or "us-east1"
    )
    bucket = os.getenv("CLAIM_DOCUMENTS_BUCKET")

    if not project_id:
        print("Error: Missing GOOGLE_CLOUD_PROJECT.")
        return

    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=f"gs://{bucket}",
    )

    print(f"Connecting to Reasoning Engine: {FLAGS.resource_id}")
    try:
        agent = agent_engines.get(FLAGS.resource_id)
        print(f"Successfully connected to agent: {agent.display_name}")

        # Create a session
        session = agent.create_session(user_id=FLAGS.user_id)
        print(f"Session created: {session['id']}")

        print("\n--- Remote Agent Chat ---")
        print("Type 'quit' or 'exit' to stop.")

        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ["quit", "exit"]:
                break

            print("\nAgent (Remote): ", end="", flush=True)
            for event in agent.stream_query(
                user_id=FLAGS.user_id,
                session_id=session["id"],
                message=user_input,
            ):
                if "content" in event:
                    if "parts" in event["content"]:
                        for part in event["content"]["parts"]:
                            if "text" in part:
                                print(part["text"], end="", flush=True)
            print()  # New line after the stream

        # Cleanup session
        agent.delete_session(user_id=FLAGS.user_id, session_id=session["id"])
        print(f"\nSession {session['id']} deleted.")

    except Exception as e:
        print(f"Error during remote execution: {e}")


if __name__ == "__main__":
    app.run(main)
