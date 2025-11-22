import sqlite3
import re
from datetime import datetime
import os

def get_backend_database_path():
    """Get the database path in the backend directory"""
    
    backend_db_path = r'C:\Users\makro\Documents\0 - Flight CO2 Calculator App\flight-co2-calculator\backend\flight_calculator.db'
    
    if os.path.exists(backend_db_path):
        print(f"✅ Found backend database: {backend_db_path}")
        
        # Verify it has data
        try:
            conn = sqlite3.connect(backend_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM flight_calculations")
            calculation_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM airports")
            airport_count = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"   - Flight calculations: {calculation_count}")
            print(f"   - Current airports: {airport_count}")
            
            return backend_db_path
            
        except Exception as e:
            print(f"   - Error checking database: {e}")
            return None
    else:
        print(f"❌ Backend database not found: {backend_db_path}")
        return None

def read_all_airports_from_js(file_path):
    """Read ALL airports from the JavaScript file using robust parsing"""
    
    print(f"📖 Reading ALL airports from: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract array content
        pattern = r'export\s+const\s+airports\s*=\s*\[(.*?)\];'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            # Try without export
            pattern = r'const\s+airports\s*=\s*\[(.*?)\];'
            match = re.search(pattern, content, re.DOTALL)
        
        if match:
            array_content = match.group(1)
            print(f"✅ Found array with {len(array_content)} characters")
            
            # Split by objects
            objects = re.findall(r'\{[^}]+\}', array_content)
            print(f"✅ Found {len(objects)} airport objects")
            
            airports = []
            for obj_str in objects:
                airport = {}
                # Extract each field
                code_match = re.search(r"code:\s*['\"]([^'\"]+)['\"]", obj_str)
                name_match = re.search(r"name:\s*['\"]([^'\"]+)['\"]", obj_str)
                city_match = re.search(r"city:\s*['\"]([^'\"]+)['\"]", obj_str)
                country_match = re.search(r"country:\s*['\"]([^'\"]+)['\"]", obj_str)
                search_match = re.search(r"search:\s*['\"]([^'\"]+)['\"]", obj_str)
                
                if code_match:
                    airport['code'] = code_match.group(1)
                if name_match:
                    airport['name'] = name_match.group(1)
                if city_match:
                    airport['city'] = city_match.group(1)
                if country_match:
                    airport['country'] = country_match.group(1)
                if search_match:
                    airport['search'] = search_match.group(1)
                
                if airport:  # Only add if we have at least a code
                    airports.append(airport)
            
            print(f"✅ Successfully parsed {len(airports)} airports")
            return airports
        
        print("❌ No airports found in the file")
        return None
        
    except Exception as e:
        print(f"❌ Error reading airports file: {e}")
        return None

def create_airports_table(conn):
    """Create the airports table if it doesn't exist"""
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='airports'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print("✅ Airports table already exists in backend database")
        return False
    else:
        create_table_sql = """
        CREATE TABLE airports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            iata_code VARCHAR(3) NOT NULL UNIQUE,
            icao_code VARCHAR(4),
            name VARCHAR(200) NOT NULL,
            city VARCHAR(100) NOT NULL,
            country VARCHAR(100) NOT NULL,
            latitude REAL,
            longitude REAL,
            timezone VARCHAR(50),
            search_field VARCHAR(300),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_table_sql)
        
        # Create indexes for faster searches
        cursor.execute("CREATE INDEX idx_airports_iata ON airports(iata_code);")
        cursor.execute("CREATE INDEX idx_airports_search ON airports(search_field);")
        cursor.execute("CREATE INDEX idx_airports_country ON airports(country);")
        cursor.execute("CREATE INDEX idx_airports_city ON airports(city);")
        
        conn.commit()
        print("✅ Airports table created in backend database with indexes")
        return True

def import_all_airports(conn, airports):
    """Import ALL airports into the backend database"""
    cursor = conn.cursor()
    
    inserted_count = 0
    updated_count = 0
    errors = []
    
    print(f"\n🔄 Importing ALL {len(airports)} airports to backend database...")
    print("This will take a moment for 3000+ airports...")
    
    # Use transaction for better performance
    cursor.execute("BEGIN TRANSACTION")
    
    try:
        for i, airport in enumerate(airports, 1):
            # Show progress
            if i % 500 == 0:
                print(f"  ✅ Processed {i}/{len(airports)} airports...")
            
            iata_code = airport.get('code')
            if not iata_code:
                errors.append(f"Row {i}: Missing IATA code")
                continue
            
            try:
                # Check if airport already exists
                cursor.execute("SELECT id FROM airports WHERE iata_code = ?", (iata_code,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing airport
                    update_sql = """
                    UPDATE airports SET 
                        name = ?, city = ?, country = ?, search_field = ?
                    WHERE iata_code = ?
                    """
                    cursor.execute(update_sql, (
                        airport.get('name', ''), 
                        airport.get('city', ''), 
                        airport.get('country', ''), 
                        airport.get('search', ''),
                        iata_code
                    ))
                    updated_count += 1
                else:
                    # Insert new airport
                    insert_sql = """
                    INSERT INTO airports 
                    (iata_code, name, city, country, search_field)
                    VALUES (?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_sql, (
                        iata_code,
                        airport.get('name', ''),
                        airport.get('city', ''),
                        airport.get('country', ''),
                        airport.get('search', '')
                    ))
                    inserted_count += 1
                
            except Exception as e:
                errors.append(f"{iata_code}: {str(e)}")
        
        # Commit the transaction
        conn.commit()
        print(f"✅ Transaction committed successfully to backend database")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Transaction failed: {e}")
        raise
    
    return inserted_count, updated_count, errors

def verify_backend_import(conn, expected_count):
    """Verify the import in the backend database"""
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("📊 BACKEND DATABASE VERIFICATION")
    print("="*60)
    
    # Count total airports
    cursor.execute("SELECT COUNT(*) FROM airports")
    actual_count = cursor.fetchone()[0]
    
    # Count flight calculations
    cursor.execute("SELECT COUNT(*) FROM flight_calculations")
    calculation_count = cursor.fetchone()[0]
    
    print(f"Expected airports: {expected_count}")
    print(f"Actual airports in backend: {actual_count}")
    print(f"Flight calculations in backend: {calculation_count}")
    
    if actual_count == expected_count:
        print("🎉 SUCCESS: All airports imported to backend!")
    else:
        print(f"⚠️  WARNING: {expected_count - actual_count} airports missing")
    
    # Show sample airports
    cursor.execute("SELECT iata_code, name, city, country FROM airports ORDER BY iata_code LIMIT 10")
    sample_airports = cursor.fetchall()
    
    print(f"\nFirst 10 airports in backend database:")
    for airport in sample_airports:
        print(f"  {airport[0]} - {airport[1]} ({airport[2]}, {airport[3]})")
    
    return actual_count

def main():
    """Main function to import ALL airports to the backend database"""
    
    backend_db_path = r'C:\Users\makro\Documents\0 - Flight CO2 Calculator App\flight-co2-calculator\backend\flight_calculator.db'
    airports_js_path = r'C:\Users\makro\Documents\0 - Flight CO2 Calculator App\flight-co2-calculator\frontend\src\data\airports.js'
    
    print("🚀 IMPORT AIRPORTS TO BACKEND DATABASE")
    print("=" * 70)
    print(f"Backend Database: {backend_db_path}")
    print(f"Source File: {airports_js_path}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Verify backend database exists
    if not os.path.exists(backend_db_path):
        print(f"❌ Backend database not found: {backend_db_path}")
        print("Please make sure the backend database exists.")
        return
    
    # Verify airports.js file exists
    if not os.path.exists(airports_js_path):
        print(f"❌ airports.js file not found: {airports_js_path}")
        return
    
    try:
        # Connect to the BACKEND database
        conn = sqlite3.connect(backend_db_path)
        print(f"✅ Connected to BACKEND database: {backend_db_path}")
        
        # Read ALL airports from file
        airports = read_all_airports_from_js(airports_js_path)
        if not airports:
            print("❌ No airports found. Cannot continue.")
            return
        
        print(f"\n📊 FILE ANALYSIS:")
        print(f"  Total airports found: {len(airports)}")
        print(f"  First airport: {airports[0].get('code')} - {airports[0].get('name')}")
        print(f"  Last airport: {airports[-1].get('code')} - {airports[-1].get('name')}")
        
        # Create table if needed
        table_created = create_airports_table(conn)
        
        # Import ALL airports to backend
        inserted_count, updated_count, errors = import_all_airports(conn, airports)
        
        # Show results
        print(f"\n📊 IMPORT RESULTS:")
        print(f"  ✅ New airports inserted: {inserted_count}")
        print(f"  🔄 Existing airports updated: {updated_count}")
        print(f"  ❌ Errors: {len(errors)}")
        print(f"  📊 Total in backend database: {inserted_count + updated_count}")
        
        if errors and len(errors) <= 5:
            print(f"\n⚠️  First 5 errors:")
            for error in errors[:5]:
                print(f"    {error}")
        
        # Final verification
        final_count = verify_backend_import(conn, len(airports))
        
        print(f"\n🎉 BACKEND IMPORT COMPLETED!")
        print(f"   Database: {backend_db_path}")
        print(f"   Total airports in backend: {final_count}")
        print(f"   All {len(airports)} airports processed")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()