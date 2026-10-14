from pydantic import BaseModel, Field
from typing import Optional, Dict
from enum import Enum


class TimePeriod(str, Enum):
    NIGHT_LOW_DEMAND = "23~5"
    MORNING_LOW = "6~9"
    DAYTIME_HIGH = "10~15"
    EVENING_MEDIUM = "16~17"
    EVENING_HIGH = "18~22"
    LATE_NIGHT = "22~23"


class StrategyType(str, Enum):
    MAXIMIZED_ENERGY_SAVING = "maximized_energy_saving"
    BALANCED_SAVING = "balanced_saving"
    EXPERIENCE_FIRST = "experience_first"
    PROACTIVE_SAVING = "proactive_saving"


class TimePeriodStrategy(BaseModel):
    time_period: TimePeriod = Field(..., description="Time period")
    strategy: StrategyType = Field(..., description="Strategy for this period")
    target_throughput_mbps: Optional[float] = Field(None, description="Target throughput if applicable")
    rate_guarantee: bool = Field(default=False, description="Whether rate is guaranteed")
    no_degrade: bool = Field(default=False, description="Whether experience can be degraded")
    notes: Optional[str] = Field(None, description="Additional notes")


# Default strategy mapping from PPTX
DEFAULT_TIME_STRATEGIES: Dict[TimePeriod, TimePeriodStrategy] = {
    TimePeriod.NIGHT_LOW_DEMAND: TimePeriodStrategy(
        time_period=TimePeriod.NIGHT_LOW_DEMAND,
        strategy=StrategyType.MAXIMIZED_ENERGY_SAVING,
        rate_guarantee=False,
        notes="Maximized energy saving, no rate guarantee"
    ),
    TimePeriod.MORNING_LOW: TimePeriodStrategy(
        time_period=TimePeriod.MORNING_LOW,
        strategy=StrategyType.PROACTIVE_SAVING,
        target_throughput_mbps=10.0,
        rate_guarantee=True,
        notes="Proactive energy saving, 10Mbps target"
    ),
    TimePeriod.DAYTIME_HIGH: TimePeriodStrategy(
        time_period=TimePeriod.DAYTIME_HIGH,
        strategy=StrategyType.EXPERIENCE_FIRST,
        no_degrade=True,
        notes="Experience first, no degrade"
    ),
    TimePeriod.EVENING_MEDIUM: TimePeriodStrategy(
        time_period=TimePeriod.EVENING_MEDIUM,
        strategy=StrategyType.PROACTIVE_SAVING,
        target_throughput_mbps=10.0,
        rate_guarantee=True,
        notes="Proactive energy saving, 10Mbps target"
    ),
    TimePeriod.EVENING_HIGH: TimePeriodStrategy(
        time_period=TimePeriod.EVENING_HIGH,
        strategy=StrategyType.EXPERIENCE_FIRST,
        no_degrade=True,
        notes="Experience first, no degrade"
    ),
    TimePeriod.LATE_NIGHT: TimePeriodStrategy(
        time_period=TimePeriod.LATE_NIGHT,
        strategy=StrategyType.BALANCED_SAVING,
        rate_guarantee=True,
        notes="Balanced strategy"
    ),
}


def get_strategy_for_hour(hour: int) -> TimePeriodStrategy:
    """Get strategy for a given hour (0-23)."""
    if 23 <= hour or hour < 5:
        return DEFAULT_TIME_STRATEGIES[TimePeriod.NIGHT_LOW_DEMAND]
    elif 6 <= hour < 9:
        return DEFAULT_TIME_STRATEGIES[TimePeriod.MORNING_LOW]
    elif 10 <= hour < 15:
        return DEFAULT_TIME_STRATEGIES[TimePeriod.DAYTIME_HIGH]
    elif 16 <= hour < 17:
        return DEFAULT_TIME_STRATEGIES[TimePeriod.EVENING_MEDIUM]
    elif 18 <= hour < 22:
        return DEFAULT_TIME_STRATEGIES[TimePeriod.EVENING_HIGH]
    else:  # 22-23
        return DEFAULT_TIME_STRATEGIES[TimePeriod.LATE_NIGHT]


def get_time_period_for_hour(hour: int) -> TimePeriod:
    """Get time period enum for a given hour."""
    if 23 <= hour or hour < 5:
        return TimePeriod.NIGHT_LOW_DEMAND
    elif 6 <= hour < 9:
        return TimePeriod.MORNING_LOW
    elif 10 <= hour < 15:
        return TimePeriod.DAYTIME_HIGH
    elif 16 <= hour < 17:
        return TimePeriod.EVENING_MEDIUM
    elif 18 <= hour < 22:
        return TimePeriod.EVENING_HIGH
    else:
        return TimePeriod.LATE_NIGHT
