"""
One-time migration script to add browser-device fields to the devices table.

Run this once (with the backend stopped) after updating models.Device to include:
  - os
  - browser
  - platform
  - user_agent
  - screen_resolution
  - timezone
  - last_ip
  - is_primary
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "antitheft.db")


def column_exists(cursor, table_name: str, column_name: str) -> bool:
  cursor.execute(f"PRAGMA table_info({table_name})")
  columns = [row[1] for row in cursor.fetchall()]
  return column_name in columns


def main():
  if not os.path.exists(DB_PATH):
    print(f"Database not found at {DB_PATH}. Nothing to migrate.")
    return

  conn = sqlite3.connect(DB_PATH)
  try:
    cursor = conn.cursor()

    # Add columns only if they don't already exist (idempotent)
    migrations = [
      ("os", "VARCHAR(100)"),
      ("browser", "VARCHAR(100)"),
      ("platform", "VARCHAR(100)"),
      ("user_agent", "TEXT"),
      ("screen_resolution", "VARCHAR(50)"),
      ("timezone", "VARCHAR(100)"),
      ("last_ip", "VARCHAR(45)"),
      ("is_primary", "BOOLEAN DEFAULT 0"),
    ]

    for column_name, column_type in migrations:
      if not column_exists(cursor, "devices", column_name):
        sql = f"ALTER TABLE devices ADD COLUMN {column_name} {column_type}"
        print(f"Adding column: {column_name} ({column_type})")
        cursor.execute(sql)
      else:
        print(f"Column already exists, skipping: {column_name}")

    conn.commit()
    print("Browser device fields migration completed successfully.")
  finally:
    conn.close()


if __name__ == "__main__":
  main()

