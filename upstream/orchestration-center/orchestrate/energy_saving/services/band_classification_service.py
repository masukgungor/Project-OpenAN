import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from orchestrate.energy_saving.models import (
    PriceBand,
    SiteClassification,
    SiteClass,
    ClusterClassificationResult,
    classify_band as classify_band_fn,
    classify_site as classify_site_fn,
    DEFAULT_PRICE_BANDS,
)
from orchestrate.energy_saving.models.time_strategy import (
    get_strategy_for_hour,
    StrategyType,
)

logger = logging.getLogger(__name__)


class BandClassificationService:
    """Service for site band classification."""

    def __init__(self):
        self._bands = DEFAULT_PRICE_BANDS

    def classify_site(self, site_id: str, current_power_kw: float) -> SiteClassification:
        """Classify a single site into power band based on time-period strategy."""
        current_band = classify_band_fn(current_power_kw)
        
        # Get current time period strategy
        current_hour = datetime.now(timezone.utc).hour
        time_strategy = get_strategy_for_hour(current_hour)
        
        # Determine target band based on optimization logic and time-period
        target_band = self._determine_target_band(current_band, time_strategy)
        
        classification = classify_site_fn(current_band, target_band)
        
        # Calculate potential energy saving based on time-period
        saving_kw = self._calculate_saving(current_band, target_band, time_strategy)
        
        return SiteClassification(
            site_id=site_id,
            current_band=current_band,
            classified_band=target_band,
            classification=classification,
            classification_reason=f"Power {current_power_kw}KW → Band {current_band} ({time_strategy.strategy.value})",
            energy_saving_potential_kw=saving_kw,
            confidence_score=0.9,
            traffic_impact={"expected_throughput_change_percent": -2.5},
        )

    def _determine_target_band(self, current_band: int, time_strategy) -> int:
        """Determine target band based on current band and time-period strategy."""
        # Experience-first periods: conservative, minimal changes
        if time_strategy.strategy == StrategyType.EXPERIENCE_FIRST:
            return current_band
        
        # Proactive saving periods: moderate changes
        if time_strategy.strategy == StrategyType.PROACTIVE_SAVING:
            if current_band > 2:
                return current_band - 1
            return current_band
        
        # Maximized energy saving: aggressive changes allowed
        if time_strategy.strategy == StrategyType.MAXIMIZED_ENERGY_SAVING:
            if current_band > 1:
                return current_band - 1
            return current_band
        
        # Balanced: slightly conservative
        if current_band > 2:
            return current_band - 1
        return current_band

    def classify_cluster(
        self, 
        cluster_id: str, 
        sites: List[Dict[str, Any]]
    ) -> ClusterClassificationResult:
        """Classify all sites in a cluster."""
        downgrade = []
        upgrade = []
        stable = []
        total_saving = 0.0

        for site_data in sites:
            site_id = site_data.get("site_id", "UNKNOWN")
            current_power_kw = site_data.get("current_power_kw", 2.0)
            
            classification = self.classify_site(site_id, current_power_kw)
            
            if classification.classification == SiteClass.DOWNGRADE:
                downgrade.append(classification)
                total_saving += classification.energy_saving_potential_kw
            elif classification.classification == SiteClass.UPGRADE:
                upgrade.append(classification)
            else:
                stable.append(classification)

        logger.info(
            f"Cluster {cluster_id}: {len(downgrade)} downgrade, "
            f"{len(upgrade)} upgrade, {len(stable)} stable, "
            f"total saving: {total_saving}KW"
        )

        return ClusterClassificationResult(
            cluster_id=cluster_id,
            total_sites=len(sites),
            downgrade_sites=downgrade,
            upgrade_sites=upgrade,
            stable_sites=stable,
            estimated_total_saving_kw=total_saving,
        )

    def _calculate_saving(self, current_band: int, target_band: int, time_strategy) -> float:
        """Calculate potential energy saving between bands based on time-period strategy."""
        current_cost = 0.0
        target_cost = 0.0
        
        for band in self._bands:
            if band.band_no == current_band:
                current_cost = band.total_ghs
            if band.band_no == target_band:
                target_cost = band.total_ghs
        
        # Base saving in KW
        base_saving_kw = (current_cost - target_cost) / 1000
        
        # Adjust based on time-period strategy
        if time_strategy.strategy == StrategyType.MAXIMIZED_ENERGY_SAVING:
            multiplier = 1.5
        elif time_strategy.strategy == StrategyType.PROACTIVE_SAVING:
            multiplier = 1.2
        elif time_strategy.strategy == StrategyType.EXPERIENCE_FIRST:
            multiplier = 0.3
        else:
            multiplier = 1.0
        
        return base_saving_kw * multiplier

    def get_band_info(self, band_no: int) -> PriceBand:
        """Get information about a specific band."""
        for band in self._bands:
            if band.band_no == band_no:
                return band
        raise ValueError(f"Band {band_no} not found")

    def get_all_bands(self) -> List[PriceBand]:
        """Get all band definitions."""
        return self._bands


# Singleton instance
_band_classification_service: BandClassificationService = None


def get_band_classification_service() -> BandClassificationService:
    """Get singleton BandClassificationService instance."""
    global _band_classification_service
    if _band_classification_service is None:
        _band_classification_service = BandClassificationService()
    return _band_classification_service
