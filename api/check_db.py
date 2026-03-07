"""
Simple script to check database tables
"""
import sqlite3
import sys
import io
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

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
    exit(1)
if not db_path.exists():
    print("ERROR: Database file not found!")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

print(f"Current tables in database: {tables}")

if 'users' in tables:
    # Check users table structure
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print(f"\nOK: Users table exists with {len(columns)} columns:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
else:
    print("\nWARNING: Users table does NOT exist yet!")
    print("   -> Restart your FastAPI server to create it automatically")

if 'jobs' in tables:
    # Check jobs table structure
    cursor.execute("PRAGMA table_info(jobs)")
    columns = cursor.fetchall()
    print(f"\nOK: Jobs table exists with {len(columns)} columns")
    # Check if user_id exists
    column_names = [col[1] for col in columns]
    if 'user_id' in column_names:
        print("   OK: user_id column exists in jobs table")
    else:
        print("   WARNING: user_id column does NOT exist in jobs table yet")

conn.close()

