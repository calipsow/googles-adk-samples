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

import os
import pathlib

import dotenv
import pytest
import vertexai
from google.adk.evaluation.agent_evaluator import AgentEvaluator

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    dotenv.load_dotenv()
    # Ensure vertexai is initialized with the correct region for evaluations
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project:
        vertexai.init(project=project, location="us-east1")


@pytest.mark.asyncio
async def test_eval_full_conversation():
    """Test the agent's basic ability on a few examples."""
    await AgentEvaluator.evaluate(
        agent_module="rag",
        eval_dataset_file_path_or_dir=str(
            pathlib.Path(__file__).parent / "data/conversation.test.json"
        ),
        num_runs=1,
        criteria={
            "response_match_score": 0.35,
            "tool_trajectory_avg_score": 0.05,
        },
    )
