# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Demo Agent - Simplest possible A2A-T agent

This is a minimal example showing how to create an A2A-T compatible agent.
It inherits from NegotiationBaseAgentExecutor which handles:
- A2A-T protocol communication
- Negotiation-T flow
- Authorization-T pre-positioning
- Notification-T push support
"""

from samples.agents.negotiation_base_agent import NegotiationBaseAgentExecutor
from loguru import logger


MY_AGENT_PROMPT = """
You are a simple demo agent for testing A2A-T protocol.

You received a task: {task}

Your job is to process this task and return a structured response.

Always respond in this format:
1. Task Received: <description of the task>
2. Processing Result: <what you did>
3. Status: SUCCESS

Task: {task}
"""


class DemoAgentExecutor(NegotiationBaseAgentExecutor):
    """Demo agent that shows minimum implementation requirements."""

    def __init__(self) -> None:
        super().__init__(agent_prompt_template=MY_AGENT_PROMPT)

    def needs_negotiation(self, input_text: str) -> bool:
        """Return True if this agent needs additional data before processing.
        
        Set to False for simple agents that can process any input directly.
        Set to True if you want the agent to request more data via negotiation.
        """
        return False

    def _execute_task(self, user_input: str, task_id: str = None, context_id: str = None) -> str:
        """This is where the actual business logic goes.
        
        Override this method to implement custom behavior.
        By default, it uses LLM with the prompt template.
        """
        return super()._execute_task(user_input, task_id, context_id)
