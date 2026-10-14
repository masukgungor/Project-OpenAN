from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime, timezone


class Region(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    CENTRAL = "central"


class EnergySavingTarget(str, Enum):
    MAXIMIZED_SAVING = "maximized_saving"
    PROACTIVE_SAVING = "proactive_saving"
    BALANCED = "balanced"
    EXPERIENCE_FIRST = "experience_first"


class SafeguardTarget(BaseModel):
    min_throughput_mbps: float = Field(default=10.0, description="Minimum throughput in Mbps")
    max_latency_ms: float = Field(default=50.0, description="Maximum latency in ms")
    coverage_maintain: bool = Field(default=True, description="Maintain coverage")


class EnergySavingIntent(BaseModel):
    intent_id: str = Field(..., description="Unique intent identifier")
    region: Region = Field(..., description="Target region")
    energy_target: EnergySavingTarget = Field(..., description="Energy saving target level")
    safeguard: SafeguardTarget = Field(..., description="User experience safeguards")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    validity_period: Dict[str, str] = Field(
        default={"start": "00:00", "end": "23:59"},
        description="Intent validity time window"
    )
    priority: int = Field(default=5, ge=1, le=10, description="Intent priority 1-10")
    cluster_id: Optional[str] = Field(None, description="Target cluster ID for optimization")
    status: str = Field(default="pending", description="Intent status: pending, in_progress, completed, failed")
    source: str = Field(default="form", description="Intent creation source: form or llm")


class EnergySavingIntentCreate(BaseModel):
    region: Region = Field(..., description="Target region")
    energy_target: EnergySavingTarget = Field(..., description="Energy saving target level")
    safeguard: SafeguardTarget = Field(default_factory=SafeguardTarget, description="User experience safeguards")
    cluster_id: Optional[str] = Field(None, description="Target cluster ID for optimization")
    priority: int = Field(default=5, ge=1, le=10, description="Intent priority 1-10")
    validity_period: Dict[str, str] = Field(
        default={"start": "00:00", "end": "23:59"},
        description="Intent validity time window"
    )
    source: str = Field(default="form", description="Intent creation source: form or llm")


class EnergySavingIntentResponse(BaseModel):
    intent_id: str
    region: Region
    energy_target: EnergySavingTarget
    safeguard: SafeguardTarget
    created_at: datetime
    validity_period: Dict[str, str]
    priority: int
    cluster_id: Optional[str]
    status: str
    source: str = "form"
