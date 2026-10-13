import importlib.util
import sys
from pathlib import Path

import pytest
import tau2.agent


def _load_adk_agent():
    """Load tau2_agent.adk_agent without importing tau2_agent.__init__ (ADC setup)."""
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    adk_path = project_root / "tau2_agent" / "adk_agent.py"
    spec = importlib.util.spec_from_file_location(
        "tau2_agent.adk_agent", adk_path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tau2_agent.adk_agent"] = mod
    loader = spec.loader
    if loader is None:
        raise ImportError(f"Cannot load module from {adk_path}")
    loader.exec_module(mod)
    return mod


adk_agent = _load_adk_agent()

# Inject the local adk_agent module into the tau2.agent namespace
# This allows 'from tau2.agent.adk_agent import AdkAgent' to work
# even though adk_agent.py is not physically in the installed tau2 package.
tau2.agent.adk_agent = adk_agent
sys.modules["tau2.agent.adk_agent"] = adk_agent


@pytest.fixture
def get_environment():
    """Fixture to provide a mock environment with tools and policy."""

    class MockTool:
        def __init__(self, name="mock_tool"):
            self.openai_schema = {
                "function": {
                    "name": name,
                    "description": f"Description for {name}",
                    "parameters": {
                        "type": "object",
                        "properties": {"arg1": {"type": "string"}},
                    },
                }
            }

    class MockEnv:
        def get_tools(self):
            return [MockTool("create_task"), MockTool("get_users")]

        def get_policy(self):
            return "You are a helpful assistant."

    return MockEnv
