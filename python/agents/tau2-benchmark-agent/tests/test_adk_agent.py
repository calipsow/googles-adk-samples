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


from collections.abc import AsyncGenerator

import pytest
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from tau2.agent.adk_agent import AdkAgent
from tau2.data_model.message import (
    AssistantMessage,
    MultiToolMessage,
    ToolMessage,
    UserMessage,
)


class MockLlm(BaseLlm):
    model: str = "mock-llm"
    response_type: str = "text"

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        if self.response_type == "tool_call":
            tool_call = types.FunctionCall(
                name="create_task",
                args={"user_id": "123", "title": "Test Task"},
            )
            llm_response = LlmResponse(
                content=types.Content(
                    parts=[types.Part(function_call=tool_call)],
                    role="model",
                )
            )
        elif self.response_type == "multi_tool_call":
            tool_call_1 = types.FunctionCall(
                name="create_task",
                args={"user_id": "123", "title": "Test Task 1"},
            )
            tool_call_2 = types.FunctionCall(name="get_users", args={})
            llm_response = LlmResponse(
                content=types.Content(
                    parts=[
                        types.Part(function_call=tool_call_1),
                        types.Part(function_call=tool_call_2),
                    ],
                    role="model",
                )
            )
        else:
            response_text = "Mock response"
            llm_response = LlmResponse(
                content=types.Content(
                    parts=[types.Part(text=response_text)],
                    role="model",
                )
            )
        yield llm_response


@pytest.fixture(params=["text", "tool_call", "multi_tool_call"])
def adk_agent(get_environment, request) -> AdkAgent:
    """Fixture for AdkAgent with a mocked LLM."""
    mock_llm = MockLlm(response_type=request.param)
    return AdkAgent(
        llm="gemini-2.5-pro",
        tools=get_environment().get_tools(),
        domain_policy=get_environment().get_policy(),
        llm_args={"model_obj": mock_llm},
    )


@pytest.fixture
def first_user_message():
    """Fixture for the first user message."""
    return UserMessage(
        content="Hello can you help me create a task?", role="user"
    )


def test_adk_agent(adk_agent: AdkAgent, first_user_message: UserMessage):
    """Test case for AdkAgent."""

    target_message_count = 2
    target_tool_calls = 2

    agent_state = adk_agent.get_init_state()
    assert agent_state is not None
    agent_msg, agent_state = adk_agent.generate_next_message(
        first_user_message, agent_state
    )
    # Check the response is an assistant message
    assert isinstance(agent_msg, AssistantMessage)

    response_type = adk_agent._adk_root_agent.model.response_type
    if response_type == "text":
        assert agent_msg.content == "Mock response"
    elif response_type == "tool_call":
        assert agent_msg.tool_calls is not None
        assert len(agent_msg.tool_calls) == 1
        assert agent_msg.tool_calls[0].name == "create_task"
    elif response_type == "multi_tool_call":
        assert agent_msg.tool_calls is not None
        assert len(agent_msg.tool_calls) == target_tool_calls

    # Check the state is updated
    assert agent_state is not None
    assert len(agent_state.messages) == target_message_count
    # Check the messages are of the correct type
    assert isinstance(agent_state.messages[0], UserMessage)
    assert isinstance(agent_state.messages[1], AssistantMessage)
    assert agent_state.messages[0].content == first_user_message.content
    assert agent_state.messages[1].content == agent_msg.content


def test_adk_agent_with_tool_call(
    get_environment, first_user_message: UserMessage
):
    """Test case for AdkAgent with a tool call and response."""

    tool_call_count = 4

    # Setup agent to respond with a tool call first
    mock_llm_tool_call = MockLlm(response_type="tool_call")
    agent = AdkAgent(
        llm="gemini-2.5-pro",
        tools=get_environment().get_tools(),
        domain_policy=get_environment().get_policy(),
        llm_args={"model_obj": mock_llm_tool_call},
    )

    # 1. First interaction: User message -> Agent tool call
    agent_state = agent.get_init_state()
    agent_msg, agent_state = agent.generate_next_message(
        first_user_message, agent_state
    )

    assert isinstance(agent_msg, AssistantMessage)
    assert agent_msg.tool_calls is not None
    assert len(agent_msg.tool_calls) == 1
    tool_call = agent_msg.tool_calls[0]
    assert tool_call.name == "create_task"

    # 2. Second interaction: Tool response -> Agent final message
    tool_message = ToolMessage(
        id=tool_call.id,
        name=tool_call.name,
        role="tool",
        requestor="assistant",
        content="Task created successfully",
        error=False,
    )

    # Switch mock to respond with text
    mock_llm_text = MockLlm(response_type="text")
    agent._adk_root_agent.model = (
        mock_llm_text  # pytype: disable=attribute-error
    )

    agent_msg_final, agent_state = agent.generate_next_message(
        tool_message, agent_state
    )

    assert isinstance(agent_msg_final, AssistantMessage)
    assert agent_msg_final.content == "Mock response"
    assert agent_msg_final.tool_calls is None
    assert (
        len(agent_state.messages) == tool_call_count
    )  # User, Assistant (tool call), ToolMessage, Assistant (text)


def test_adk_agent_with_multi_tool_call(
    get_environment, first_user_message: UserMessage
):
    """Test case for AdkAgent with multiple tool calls."""

    target_tool_call_count = 2
    target_message_count = 5

    # Setup agent to respond with multiple tool calls
    mock_llm_multi_tool_call = MockLlm(response_type="multi_tool_call")
    agent = AdkAgent(
        llm="gemini-2.5-pro",
        tools=get_environment().get_tools(),
        domain_policy=get_environment().get_policy(),
        llm_args={"model_obj": mock_llm_multi_tool_call},
    )

    # 1. First interaction: User message -> Agent multi tool call
    agent_state = agent.get_init_state()
    agent_msg, agent_state = agent.generate_next_message(
        first_user_message, agent_state
    )

    assert isinstance(agent_msg, AssistantMessage)
    assert agent_msg.tool_calls is not None
    assert len(agent_msg.tool_calls) == target_tool_call_count
    tool_call_1 = agent_msg.tool_calls[0]
    tool_call_2 = agent_msg.tool_calls[1]
    assert tool_call_1.name == "create_task"
    assert tool_call_2.name == "get_users"

    # 2. Second interaction: MultiToolMessage response -> Agent final message
    tool_message_1 = ToolMessage(
        id=tool_call_1.id,
        name=tool_call_1.name,
        role="tool",
        content="Task created",
        requestor="assistant",
        error=False,
    )
    tool_message_2 = ToolMessage(
        id=tool_call_2.id,
        name=tool_call_2.name,
        role="tool",
        content="['user1', 'user2']",
        requestor="assistant",
        error=False,
    )
    multi_tool_message = MultiToolMessage(
        role="tool", tool_messages=[tool_message_1, tool_message_2]
    )

    # Switch mock to respond with text
    mock_llm_text = MockLlm(response_type="text")
    agent._adk_root_agent.model = (
        mock_llm_text  # pytype: disable=attribute-error
    )

    agent_msg_final, agent_state = agent.generate_next_message(
        multi_tool_message, agent_state
    )

    assert isinstance(agent_msg_final, AssistantMessage)
    assert agent_msg_final.content == "Mock response"
    assert agent_msg_final.tool_calls is None
    assert (
        len(agent_state.messages) == target_message_count
    )  # System, User, Assistant (tool calls), MultiToolMessage, Assistant (text)
