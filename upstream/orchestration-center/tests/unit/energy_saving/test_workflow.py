import pytest
from orchestrate.energy_saving.workflows import (
    ENERGY_SAVING_WORKFLOW,
    ENERGY_SAVING_WORKFLOW_STEPS,
    get_energy_saving_workflow,
    get_workflow_steps,
)


class TestEnergySavingWorkflow:
    """Test Energy Saving Workflow definition."""

    def test_workflow_definition(self):
        assert ENERGY_SAVING_WORKFLOW["workflow_id"] == "energy_saving_optimization_v1"
        assert ENERGY_SAVING_WORKFLOW["version"] == "1.0.0"
        assert "steps" in ENERGY_SAVING_WORKFLOW

    def test_workflow_steps_count(self):
        assert len(ENERGY_SAVING_WORKFLOW_STEPS) == 8

    def test_workflow_input_schema(self):
        schema = ENERGY_SAVING_WORKFLOW["input_schema"]
        assert "region" in schema["required"]
        assert "energy_target" in schema["required"]

    def test_workflow_output_schema(self):
        schema = ENERGY_SAVING_WORKFLOW["output_schema"]
        assert "intent_id" in schema["properties"]
        assert "plan_id" in schema["properties"]
        assert "status" in schema["properties"]

    def test_workflow_steps_have_required_fields(self):
        for step in ENERGY_SAVING_WORKFLOW_STEPS:
            assert "step_id" in step
            assert "agent" in step
            assert "action" in step
            assert "input" in step
            assert "output" in step
            assert "description" in step

    def test_workflow_step_dependencies(self):
        step_1 = next(s for s in ENERGY_SAVING_WORKFLOW_STEPS if s["step_id"] == "step_1_create_intent")
        step_2 = next(s for s in ENERGY_SAVING_WORKFLOW_STEPS if s["step_id"] == "step_2_get_electricity_price")
        
        assert "depends_on" not in step_1 or step_1["depends_on"] == []
        assert "step_1_create_intent" in step_2["depends_on"]

    def test_get_energy_saving_workflow(self):
        workflow = get_energy_saving_workflow()
        assert workflow["workflow_id"] == "energy_saving_optimization_v1"

    def test_get_workflow_steps(self):
        steps = get_workflow_steps()
        assert len(steps) == 8


class TestWorkflowStepExecutionOrder:
    """Test workflow step execution order logic."""

    def test_step_1_no_dependencies(self):
        step_1 = next(s for s in ENERGY_SAVING_WORKFLOW_STEPS if s["step_id"] == "step_1_create_intent")
        assert step_1.get("depends_on", []) == []

    def test_step_2_depends_on_step_1(self):
        step_2 = next(s for s in ENERGY_SAVING_WORKFLOW_STEPS if s["step_id"] == "step_2_get_electricity_price")
        assert "step_1_create_intent" in step_2["depends_on"]

    def test_step_3_depends_on_step_2(self):
        step_3 = next(s for s in ENERGY_SAVING_WORKFLOW_STEPS if s["step_id"] == "step_3_classify_cluster")
        assert "step_2_get_electricity_price" in step_3["depends_on"]

    def test_step_4_depends_on_step_3(self):
        step_4 = next(s for s in ENERGY_SAVING_WORKFLOW_STEPS if s["step_id"] == "step_4_optimize_cluster")
        assert "step_3_classify_cluster" in step_4["depends_on"]

    def test_step_5_depends_on_step_4(self):
        step_5 = next(s for s in ENERGY_SAVING_WORKFLOW_STEPS if s["step_id"] == "step_5_negotiate_with_mae")
        assert "step_4_optimize_cluster" in step_5["depends_on"]

    def test_step_6_depends_on_step_5(self):
        step_6 = next(s for s in ENERGY_SAVING_WORKFLOW_STEPS if s["step_id"] == "step_6_validate_and_approve")
        assert "step_5_negotiate_with_mae" in step_6["depends_on"]

    def test_step_7_depends_on_step_6_and_has_condition(self):
        step_7 = next(s for s in ENERGY_SAVING_WORKFLOW_STEPS if s["step_id"] == "step_7_execute_plan")
        assert "step_6_validate_and_approve" in step_7["depends_on"]
        assert step_7["condition"] == "is_approved == true"

    def test_step_8_depends_on_step_7(self):
        step_8 = next(s for s in ENERGY_SAVING_WORKFLOW_STEPS if s["step_id"] == "step_8_report_results")
        assert "step_7_execute_plan" in step_8["depends_on"]


class TestWorkflowTimeouts:
    """Test workflow timeout configuration."""

    def test_timeouts_configured(self):
        timeouts = ENERGY_SAVING_WORKFLOW.get("timeouts", {})
        assert "step_1_create_intent" in timeouts
        assert "step_7_execute_plan" in timeouts
        # Execute plan should have longer timeout
        assert timeouts["step_7_execute_plan"] > timeouts["step_1_create_intent"]
