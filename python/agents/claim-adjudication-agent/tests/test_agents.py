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

"""Test cases for the Health Claim Adjudication Agent."""


import dotenv
import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types

from claim_adjudication_agent.agent import (
    cashless_health_claim_advisor_workflow,
)

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    # Load from the root or the claim_adjudication_agent folder
    dotenv.load_dotenv()


@pytest.mark.asyncio
async def test_health_claim_workflow():
    """Runs the workflow on a sample claim ID and expects a summary response."""

    # Simple input to trigger the workflow
    user_input = "Adjudicate the claim ID CLAIMIDX0001"
    app_name = "claim-adjudication-agent"

    runner = InMemoryRunner(
        agent=cashless_health_claim_advisor_workflow, app_name=app_name
    )

    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="test_user"
    )

    content = types.Content(parts=[types.Part(text=user_input)])
    response = ""

    # Execute the workflow
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content,
    ):
        print(f"Event: {event}")
        if (
            event.content
            and event.content.parts
            and event.content.parts[0].text
        ):
            response += event.content.parts[0].text

    # Basic assertions to ensure the agent produced meaningful output
    # We expect the summary to mention adjudication or status
    response_lower = response.lower()

    # Note: These keywords depend on the actual agent prompts and tool outputs
    keywords = ["claim", "adjudication", "summary", "status"]
    assert any(keyword in response_lower for keyword in keywords)
