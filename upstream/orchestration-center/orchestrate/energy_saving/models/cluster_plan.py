from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class TrafficMigrationAction(BaseModel):
    site_id: str = Field(..., description="Site to perform action on")
    action_type: str = Field(..., description="Action type: decrease_power, increase_tilt, ho_out, ho_in, increase_power, decrease_tilt")
    parameter_value: float = Field(..., description="Parameter value (e.g., power dB, tilt degrees)")
    target_site_ids: Optional[List[str]] = Field(None, description="For HO actions, target sites")
    execution_window: str = Field(..., description="Time window for execution e.g., '23~5'")
    priority: int = Field(default=5, ge=1, le=10)


class ClusterOptimizationPlan(BaseModel):
    plan_id: str = Field(..., description="Unique plan identifier")
    cluster_id: str = Field(..., description="Cluster identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Plan creation timestamp")
    optimization_horizon: str = Field(default="monthly", description="Planning horizon e.g., 'monthly'")
    migration_out_actions: List[TrafficMigrationAction] = Field(default_factory=list, description="Actions for downgrade/upgrade sites")
    migration_in_actions: List[TrafficMigrationAction] = Field(default_factory=list, description="Actions for stable-maintained sites")
    expected_cost_reduction_percent: float = Field(..., description="Expected electricity cost reduction percentage")
    risk_assessment: Dict[str, float] = Field(..., description="Risk metrics: coverage_risk, experience_risk")
    status: str = Field(default="pending", description="Plan status: pending, approved, executing, completed, failed")


class NegotiationRequest(BaseModel):
    intent_id: str = Field(..., description="Intent identifier")
    region: str = Field(..., description="Region")
    target: str = Field(..., description="Energy saving target")
    safeguard: Dict = Field(..., description="Safeguard parameters")
    cluster_plan: Dict = Field(..., description="Cluster optimization plan summary")
    time_period_strategies: List[Dict] = Field(..., description="Time period strategies")


class NegotiationResponse(BaseModel):
    achievable: bool = Field(..., description="Whether target is achievable")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Constraints from MAE")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors identified by MAE")
    negotiation_id: str = Field(..., description="Unique negotiation identifier")
