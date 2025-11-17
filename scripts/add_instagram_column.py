"""
Small helper to add the `instagram_url` column to the `entrenadores` table
in the development SQLite database `database/entrenapro.db`.

Usage (PowerShell, from repo root):
    python .\scripts\add_instagram_column.py

This script:
- Resolves the repo root relative to this script file.
- Opens the SQLite file at `database/entrenapro.db`.
- Uses `PRAGMA table_info(entrenadores)` to check for the column.
- If missing, runs `ALTER TABLE ... ADD COLUMN instagram_url VARCHAR(255)`
  and commits the change.

This is intended for development only.
"""
import os
import sqlite3

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(repo_root, 'database', 'entrenapro.db')
    print(f"Repository root: {repo_root}")
    print(f"Database file: {db_path}")

    if not os.path.exists(db_path):
        print("ERROR: database file not found at:", db_path)
        return 2

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("PRAGMA table_info(entrenadores)")
        cols = cur.fetchall()
        col_names = [c[1] for c in cols]
        print("Existing columns:", col_names)

        to_add = []
        if 'instagram_url' not in col_names:
            to_add.append(('instagram_url', "VARCHAR(255)"))
        if 'youtube_url' not in col_names:
            to_add.append(('youtube_url', "VARCHAR(255)"))

        if not to_add:
            print("Columns 'instagram_url' and 'youtube_url' already exist. Nothing to do.")
            return 0

        for col_name, col_type in to_add:
            print(f"Adding column '{col_name}' to table 'entrenadores'...")
            try:
                cur.execute(f"ALTER TABLE entrenadores ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"Done: column '{col_name}' added.")
            except Exception as e:
                print(f"Failed to add column {col_name}:", e)
                print("No further automatic recovery attempted. If this fails, consider manual migration or restoring a DB backup.")
                return 3
        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    raise SystemExit(main())
