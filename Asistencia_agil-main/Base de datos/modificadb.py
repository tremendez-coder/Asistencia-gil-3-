# modificadb.py
import sqlite3

conn = sqlite3.connect('recognizer/database.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE personas ADD COLUMN hora_marcado TEXT")
    print("Columna 'hora_marcado' agregada.")
except sqlite3.OperationalError:
    print("La columna ya existe.")

conn.commit()
conn.close()