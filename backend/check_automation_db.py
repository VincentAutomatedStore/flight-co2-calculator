#!/usr/bin/env python3
"""
Script to check automation database records
"""

import sqlite3
import os
from pathlib import Path

def check_automation_database():
    # Try to find the database file
    db_paths = [
        'instance/automation.db',
        'automation.db',
        'app/instance/automation.db',
        '../instance/automation.db',
        'carbon_calculator.db'
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Database file not found. Tried:")
        for path in db_paths:
            print(f"   - {path}")
        return
    
    print(f"📁 Database found: {db_path}")
    print(f"📊 Database size: {os.path.getsize(db_path) / (1024*1024):.2f} MB")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📋 Tables in database:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} records")
            
            # Show first few column names for each table
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"     Columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
        
        # Check for calculation-related tables specifically
        print(f"\n🔍 Detailed calculation records:")
        calculation_tables = ['calculation', 'automation_calculation', 'batch_calculation', 'calculation_result']
        
        for table in calculation_tables:
            if table in [t[0] for t in tables]:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"   - {table}: {count} records")
                
                # Show sample data
                cursor.execute(f"SELECT * FROM {table} LIMIT 1;")
                sample = cursor.fetchone()
                if sample:
                    print(f"     Sample: {sample}")
        
        # Check data sources distribution
        print(f"\n📊 Data source distribution:")
        for table in ['calculation', 'automation_calculation']:
            if table in [t[0] for t in tables]:
                cursor.execute(f"""
                    SELECT data_source, COUNT(*) as count 
                    FROM {table} 
                    GROUP BY data_source 
                    ORDER BY count DESC;
                """)
                sources = cursor.fetchall()
                if sources:
                    print(f"   {table} data sources:")
                    for source, count in sources:
                        print(f"     - {source}: {count} records")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_automation_database()