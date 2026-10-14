import uuid
import logging
from datetime import datetime, timezone
from typing import List

from orchestrate.energy_saving.models import (
    ClusterClassificationResult,
    ClusterOptimizationPlan,
    TrafficMigrationAction,
    EnergySavingTarget,
)
from orchestrate.energy_saving.models.time_strategy import (
    get_strategy_for_hour,
    get_time_period_for_hour,
    StrategyType,
)

logger = logging.getLogger(__name__)


class ClusterOptimizationService:
    """Service for cluster-level electricity cost optimization."""

    def __init__(self):
        pass

    def create_optimization_plan(
        self,
        cluster_id: str,
        classification_result: ClusterClassificationResult,
        target: str = "maximized_saving",
    ) -> ClusterOptimizationPlan:
        """Generate cluster optimization plan based on classification."""
        plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"
        
        # Get current time period strategy
        current_hour = datetime.now(timezone.utc).hour
        time_strategy = get_strategy_for_hour(current_hour)
        time_period = get_time_period_for_hour(current_hour)
        
        migration_out = []
        migration_in = []

        # Generate migration actions for DOWNGRADE sites
        for site in classification_result.downgrade_sites:
            action = self._create_downgrade_action(site.site_id, target, time_strategy)
            migration_out.append(action)

        # Generate migration actions for UPGRADE sites
        for site in classification_result.upgrade_sites:
            action = self._create_upgrade_action(site.site_id, time_strategy)
            migration_out.append(action)

        # Stable sites can accept migrated traffic
        for site in classification_result.stable_sites:
            action = TrafficMigrationAction(
                site_id=site.site_id,
                action_type="ho_in",
                parameter_value=0.0,
                execution_window=time_period.value,
                priority=3,
            )
            migration_in.append(action)

        # Calculate expected cost reduction
        expected_reduction = self._calculate_expected_reduction(
            classification_result, target, time_strategy
        )

        # Risk assessment
        risk_assessment = self._assess_risk(
            classification_result, expected_reduction, time_strategy
        )

        logger.info(
            f"Created optimization plan {plan_id} for cluster {cluster_id}: "
            f"time_period={time_period.value}, strategy={time_strategy.strategy.value}, "
            f"reduction={expected_reduction}%, risk={risk_assessment}"
        )

        return ClusterOptimizationPlan(
            plan_id=plan_id,
            cluster_id=cluster_id,
            optimization_horizon="monthly",
            migration_out_actions=migration_out,
            migration_in_actions=migration_in,
            expected_cost_reduction_percent=expected_reduction,
            risk_assessment=risk_assessment,
            status="pending",
        )

    def _create_downgrade_action(self, site_id: str, target: str, time_strategy) -> TrafficMigrationAction:
        """Create migration action for DOWNGRADE site based on time-period strategy."""
        execution_window = ""
        priority = 5
        
        # Determine execution window based on strategy
        if time_strategy.strategy == StrategyType.MAXIMIZED_ENERGY_SAVING:
            execution_window = "23~5"
            priority = 5
        elif time_strategy.strategy == StrategyType.PROACTIVE_SAVING:
            execution_window = "6~9"
            priority = 4
        elif time_strategy.strategy == StrategyType.EXPERIENCE_FIRST:
            execution_window = "10~15"
            priority = 3
        
        # Choose action type based on target and strategy
        if target == EnergySavingTarget.MAXIMIZED_SAVING.value:
            action_type = "decrease_power"
            parameter_value = 3.0
        elif target == EnergySavingTarget.PROACTIVE_SAVING.value:
            action_type = "increase_tilt"
            parameter_value = 2.5
        elif target == EnergySavingTarget.BALANCED.value:
            action_type = "increase_tilt"
            parameter_value = 2.0
        else:
            action_type = "ho_out"
            parameter_value = 10.0
        
        return TrafficMigrationAction(
            site_id=site_id,
            action_type=action_type,
            parameter_value=parameter_value,
            execution_window=execution_window,
            priority=priority,
        )

    def _create_upgrade_action(self, site_id: str, time_strategy) -> TrafficMigrationAction:
        """Create migration action for UPGRADE site based on time-period strategy."""
        execution_window = ""
        
        if time_strategy.strategy == StrategyType.MAXIMIZED_ENERGY_SAVING:
            execution_window = "23~5"
        elif time_strategy.strategy == StrategyType.PROACTIVE_SAVING:
            execution_window = "6~9"
        elif time_strategy.strategy == StrategyType.EXPERIENCE_FIRST:
            execution_window = "10~15"
        
        return TrafficMigrationAction(
            site_id=site_id,
            action_type="increase_power",
            parameter_value=2.0,
            execution_window=execution_window,
            priority=5,
        )

    def _calculate_expected_reduction(
        self,
        classification_result: ClusterClassificationResult,
        target: str,
        time_strategy,
    ) -> float:
        """Calculate expected cost reduction percentage based on time-period strategy."""
        downgrade_count = len(classification_result.downgrade_sites)
        total_sites = classification_result.total_sites
        
        if total_sites == 0:
            return 0.0
        
        # Base reduction per downgrade site
        base_reduction_per_site = 1.5  # percent
        
        # Adjust based on target
        if target == EnergySavingTarget.MAXIMIZED_SAVING.value:
            target_multiplier = 1.5
        elif target == EnergySavingTarget.PROACTIVE_SAVING.value:
            target_multiplier = 1.2
        elif target == EnergySavingTarget.BALANCED.value:
            target_multiplier = 1.0
        else:
            target_multiplier = 0.5
        
        # Adjust based on time-period strategy
        if time_strategy.strategy == StrategyType.MAXIMIZED_ENERGY_SAVING:
            strategy_multiplier = 1.5
        elif time_strategy.strategy == StrategyType.PROACTIVE_SAVING:
            strategy_multiplier = 1.2
        elif time_strategy.strategy == StrategyType.EXPERIENCE_FIRST:
            strategy_multiplier = 0.5
        else:
            strategy_multiplier = 1.0
        
        expected = downgrade_count * base_reduction_per_site * target_multiplier * strategy_multiplier
        
        # Cap at reasonable maximum
        return min(expected, 25.0)

    def _assess_risk(
        self,
        classification_result: ClusterClassificationResult,
        expected_reduction: float,
        time_strategy,
    ) -> dict:
        """Assess risk of the optimization plan based on time-period strategy."""
        total_sites = classification_result.total_sites
        if total_sites == 0:
            return {"coverage_risk": 0.0, "experience_risk": 0.0}
        
        downgrade_ratio = len(classification_result.downgrade_sites) / total_sites
        upgrade_ratio = len(classification_result.upgrade_sites) / total_sites
        
        # Coverage risk: higher when many sites are being downgraded
        coverage_risk = downgrade_ratio * 0.2
        
        # Experience risk: depends on target type and site ratios
        experience_risk = (downgrade_ratio * 0.1) + (upgrade_ratio * 0.05)
        
        # Experience-first periods have higher experience risk tolerance
        if time_strategy.strategy == StrategyType.EXPERIENCE_FIRST:
            experience_risk *= 1.2
        elif time_strategy.strategy == StrategyType.MAXIMIZED_ENERGY_SAVING:
            coverage_risk *= 1.1
        
        # Add risk for high expected reduction
        if expected_reduction > 15:
            coverage_risk += 0.1
            experience_risk += 0.05
        
        return {
            "coverage_risk": round(min(coverage_risk, 1.0), 3),
            "experience_risk": round(min(experience_risk, 1.0), 3),
        }

    def validate_plan(self, plan: ClusterOptimizationPlan) -> bool:
        """Validate optimization plan before execution."""
        # Check if plan has actions
        if not plan.migration_out_actions and not plan.migration_in_actions:
            logger.warning(f"Plan {plan.plan_id} has no actions")
            return False
        
        # Check risk levels
        if plan.risk_assessment["coverage_risk"] > 0.5:
            logger.warning(
                f"Plan {plan.plan_id} has high coverage risk: "
                f"{plan.risk_assessment['coverage_risk']}"
            )
            return False
        
        return True


# Singleton instance
_cluster_optimization_service: ClusterOptimizationService = None


def get_cluster_optimization_service() -> ClusterOptimizationService:
    """Get singleton ClusterOptimizationService instance."""
    global _cluster_optimization_service
    if _cluster_optimization_service is None:
        _cluster_optimization_service = ClusterOptimizationService()
    return _cluster_optimization_service
