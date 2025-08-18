"""
Timezone utilities for consistent UTC+7 (Asia/Bangkok) time handling.
All user-visible datetime operations should use these helpers.
"""

import pytz
from datetime import datetime, date


# Define the UTC+7 timezone (Asia/Bangkok)
BANGKOK_TZ = pytz.timezone('Asia/Bangkok')


def get_current_bangkok_time():
    """Get current datetime in UTC+7 timezone"""
    return datetime.now(BANGKOK_TZ)


def get_current_bangkok_date():
    """Get current date in UTC+7 timezone"""
    return get_current_bangkok_time().date()


def format_bangkok_datetime(dt=None, format_str='%d/%m/%Y %H:%M:%S'):
    """Format datetime in UTC+7 timezone for user display"""
    if dt is None:
        dt = get_current_bangkok_time()
    elif dt.tzinfo is None:
        # If datetime is naive, assume it's already Bangkok time
        dt = BANGKOK_TZ.localize(dt)
    elif dt.tzinfo != BANGKOK_TZ:
        # Convert to Bangkok timezone if it's in a different timezone
        dt = dt.astimezone(BANGKOK_TZ)
    
    return dt.strftime(format_str)


def format_bangkok_date(dt=None, format_str='%d/%m/%Y'):
    """Format date in UTC+7 timezone for user display"""
    if dt is None:
        dt = get_current_bangkok_date()
    elif isinstance(dt, datetime):
        dt = dt.date()
    
    return dt.strftime(format_str)


def format_bangkok_time(dt=None, format_str='%H:%M:%S'):
    """Format time in UTC+7 timezone for user display"""
    if dt is None:
        dt = get_current_bangkok_time()
    elif dt.tzinfo is None:
        dt = BANGKOK_TZ.localize(dt)
    elif dt.tzinfo != BANGKOK_TZ:
        dt = dt.astimezone(BANGKOK_TZ)
    
    return dt.strftime(format_str)


def convert_to_bangkok_timezone(dt):
    """Convert any datetime to Bangkok timezone"""
    if dt.tzinfo is None:
        # If naive, assume UTC and convert
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(BANGKOK_TZ)


def get_bangkok_datetime_str():
    """Get current Bangkok datetime as formatted string (DD/MM/YYYY HH:MM:SS)"""
    return format_bangkok_datetime()


def get_bangkok_date_str():
    """Get current Bangkok date as formatted string (DD/MM/YYYY)"""
    return format_bangkok_date()


def get_bangkok_time_str():
    """Get current Bangkok time as formatted string (HH:MM:SS)"""
    return format_bangkok_time()