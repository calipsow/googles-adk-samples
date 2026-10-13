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

"""Test cases for the supply chain agent and its sub-agents."""

import os
import sys
import unittest
import warnings

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from supply_chain.agent import root_agent
from supply_chain.sub_agents.chart_generator.agent import chart_generator_agent
from supply_chain.sub_agents.demand_sense.agent import demand_sense_agent
from supply_chain.sub_agents.market_pulse.agent import market_pulse_agent
from supply_chain.sub_agents.ops_insight.agent import ops_insight_agent
from supply_chain.sub_agents.weather_report.agent import weather_report_agent

# Suppress all warnings to clean up test output
warnings.filterwarnings("ignore")

session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()


class TestAgents(unittest.IsolatedAsyncioTestCase):
    """Test cases for the supply chain agent and its sub-agents."""

    async def asyncSetUp(self):
        """Set up for test methods."""
        super().setUp()
        self.session = await session_service.create_session(
            app_name="SupplyChainAgent",
            user_id="test_user",
        )
        self.user_id = "test_user"
        self.session_id = self.session.id

        self.runner = Runner(
            app_name="SupplyChainAgent",
            agent=root_agent,
            artifact_service=artifact_service,
            session_service=session_service,
        )

    def _run_agent(self, agent, query):
        """Helper method to run an agent and get the final response."""
        self.runner.agent = agent
        content = types.Content(role="user", parts=[types.Part(text=query)])
        events = list(
            self.runner.run(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=content,
            )
        )

        last_event = events[-1]
        final_response = "".join(
            [part.text for part in last_event.content.parts if part.text]
        )
        return final_response

    @pytest.mark.root_agent
    async def test_root_agent_can_respond(self):
        """Test the root agent with a general query."""
        query = "What capabilities do you have?"
        response = self._run_agent(root_agent, query)
        print(response)
        self.assertIsNotNone(response)

    @pytest.mark.demand
    async def test_demand_agent_can_forecast(self):
        """Test the demand_sense_agent."""
        query = "Forecast demand for the next 2 days in Delhi."
        response = self._run_agent(demand_sense_agent, query)
        print(response)
        self.assertIsNotNone(response)

    @pytest.mark.market
    async def test_market_agent_can_search(self):
        """Test the market_pulse_agent."""
        query = "What are the latest trends in power consumption in Delhi?"
        response = self._run_agent(market_pulse_agent, query)
        print(response)
        self.assertIsNotNone(response)

    @pytest.mark.ops
    async def test_ops_agent_can_respond(self):
        """Test the ops_insight_agent."""
        query = "Tell me the state with max power generation?"
        response = self._run_agent(ops_insight_agent, query)
        print(response)
        self.assertIsNotNone(response)

    @pytest.mark.weather
    async def test_weather_agent_can_fetch_report(self):
        """Test the weather_report_agent."""
        query = "What is the weather like in Delhi on 2025-01-13?"
        response = self._run_agent(weather_report_agent, query)
        print(response)
        self.assertIsNotNone(response)

    @pytest.mark.chart
    async def test_chart_agent_can_generate_chart(self):
        """Test the chart_generator_agent."""
        query = "Plot a line chart for the following data: [10, 20, 30, 40, 50]"
        response = self._run_agent(chart_generator_agent, query)
        print(response)
        self.assertIsNotNone(response)


if __name__ == "__main__":
    unittest.main()
