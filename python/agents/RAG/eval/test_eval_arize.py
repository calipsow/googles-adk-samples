#!/usr/bin/env python3
"""
Arize-based evaluation suite for the RAG agent.
This follows the Arize documentation pattern for experiments while using Google Vertex AI for evaluations.
"""

import json
import os
import time
import uuid
import warnings
from typing import Any

import pandas as pd

# Google Cloud imports for Vertex AI evaluations
import vertexai

# Arize imports
from arize import ArizeClient
from arize.experiments import EvaluationResult
from dotenv import load_dotenv

# ADK imports for running the agent
from google.adk.runners import InMemoryRunner
from google.genai.types import Part, UserContent
from vertexai.preview.evaluation import EvalTask

# Import the RAG agent
from rag.agent import root_agent

load_dotenv()

# Environment variables
ARIZE_API_KEY = os.getenv("ARIZE_API_KEY")
ARIZE_SPACE_ID = os.getenv("ARIZE_SPACE_ID")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")

if not all([ARIZE_API_KEY, ARIZE_SPACE_ID, GOOGLE_CLOUD_PROJECT]):
    warnings.warn(
        "Missing required environment variables: ARIZE_API_KEY, ARIZE_SPACE_ID, GOOGLE_CLOUD_PROJECT. "
        "Arize evaluations will be skipped.",
        stacklevel=2,
    )
    # Define a dummy arize_client to avoid NameError during collection
    arize_client = None
else:
    # Initialize Vertex AI
    vertexai.init(project=GOOGLE_CLOUD_PROJECT, location="us-east1")

    # Initialize Arize client
    arize_client = ArizeClient(api_key=ARIZE_API_KEY)


def load_test_data() -> list[dict]:
    """Load the conversation test data from JSON file."""
    with open("eval/data/conversation.test.json") as f:
        return json.load(f)


def create_arize_dataset():
    """Create an Arize dataset from the test data."""
    if arize_client is None:
        return None

    test_data = load_test_data()

    # Transform data for Arize format - simplified structure
    dataset_rows = []
    for i, item in enumerate(test_data):
        dataset_rows.append(
            {
                "id": str(i),  # Add explicit ID
                "query": item["query"],
                "expected_tool_use": json.dumps(
                    item["expected_tool_use"]
                ),  # Convert to JSON string
                "reference": item["reference"],
            }
        )

    # Create DataFrame
    df = pd.DataFrame(dataset_rows)

    # Debug: Print the DataFrame structure
    print("DataFrame shape:", df.shape)
    print("DataFrame columns:", df.columns.tolist())
    print("DataFrame dtypes:", df.dtypes.to_dict())
    print("First row sample:", df.iloc[0].to_dict())

    # Create dataset in Arize using the correct API
    dataset_name = f"rag_agent_evaluation_dataset-{uuid.uuid4()}"

    print(f"Creating dataset: {dataset_name}")
    dataset = arize_client.datasets.create(
        space=ARIZE_SPACE_ID,
        name=dataset_name,
        examples=df,
    )

    print(f"Dataset created with ID: {dataset.id}")
    time.sleep(5)  # Wait after dataset creation
    return dataset


def extract_tool_calls_from_response(
    response_text: str, agent_runner
) -> list[dict]:
    """
    Extract tool call information from the agent's response and execution context.
    This creates the trajectory format expected by Vertex AI evaluation API.
    """
    tool_calls = []
    max_response_length = 100

    # For ADK agents, we need to examine the execution traces
    # This is a simplified implementation - you may need to adjust based on
    # how you want to capture tool usage from the ADK agent execution

    # Check if the response indicates tool usage
    if any(
        keyword in response_text.lower()
        for keyword in [
            "according to",
            "based on",
            "source:",
            "[citation",
            "retrieved",
            "documentation",
        ]
    ):
        # Infer that the RAG tool was used
        tool_calls.append(
            {
                "tool_name": "retrieve_rag_documentation",
                "tool_input": response_text[:max_response_length] + "..."
                if len(response_text) > max_response_length
                else response_text,
            }
        )

    return tool_calls


async def call_rag_agent(query: str) -> dict[str, Any]:
    """Call the RAG agent programmatically and return response with metadata."""
    runner = InMemoryRunner(agent=root_agent)
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="test_user"
    )

    content = UserContent(parts=[Part(text=query)])
    response_parts = []

    for event in runner.run(
        user_id=session.user_id, session_id=session.id, new_message=content
    ):
        for part in event.content.parts:
            response_parts.append(part.text)

    response_text = "\n".join(response_parts)

    # Extract tool usage information
    tool_calls = extract_tool_calls_from_response(response_text, runner)

    return {"response": response_text, "tool_calls": tool_calls}


async def task_function(dataset_row: dict) -> str:
    """
    Task function for Arize experiments.
    This calls the RAG agent and returns the response.
    """
    query = dataset_row.get("query", "")

    # Call the agent - use await instead of asyncio.run since we're in async context
    result = await call_rag_agent(query)

    # Store additional metadata for evaluations
    # Note: We'll add this to the response string as JSON for evaluation access
    metadata = {
        "agent_response": result["response"],
        "tool_calls": result["tool_calls"],
        "expected_tool_use": dataset_row.get("expected_tool_use", "[]"),
        "reference": dataset_row.get("reference", ""),
    }

    return json.dumps(metadata)


# Vertex AI Evaluation Functions using the native evaluation API
def create_reference_trajectory(expected_tool_use: list[dict]) -> list[dict]:
    """Convert expected tool use to reference trajectory format."""
    if not expected_tool_use:
        return []

    trajectory = []
    for tool_use in expected_tool_use:
        trajectory.append(
            {
                "tool_name": tool_use.get("tool_name", ""),
                "tool_input": tool_use.get("tool_input", {}),
            }
        )
    return trajectory


def evaluate_with_vertex_ai_single_metric(
    predicted_trajectory: list[dict],
    reference_trajectory: list[dict],
    metric: str,
) -> dict[str, Any]:
    """Evaluate using Vertex AI's native evaluation API for a single metric."""
    try:
        # Create evaluation dataset
        eval_dataset = pd.DataFrame(
            {
                "predicted_trajectory": [predicted_trajectory],
                "reference_trajectory": [reference_trajectory],
            }
        )

        # Create evaluation task for single metric
        eval_task = EvalTask(
            dataset=eval_dataset,
            metrics=[metric],
        )

        # Run evaluation
        eval_result = eval_task.evaluate()

        # Extract metric
        metric_value = eval_result.summary_metrics.get(f"{metric}/mean", 0.0)
        results = {metric: metric_value}

        return results

    except Exception as e:
        print(f"Error in Vertex AI evaluation for {metric}: {e}")
        return {metric: 0.0}


def trajectory_exact_match_evaluator(
    output: str, dataset_row: dict
) -> EvaluationResult:
    """Evaluator for trajectory exact match using Vertex AI evaluation API."""
    try:
        metadata = json.loads(output)
        actual_tool_calls = metadata.get("tool_calls", [])
        expected_tool_use = json.loads(
            dataset_row.get("expected_tool_use", "[]")
        )

        # Simple exact match logic
        if len(actual_tool_calls) != len(expected_tool_use):
            return EvaluationResult(
                score=0.0,
                label="no_exact_match",
                explanation=f"Length mismatch: expected {len(expected_tool_use)} tools, got {len(actual_tool_calls)}",
            )

        if not expected_tool_use and not actual_tool_calls:
            return EvaluationResult(
                score=1.0,
                label="exact_match",
                explanation="Both expected and actual tool usage are empty - perfect match",
            )

        # Check if tool names match
        actual_names = [tc.get("tool_name", "") for tc in actual_tool_calls]
        expected_names = [et.get("tool_name", "") for et in expected_tool_use]

        score = 1.0 if actual_names == expected_names else 0.0
        label = "exact_match" if score == 1.0 else "no_exact_match"
        explanation = f"Tool sequence match: expected {expected_names}, got {actual_names}"

        return EvaluationResult(
            score=score, label=label, explanation=explanation
        )

    except Exception as e:
        return EvaluationResult(
            score=0.0, label="error", explanation=f"Evaluation error: {e!s}"
        )


def trajectory_precision_evaluator(
    output: str, dataset_row: dict
) -> EvaluationResult:
    """Evaluator for trajectory precision using Vertex AI evaluation API."""
    high_precision = 0.9
    medium_precision = 0.7

    try:
        metadata = json.loads(output)
        actual_tool_calls = metadata.get("tool_calls", [])
        expected_tool_use = json.loads(
            dataset_row.get("expected_tool_use", "[]")
        )

        if not expected_tool_use:
            score = 1.0 if not actual_tool_calls else 0.0
            label = "perfect" if score == 1.0 else "unexpected_tools"
            explanation = "No tools expected" + (
                ""
                if score == 1.0
                else f", but got {len(actual_tool_calls)} tools"
            )
            return EvaluationResult(
                score=score, label=label, explanation=explanation
            )

        # Calculate precision: how many of the actual tools were expected
        actual_names = {tc.get("tool_name", "") for tc in actual_tool_calls}
        expected_names = {et.get("tool_name", "") for et in expected_tool_use}

        if not actual_names:
            return EvaluationResult(
                score=0.0,
                label="no_tools_used",
                explanation="No tools used when tools were expected",
            )

        intersection = actual_names.intersection(expected_names)
        score = len(intersection) / len(actual_names)

        if score >= high_precision:
            label = "high_precision"
        elif score >= medium_precision:
            label = "medium_precision"
        else:
            label = "low_precision"

        explanation = f"Precision: {len(intersection)}/{len(actual_names)} = {score:.2f}. Expected: {sorted(expected_names)}, Used: {sorted(actual_names)}"

        return EvaluationResult(
            score=score, label=label, explanation=explanation
        )

    except Exception as e:
        return EvaluationResult(
            score=0.0, label="error", explanation=f"Evaluation error: {e!s}"
        )


def tool_name_match_evaluator(
    output: str, dataset_row: dict
) -> EvaluationResult:
    """Evaluator for tool name matching, ignoring parameters."""
    max_score = 1.0
    good_score = 0.7

    try:
        metadata = json.loads(output)
        actual_tool_calls = metadata.get("tool_calls", [])
        expected_tool_use = json.loads(
            dataset_row.get("expected_tool_use", "[]")
        )

        # Extract tool names only
        actual_tool_names = set()
        for tool_call in actual_tool_calls:
            if isinstance(tool_call, dict) and "tool_name" in tool_call:
                actual_tool_names.add(tool_call["tool_name"])

        expected_tool_names = set()
        for expected_tool in expected_tool_use:
            if isinstance(expected_tool, dict) and "tool_name" in expected_tool:
                expected_tool_names.add(expected_tool["tool_name"])

        # Calculate match score
        if not expected_tool_names:
            # If no tools expected, score 1.0 if no tools used, 0.0 if tools used
            score = max_score if not actual_tool_names else 0.0
            label = (
                "correct_no_tools" if score == max_score else "unexpected_tools"
            )
            explanation = f"No tools expected. Got: {sorted(actual_tool_names) if actual_tool_names else 'none'}"
        else:
            # Calculate intersection over expected (precision for expected tools)
            intersection = actual_tool_names.intersection(expected_tool_names)
            score = len(intersection) / len(expected_tool_names)

            if score == max_score:
                label = "perfect_match"
            elif score >= good_score:
                label = "good_match"
            elif score > 0:
                label = "partial_match"
            else:
                label = "no_match"

            explanation = f"Tool name coverage: {len(intersection)}/{len(expected_tool_names)} = {score:.2f}. Expected: {sorted(expected_tool_names)}, Got: {sorted(actual_tool_names)}"

        return EvaluationResult(
            score=score, label=label, explanation=explanation
        )

    except Exception as e:
        return EvaluationResult(
            score=0.0, label="error", explanation=f"Evaluation error: {e!s}"
        )


def run_evaluation_experiment():
    """Run the complete evaluation experiment using Arize."""
    if arize_client is None:
        print("Skipping evaluation due to missing environment variables.")
        return None

    # Create dataset
    print("Creating Arize dataset...")
    dataset = create_arize_dataset()

    # Define evaluators - using Vertex AI evaluation API (separate metrics for better Arize visibility)
    evaluators = [
        trajectory_exact_match_evaluator,
        trajectory_precision_evaluator,
        tool_name_match_evaluator,
    ]

    # Run experiment
    print("Running experiment...")
    experiment_result, _ = arize_client.experiments.run(
        space=ARIZE_SPACE_ID,
        dataset=dataset.id,
        task=task_function,
        evaluators=evaluators,
        name=f"rag_agent_evaluation_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
        concurrency=2,  # Reduce concurrency to be more gentle on APIs
        exit_on_error=False,
    )

    experiment_id = experiment_result.id if experiment_result else "unknown"

    print(f"Experiment completed! Experiment ID: {experiment_id}")
    print("View results in the Arize UI")

    return experiment_result


if __name__ == "__main__":
    run_evaluation_experiment()
