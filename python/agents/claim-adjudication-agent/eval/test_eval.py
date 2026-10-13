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

"""Basic evaluation for Health Claim Adjudication Agent"""

import pathlib

import dotenv
import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    # Load from the root or the claim_adjudication_agent folder
    dotenv.load_dotenv()


@pytest.mark.asyncio
async def test_claim_adjudication_eval():
    """Test the health claim agent's ability to adjudicate specific cases."""
    # The name here must match the agent name in agent.py
    agent_name = "cashless_health_claim_advisor_workflow"

    # Path to the data directory containing the evaluation sets
    data_path = str(pathlib.Path(__file__).parent / "data")

    await AgentEvaluator.evaluate(
        agent_name,
        data_path,
        num_runs=1,  # Set to 1 for quick validation, increase for better metrics
    )
