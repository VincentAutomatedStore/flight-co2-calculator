import sqlite3
import os

def quick_database_info(db_path='flight_calculator_v2.db'):
    """Quick overview of SQLite database"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    # Get file size
    file_size = os.path.getsize(db_path) / (1024 * 1024)  # Convert to MB
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"📁 Database: {db_path}")
    print(f"📏 Size: {file_size:.2f} MB")
    print("=" * 50)
    
    # Get all tables with row counts
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 Found {len(tables)} tables:\n")
    
    for table in tables:
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        
        # Get columns
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"┌─ {table} ({row_count} rows)")
        print(f"├─ Columns: {', '.join(column_names)}")
        
        # Check for primary key
        pk_columns = [col[1] for col in columns if col[5] > 0]
        if pk_columns:
            print(f"└─ Primary Key: {', '.join(pk_columns)}")
        else:
            print(f"└─ No primary key")
        
        print()
    
    conn.close()

# Run the quick overview
quick_database_info()