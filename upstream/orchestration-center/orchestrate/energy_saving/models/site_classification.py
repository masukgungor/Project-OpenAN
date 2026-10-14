from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class SiteClass(str, Enum):
    DOWNGRADE = "downgrade"
    UPGRADE = "upgrade"
    STABLE_MAINTAINED = "stable_maintained"


class SiteClassification(BaseModel):
    site_id: str = Field(..., description="Unique site identifier")
    current_band: int = Field(..., ge=1, le=5, description="Current power band (1-5)")
    classified_band: int = Field(..., ge=1, le=5, description="Target power band (1-5)")
    classification: SiteClass = Field(..., description="Site classification")
    classification_reason: str = Field(..., description="Reason for classification")
    energy_saving_potential_kw: float = Field(..., description="Potential energy saving in KW")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    traffic_impact: Optional[Dict[str, float]] = Field(None, description="Expected traffic impact metrics")


class ClusterClassificationResult(BaseModel):
    cluster_id: str = Field(..., description="Cluster identifier")
    classified_at: datetime = Field(default_factory=lambda: datetime.now(), description="Classification timestamp")
    total_sites: int = Field(..., description="Total sites in cluster")
    downgrade_sites: List[SiteClassification] = Field(default_factory=list, description="Sites that can reduce power")
    upgrade_sites: List[SiteClassification] = Field(default_factory=list, description="Sites that need more power")
    stable_sites: List[SiteClassification] = Field(default_factory=list, description="Sites to maintain current state")
    estimated_total_saving_kw: float = Field(..., description="Estimated total saving in KW")


def classify_band(power_kw: float) -> int:
    """Classify a site into power band based on current power consumption."""
    if power_kw < 1.0:
        return 1
    elif power_kw < 2.0:
        return 2
    elif power_kw < 3.0:
        return 3
    elif power_kw < 4.0:
        return 4
    else:
        return 5


def classify_site(current_band: int, target_band: int) -> SiteClass:
    """Classify a site based on current vs target band."""
    if current_band > target_band:
        return SiteClass.DOWNGRADE
    elif current_band < target_band:
        return SiteClass.UPGRADE
    else:
        return SiteClass.STABLE_MAINTAINED


def calculate_energy_saving(current_band: int, target_band: int, price_bands: List[Dict]) -> float:
    """Calculate potential energy saving between bands."""
    current_cost = 0.0
    target_cost = 0.0
    
    for band in price_bands:
        if band["band_no"] == current_band:
            current_cost = band["total_ghs"]
        if band["band_no"] == target_band:
            target_cost = band["total_ghs"]
    
    return current_cost - target_cost
