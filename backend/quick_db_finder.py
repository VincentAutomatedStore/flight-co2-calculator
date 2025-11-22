import os
import sqlite3

def quick_find():
    """Quick check of common database locations"""
    
    locations = [
        'flight_calculator.db',
        'flight_calculator_v2.db',
        'instance/flight_calculator.db',
        '../flight_calculator.db',
        '../../flight_calculator.db',
        'flight_calculator_v1.db',
        'app.db',
        'data/flight_calculator.db'
    ]
    
    print("🚀 Quick Database Search")
    print("=" * 40)
    
    found_dbs = []
    
    for location in locations:
        if os.path.exists(location):
            print(f"✅ FOUND: {location}")
            
            conn = sqlite3.connect(location)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Check for data in key tables
            data_found = False
            for table in ['flight_calculations', 'FlightCalculation']:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"   🎉 {table}: {count} rows - THIS HAS YOUR DATA!")
                        data_found = True
                    else:
                        print(f"   {table}: {count} rows")
            
            if not data_found:
                print(f"   ℹ️ No data found in key tables")
            
            conn.close()
            found_dbs.append(location)
            print()
    
    if not found_dbs:
        print("❌ No database files found in common locations")
    
    return found_dbs

# Run the quick search
found = quick_find()

if found:
    print("🎯 Databases found. Your data is likely in one of these files!")
else:
    print("💡 No databases found. Let me check your Flask configuration...")