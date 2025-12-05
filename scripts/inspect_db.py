import sqlite3
import os
p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'entrenapro.db')
print('DB file:', p)
print('Exists:', os.path.exists(p))
conn = sqlite3.connect(p)
c = conn.cursor()
print('Tables:', [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
print('\nentrenadores columns:')
for col in c.execute('PRAGMA table_info(entrenadores)').fetchall():
    print(col)
print('\npassword_reset_tokens columns:')
for col in c.execute('PRAGMA table_info(password_reset_tokens)').fetchall():
    print(col)
conn.close()
