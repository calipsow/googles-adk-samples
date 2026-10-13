from sdlc_user_story_refiner.config import AgentConfig
from sdlc_user_story_refiner.prompt import get_prompt


def test_get_prompt_with_tools():
    """Test that the prompt includes tool usage instructions when tools are enabled."""
    prompt = get_prompt(tools_enabled=True)
    assert "Context & Knowledge Base Retrieval" in prompt
    assert "Actively query Spanner to retrieve relevant context" in prompt
    assert "Context Limitations" not in prompt


def test_get_prompt_without_tools():
    """Test that the prompt includes limitations instructions when tools are disabled."""
    prompt = get_prompt(tools_enabled=False)
    assert "Context Limitations" in prompt
    assert (
        "You do NOT have access to search tools or external databases" in prompt
    )
    assert "Context & Knowledge Base Retrieval" not in prompt


def test_agent_config_defaults():
    """Test that the agent config has expected default values."""
    config = AgentConfig()
    assert config.default_llm == "gemini-2.5-pro"
