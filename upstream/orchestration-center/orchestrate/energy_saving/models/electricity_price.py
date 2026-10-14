from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PriceBand(BaseModel):
    band_no: int = Field(..., ge=1, le=5, description="Band number 1-5")
    kw_min: float = Field(..., description="Minimum KW for this band")
    kw_max: float = Field(..., description="Maximum KW for this band")
    total_ghs: float = Field(..., description="Total GHS for this band")


class TimeSlotPrice(BaseModel):
    time_period: str = Field(..., description="Time period e.g., '23~5', '6~9'")
    start_hour: int = Field(..., ge=0, le=23, description="Start hour (0-23)")
    end_hour: int = Field(..., ge=0, le=23, description="End hour (0-23)")
    price: float = Field(..., description="Electricity price factor")
    strategy: str = Field(..., description="Recommended strategy for this period")


class ElectricityPriceData(BaseModel):
    region: str = Field(..., description="Region code")
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(), description="Fetch timestamp")
    valid_until: datetime = Field(..., description="Data validity timestamp")
    time_slot_prices: List[TimeSlotPrice] = Field(..., description="Prices by time slot")
    price_bands: List[PriceBand] = Field(..., description="Power band classifications")
    currency: str = Field(default="GHS", description="Currency code")


class ElectricityPriceResponse(BaseModel):
    region: str
    current_price: float
    time_slots: List[TimeSlotPrice]
    bands: List[PriceBand]
    valid_until: datetime


# Predefined price bands from PPTX
DEFAULT_PRICE_BANDS = [
    PriceBand(band_no=1, kw_min=0.0, kw_max=0.99, total_ghs=8247.66),
    PriceBand(band_no=2, kw_min=1.0, kw_max=1.99, total_ghs=10628.25),
    PriceBand(band_no=3, kw_min=2.0, kw_max=2.99, total_ghs=11956.25),
    PriceBand(band_no=4, kw_min=3.0, kw_max=3.99, total_ghs=15409.75),
    PriceBand(band_no=5, kw_min=4.0, kw_max=4.99, total_ghs=17784.09),
]

# Predefined time slot prices from PPTX
DEFAULT_TIME_SLOT_PRICES = [
    TimeSlotPrice(time_period="23~5", start_hour=23, end_hour=5, price=1.0, strategy="maximized_energy_saving"),
    TimeSlotPrice(time_period="6~9", start_hour=6, end_hour=9, price=1.176, strategy="proactive_saving"),
    TimeSlotPrice(time_period="10~15", start_hour=10, end_hour=15, price=0.824, strategy="experience_first"),
    TimeSlotPrice(time_period="16~17", start_hour=16, end_hour=17, price=1.176, strategy="proactive_saving"),
    TimeSlotPrice(time_period="18~22", start_hour=18, end_hour=22, price=1.765, strategy="experience_first"),
    TimeSlotPrice(time_period="22~23", start_hour=22, end_hour=23, price=1.176, strategy="balanced"),
]
