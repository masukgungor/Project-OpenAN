import pytest
from orchestrate.energy_saving.agents import EnergyAgent, get_energy_agent
from orchestrate.energy_saving.models import (
    Region,
    EnergySavingTarget,
    SafeguardTarget,
    EnergySavingIntentCreate,
)


@pytest.fixture
def energy_agent():
    """Get fresh Energy Agent instance for each test."""
    agent = get_energy_agent()
    # Clear any existing intents
    agent._intents.clear()
    return agent


class TestEnergyAgentIntent:
    """Test Energy Agent intent management."""

    def test_create_intent(self, energy_agent):
        intent_create = EnergySavingIntentCreate(
            region=Region.NORTH,
            energy_target=EnergySavingTarget.MAXIMIZED_SAVING,
        )
        intent = energy_agent.create_intent(intent_create)
        
        assert intent.intent_id is not None
        assert intent.region == Region.NORTH
        assert intent.energy_target == EnergySavingTarget.MAXIMIZED_SAVING
        assert intent.status == "pending"

    def test_get_intent(self, energy_agent):
        intent_create = EnergySavingIntentCreate(
            region=Region.SOUTH,
            energy_target=EnergySavingTarget.BALANCED,
        )
        created = energy_agent.create_intent(intent_create)
        
        retrieved = energy_agent.get_intent(created.intent_id)
        
        assert retrieved is not None
        assert retrieved.intent_id == created.intent_id
        assert retrieved.region == Region.SOUTH

    def test_get_intent_not_found(self, energy_agent):
        result = energy_agent.get_intent("NON-EXISTENT")
        assert result is None

    def test_list_intents(self, energy_agent):
        # Create multiple intents
        for region in [Region.NORTH, Region.SOUTH, Region.EAST]:
            energy_agent.create_intent(
                EnergySavingIntentCreate(
                    region=region,
                    energy_target=EnergySavingTarget.MAXIMIZED_SAVING,
                )
            )
        
        intents = energy_agent.list_intents()
        assert len(intents) == 3

    def test_list_intents_filtered_by_region(self, energy_agent):
        energy_agent.create_intent(
            EnergySavingIntentCreate(region=Region.NORTH, energy_target=EnergySavingTarget.MAXIMIZED_SAVING)
        )
        energy_agent.create_intent(
            EnergySavingIntentCreate(region=Region.SOUTH, energy_target=EnergySavingTarget.MAXIMIZED_SAVING)
        )
        
        north_intents = energy_agent.list_intents(region="north")
        assert len(north_intents) == 1
        assert north_intents[0].region == Region.NORTH


class TestEnergyAgentElectricityPrice:
    """Test Energy Agent electricity price functionality."""

    def test_get_electricity_price(self, energy_agent):
        response = energy_agent.get_electricity_price("north")
        
        assert response.region == "north"
        assert len(response.time_slots) > 0
        assert len(response.bands) == 5
        assert response.current_price > 0

    def test_price_caching(self, energy_agent):
        # First call
        response1 = energy_agent.get_electricity_price("north")
        # Second call should use cache
        response2 = energy_agent.get_electricity_price("north")
        
        assert response1.region == response2.region
        assert len(response1.time_slots) == len(response2.time_slots)


class TestEnergyAgentClassification:
    """Test Energy Agent site classification functionality."""

    def test_classify_site(self, energy_agent):
        classification = energy_agent.classify_site("SITE001", 2.5)
        
        assert classification.site_id == "SITE001"
        assert classification.current_band == 3  # 2.0-2.99KW → Band 3
        assert classification.classification in ["downgrade", "upgrade", "stable_maintained"]
        assert 0.0 <= classification.confidence_score <= 1.0

    def test_classify_site_band_1(self, energy_agent):
        classification = energy_agent.classify_site("SITE002", 0.5)
        assert classification.current_band == 1

    def test_classify_site_band_5(self, energy_agent):
        classification = energy_agent.classify_site("SITE003", 4.5)
        assert classification.current_band == 5

    def test_classify_cluster(self, energy_agent):
        sites = [
            {"site_id": "SITE001", "current_power_kw": 2.5},
            {"site_id": "SITE002", "current_power_kw": 1.5},
            {"site_id": "SITE003", "current_power_kw": 3.5},
        ]
        
        result = energy_agent.classify_cluster("CLUSTER001", sites)
        
        assert result.cluster_id == "CLUSTER001"
        assert result.total_sites == 3
        assert len(result.downgrade_sites) + len(result.upgrade_sites) + len(result.stable_sites) == 3


class TestEnergyAgentOptimization:
    """Test Energy Agent cluster optimization functionality."""

    def test_optimize_cluster(self, energy_agent):
        # First classify cluster
        sites = [
            {"site_id": "SITE001", "current_power_kw": 2.5},
            {"site_id": "SITE002", "current_power_kw": 1.5},
            {"site_id": "SITE003", "current_power_kw": 3.5},
        ]
        classification = energy_agent.classify_cluster("CLUSTER001", sites)
        
        # Then optimize
        plan = energy_agent.optimize_cluster("CLUSTER001", classification)
        
        assert plan.plan_id is not None
        assert plan.cluster_id == "CLUSTER001"
        assert plan.status == "pending"
        assert plan.expected_cost_reduction_percent >= 0

    def test_negotiate_with_mae(self, energy_agent):
        # Create an intent first
        intent_create = EnergySavingIntentCreate(
            region=Region.NORTH,
            energy_target=EnergySavingTarget.MAXIMIZED_SAVING,
        )
        intent = energy_agent.create_intent(intent_create)
        
        # Create a mock plan
        from orchestrate.energy_saving.models import ClusterOptimizationPlan
        mock_plan = ClusterOptimizationPlan(
            plan_id="PLAN-TEST",
            cluster_id="CLUSTER001",
            expected_cost_reduction_percent=10.0,
            risk_assessment={"coverage_risk": 0.1, "experience_risk": 0.05},
        )
        
        response = energy_agent.negotiate_with_mae(mock_plan, intent)
        
        assert response.negotiation_id is not None
        assert response.achievable is not None
        assert isinstance(response.constraints, dict)


class TestEnergyAgentAgentCard:
    """Test Energy Agent agent card."""

    def test_get_agent_card(self, energy_agent):
        card = energy_agent.get_agent_card()
        
        assert card["name"] == "energy-agent"
        assert card["version"] == "1.0.0"
        assert "capabilities" in card
        assert "skills" in card
        assert len(card["capabilities"]) > 0
        assert len(card["skills"]) > 0
