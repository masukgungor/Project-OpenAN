import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from orchestrate.energy_saving.models import (
    ElectricityPriceData,
    ElectricityPriceResponse,
    DEFAULT_PRICE_BANDS,
    DEFAULT_TIME_SLOT_PRICES,
    PriceBand,
    TimeSlotPrice,
)

logger = logging.getLogger(__name__)


class ElectricityPriceService:
    """Service for fetching and managing electricity prices."""

    def __init__(self):
        self._cache: Dict[str, ElectricityPriceData] = {}
        self._cache_ttl_seconds = 300  # 5 minutes

    def get_price(self, region: str) -> ElectricityPriceResponse:
        """Get electricity price for region with caching."""
        # Check cache
        if region in self._cache:
            cached = self._cache[region]
            if datetime.now() < cached.valid_until:
                logger.debug(f"Cache hit for region: {region}")
                return self._to_response(cached)

        # Fetch from external API (mock for now)
        logger.info(f"Fetching electricity price for region: {region}")
        price_data = self._fetch_from_api(region)
        self._cache[region] = price_data
        return self._to_response(price_data)

    def _fetch_from_api(self, region: str) -> ElectricityPriceData:
        """Fetch electricity price from external API (mock implementation)."""
        # In real implementation, this would call external electricity price API
        # For now, return default values
        return ElectricityPriceData(
            region=region,
            valid_until=datetime.now() + timedelta(seconds=self._cache_ttl_seconds),
            time_slot_prices=DEFAULT_TIME_SLOT_PRICES,
            price_bands=DEFAULT_PRICE_BANDS,
        )

    def _to_response(self, data: ElectricityPriceData) -> ElectricityPriceResponse:
        """Convert ElectricityPriceData to response format."""
        current_price = data.time_slot_prices[0].price if data.time_slot_prices else 0.0
        return ElectricityPriceResponse(
            region=data.region,
            current_price=current_price,
            time_slots=data.time_slot_prices,
            bands=data.price_bands,
            valid_until=data.valid_until,
        )

    def get_bands(self) -> List[PriceBand]:
        """Get all price bands."""
        return DEFAULT_PRICE_BANDS

    def get_time_slots(self) -> List[TimeSlotPrice]:
        """Get all time slot prices."""
        return DEFAULT_TIME_SLOT_PRICES

    def clear_cache(self, region: Optional[str] = None):
        """Clear price cache."""
        if region:
            self._cache.pop(region, None)
            logger.info(f"Cleared cache for region: {region}")
        else:
            self._cache.clear()
            logger.info("Cleared all price cache")


# Singleton instance
_electricity_price_service: Optional[ElectricityPriceService] = None


def get_electricity_price_service() -> ElectricityPriceService:
    """Get singleton ElectricityPriceService instance."""
    global _electricity_price_service
    if _electricity_price_service is None:
        _electricity_price_service = ElectricityPriceService()
    return _electricity_price_service
