#!/usr/bin/env python3
"""
Script to clean/truncate the flight_calculations table
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import FlightCalculation

def clean_flight_calculations():
    """Completely empty the flight_calculations table"""
    with app.app_context():
        try:
            # Count records before deletion
            count_before = FlightCalculation.query.count()
            print(f"📊 Records before cleanup: {count_before}")
            
            # Delete all records
            deleted_count = FlightCalculation.query.delete()
            db.session.commit()
            
            print(f"✅ Successfully deleted {deleted_count} records from flight_calculations table")
            print("🗑️  Table is now empty and ready for automated processing")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error cleaning table: {e}")
            return False
    
    return True

def clean_automation_results_only():
    """Clean only automation results (if you have a way to identify them)"""
    with app.app_context():
        try:
            # If you have a way to identify automation results (e.g., by source or batch_id)
            # This is a placeholder - adjust based on your actual schema
            automation_results = FlightCalculation.query.filter(
                FlightCalculation.data_source == 'ICAO_API'
            ).delete()
            
            db.session.commit()
            print(f"✅ Deleted {automation_results} automation results")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error cleaning automation results: {e}")

def clean_old_records(days_old=30):
    """Clean records older than specified days"""
    from datetime import datetime, timedelta
    
    with app.app_context():
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_records = FlightCalculation.query.filter(
                FlightCalculation.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            print(f"✅ Deleted {old_records} records older than {days_old} days")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error cleaning old records: {e}")

if __name__ == "__main__":
    print("🔄 Flight Calculations Table Cleaner")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            clean_flight_calculations()
        elif sys.argv[1] == "old":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            clean_old_records(days)
        elif sys.argv[1] == "auto":
            clean_automation_results_only()
        else:
            print("❌ Unknown command. Usage:")
            print("  python clean_database.py all     - Delete ALL records")
            print("  python clean_database.py old [30] - Delete records older than days (default: 30)")
            print("  python clean_database.py auto    - Delete only automation results")
    else:
        # Interactive mode
        response = input("❓ Delete ALL records from flight_calculations? (y/N): ")
        if response.lower() in ['y', 'yes']:
            clean_flight_calculations()
        else:
            print("Operation cancelled.")