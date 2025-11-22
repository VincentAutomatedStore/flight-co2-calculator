#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automation Database Cleaner for Flight CO2 Calculator
Location: C:\\Users\\makro\\Documents\\0 - Flight CO2 Calculator App\\flight-co2-calculator\\backend
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

# Database path - using raw string and proper Windows path
DB_PATH = r"C:\Users\makro\Documents\0 - Flight CO2 Calculator App\flight-co2-calculator\backend\flight_calculator.db"

def get_db_connection():
    """Get SQLite database connection"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print("❌ Database connection error:", e)
        return None

def get_table_info():
    """Get information about tables in the database"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        table_info = {}
        for table in tables:
            # Get row count for each table
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()[0]
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            table_info[table] = {
                'count': count,
                'columns': columns
            }
        
        return table_info
    except sqlite3.Error as e:
        print("❌ Error getting table info:", e)
        return None
    finally:
        conn.close()

def clean_flight_calculations(clean_type='all', days_old=30):
    """Clean the flight_calculations table"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get count before cleanup
        cursor.execute("SELECT COUNT(*) as count FROM flight_calculations")
        count_before = cursor.fetchone()[0]
        
        if clean_type == 'all':
            # Delete all records
            cursor.execute("DELETE FROM flight_calculations")
            deleted_count = count_before
            
        elif clean_type == 'old':
            # Delete records older than specified days
            cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("DELETE FROM flight_calculations WHERE created_at < ?", (cutoff_date,))
            deleted_count = cursor.rowcount
            
        elif clean_type == 'auto':
            # Delete automation results (ICAO_API sourced)
            cursor.execute("DELETE FROM flight_calculations WHERE data_source = 'ICAO_API'")
            deleted_count = cursor.rowcount
            
        elif clean_type == 'manual':
            # Delete manual calculations
            cursor.execute("DELETE FROM flight_calculations WHERE data_source != 'ICAO_API' OR data_source IS NULL")
            deleted_count = cursor.rowcount
            
        else:
            print("❌ Invalid clean type")
            return False
        
        # Reset auto-increment
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='flight_calculations'")
        except sqlite3.Error:
            pass  # Table might not exist yet
        
        conn.commit()
        
        print("✅ Successfully deleted", deleted_count, "records from flight_calculations")
        print("📊 Table had", count_before, "records, now has", count_before - deleted_count, "records")
        
        return True
        
    except sqlite3.Error as e:
        print("❌ Database error:", e)
        conn.rollback()
        return False
    finally:
        conn.close()

def clean_airports_table():
    """Clean the airports table (if exists)"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if airports table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='airports'")
        if not cursor.fetchone():
            print("ℹ️  Airports table doesn't exist")
            return True
        
        cursor.execute("SELECT COUNT(*) as count FROM airports")
        count_before = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM airports")
        
        # Reset auto-increment
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='airports'")
        except sqlite3.Error:
            pass
        
        conn.commit()
        
        print("✅ Deleted", count_before, "records from airports table")
        return True
        
    except sqlite3.Error as e:
        print("❌ Error cleaning airports:", e)
        conn.rollback()
        return False
    finally:
        conn.close()

def backup_database():
    """Create a backup of the database"""
    backup_path = DB_PATH + '.backup.' + datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print("✅ Database backed up to:", backup_path)
        return backup_path
    except Exception as e:
        print("❌ Backup failed:", e)
        return None

def show_database_stats():
    """Show current database statistics"""
    print("\n📊 DATABASE STATISTICS")
    print("=" * 50)
    
    table_info = get_table_info()
    if not table_info:
        print("❌ Could not read database statistics")
        return
    
    for table_name, info in table_info.items():
        print("📋", table_name + ":")
        print("   📈 Records:", info['count'])
        if info['columns']:
            print("   🗂️  Columns:", ', '.join(info['columns'][:3]) + ('...' if len(info['columns']) > 3 else ''))
        print()

def interactive_clean():
    """Interactive cleaning mode"""
    print("\n🔄 INTERACTIVE DATABASE CLEANER")
    print("=" * 50)
    
    show_database_stats()
    
    print("🧹 CLEANING OPTIONS:")
    print("1. Delete ALL records from flight_calculations")
    print("2. Delete OLD records (older than X days)")
    print("3. Delete AUTOMATION results only (ICAO_API)")
    print("4. Delete MANUAL calculations only")
    print("5. Clean airports table")
    print("6. Show database statistics")
    print("7. Create backup")
    print("8. Exit")
    
    while True:
        try:
            choice = input("\n🎯 Enter your choice (1-8): ").strip()
            
            if choice == '1':
                if input("❓ Delete ALL records? (y/N): ").lower() in ['y', 'yes']:
                    clean_flight_calculations('all')
                break
                
            elif choice == '2':
                days = input("📅 Delete records older than how many days? (default: 30): ").strip()
                days = int(days) if days.isdigit() else 30
                clean_flight_calculations('old', days)
                break
                
            elif choice == '3':
                clean_flight_calculations('auto')
                break
                
            elif choice == '4':
                clean_flight_calculations('manual')
                break
                
            elif choice == '5':
                if input("❓ Clean airports table? (y/N): ").lower() in ['y', 'yes']:
                    clean_airports_table()
                break
                
            elif choice == '6':
                show_database_stats()
                continue
                
            elif choice == '7':
                backup_database()
                continue
                
            elif choice == '8':
                print("👋 Goodbye!")
                return
                
            else:
                print("❌ Invalid choice. Please enter 1-8.")
                
        except KeyboardInterrupt:
            print("\n👋 Operation cancelled by user.")
            return
        except Exception as e:
            print("❌ Error:", e)

def main():
    """Main function"""
    print("🚀 FLIGHT CO2 CALCULATOR - DATABASE CLEANER")
    print("📍 Location:", DB_PATH)
    print("=" * 60)
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print("❌ Database file not found:", DB_PATH)
        print("💡 Please make sure you're running this script from the backend directory")
        return
    
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "all":
            clean_flight_calculations('all')
        elif sys.argv[1] == "old":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            clean_flight_calculations('old', days)
        elif sys.argv[1] == "auto":
            clean_flight_calculations('auto')
        elif sys.argv[1] == "manual":
            clean_flight_calculations('manual')
        elif sys.argv[1] == "airports":
            clean_airports_table()
        elif sys.argv[1] == "stats":
            show_database_stats()
        elif sys.argv[1] == "backup":
            backup_database()
        else:
            print("❌ Unknown command")
            print("\n📖 USAGE:")
            print("  python clean_automation_db.py all       - Delete ALL flight calculations")
            print("  python clean_automation_db.py old [30]  - Delete records older than days")
            print("  python clean_automation_db.py auto      - Delete automation results")
            print("  python clean_automation_db.py manual    - Delete manual calculations")
            print("  python clean_automation_db.py airports  - Clean airports table")
            print("  python clean_automation_db.py stats     - Show database statistics")
            print("  python clean_automation_db.py backup    - Create backup")
            print("  python clean_automation_db.py           - Interactive mode")
    else:
        # Interactive mode
        interactive_clean()
    
    print("\n" + "=" * 60)
    print("✅ Cleaning process completed!")

if __name__ == "__main__":
    main()