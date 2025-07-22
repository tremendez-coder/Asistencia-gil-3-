# creardb.py
import sqlite3

conn = sqlite3.connect('recognizer/database.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS personas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        presente TEXT DEFAULT 'ausente',
        hora_marcado TEXT
    ) 
''')
conn.commit()
conn.close()
print("[INFO] Base de datos y tabla creadas correctamente.")
