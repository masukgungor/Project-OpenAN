from datetime import datetime, timezone
from typing import Tuple


def get_current_utc() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def parse_time_period(time_period: str) -> Tuple[int, int]:
    """Parse time period string like '23~5' to (start_hour, end_hour).
    
    Args:
        time_period: Time period string, e.g., '23~5'
        
    Returns:
        Tuple of (start_hour, end_hour)
        
    Examples:
        >>> parse_time_period("23~5")
        (23, 5)
        >>> parse_time_period("6~9")
        (6, 9)
    """
    parts = time_period.split("~")
    start_hour = int(parts[0])
    end_hour = int(parts[1])
    return (start_hour, end_hour)


def is_hour_in_period(hour: int, time_period: str) -> bool:
    """Check if hour is within time period.
    
    Args:
        hour: Hour to check (0-23)
        time_period: Time period string, e.g., '23~5'
        
    Returns:
        True if hour is in period, False otherwise
    """
    start, end = parse_time_period(time_period)
    
    if start <= end:
        # Normal range, e.g., 6~9 (6,7,8,9)
        return start <= hour <= end
    else:
        # Overnight range, e.g., 23~5 (23,0,1,2,3,4,5)
        return hour >= start or hour <= end


def get_hour_range(time_period: str) -> list:
    """Get list of hours in time period.
    
    Args:
        time_period: Time period string, e.g., '23~5'
        
    Returns:
        List of hours in the period
    """
    start, end = parse_time_period(time_period)
    
    if start <= end:
        return list(range(start, end + 1))
    else:
        # Overnight range
        return list(range(start, 24)) + list(range(0, end + 1))


def format_time_period(start_hour: int, end_hour: int) -> str:
    """Format start and end hours to time period string.
    
    Args:
        start_hour: Start hour (0-23)
        end_hour: End hour (0-23)
        
    Returns:
        Time period string, e.g., '23~5'
    """
    return f"{start_hour}~{end_hour}"
