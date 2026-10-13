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
from unittest.mock import MagicMock, patch

from google.adk.models import LlmResponse
from google.genai import types

from brand_aligner_agent.models import (
    AssetEvaluation,
    CriterionVerdict,
    GuidelineVerdict,
)
from brand_aligner_agent.utils import (
    _text_progress_bar,
    after_model_callback,
    generate_radar_chart,
)


class TestUtils(unittest.IsolatedAsyncioTestCase):
    def test_text_progress_bar(self):
        # 0%
        self.assertEqual(_text_progress_bar(0, 10), "[░░░░░░░░░░]")
        # 50%
        self.assertEqual(_text_progress_bar(50, 10), "[█████░░░░░]")
        # 100%
        self.assertEqual(_text_progress_bar(100, 10), "[██████████]")
        # Bounds
        self.assertEqual(_text_progress_bar(-10, 10), "[░░░░░░░░░░]")
        self.assertEqual(_text_progress_bar(150, 10), "[██████████]")
        self.assertEqual(_text_progress_bar(-10, -10), "[░░░░░░░░░░░░░░░░░░░░]")
        self.assertEqual(_text_progress_bar(150, -10), "[████████████████████]")

    def test_after_model_callback_no_text(self):
        context = MagicMock()
        response = LlmResponse(content=types.Content(parts=[]))
        result = after_model_callback(context, response)
        self.assertIsNone(result)

    def test_after_model_callback_updates_text(self):
        # Setup context state
        context = MagicMock()
        context.agent_name = "test_agent"
        context.session.state = {
            "guideline_files": ["g1"],
            "asset_files": ["a1", "a2"],
            "processed_guidelines": [],
            "evaluation_results": [],
        }

        # Original response
        part = types.Part(text="Hello")
        response = LlmResponse(content=types.Content(parts=[part]))

        # Execute
        # Weights: (1*1) + (2*2) = 5 total
        # Current: 0
        # Progress: 0%
        after_model_callback(context, response)

        # Assert text modification (in-place)
        self.assertIn("Hello", part.text)
        self.assertIn("[", part.text)  # Progress bar added

    def test_after_model_callback_summarizer_100_percent(self):
        context = MagicMock()
        context.agent_name = "summarizer_agent"
        context.session.state = {}

        part = types.Part(text="Summary")
        response = LlmResponse(content=types.Content(parts=[part]))

        after_model_callback(context, response)
        # Should be 100% full
        self.assertIn("██████████", part.text)

    @patch("brand_aligner_agent.utils.plt")
    async def test_generate_radar_chart_no_categories(self, mock_plt):
        # Empty evaluation
        eval_result = AssetEvaluation(
            asset_id="1",
            asset_name="test",
            description="d",
            guideline_verdicts=[],
            final_score=0.0,
        )

        result = await generate_radar_chart(eval_result)
        self.assertIsNone(result)

    @patch("brand_aligner_agent.utils.plt")
    async def test_generate_radar_chart_success(self, mock_plt):
        # Setup evaluation with data
        criterion_verdict = CriterionVerdict(
            criterion_id="c1",
            question="q",
            gt_answer="yes",
            verdict="yes",
            category="Quality",
            guideline_id="g1",
        )
        guideline_verdict = GuidelineVerdict(
            guideline_id="g1", mean_score=1.0, verdicts=[criterion_verdict]
        )
        eval_result = AssetEvaluation(
            asset_id="1",
            asset_name="test",
            description="d",
            guideline_verdicts=[guideline_verdict],
            final_score=1.0,
        )

        # Mock BytesIO
        mock_buf = MagicMock()
        mock_buf.read.return_value = b"png_data"

        # Mock plt.subplots to return figure/axes
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        # Patch io.BytesIO inside the module (if imported directly) or mock saving
        with patch(
            "brand_aligner_agent.utils.io.BytesIO", return_value=mock_buf
        ):
            result = await generate_radar_chart(eval_result)

        self.assertEqual(result, b"png_data")
        mock_plt.subplots.assert_called_once()
