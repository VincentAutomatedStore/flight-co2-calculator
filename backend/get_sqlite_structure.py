import sqlite3
import json
from datetime import datetime

def get_database_structure(db_path='flight_calculator.db'):
    """Get complete SQLite database structure"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"📊 SQLite Database Structure: {db_path}")
        print("=" * 60)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
        
        print("\n" + "=" * 60)
        
        database_info = {
            'database_name': db_path,
            'export_date': datetime.now().isoformat(),
            'tables': {}
        }
        
        # Get structure for each table
        for table in tables:
            if table == 'sqlite_sequence':  # Skip SQLite internal table
                continue
                
            print(f"\n📋 Table: {table}")
            print("-" * 40)
            
            # Get column information
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            table_info = {
                'columns': [],
                'row_count': 0,
                'indexes': [],
                'foreign_keys': []
            }
            
            print("Columns:")
            for col in columns:
                col_info = {
                    'cid': col[0],
                    'name': col[1],
                    'type': col[2],
                    'notnull': bool(col[3]),
                    'default_value': col[4],
                    'pk': bool(col[5])
                }
                table_info['columns'].append(col_info)
                
                # Print column details
                pk_indicator = " (PRIMARY KEY)" if col[5] else ""
                notnull_indicator = " NOT NULL" if col[3] else ""
                default_indicator = f" DEFAULT {col[4]}" if col[4] is not None else ""
                print(f"  ├─ {col[1]} ({col[2]}){pk_indicator}{notnull_indicator}{default_indicator}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            table_info['row_count'] = row_count
            print(f"  └─ Row count: {row_count}")
            
            # Get indexes
            cursor.execute(f"PRAGMA index_list({table})")
            indexes = cursor.fetchall()
            
            if indexes:
                print("Indexes:")
                for idx in indexes:
                    index_name = idx[1]
                    unique = "UNIQUE" if idx[2] else "INDEX"
                    table_info['indexes'].append({
                        'name': index_name,
                        'unique': bool(idx[2]),
                        'origin': idx[3]
                    })
                    print(f"  ├─ {unique}: {index_name}")
                    
                    # Get index columns
                    cursor.execute(f"PRAGMA index_info({index_name})")
                    index_cols = cursor.fetchall()
                    col_names = [col[2] for col in index_cols]
                    print(f"  └─ Columns: {', '.join(col_names)}")
            
            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            foreign_keys = cursor.fetchall()
            
            if foreign_keys:
                print("Foreign Keys:")
                for fk in foreign_keys:
                    fk_info = {
                        'id': fk[0],
                        'seq': fk[1],
                        'table': fk[2],
                        'from_column': fk[3],
                        'to_column': fk[4],
                        'on_update': fk[5],
                        'on_delete': fk[6],
                        'match': fk[7]
                    }
                    table_info['foreign_keys'].append(fk_info)
                    print(f"  └─ {fk[3]} → {fk[2]}.{fk[4]}")
            
            database_info['tables'][table] = table_info
        
        conn.close()
        
        # Save to JSON file
        json_filename = f"sqlite_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(database_info, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Database structure saved to: {json_filename}")
        return database_info
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return None

def generate_sql_schema(db_path='flight_calculator.db'):
    """Generate SQL CREATE statements from SQLite database"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        sql_filename = f"sqlite_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        with open(sql_filename, 'w', encoding='utf-8') as f:
            f.write(f"-- SQLite Database Schema\n")
            f.write(f"-- Generated: {datetime.now().isoformat()}\n")
            f.write(f"-- Database: {db_path}\n\n")
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                if table == 'sqlite_sequence':
                    continue
                    
                # Get CREATE TABLE statement
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                create_stmt = cursor.fetchone()[0]
                
                f.write(f"-- Table: {table}\n")
                f.write(create_stmt + ";\n\n")
                
                # Get CREATE INDEX statements
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{table}'")
                indexes = cursor.fetchall()
                
                for idx in indexes:
                    if idx[0]:  # Ensure it's not None
                        f.write(idx[0] + ";\n")
                
                f.write("\n")
        
        conn.close()
        print(f"✅ SQL schema saved to: {sql_filename}")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")

def get_table_sample_data(db_path='flight_calculator.db', table_name='flight_calculations', limit=5):
    """Get sample data from a specific table"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n📋 Sample data from table: {table_name}")
        print("-" * 50)
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        print("Columns:", ", ".join(columns))
        print()
        
        # Get sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        print(f"Sample data (first {len(rows)} rows):")
        for i, row in enumerate(rows):
            print(f"Row {i+1}:")
            for col_name, value in zip(columns, row):
                # Truncate long values for display
                display_value = str(value)
                if len(display_value) > 50:
                    display_value = display_value[:47] + "..."
                print(f"  {col_name}: {display_value}")
            print()
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Error reading table {table_name}: {e}")

if __name__ == "__main__":
    db_path = 'flight_calculator.db'  # Change this if your DB has different name
    
    print("🔍 SQLite Database Structure Explorer")
    print("=" * 50)
    
    # 1. Get complete database structure
    structure = get_database_structure(db_path)
    
    # 2. Generate SQL schema
    generate_sql_schema(db_path)
    
    # 3. Get sample data from flight_calculations table
    get_table_sample_data(db_path, 'flight_calculations')
    
    print("\n🎉 All operations completed!")