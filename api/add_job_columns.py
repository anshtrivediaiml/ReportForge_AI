"""
Script to add new columns to the jobs table for user association
This is safe because user_id is nullable - existing jobs will work fine
"""
import sqlite3
import sys
from pathlib import Path

# Try multiple possible paths
possible_paths = [
    Path("reportforge.db"),  # If run from api directory
    Path("api/reportforge.db"),  # If run from project root
]

db_path = None
for path in possible_paths:
    if path.exists():
        db_path = path
        break

if db_path is None:
    print("ERROR: Database file not found!")
    print(f"   Searched: {[str(p) for p in possible_paths]}")
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("Checking jobs table structure...")

# Get current columns
cursor.execute("PRAGMA table_info(jobs)")
existing_columns = [row[1] for row in cursor.fetchall()]
print(f"Current columns: {existing_columns}")

# Columns to add (all nullable for backward compatibility)
columns_to_add = [
    ("user_id", "INTEGER"),
    ("title", "VARCHAR(200)"),
    ("original_filename", "VARCHAR(255)"),
    ("file_size", "BIGINT"),
    ("processing_time", "REAL"),
]

added_columns = []
for col_name, col_type in columns_to_add:
    if col_name not in existing_columns:
        try:
            # SQLite doesn't support adding foreign keys directly, so we add the column first
            if col_name == "user_id":
                # Add column without foreign key constraint (SQLite limitation)
                cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
                print(f"  Added column: {col_name} ({col_type})")
                added_columns.append(col_name)
            else:
                cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
                print(f"  Added column: {col_name} ({col_type})")
                added_columns.append(col_name)
        except sqlite3.OperationalError as e:
            print(f"  ERROR adding {col_name}: {e}")
    else:
        print(f"  Column {col_name} already exists, skipping")

if added_columns:
    conn.commit()
    print(f"\nSUCCESS: Added {len(added_columns)} column(s) to jobs table")
    print(f"  Added: {', '.join(added_columns)}")
    print("\nNote: Foreign key constraint will be enforced by SQLAlchemy")
    print("      All new columns are nullable, so existing jobs are safe")
else:
    print("\nAll columns already exist - no changes needed")

# Verify
cursor.execute("PRAGMA table_info(jobs)")
columns = cursor.fetchall()
print(f"\nFinal jobs table has {len(columns)} columns")
if 'user_id' in [col[1] for col in columns]:
    print("  OK: user_id column now exists")

conn.close()

