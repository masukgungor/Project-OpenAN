"""
Energy Saving Workflow Definition (PSOP)

This module defines the Problem-Solving Oriented Protocol (PSOP) workflow
for the Energy Saving Use Case.
"""

ENERGY_SAVING_WORKFLOW_STEPS = [
    {
        "step_id": "step_1_create_intent",
        "agent": "energy-agent",
        "action": "create_intent",
        "input": {
            "region": "${region}",
            "energy_target": "${energy_target}",
            "safeguard": "${safeguard}",
            "cluster_id": "${cluster_id}",
            "priority": "${priority}",
        },
        "output": {
            "intent_id": "intent_id",
            "intent": "intent_data",
        },
        "description": "Create energy saving intent from user parameters",
        "on_failure": "retry_3_times",
    },
    {
        "step_id": "step_2_get_electricity_price",
        "agent": "energy-agent",
        "action": "get_electricity_price",
        "input": {
            "region": "${region}",
        },
        "output": {
            "electricity_price": "price_data",
        },
        "description": "Fetch current electricity prices for the region",
        "depends_on": ["step_1_create_intent"],
        "on_failure": "retry_3_times",
    },
    {
        "step_id": "step_3_classify_cluster",
        "agent": "energy-agent",
        "action": "classify_cluster",
        "input": {
            "cluster_id": "${cluster_id}",
            "sites": "${site_data}",
        },
        "output": {
            "classification_result": "cluster_classification",
        },
        "description": "Classify all sites in the cluster into power bands",
        "depends_on": ["step_2_get_electricity_price"],
        "on_failure": "continue_with_warning",
    },
    {
        "step_id": "step_4_optimize_cluster",
        "agent": "energy-agent",
        "action": "optimize_cluster",
        "input": {
            "cluster_id": "${cluster_id}",
            "classification_result": "${classification_result}",
            "target": "${energy_target}",
        },
        "output": {
            "optimization_plan": "cluster_plan",
        },
        "description": "Generate cluster optimization plan with traffic migration actions",
        "depends_on": ["step_3_classify_cluster"],
        "on_failure": "rollback",
    },
    {
        "step_id": "step_5_negotiate_with_mae",
        "agent": "energy-agent",
        "action": "negotiate_with_mae",
        "input": {
            "plan": "${optimization_plan}",
            "intent": "${intent_data}",
        },
        "output": {
            "negotiation_result": "negotiation_response",
        },
        "description": "Negotiate with MAE via A2A-T to confirm achievability",
        "depends_on": ["step_4_optimize_cluster"],
        "on_failure": "retry_2_times",
    },
    {
        "step_id": "step_6_validate_and_approve",
        "agent": "orchestrator",
        "action": "validate_plan",
        "input": {
            "plan": "${optimization_plan}",
            "negotiation_result": "${negotiation_result}",
        },
        "output": {
            "approved": "is_approved",
            "plan": "validated_plan",
        },
        "description": "Validate plan based on negotiation results and approve/reject",
        "depends_on": ["step_5_negotiate_with_mae"],
        "on_failure": "reject_and_notify",
    },
    {
        "step_id": "step_7_execute_plan",
        "agent": "mae",
        "action": "execute_plan",
        "input": {
            "plan": "${validated_plan}",
            "constraints": "${negotiation_result.constraints}",
        },
        "output": {
            "execution_result": "execution_status",
        },
        "description": "Execute approved optimization plan on MAE platform",
        "depends_on": ["step_6_validate_and_approve"],
        "condition": "is_approved == true",
        "on_failure": "compensate_and_notify",
    },
    {
        "step_id": "step_8_report_results",
        "agent": "orchestrator",
        "action": "compile_results",
        "input": {
            "intent_id": "${intent_id}",
            "plan": "${validated_plan}",
            "execution_result": "${execution_result}",
        },
        "output": {
            "final_report": "energy_saving_report",
        },
        "description": "Compile final energy saving report with results",
        "depends_on": ["step_7_execute_plan"],
    },
]


ENERGY_SAVING_WORKFLOW = {
    "workflow_id": "energy_saving_optimization_v1",
    "name": "Energy Saving Optimization Workflow",
    "description": (
        "Monthly collaborative optimization of electricity cost reduction at cluster level. "
        "This workflow orchestrates intent creation, price fetching, site classification, "
        "cluster optimization, MAE negotiation, and plan execution."
    ),
    "version": "1.0.0",
    "category": "energy-saving",
    "steps": ENERGY_SAVING_WORKFLOW_STEPS,
    "input_schema": {
        "type": "object",
        "required": ["region", "energy_target"],
        "properties": {
            "region": {
                "type": "string",
                "enum": ["north", "south", "east", "west", "central"],
                "description": "Target region for energy saving",
            },
            "energy_target": {
                "type": "string",
                "enum": ["maximized_saving", "balanced", "experience_first"],
                "description": "Energy saving target level",
            },
            "safeguard": {
                "type": "object",
                "properties": {
                    "min_throughput_mbps": {"type": "number", "default": 10.0},
                    "max_latency_ms": {"type": "number", "default": 50.0},
                    "coverage_maintain": {"type": "boolean", "default": True},
                },
            },
            "cluster_id": {
                "type": "string",
                "description": "Target cluster ID for optimization",
            },
            "site_data": {
                "type": "array",
                "description": "List of site data for classification",
                "items": {
                    "type": "object",
                    "properties": {
                        "site_id": {"type": "string"},
                        "current_power_kw": {"type": "number"},
                    },
                },
            },
            "priority": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
                "default": 5,
            },
        },
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "intent_id": {"type": "string"},
            "plan_id": {"type": "string"},
            "status": {
                "type": "string",
                "enum": ["completed", "failed", "partial"],
            },
            "estimated_saving_percent": {"type": "number"},
            "actual_saving_percent": {"type": "number"},
            "execution_summary": {"type": "string"},
        },
    },
    "error_handling": {
        "retry_policy": {
            "max_retries": 3,
            "backoff_factor": 2,
            "retry_on_status_codes": [408, 429, 500, 502, 503, 504],
        },
        "fallback_strategy": "continue_with_warning",
        "rollback_on_failure": True,
    },
    "timeouts": {
        "step_1_create_intent": 30,
        "step_2_get_electricity_price": 60,
        "step_3_classify_cluster": 120,
        "step_4_optimize_cluster": 120,
        "step_5_negotiate_with_mae": 180,
        "step_6_validate_and_approve": 30,
        "step_7_execute_plan": 600,
        "step_8_report_results": 30,
    },
}


def get_energy_saving_workflow():
    """Return the energy saving workflow definition."""
    return ENERGY_SAVING_WORKFLOW


def get_workflow_steps():
    """Return the energy saving workflow steps."""
    return ENERGY_SAVING_WORKFLOW_STEPS
