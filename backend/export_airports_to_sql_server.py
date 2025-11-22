import sqlite3
import os
from datetime import datetime

def discover_database_tables():
    """Discover what tables exist in the database"""
    
    backend_db_path = r'C:\Users\makro\Documents\0 - Flight CO2 Calculator App\flight-co2-calculator\backend\flight_calculator.db'
    
    print("🔍 DISCOVERING DATABASE TABLES")
    print("=" * 50)
    
    if not os.path.exists(backend_db_path):
        print(f"❌ Database not found: {backend_db_path}")
        return None, None
    
    try:
        conn = sqlite3.connect(backend_db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Tables found in database:")
        for table in tables:
            print(f"  - {table}")
            
            # Show row count for each table
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                print(f"    Rows: {row_count}")
                
                # Show column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"    Columns: {', '.join(columns)}")
                
            except Exception as e:
                print(f"    Error reading table: {e}")
            
            print()
        
        # Identify which table contains airports data
        airport_tables = []
        for table in tables:
            if 'airport' in table.lower():
                airport_tables.append(table)
            elif table.lower() in ['airports', 'airport']:
                airport_tables.append(table)
        
        conn.close()
        
        return tables, airport_tables
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        return None, None

def find_airports_table():
    """Find the actual airports table by examining data"""
    
    backend_db_path = r'C:\Users\makro\Documents\0 - Flight CO2 Calculator App\flight-co2-calculator\backend\flight_calculator.db'
    
    print("\n🔍 SEARCHING FOR AIRPORTS TABLE")
    print("=" * 50)
    
    if not os.path.exists(backend_db_path):
        return None
    
    try:
        conn = sqlite3.connect(backend_db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check each table for airport-like data
        candidate_tables = []
        
        for table in tables:
            try:
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1].lower() for col in cursor.fetchall()]
                
                # Check if this looks like an airports table
                airport_indicators = 0
                if 'iata' in str(columns) or 'code' in str(columns):
                    airport_indicators += 1
                if 'name' in str(columns):
                    airport_indicators += 1
                if 'city' in str(columns):
                    airport_indicators += 1
                if 'country' in str(columns):
                    airport_indicators += 1
                
                if airport_indicators >= 2:  # At least 2 airport-like columns
                    cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                    sample_row = cursor.fetchone()
                    
                    candidate_tables.append({
                        'name': table,
                        'columns': columns,
                        'sample': sample_row,
                        'score': airport_indicators
                    })
                    
            except Exception as e:
                continue
        
        # Sort by score (most likely first)
        candidate_tables.sort(key=lambda x: x['score'], reverse=True)
        
        print("Potential airports tables found:")
        for candidate in candidate_tables:
            print(f"  📊 Table: {candidate['name']} (score: {candidate['score']}/4)")
            print(f"     Columns: {candidate['columns']}")
            if candidate['sample']:
                print(f"     Sample: {candidate['sample']}")
            print()
        
        conn.close()
        
        if candidate_tables:
            return candidate_tables[0]['name']  # Return the most likely table
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error searching for airports table: {e}")
        return None

def export_airports_data(table_name):
    """Export airports data from the specified table"""
    
    backend_db_path = r'C:\Users\makro\Documents\0 - Flight CO2 Calculator App\flight-co2-calculator\backend\flight_calculator.db'
    
    print(f"🚀 EXPORTING DATA FROM TABLE: {table_name}")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect(backend_db_path)
        cursor = conn.cursor()
        
        # Get table structure
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        columns = [col[1] for col in columns_info]
        
        print(f"📋 Table structure: {', '.join(columns)}")
        
        # Get total row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cursor.fetchone()[0]
        print(f"📊 Total rows: {total_rows}")
        
        if total_rows == 0:
            print("❌ No data found in table")
            return
        
        # Get all data
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY {columns[0]}")
        data = cursor.fetchall()
        
        # Generate SQL Server INSERT script
        filename = f"sqlserver_{table_name}_exports.sql"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"-- SQL Server INSERT statements for table: {table_name}\n")
            f.write(f"-- Generated on: {datetime.now().isoformat()}\n")
            f.write(f"-- Total rows: {total_rows}\n")
            f.write(f"-- Source: SQLite database\n\n")
            
            # Check if we should use identity insert (if there's an ID column)
            has_id_column = any(col[1].lower() == 'id' for col in columns_info)
            if has_id_column:
                f.write("-- Enable identity insert to preserve original IDs\n")
                f.write(f"SET IDENTITY_INSERT [{table_name}] ON;\n\n")
            
            # Write data in batches
            batch_size = 100
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                f.write(f"-- Batch {i//batch_size + 1}: Rows {i+1} to {i+len(batch)}\n")
                
                for row in batch:
                    values = []
                    for value in row:
                        if value is None:
                            values.append("NULL")
                        elif isinstance(value, str):
                            escaped_value = value.replace("'", "''")
                            values.append(f"'{escaped_value}'")
                        elif isinstance(value, (int, float)):
                            values.append(str(value))
                        else:
                            values.append(f"'{str(value)}'")
                    
                    columns_str = ", ".join([f"[{col}]" for col in columns])
                    values_str = ", ".join(values)
                    
                    insert_sql = f"INSERT INTO [{table_name}] ({columns_str}) VALUES ({values_str});"
                    f.write(insert_sql + "\n")
                
                f.write("\n")
            
            if has_id_column:
                f.write("-- Disable identity insert after import\n")
                f.write(f"SET IDENTITY_INSERT [{table_name}] OFF;\n")
        
        print(f"✅ Exported to: {filename}")
        
        # Generate summary
        generate_data_summary(table_name, data, columns, total_rows)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")

def generate_data_summary(table_name, data, columns, total_rows):
    """Generate a summary of the exported data"""
    
    filename = f"{table_name}_export_summary.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"EXPORT SUMMARY - TABLE: {table_name}\n")
        f.write("=" * 50 + "\n")
        f.write(f"Export Date: {datetime.now().isoformat()}\n")
        f.write(f"Total Rows: {total_rows}\n")
        f.write(f"Columns: {', '.join(columns)}\n\n")
        
        # Show sample data
        f.write("SAMPLE DATA (first 10 rows):\n")
        f.write("-" * 40 + "\n")
        for i in range(min(10, len(data))):
            f.write(f"Row {i+1}:\n")
            for col_name, value in zip(columns, data[i]):
                f.write(f"  {col_name}: {value}\n")
            f.write("\n")
    
    print(f"📊 Summary generated: {filename}")

def main():
    """Main function to discover and export airports data"""
    
    print("🚀 AUTOMATIC DATABASE TABLE DISCOVERY AND EXPORT")
    print("=" * 70)
    
    # First discover all tables
    all_tables, airport_tables = discover_database_tables()
    
    if not all_tables:
        print("❌ No tables found in database")
        return
    
    # If we found obvious airport tables, use them
    if airport_tables:
        print(f"🎯 Found airport tables: {airport_tables}")
        table_name = airport_tables[0]  # Use the first one
    else:
        # Otherwise, search more thoroughly
        print("\n🔄 No obvious airport tables found, searching more thoroughly...")
        table_name = find_airports_table()
    
    if not table_name:
        print("❌ Could not identify airports table automatically")
        print("\nPlease specify the table name manually:")
        for table in all_tables:
            print(f"  - {table}")
        return
    
    print(f"\n🎯 USING TABLE: {table_name}")
    
    # Export the data
    export_airports_data(table_name)
    
    print(f"\n🎉 EXPORT COMPLETED!")

if __name__ == "__main__":
    main()