import re
from datetime import timedelta


def get_interval_minutes(iso8601_interval: str) -> int:
    """
    Convert an ISO 8601 duration string to total minutes.
    Example: 'PT15M' -> 15, 'PT1H' -> 60
    """
    # Handle hour format (PT1H, PT2H, etc.)
    hour_match = re.match(r"PT(\d+)H", iso8601_interval)
    if hour_match:
        return int(hour_match.group(1)) * 60
    
    # Handle minute format (PT15M, PT60M, etc.)
    minute_match = re.match(r"PT(\d+)M", iso8601_interval)
    if minute_match:
        return int(minute_match.group(1))
    
    raise ValueError(f"Unsupported ISO 8601 interval format: {iso8601_interval}")


def bucket_time(ts, bucket_size):
    """
    Get the bucket time for the interval.

    e.g. for a bucket size of 15 minutes, the time 10:07 would be rounded down to 10:00,
    """
    return ts - timedelta(
        minutes=ts.minute % bucket_size, seconds=ts.second, microseconds=ts.microsecond
    )
