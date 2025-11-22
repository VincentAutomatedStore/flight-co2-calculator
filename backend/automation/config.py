import os
from datetime import time
from typing import Dict, Any

class SchedulerConfig:
    """Configuration for the automation scheduler"""
    
    # Directory paths
    SCHEDULED_DIR = "data/scheduled"
    PROCESSED_DIR = "data/processed"
    ERRORS_DIR = "data/errors"
    
    # Default schedule times
    DAILY_TIME = time(2, 0)  # 2:00 AM
    WEEKLY_TIME = time(2, 0)  # 2:00 AM on Monday
    MONTHLY_TIME = time(2, 0)  # 2:00 AM on 1st of month
    
    # File patterns
    CSV_PATTERN = "*.csv"
    
    @classmethod
    def ensure_directories(cls):
        """Create all required directories"""
        os.makedirs(cls.SCHEDULED_DIR, exist_ok=True)
        os.makedirs(cls.PROCESSED_DIR, exist_ok=True)
        os.makedirs(cls.ERRORS_DIR, exist_ok=True)