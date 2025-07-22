# eliminabd.py
import sqlite3
import os

ruta_bd = 'recognizer/database.db'

if not os.path.exists(ruta_bd):
    print("[ERROR] No se encontró la base de datos recognizer/database.db")
    exit()

conn = sqlite3.connect(ruta_bd)
cursor = conn.cursor()

# Eliminar la tabla si existe
cursor.execute("DROP TABLE IF EXISTS personas")

# Crear la tabla limpia desde cero
cursor.execute("""
    CREATE TABLE personas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        presente TEXT DEFAULT 'ausente',
        hora_marcado TEXT
    )
""")

conn.commit()
conn.close()
print("[INFO] Tabla 'personas' reiniciada correctamente.")
