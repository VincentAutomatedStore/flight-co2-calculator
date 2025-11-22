import sqlite3
import json
from datetime import datetime

def export_flight_calculations_to_sql_server():
    """Export only flight_calculations table data to SQL Server INSERT scripts"""
    
    # Connect to the CORRECT SQLite database (without _v2)
    sqlite_conn = sqlite3.connect('flight_calculator.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    print("Exporting data from table: flight_calculations")
    print("Source: flight_calculator.db (found 10 rows!)")
    
    # Get table structure
    sqlite_cursor.execute("PRAGMA table_info(flight_calculations)")
    columns_info = sqlite_cursor.fetchall()
    columns = [row[1] for row in columns_info]
    
    print(f"Columns found: {columns}")
    
    # Get all data from flight_calculations table
    sqlite_cursor.execute("SELECT * FROM flight_calculations")
    rows = sqlite_cursor.fetchall()
    
    print(f"Found {len(rows)} rows in flight_calculations table")
    
    # Generate SQL Server INSERT statements
    insert_statements = []
    
    for row in rows:
        values = []
        for i, value in enumerate(row):
            col_name = columns[i]
            
            if value is None:
                values.append("NULL")
            elif isinstance(value, str):
                # Escape single quotes and handle strings
                escaped_value = value.replace("'", "''")
                values.append(f"'{escaped_value}'")
            elif isinstance(value, int):
                values.append(str(value))
            elif isinstance(value, float):
                # Handle float values, ensure proper decimal format
                values.append(str(value))
            elif isinstance(value, datetime):
                # Convert datetime to SQL Server format
                values.append(f"'{value.isoformat()}'")
            elif isinstance(value, bool):
                # Convert boolean to bit (1 for True, 0 for False)
                values.append("1" if value else "0")
            else:
                # Convert any other type to string
                values.append(f"'{str(value)}'")
        
        columns_str = ", ".join([f"[{col}]" for col in columns])
        values_str = ", ".join(values)
        
        insert_stmt = f"INSERT INTO [flight_calculations] ({columns_str}) VALUES ({values_str});"
        insert_statements.append(insert_stmt)
    
    # Write to file
    filename = "sqlserver_flight_calculations_inserts.sql"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"-- SQL Server INSERT statements for table: flight_calculations\n")
        f.write(f"-- Generated on: {datetime.now().isoformat()}\n")
        f.write(f"-- Total rows: {len(insert_statements)}\n")
        f.write(f"-- Source: SQLite database 'flight_calculator.db'\n")
        f.write(f"-- NOTE: This is the CORRECT database with actual data!\n\n")
        
        # Check if we need identity insert (if id column is primary key)
        has_identity = any(col[5] > 0 for col in columns_info if col[1] == 'id')
        
        if has_identity:
            f.write("-- Enable identity insert to preserve original IDs\n")
            f.write("SET IDENTITY_INSERT [flight_calculations] ON;\n\n")
        
        # Write all INSERT statements
        for stmt in insert_statements:
            f.write(stmt + "\n")
        
        if has_identity:
            f.write("\n-- Disable identity insert after import\n")
            f.write("SET IDENTITY_INSERT [flight_calculations] OFF;\n")
    
    print(f"✅ Exported {len(insert_statements)} rows to {filename}")
    
    # Also generate a summary report
    generate_export_summary(sqlite_cursor, rows, columns)
    
    sqlite_conn.close()
    print("\n🎉 Export completed!")

def generate_export_summary(cursor, rows, columns):
    """Generate a summary report of the exported data"""
    
    summary_filename = "export_summary.txt"
    
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write("FLIGHT CALCULATIONS EXPORT SUMMARY\n")
        f.write("=" * 50 + "\n")
        f.write(f"Export Date: {datetime.now().isoformat()}\n")
        f.write(f"Total Rows Exported: {len(rows)}\n")
        f.write(f"Source Database: flight_calculator.db\n")
        f.write(f"Target: SQL Server\n")
        f.write(f"Columns: {', '.join(columns)}\n\n")
        
        # Get some statistics about the data
        if rows:
            # Count by cabin class
            cursor.execute("SELECT cabin_class, COUNT(*) FROM flight_calculations GROUP BY cabin_class")
            cabin_stats = cursor.fetchall()
            
            f.write("CABIN CLASS DISTRIBUTION:\n")
            for cabin, count in cabin_stats:
                f.write(f"  {cabin}: {count} calculations\n")
            
            f.write("\n")
            
            # Count round trips vs one-way
            cursor.execute("SELECT round_trip, COUNT(*) FROM flight_calculations GROUP BY round_trip")
            trip_stats = cursor.fetchall()
            
            f.write("TRIP TYPE DISTRIBUTION:\n")
            for round_trip, count in trip_stats:
                trip_type = "Round Trip" if round_trip else "One Way"
                f.write(f"  {trip_type}: {count} calculations\n")
            
            f.write("\n")
            
            # Date range
            cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM flight_calculations")
            min_date, max_date = cursor.fetchone()
            
            f.write(f"DATE RANGE: {min_date} to {max_date}\n")
            
            # Get passenger statistics
            cursor.execute("SELECT MIN(passengers), MAX(passengers), AVG(passengers) FROM flight_calculations")
            min_pass, max_pass, avg_pass = cursor.fetchone()
            f.write(f"PASSENGERS: Min={min_pass}, Max={max_pass}, Avg={avg_pass:.1f}\n")
            
            # Get CO2 statistics
            cursor.execute("SELECT MIN(total_co2_kg), MAX(total_co2_kg), AVG(total_co2_kg) FROM flight_calculations")
            min_co2, max_co2, avg_co2 = cursor.fetchone()
            f.write(f"CO2 EMISSIONS: Min={min_co2}kg, Max={max_co2}kg, Avg={avg_co2:.1f}kg\n")
            
            # Sample data preview
            f.write("\nSAMPLE DATA (first 3 rows):\n")
            f.write("-" * 50 + "\n")
            
            for i, row in enumerate(rows[:3]):
                f.write(f"Row {i+1}:\n")
                for col_name, value in zip(columns, row):
                    # Format the output nicely
                    if col_name == 'created_at' and value:
                        try:
                            # Format datetime nicely
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                            f.write(f"  {col_name}: {formatted_date}\n")
                        except:
                            f.write(f"  {col_name}: {value}\n")
                    else:
                        f.write(f"  {col_name}: {value}\n")
                f.write("\n")
    
    print(f"📊 Export summary saved to {summary_filename}")

def verify_sqlite_data():
    """Verify the CORRECT SQLite database and flight_calculations table exists"""
    
    try:
        # Check the CORRECT database (without _v2)
        sqlite_conn = sqlite3.connect('flight_calculator.db')
        sqlite_cursor = sqlite_conn.cursor()
        
        # Check if flight_calculations table exists
        sqlite_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='flight_calculations'
        """)
        
        table_exists = sqlite_cursor.fetchone()
        
        if not table_exists:
            print("❌ ERROR: 'flight_calculations' table not found in flight_calculator.db")
            return False
        
        # Check row count
        sqlite_cursor.execute("SELECT COUNT(*) FROM flight_calculations")
        row_count = sqlite_cursor.fetchone()[0]
        
        print(f"✅ flight_calculations table found with {row_count} rows")
        
        # Show table structure
        sqlite_cursor.execute("PRAGMA table_info(flight_calculations)")
        columns = sqlite_cursor.fetchall()
        
        print("\nTable structure:")
        for col in columns:
            pk_indicator = " (PRIMARY KEY)" if col[5] > 0 else ""
            notnull_indicator = " NOT NULL" if col[3] else ""
            print(f"  {col[1]} ({col[2]}){pk_indicator}{notnull_indicator}")
        
        sqlite_conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ SQLite database error: {e}")
        return False

def preview_export_data():
    """Preview what will be exported"""
    
    sqlite_conn = sqlite3.connect('flight_calculator.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    print("\n📋 DATA PREVIEW (first 2 rows):")
    print("-" * 50)
    
    sqlite_cursor.execute("SELECT * FROM flight_calculations LIMIT 2")
    rows = sqlite_cursor.fetchall()
    
    # Get column names
    sqlite_cursor.execute("PRAGMA table_info(flight_calculations)")
    columns = [col[1] for col in sqlite_cursor.fetchall()]
    
    for i, row in enumerate(rows):
        print(f"Row {i+1}:")
        for col_name, value in zip(columns, row):
            print(f"  {col_name}: {value}")
        print()
    
    sqlite_conn.close()

if __name__ == "__main__":
    print("🚀 Exporting flight_calculations data to SQL Server INSERT scripts...")
    print("=" * 60)
    print("NOTE: Using flight_calculator.db (the correct database with data!)")
    print("=" * 60)
    
    # First verify the data exists in the CORRECT database
    if verify_sqlite_data():
        # Show data preview
        preview_export_data()
        
        print("\n" + "=" * 60)
        # Proceed with export
        export_flight_calculations_to_sql_server()
    else:
        print("\n❌ Cannot proceed with export. Please check your SQLite database.")