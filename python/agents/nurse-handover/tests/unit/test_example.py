from nurse_handover import agent


def test_load_agent() -> None:
    """Test that the agent can be successfully loaded."""

    _ = agent.root_agent
