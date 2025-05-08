from datetime import datetime, timedelta

def is_date_in_this_week(date_to_check):
    """
    Checks if a given datetime.date object falls within the current week (Monday to Sunday).

    Args:
        date_to_check: A datetime.date object to check.

    Returns:
        True if the date is in the current week, False otherwise.
    """
    now = datetime.now().date()
    start_of_week = now - timedelta(days=now.weekday())  # Monday of the current week
    end_of_week = start_of_week + timedelta(days=6)     # Sunday of the current week
    return start_of_week <= date_to_check <= end_of_week