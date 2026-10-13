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

import unittest
from unittest.mock import AsyncMock, MagicMock

from google.adk.models import LlmRequest
from google.genai import types

from brand_aligner_agent.tools import (
    _append_to_session_state,
    save_files_as_artifacts,
    save_plan_to_state_tool,
)


class TestTools(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_context = MagicMock()
        self.mock_context.state = {}
        self.mock_context.agent_name = "test_agent"
        self.mock_context.invocation_id = "test_invocation"
        self.mock_context.save_artifact = AsyncMock()

    async def test_save_files_as_artifacts_no_content(self):
        llm_request = LlmRequest(contents=[])
        result = await save_files_as_artifacts(self.mock_context, llm_request)
        self.assertIsNone(result)
        self.mock_context.save_artifact.assert_not_called()

    async def test_save_files_as_artifacts_with_inline_data(self):
        # Create a Part with inline data
        blob = types.Blob(mime_type="image/png", data=b"fake_data")
        part = types.Part(inline_data=blob)

        # Create user content
        user_content = types.Content(role="user", parts=[part])
        llm_request = LlmRequest(contents=[user_content])

        # Execute
        await save_files_as_artifacts(self.mock_context, llm_request)

        # Assert
        self.mock_context.save_artifact.assert_called_once()
        call_args = self.mock_context.save_artifact.call_args
        self.assertIn("filename", call_args.kwargs)
        self.assertIn("artifact", call_args.kwargs)
        # Default filename format: artifact_{invocation_id}_{index}
        self.assertEqual(
            call_args.kwargs["filename"], "artifact_test_invocation_0"
        )

    async def test_save_plan_to_state_tool(self):
        # Setup
        guidelines = ["g1.pdf", "g2.txt"]
        assets = ["a1.png"]
        additional_guidance = "Be careful."

        # Mock ToolContext (duck typing)
        mock_tool_context = MagicMock()
        mock_tool_context.state = {}

        # Execute
        result = await save_plan_to_state_tool(
            guidelines, assets, mock_tool_context, additional_guidance
        )

        # Assert
        self.assertEqual(result, "Plan saved successfully.")
        self.assertEqual(mock_tool_context.state["guideline_files"], guidelines)
        self.assertEqual(mock_tool_context.state["asset_files"], assets)
        self.assertEqual(
            mock_tool_context.state["additional_guidance"], additional_guidance
        )

    async def test_append_to_session_state(self):
        # Initial empty state
        key = "test_list"
        item1 = {"id": 1}

        # Call 1
        await _append_to_session_state(key, item1, self.mock_context)
        self.assertEqual(self.mock_context.state[key], [item1])

        # Call 2
        item2 = {"id": 2}
        await _append_to_session_state(key, item2, self.mock_context)
        self.assertEqual(self.mock_context.state[key], [item1, item2])

    async def test_append_to_session_state_pydantic(self):
        # Test appending a Pydantic model (simulated with an object having model_dump)
        key = "pydantic_list"
        mock_model = MagicMock()
        mock_model.model_dump.return_value = {"data": "value"}

        await _append_to_session_state(key, mock_model, self.mock_context)
        self.assertEqual(self.mock_context.state[key], [{"data": "value"}])
