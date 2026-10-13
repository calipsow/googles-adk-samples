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
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd

from brand_aligner_agent.models import (
    Asset,
    AssetEvaluation,
    Category,
    Criterion,
    Guideline,
    GuidelineResponse,
    Severity,
)
from brand_aligner_agent.services import (
    EvalService,
    GuidelineService,
    _compute_scores_from_result,
)


class TestGuidelineService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_id = "test-project"
        self.location = "test-location"
        self.model_name = "test-model"
        self.service = GuidelineService(
            self.project_id,
            self.location,
            self.model_name,
        )

    @patch("brand_aligner_agent.services.genai.Client")
    async def test_extract_guideline_from_doc_success(self, mock_client_cls):
        # Setup mocks
        mock_client = mock_client_cls.return_value
        mock_model_response = MagicMock()

        # Create a mock parsed response object
        mock_parsed = GuidelineResponse(
            name="Test Guide",
            description="Test Description",
            applicable_categories=[Category.IMAGE],
            criteria=[
                Criterion(
                    name="Test Criterion",
                    criterion_value="Do this",
                    severity=Severity.BLOCKER,
                    category="General",
                )
            ],
        )
        mock_model_response.parsed = mock_parsed.model_dump()

        mock_client.aio.models.generate_content = AsyncMock(
            return_value=mock_model_response
        )

        # Execute
        result = await self.service.extract_guideline_from_doc(
            "gs://bucket/file.pdf", "application/pdf"
        )

        # Assert
        self.assertIsInstance(result, GuidelineResponse)
        self.assertEqual(result.name, "Test Guide")
        self.assertEqual(len(result.criteria), 1)

        # Verify call
        mock_client.aio.models.generate_content.assert_called_once()

    @patch("brand_aligner_agent.services.genai.Client")
    async def test_extract_guideline_from_doc_failure(self, mock_client_cls):
        # Setup mocks to raise exception
        mock_client = mock_client_cls.return_value
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("API Error")
        )

        # Execute & Assert
        with self.assertRaises(Exception) as context:
            await self.service.extract_guideline_from_doc(
                "gs://bucket/file.pdf", "application/pdf"
            )
        self.assertIn(
            "Failed to process document with AI", str(context.exception)
        )


class TestEvalService(unittest.TestCase):
    def setUp(self):
        self.project_id = "test-project"
        self.location = "test-location"
        self.model_name = "test-model"
        self.bucket_name = "test-bucket"

        # Patch external dependencies in __init__
        with (
            patch("brand_aligner_agent.services.vertexai.init"),
            patch("brand_aligner_agent.services.storage.Client"),
            patch("brand_aligner_agent.services.RubricBasedMetric"),
            patch("brand_aligner_agent.services.GenerativeModel"),
        ):
            self.service = EvalService(
                self.project_id,
                self.location,
                self.model_name,
                self.bucket_name,
            )

    def test_get_asset_type(self):
        # Accessing private method for testing logic
        self.assertEqual(
            self.service._get_asset_type("gs://bucket/image.png"), "image"
        )
        self.assertEqual(
            self.service._get_asset_type("gs://bucket/image.jpg"), "image"
        )
        self.assertEqual(
            self.service._get_asset_type("gs://bucket/video.mp4"), "video"
        )
        self.assertEqual(
            self.service._get_asset_type("gs://bucket/video.mov"), "video"
        )
        self.assertEqual(
            self.service._get_asset_type("gs://bucket/file.txt"), "unknown"
        )

    def test_filter_relevant_criteria_empty(self):
        criteria = []
        result = self.service._filter_relevant_criteria(criteria, "image")
        self.assertEqual(result, [])

    def test_filter_relevant_criteria_unknown_type(self):
        criteria = [
            Criterion(
                name="C1",
                criterion_value="V1",
                severity=Severity.WARNING,
                category="Cat",
            )
        ]
        result = self.service._filter_relevant_criteria(criteria, "unknown")
        self.assertEqual(result, criteria)

    def test_filter_relevant_criteria_success(self):
        # Setup
        criteria = [
            Criterion(
                criterion_id="c1",
                name="C1",
                criterion_value="V1",
                severity=Severity.WARNING,
                category="Cat",
            ),
            Criterion(
                criterion_id="c2",
                name="C2",
                criterion_value="V2",
                severity=Severity.WARNING,
                category="Cat",
            ),
        ]

        mock_response = MagicMock()
        mock_response.text = '```json\n{"relevant_criterion_ids": ["c1"]}\n```'
        self.service.filtering_model.generate_content = MagicMock(
            return_value=mock_response
        )

        # Execute
        result = self.service._filter_relevant_criteria(criteria, "image")

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].criterion_id, "c1")

    def test_filter_relevant_criteria_failure(self):
        # Test fallback on JSON error
        criteria = [
            Criterion(
                name="C1",
                criterion_value="V1",
                severity=Severity.WARNING,
                category="Cat",
            )
        ]

        mock_response = MagicMock()
        mock_response.text = "Not JSON"
        self.service.filtering_model.generate_content = MagicMock(
            return_value=mock_response
        )

        # Execute
        result = self.service._filter_relevant_criteria(criteria, "image")

        # Assert fallback to all criteria
        self.assertEqual(result, criteria)

    def test_compute_scores_from_result(self):
        # Setup data
        guideline = Guideline(
            name="Test",
            description="Test",
            file_uri="gs://file",
            criteria=[
                Criterion(
                    criterion_id="c1",
                    name="C1",
                    criterion_value="V1",
                    severity=Severity.WARNING,
                    category="Cat1",
                ),
                Criterion(
                    criterion_id="c2",
                    name="C2",
                    criterion_value="V2",
                    severity=Severity.BLOCKER,
                    category="Cat2",
                ),
            ],
        )

        # Mock rubrics in DataFrame
        rubric1 = MagicMock()
        rubric1.criterion_id = "c1"
        rubric1.question = "Q1"
        rubric1.gt_answer = "yes"
        rubric1.question_justification = "j1"
        rubric1.guideline_id = guideline.guideline_id

        rubric2 = MagicMock()
        rubric2.criterion_id = "c2"
        rubric2.question = "Q2"
        rubric2.gt_answer = "yes"  # Blocker implies yes override in logic
        rubric2.question_justification = "j2"
        rubric2.guideline_id = guideline.guideline_id

        # Mock verdicts
        # Q1: Verdict Yes (Match) -> 1.0
        # Q2: Verdict No (Mismatch) -> 0.0
        verdicts = {
            "q1": {"verdict": "yes", "justification": "j1"},
            "q2": {"verdict": "no", "justification": "j2"},
        }

        df = pd.DataFrame(
            [
                {
                    "rubrics_internal": [rubric1, rubric2],
                    "gecko_metric/verdicts": verdicts,
                }
            ]
        )

        # Execute
        mean_score, results = _compute_scores_from_result(df, guideline)

        # Assert
        self.assertEqual(mean_score, 0.5)  # (1.0 + 0.0) / 2
        self.assertEqual(len(results), 2)

        # Check verdict mapping
        self.assertEqual(results[0].verdict, "yes")
        self.assertEqual(results[1].verdict, "no")
        self.assertEqual(results[0].category, "Cat1")
        self.assertEqual(results[1].category, "Cat2")

    @patch.object(EvalService, "_run_evaluation_task")
    def test_evaluate_asset(self, mock_run_task):
        # Setup
        asset = Asset(
            asset_id="a1",
            asset_uri="gs://b/a.png",
            asset_name="a.png",
            asset_prompt="prompt",
            category=Category.IMAGE,
        )
        guidelines = [
            Guideline(
                name="G1",
                description="D1",
                file_uri="gs://f.pdf",
                criteria=[
                    Criterion(
                        name="C1",
                        criterion_value="V1",
                        severity=Severity.WARNING,
                        category="Cat",
                    )
                ],
            )
        ]

        # Mock scores for DSG and BAS calls
        # Call 1: DSG -> score 1.0
        # Call 2: BAS -> score 0.0
        mock_run_task.side_effect = [
            (1.0, []),  # DSG
            (0.0, []),  # BAS
        ]

        # Execute
        result = self.service.evaluate_asset(
            asset,
            guidelines,
            "guidance",
            "user1",
            "app1",
        )

        # Assert
        self.assertIsInstance(result, AssetEvaluation)
        self.assertEqual(result.asset_id, "a1")
        # Final score should be mean of [1.0, 0.0] = 0.5
        self.assertEqual(result.final_score, 0.5)
        self.assertEqual(len(result.guideline_verdicts), 2)
