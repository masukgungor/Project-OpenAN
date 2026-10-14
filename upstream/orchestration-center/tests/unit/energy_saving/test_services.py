import pytest
from orchestrate.energy_saving.services import (
    get_electricity_price_service,
    get_band_classification_service,
    get_cluster_optimization_service,
)
from orchestrate.energy_saving.models import (
    SiteClass,
    Region,
    EnergySavingTarget,
    SafeguardTarget,
)


class TestElectricityPriceService:
    """Test Electricity Price Service."""

    def test_get_price(self):
        service = get_electricity_price_service()
        response = service.get_price("north")
        
        assert response.region == "north"
        assert len(response.time_slots) == 6
        assert len(response.bands) == 5

    def test_get_bands(self):
        service = get_electricity_price_service()
        bands = service.get_bands()
        
        assert len(bands) == 5
        assert bands[0].band_no == 1
        assert bands[4].band_no == 5

    def test_clear_cache(self):
        service = get_electricity_price_service()
        service.get_price("north")  # Populate cache
        service.clear_cache("north")  # Clear
        # Should still work after clear
        response = service.get_price("north")
        assert response.region == "north"


class TestBandClassificationService:
    """Test Band Classification Service."""

    def test_classify_site(self):
        service = get_band_classification_service()
        result = service.classify_site("SITE001", 2.5)
        
        assert result.site_id == "SITE001"
        assert result.current_band == 3
        assert result.classification in [SiteClass.DOWNGRADE, SiteClass.UPGRADE, SiteClass.STABLE_MAINTAINED]

    def test_classify_cluster(self):
        service = get_band_classification_service()
        sites = [
            {"site_id": "SITE001", "current_power_kw": 0.5},
            {"site_id": "SITE002", "current_power_kw": 1.5},
            {"site_id": "SITE003", "current_power_kw": 2.5},
            {"site_id": "SITE004", "current_power_kw": 3.5},
            {"site_id": "SITE005", "current_power_kw": 4.5},
        ]
        result = service.classify_cluster("CLUSTER001", sites)
        
        assert result.cluster_id == "CLUSTER001"
        assert result.total_sites == 5
        assert len(result.downgrade_sites) + len(result.upgrade_sites) + len(result.stable_sites) == 5

    def test_get_band_info(self):
        service = get_band_classification_service()
        band = service.get_band_info(1)
        
        assert band.band_no == 1
        assert band.kw_min == 0.0
        assert band.kw_max == 0.99


class TestClusterOptimizationService:
    """Test Cluster Optimization Service."""

    def test_create_optimization_plan(self):
        from orchestrate.energy_saving.models import ClusterClassificationResult, SiteClassification
        
        service = get_cluster_optimization_service()
        
        # Create mock classification result
        classification = ClusterClassificationResult(
            cluster_id="CLUSTER001",
            total_sites=3,
            downgrade_sites=[
                SiteClassification(
                    site_id="SITE001",
                    current_band=3,
                    classified_band=2,
                    classification=SiteClass.DOWNGRADE,
                    classification_reason="test",
                    energy_saving_potential_kw=1.5,
                    confidence_score=0.9,
                )
            ],
            upgrade_sites=[],
            stable_sites=[
                SiteClassification(
                    site_id="SITE002",
                    current_band=2,
                    classified_band=2,
                    classification=SiteClass.STABLE_MAINTAINED,
                    classification_reason="test",
                    energy_saving_potential_kw=0.0,
                    confidence_score=0.9,
                )
            ],
            estimated_total_saving_kw=1.5,
        )
        
        plan = service.create_optimization_plan("CLUSTER001", classification)
        
        assert plan.plan_id is not None
        assert plan.cluster_id == "CLUSTER001"
        assert len(plan.migration_out_actions) > 0
        assert plan.expected_cost_reduction_percent > 0

    def test_validate_plan(self):
        from orchestrate.energy_saving.models import ClusterOptimizationPlan, TrafficMigrationAction
        
        service = get_cluster_optimization_service()
        
        # Valid plan
        valid_plan = ClusterOptimizationPlan(
            plan_id="PLAN001",
            cluster_id="CLUSTER001",
            migration_out_actions=[
                TrafficMigrationAction(
                    site_id="SITE001",
                    action_type="decrease_power",
                    parameter_value=3.0,
                    execution_window="23~5",
                )
            ],
            expected_cost_reduction_percent=10.0,
            risk_assessment={"coverage_risk": 0.1, "experience_risk": 0.05},
        )
        
        assert service.validate_plan(valid_plan) is True

    def test_validate_plan_high_risk(self):
        from orchestrate.energy_saving.models import ClusterOptimizationPlan, TrafficMigrationAction
        
        service = get_cluster_optimization_service()
        
        # High risk plan
        high_risk_plan = ClusterOptimizationPlan(
            plan_id="PLAN002",
            cluster_id="CLUSTER001",
            migration_out_actions=[
                TrafficMigrationAction(
                    site_id="SITE001",
                    action_type="decrease_power",
                    parameter_value=3.0,
                    execution_window="23~5",
                )
            ],
            expected_cost_reduction_percent=10.0,
            risk_assessment={"coverage_risk": 0.6, "experience_risk": 0.05},  # High coverage risk
        )
        
        assert service.validate_plan(high_risk_plan) is False
