from typing import Dict, List, Optional
import re


def parse_price_response(response: Dict) -> Dict:
    """Parse electricity price API response.
    
    Args:
        response: Raw API response dictionary
        
    Returns:
        Parsed price data
    """
    return {
        "region": response.get("region", ""),
        "current_price": response.get("current_price", 0.0),
        "time_slots": response.get("time_slots", []),
        "bands": response.get("bands", []),
        "valid_until": response.get("valid_until", ""),
    }


def normalize_region(region: str) -> str:
    """Normalize region name to lowercase.
    
    Args:
        region: Region name (case-insensitive)
        
    Returns:
        Normalized region name
    """
    return region.lower().strip()


def validate_region(region: str, valid_regions: List[str]) -> bool:
    """Validate region name.
    
    Args:
        region: Region name to validate
        valid_regions: List of valid region names
        
    Returns:
        True if region is valid, False otherwise
    """
    return normalize_region(region) in [r.lower() for r in valid_regions]


def extract_price_number(price_str: str) -> float:
    """Extract numeric price from string.
    
    Args:
        price_str: Price string, e.g., '1.23 USD' or '1.23'
        
    Returns:
        Numeric price value
    """
    match = re.search(r"[\d.]+", price_str)
    if match:
        return float(match.group())
    return 0.0


def calculate_average_price(time_slot_prices: List[Dict]) -> float:
    """Calculate average price from time slot prices.
    
    Args:
        time_slot_prices: List of time slot price dictionaries
        
    Returns:
        Average price
    """
    if not time_slot_prices:
        return 0.0
    
    total = sum(slot.get("price", 0.0) for slot in time_slot_prices)
    return total / len(time_slot_prices)


def find_cheapest_time_slot(time_slot_prices: List[Dict]) -> Optional[Dict]:
    """Find cheapest time slot.
    
    Args:
        time_slot_prices: List of time slot price dictionaries
        
    Returns:
        Cheapest time slot or None
    """
    if not time_slot_prices:
        return None
    
    return min(time_slot_prices, key=lambda x: x.get("price", float("inf")))


def find_expensive_time_slot(time_slot_prices: List[Dict]) -> Optional[Dict]:
    """Find most expensive time slot.
    
    Args:
        time_slot_prices: List of time slot price dictionaries
        
    Returns:
        Most expensive time slot or None
    """
    if not time_slot_prices:
        return None
    
    return max(time_slot_prices, key=lambda x: x.get("price", 0.0))
