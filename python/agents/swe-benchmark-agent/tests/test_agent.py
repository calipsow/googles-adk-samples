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

"""Integration tests for SWE Agent."""

import unittest
from typing import Any

from swe_benchmark_agent.orchestrator import (
    MAX_VERIFICATION_TURN_COUNT,
    Orchestrator,
)


class MockEnvironment:
    """Mock environment for testing."""

    def __init__(self, instance: dict[str, str]):
        self.instance = instance
        self.commands_executed = []

    def execute(self, command: str) -> tuple[int, str]:
        """Mock command execution."""
        self.commands_executed.append(command)

        # Mock responses for different commands
        if command.startswith("cat"):
            return 0, "def hello():\n    print('Hello, World!')\n"
        if command.startswith("ls"):
            return 0, "test.py\nREADME.md\n"
        if "git diff" in command:
            return 0, "diff --git a/test.py b/test.py\n"
        return 0, ""

    def copy_to(self, src: str, dest: str) -> None:
        """Mock file copy."""

    def get_working_dir(self) -> str:
        """Mock get working directory."""
        return "/app"

    def close(self) -> None:
        """Mock cleanup."""

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        self.close()


class TestSweAgent(unittest.TestCase):
    """Test cases for SWE Agent components."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_instance = {
            "instance_id": "test-instance-1",
            "repo": "test/repo",
            "problem_statement": "Fix the bug in the hello function",
        }
        self.mock_env = MockEnvironment(self.test_instance)

    def test_orchestrator_initialization(self) -> None:
        """Test that orchestrator initializes correctly."""
        orchestrator = Orchestrator(self.mock_env, benchmark_type="swebench")

        self.assertIsNotNone(orchestrator)
        self.assertEqual(orchestrator.benchmark_type, "swebench")
        self.assertEqual(orchestrator.working_dir, "/testbed")
        self.assertIsNone(orchestrator.patch)

    def test_orchestrator_terminalbench_initialization(self) -> None:
        """Test orchestrator initialization for terminalbench."""
        orchestrator = Orchestrator(
            self.mock_env, benchmark_type="terminalbench"
        )

        self.assertEqual(orchestrator.benchmark_type, "terminalbench")
        self.assertEqual(orchestrator.working_dir, "/app")

    def test_read_file_range(self) -> None:
        """Test reading a file range."""
        orchestrator = Orchestrator(self.mock_env, benchmark_type="swebench")

        result = orchestrator.read_file_range(
            "test.py", start_line=1, end_line=2
        )

        self.assertIn("test.py", result)
        self.assertIn("def hello():", result)
        self.assertTrue(
            any("cat" in cmd for cmd in self.mock_env.commands_executed)
        )

    def test_run_shell_command(self) -> None:
        """Test running a shell command."""
        orchestrator = Orchestrator(self.mock_env, benchmark_type="swebench")

        result = orchestrator.run_shell_command("ls -la")

        self.assertIn("Command exited with status", result)
        self.assertTrue(
            any("ls -la" in cmd for cmd in self.mock_env.commands_executed)
        )

    def test_submit_swebench(self) -> None:
        """Test submission for swebench."""
        orchestrator = Orchestrator(self.mock_env, benchmark_type="swebench")

        result = orchestrator.submit()

        self.assertEqual(result, "Submitted successfully.")
        self.assertIsNotNone(orchestrator.patch)
        self.assertTrue(
            any("git diff" in cmd for cmd in self.mock_env.commands_executed)
        )

    def test_create_file(self) -> None:
        """Test creating a new file."""
        orchestrator = Orchestrator(self.mock_env, benchmark_type="swebench")

        result = orchestrator.create_file("new_file.py", "print('test')")

        self.assertIn("created successfully", result)

    def test_edit_file_invalid_format(self) -> None:
        """Test edit_file with invalid diff format."""
        orchestrator = Orchestrator(self.mock_env, benchmark_type="swebench")

        result = orchestrator.edit_file("test.py", "invalid diff")

        self.assertIn("Invalid diff format", result)

    def test_undo_last_edit_no_backup(self) -> None:
        """Test undo when no backup exists."""
        orchestrator = Orchestrator(self.mock_env, benchmark_type="swebench")

        result = orchestrator.undo_last_edit("test.py")

        self.assertIn("Unable to undo", result)


if __name__ == "__main__":
    unittest.main()
