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

"""MAE (Multi-Agent Environment) Agent -- handles negotiation for RAN energy saving.

Receives negotiation requests from Energy Saving Agent via A2A-T,
evaluates constraints, and returns negotiation responses.
"""

import asyncio
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

from loguru import logger

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    Artifact,
    Part,
    Message,
)

from common.llm import get_llm_instance


class MaeAgentExecutor(AgentExecutor):
    """MAE Agent for negotiation with RAN Energy Saving Agent.

    Handles:
    - Cluster optimization plan evaluation
    - Constraint validation
    - Risk assessment
    - Negotiation response generation
    """

    _llm_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mae_llm_")

    def __init__(self) -> None:
        self.name = "MAE Agent"
        self.version = "1.0.0"
        self.description = "Multi-Agent Environment Agent for RAN energy saving negotiation"
        self.llm_client = get_llm_instance()
        logger.info(f"[MaeAgent] Initialized")

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_input = context.get_user_input()
        task_id = context.task_id
        context_id = context.context_id

        logger.info(f"[MaeAgent] ========== NEGOTIATION REQUEST ==========")
        logger.info(f"[MaeAgent] Task ID: {task_id}")
        logger.info(f"[MaeAgent] Input: {user_input[:1000] if user_input else 'empty'}...")

        try:
            await event_queue.enqueue_event(Task(
                id=task_id,
                context_id=context_id,
                status=TaskStatus(
                    state=TaskState.TASK_STATE_WORKING,
                    message=Message(role=2, parts=[Part(text="MAE Agent evaluating negotiation request...")]),
                ),
            ))

            negotiation_result = await self._process_negotiation(user_input)

            logger.info(f"[MaeAgent] ========== NEGOTIATION RESULT ==========")
            logger.info(f"[MaeAgent] Achievable: {negotiation_result.get('achievable')}")
            logger.info(f"[MaeAgent] Constraints: {json.dumps(negotiation_result.get('constraints', {}), indent=2)}")
            logger.info(f"[MaeAgent] Risk Factors: {negotiation_result.get('risk_factors', [])}")
            logger.info(f"[MaeAgent] Recommendations: {negotiation_result.get('recommendations', [])}")
            logger.info(f"[MaeAgent] Negotiation ID: {negotiation_result.get('negotiation_id')}")
            logger.info(f"[MaeAgent] =======================================")

            await event_queue.enqueue_event(Task(
                id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED),
                artifacts=[
                    Artifact(
                        name="negotiation_result",
                        parts=[Part(text=json.dumps(negotiation_result, ensure_ascii=False, indent=2))],
                    )
                ],
                metadata={},
            ))

        except Exception as e:
            logger.error(f"[MaeAgent] Failed: {e}", exc_info=True)
            await event_queue.enqueue_event(self._error_task(context, str(e)))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info(f"[MaeAgent] Task cancelled: task_id={context.task_id}")

    async def _process_negotiation(self, user_input: str) -> Dict[str, Any]:
        if not self.llm_client:
            return self._mock_negotiation_response(user_input)

        try:
            prompt = self._build_negotiation_prompt(user_input)
            t0 = time.time()
            logger.info(f"[MaeAgent] Calling LLM for negotiation...")

            _, response_text = await asyncio.get_event_loop().run_in_executor(
                self._llm_executor, self.llm_client.ask_llm, prompt
            )

            logger.info(f"[MaeAgent] LLM negotiation done ({time.time()-t0:.2f}s)")

            try:
                result = json.loads(response_text.strip())
                return result
            except json.JSONDecodeError:
                logger.warning(f"[MaeAgent] LLM response not valid JSON, using mock: {response_text[:200]}")
                return self._mock_negotiation_response(user_input)

        except Exception as e:
            logger.error(f"[MaeAgent] LLM negotiation failed: {e}")
            return self._mock_negotiation_response(user_input)

    def _build_negotiation_prompt(self, user_input: str) -> str:
        return f"""# Role
You are the MAE (Multi-Agent Environment) Agent responsible for evaluating RAN energy saving optimization plans.

# Task
Evaluate the incoming optimization plan and provide a negotiation response with:
1. Whether the plan is achievable
2. Validated or adjusted constraints
3. Identified risk factors
4. Final recommendations

# Input
{user_input}

# Output Format (JSON only)
{{
    "achievable": true/false,
    "constraints": {{
        "max_power_reduction_percent": number,
        "min_throughput_mbps": number,
        "execution_window_hours": [list of hours],
        "coverage_maintain": boolean
    }},
    "risk_factors": ["list of risk strings"],
    "recommendations": ["list of recommendation strings"],
    "negotiation_id": "NEG-XXXXXXXX"
}}

Respond ONLY with valid JSON, no additional text."""

    def _mock_negotiation_response(self, user_input: str) -> Dict[str, Any]:
        negotiation_id = f"NEG-{uuid.uuid4().hex[:8].upper()}"
        return {
            "achievable": True,
            "constraints": {
                "max_power_reduction_percent": 15,
                "min_throughput_mbps": 10,
                "execution_window_hours": [23, 0, 1, 2, 3, 4, 5],
                "coverage_maintain": True
            },
            "risk_factors": [
                "Coverage degradation risk during peak hours",
                "User experience impact in high-density areas"
            ],
            "recommendations": [
                "Execute power reduction during off-peak hours only",
                "Monitor KPIs every 15 minutes during first hour",
                "Prepare rollback plan if coverage drops below threshold"
            ],
            "negotiation_id": negotiation_id
        }

    def _error_task(self, context: RequestContext, error: str):
        return Task(
            id=context.task_id,
            context_id=context.context_id,
            status=TaskStatus(
                state=TaskState.TASK_STATE_FAILED,
                message=Message(role=2, parts=[Part(text=f"MAE Agent error: {error}")]),
            ),
            metadata={},
        )
