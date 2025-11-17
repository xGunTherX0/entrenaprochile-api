"""
Set or update the `youtube_url` value for an entrenador identified by `usuario_id`.
Usage (PowerShell, from repo root):
    python .\scripts\set_trainer_youtube.py --usuario_id 7 --url "https://youtube.com/channel/ABC123"

This script is safe for development SQLite. It will report whether a row was updated.
"""
import os
import sqlite3
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--usuario_id', type=int, required=True, help='usuario.id of the entrenador')
    parser.add_argument('--url', type=str, required=True, help='YouTube URL to set')
    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(repo_root, 'database', 'entrenapro.db')
    if not os.path.exists(db_path):
        print('ERROR: database file not found at', db_path)
        return 2

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        # Check trainer exists
        row = cur.execute('SELECT id, usuario_id, youtube_url FROM entrenadores WHERE usuario_id = ?', (args.usuario_id,)).fetchone()
        if not row:
            print(f'No entrenador row found for usuario_id={args.usuario_id}')
            return 3
        # Update
        cur.execute('UPDATE entrenadores SET youtube_url = ? WHERE usuario_id = ?', (args.url, args.usuario_id))
        conn.commit()
        print(f'Updated usuario_id={args.usuario_id} youtube_url -> {args.url}')
        return 0
    except Exception as e:
        print('ERROR:', e)
        return 4
    finally:
        conn.close()

if __name__ == '__main__':
    raise SystemExit(main())
