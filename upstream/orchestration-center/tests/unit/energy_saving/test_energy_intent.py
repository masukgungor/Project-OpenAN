import pytest
from orchestrate.energy_saving.models.energy_intent import (
    Region,
    EnergySavingTarget,
    SafeguardTarget,
    EnergySavingIntent,
    EnergySavingIntentCreate,
)


class TestRegion:
    def test_region_values(self):
        assert Region.NORTH.value == "north"
        assert Region.SOUTH.value == "south"
        assert Region.EAST.value == "east"
        assert Region.WEST.value == "west"
        assert Region.CENTRAL.value == "central"

    def test_region_count(self):
        assert len(Region) == 5


class TestEnergySavingTarget:
    def test_target_values(self):
        assert EnergySavingTarget.MAXIMIZED_SAVING.value == "maximized_saving"
        assert EnergySavingTarget.BALANCED.value == "balanced"
        assert EnergySavingTarget.EXPERIENCE_FIRST.value == "experience_first"

    def test_target_count(self):
        assert len(EnergySavingTarget) == 3


class TestSafeguardTarget:
    def test_default_values(self):
        safeguard = SafeguardTarget()
        assert safeguard.min_throughput_mbps == 10.0
        assert safeguard.max_latency_ms == 50.0
        assert safeguard.coverage_maintain is True

    def test_custom_values(self):
        safeguard = SafeguardTarget(
            min_throughput_mbps=15.0,
            max_latency_ms=30.0,
            coverage_maintain=False
        )
        assert safeguard.min_throughput_mbps == 15.0
        assert safeguard.max_latency_ms == 30.0
        assert safeguard.coverage_maintain is False


class TestEnergySavingIntent:
    def test_create_intent_with_required_fields(self):
        intent = EnergySavingIntent(
            intent_id="TEST-001",
            region=Region.NORTH,
            energy_target=EnergySavingTarget.MAXIMIZED_SAVING,
            safeguard=SafeguardTarget()
        )
        assert intent.intent_id == "TEST-001"
        assert intent.region == Region.NORTH
        assert intent.energy_target == EnergySavingTarget.MAXIMIZED_SAVING
        assert intent.priority == 5  # default
        assert intent.status == "pending"  # default

    def test_create_intent_with_all_fields(self):
        intent = EnergySavingIntent(
            intent_id="TEST-002",
            region=Region.SOUTH,
            energy_target=EnergySavingTarget.EXPERIENCE_FIRST,
            safeguard=SafeguardTarget(min_throughput_mbps=20.0),
            cluster_id="CLUSTER-001",
            priority=8,
            validity_period={"start": "06:00", "end": "22:00"}
        )
        assert intent.intent_id == "TEST-002"
        assert intent.region == Region.SOUTH
        assert intent.energy_target == EnergySavingTarget.EXPERIENCE_FIRST
        assert intent.safeguard.min_throughput_mbps == 20.0
        assert intent.cluster_id == "CLUSTER-001"
        assert intent.priority == 8
        assert intent.validity_period == {"start": "06:00", "end": "22:00"}

    def test_intent_id_is_required(self):
        with pytest.raises(Exception):  # ValidationError
            EnergySavingIntent(
                region=Region.NORTH,
                energy_target=EnergySavingTarget.MAXIMIZED_SAVING,
                safeguard=SafeguardTarget()
            )

    def test_region_is_required(self):
        with pytest.raises(Exception):  # ValidationError
            EnergySavingIntent(
                intent_id="TEST-003",
                energy_target=EnergySavingTarget.MAXIMIZED_SAVING,
                safeguard=SafeguardTarget()
            )

    def test_priority_validation(self):
        # priority > 10 should fail
        with pytest.raises(Exception):
            EnergySavingIntent(
                intent_id="TEST-004",
                region=Region.NORTH,
                energy_target=EnergySavingTarget.MAXIMIZED_SAVING,
                safeguard=SafeguardTarget(),
                priority=15
            )

        # priority < 1 should fail
        with pytest.raises(Exception):
            EnergySavingIntent(
                intent_id="TEST-005",
                region=Region.NORTH,
                energy_target=EnergySavingTarget.MAXIMIZED_SAVING,
                safeguard=SafeguardTarget(),
                priority=0
            )


class TestEnergySavingIntentCreate:
    def test_create_intent_create_model(self):
        intent_create = EnergySavingIntentCreate(
            region=Region.EAST,
            energy_target=EnergySavingTarget.BALANCED
        )
        assert intent_create.region == Region.EAST
        assert intent_create.energy_target == EnergySavingTarget.BALANCED
        assert intent_create.safeguard.min_throughput_mbps == 10.0  # default

    def test_create_model_with_custom_safeguard(self):
        intent_create = EnergySavingIntentCreate(
            region=Region.WEST,
            energy_target=EnergySavingTarget.EXPERIENCE_FIRST,
            safeguard=SafeguardTarget(coverage_maintain=False)
        )
        assert intent_create.safeguard.coverage_maintain is False
