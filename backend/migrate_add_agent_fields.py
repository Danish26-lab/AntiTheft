"""
Migration: add agent-specific hardware fields to devices and create device_link_tokens table.
Run once with backend stopped.
"""
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "antitheft.db")


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cursor.fetchall()]


def table_exists(cursor, table):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None


def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()

        # Add new device columns
        new_cols = [
            ("brand", "VARCHAR(100)"),
            ("model_name", "VARCHAR(150)"),
            ("cpu_info", "VARCHAR(200)"),
            ("hostname", "VARCHAR(150)")
        ]
        for col, col_type in new_cols:
            if not column_exists(cur, "devices", col):
                print(f"Adding column: {col} ({col_type})")
                cur.execute(f"ALTER TABLE devices ADD COLUMN {col} {col_type}")
            else:
                print(f"Column exists, skipping: {col}")

        # Create device_link_tokens table if not present
        if not table_exists(cur, "device_link_tokens"):
            print("Creating table: device_link_tokens")
            cur.execute(
                """
                CREATE TABLE device_link_tokens (
                    id INTEGER PRIMARY KEY,
                    token VARCHAR(64) NOT NULL UNIQUE,
                    user_id INTEGER NOT NULL,
                    expires_at DATETIME NOT NULL,
                    used BOOLEAN DEFAULT 0,
                    used_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """
            )
        else:
            print("Table device_link_tokens already exists, skipping.")

        conn.commit()
        print("Migration completed.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

