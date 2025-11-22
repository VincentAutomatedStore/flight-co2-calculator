import sqlite3
import json
from datetime import datetime

def export_sqlite_to_sql_server_scripts():
    """Export SQLite data to SQL Server INSERT scripts"""
    
    # Connect to SQLite database
    sqlite_conn = sqlite3.connect('flight_calculator_v2.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Get all tables
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in sqlite_cursor.fetchall()]
    
    print(f"Found tables: {tables}")
    
    # Export data for each table
    for table in tables:
        if table == 'sqlite_sequence':  # Skip SQLite internal table
            continue
            
        print(f"\nExporting data from table: {table}")
        
        # Get table structure
        sqlite_cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in sqlite_cursor.fetchall()]
        
        # Get all data
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        # Generate SQL Server INSERT statements
        insert_statements = []
        
        for row in rows:
            values = []
            for i, value in enumerate(row):
                if value is None:
                    values.append("NULL")
                elif isinstance(value, str):
                    # Escape single quotes and handle strings
                    escaped_value = value.replace("'", "''")
                    values.append(f"'{escaped_value}'")
                elif isinstance(value, (int, float)):
                    values.append(str(value))
                elif isinstance(value, datetime):
                    values.append(f"'{value.isoformat()}'")
                else:
                    values.append(f"'{str(value)}'")
            
            columns_str = ", ".join([f"[{col}]" for col in columns])
            values_str = ", ".join(values)
            
            insert_stmt = f"INSERT INTO [{table}] ({columns_str}) VALUES ({values_str});"
            insert_statements.append(insert_stmt)
        
        # Write to file
        filename = f"sqlserver_{table}_inserts.sql"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"-- INSERT statements for table: {table}\n")
            f.write(f"-- Generated on: {datetime.now().isoformat()}\n")
            f.write(f"-- Total rows: {len(insert_statements)}\n\n")
            
            for stmt in insert_statements:
                f.write(stmt + "\n")
        
        print(f"✅ Exported {len(insert_statements)} rows to {filename}")
    
    sqlite_conn.close()
    print("\n🎉 Export completed!")

def export_airports_specific():
    """Export just airports data with proper SQL Server syntax"""
    
    sqlite_conn = sqlite3.connect('flight_calculator_v2.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Export airports table
    sqlite_cursor.execute("SELECT * FROM airports")
    airports = sqlite_cursor.fetchall()
    
    # Get column names
    sqlite_cursor.execute("PRAGMA table_info(airports)")
    columns = [row[1] for row in sqlite_cursor.fetchall()]
    
    insert_statements = []
    
    for airport in airports:
        values = []
        for i, value in enumerate(airport):
            col_name = columns[i]
            
            if value is None:
                if col_name == 'icao_code':
                    values.append("NULL")  # Explicit NULL for icao_code
                else:
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
        
        insert_stmt = f"INSERT INTO [airports] ({columns_str}) VALUES ({values_str});"
        insert_statements.append(insert_stmt)
    
    # Write airports to file
    with open('sqlserver_airports_inserts.sql', 'w', encoding='utf-8') as f:
        f.write("-- AIRPORTS INSERT STATEMENTS\n")
        f.write("-- Generated for SQL Server\n\n")
        
        for stmt in insert_statements:
            f.write(stmt + "\n")
    
    print(f"✅ Exported {len(insert_statements)} airports to sqlserver_airports_inserts.sql")
    sqlite_conn.close()

if __name__ == "__main__":
    print("Exporting SQLite data to SQL Server INSERT scripts...")
    export_sqlite_to_sql_server_scripts()
    export_airports_specific()