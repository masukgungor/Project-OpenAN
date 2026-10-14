import pytest
from orchestrate.energy_saving.models import (
    TimePeriod,
    StrategyType,
    TimePeriodStrategy,
    DEFAULT_TIME_STRATEGIES,
    get_strategy_for_hour,
    get_time_period_for_hour,
    classify_band,
    classify_site,
    SiteClass,
)


class TestTimePeriod:
    def test_time_period_values(self):
        assert TimePeriod.NIGHT_LOW_DEMAND.value == "23~5"
        assert TimePeriod.MORNING_LOW.value == "6~9"
        assert TimePeriod.DAYTIME_HIGH.value == "10~15"

    def test_time_period_count(self):
        assert len(TimePeriod) == 6


class TestStrategyType:
    def test_strategy_values(self):
        assert StrategyType.MAXIMIZED_ENERGY_SAVING.value == "maximized_energy_saving"
        assert StrategyType.PROACTIVE_SAVING.value == "proactive_saving"
        assert StrategyType.EXPERIENCE_FIRST.value == "experience_first"


class TestGetStrategyForHour:
    def test_night_hours(self):
        strategy = get_strategy_for_hour(0)
        assert strategy.strategy == StrategyType.MAXIMIZED_ENERGY_SAVING
        assert strategy.rate_guarantee is False

    def test_morning_hours(self):
        strategy = get_strategy_for_hour(7)
        assert strategy.strategy == StrategyType.PROACTIVE_SAVING
        assert strategy.target_throughput_mbps == 10.0
        assert strategy.rate_guarantee is True

    def test_daytime_hours(self):
        strategy = get_strategy_for_hour(12)
        assert strategy.strategy == StrategyType.EXPERIENCE_FIRST
        assert strategy.no_degrade is True

    def test_evening_hours(self):
        strategy = get_strategy_for_hour(19)
        assert strategy.strategy == StrategyType.EXPERIENCE_FIRST

    def test_late_night(self):
        strategy = get_strategy_for_hour(22)
        assert strategy.strategy == StrategyType.BALANCED_SAVING


class TestGetTimePeriodForHour:
    def test_hour_mappings(self):
        assert get_time_period_for_hour(0) == TimePeriod.NIGHT_LOW_DEMAND
        assert get_time_period_for_hour(7) == TimePeriod.MORNING_LOW
        assert get_time_period_for_hour(12) == TimePeriod.DAYTIME_HIGH
        assert get_time_period_for_hour(16) == TimePeriod.EVENING_MEDIUM
        assert get_time_period_for_hour(19) == TimePeriod.EVENING_HIGH
        assert get_time_period_for_hour(22) == TimePeriod.LATE_NIGHT


class TestClassifyBand:
    def test_band_1(self):
        assert classify_band(0.5) == 1
        assert classify_band(0.99) == 1

    def test_band_2(self):
        assert classify_band(1.0) == 2
        assert classify_band(1.5) == 2
        assert classify_band(1.99) == 2

    def test_band_3(self):
        assert classify_band(2.0) == 3
        assert classify_band(2.5) == 3
        assert classify_band(2.99) == 3

    def test_band_4(self):
        assert classify_band(3.0) == 4
        assert classify_band(3.5) == 4
        assert classify_band(3.99) == 4

    def test_band_5(self):
        assert classify_band(4.0) == 5
        assert classify_band(5.0) == 5


class TestClassifySite:
    def test_downgrade(self):
        result = classify_site(current_band=4, target_band=2)
        assert result == SiteClass.DOWNGRADE

    def test_upgrade(self):
        result = classify_site(current_band=2, target_band=4)
        assert result == SiteClass.UPGRADE

    def test_stable(self):
        result = classify_site(current_band=3, target_band=3)
        assert result == SiteClass.STABLE_MAINTAINED
