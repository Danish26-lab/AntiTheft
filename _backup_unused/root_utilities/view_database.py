#!/usr/bin/env python3
"""
Simple script to view database contents
"""

import sqlite3
import sys
from pathlib import Path

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

# Get database path
database_dir = Path(__file__).parent / 'database'
db_path = database_dir / 'antitheft.db'

if not db_path.exists():
    print(f"Database not found at: {db_path}")
    sys.exit(1)

print(f"Database: {db_path}")
print("=" * 60)
print()

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    if not tables:
        print("No tables found in database.")
        sys.exit(0)
    
    print(f"Found {len(tables)} table(s):\n")
    
    for (table_name,) in tables:
        print(f"\n{'='*60}")
        print(f"Table: {table_name}")
        print('='*60)
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"Rows: {count}\n")
        
        if count > 0:
            # Get all data
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            
            # Display data in table format
            if HAS_TABULATE:
                print(tabulate(rows, headers=columns, tablefmt='grid'))
            else:
                # Simple table format without tabulate
                # Print header
                header = " | ".join(f"{col:15}" for col in columns)
                print(header)
                print("-" * len(header))
                # Print rows
                for row in rows:
                    row_str = " | ".join(f"{str(val):15}" for val in row)
                    print(row_str)
        else:
            print("(empty)")
        
        print()
    
    conn.close()
    print("Database viewed successfully!")
    
except sqlite3.Error as e:
    print(f"Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

