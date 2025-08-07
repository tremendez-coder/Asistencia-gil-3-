import sqlite3

# Conexión a la base de datos
conn = sqlite3.connect('recognizer/database.db')
cursor = conn.cursor()

# Crear la tabla personas si no existe
cursor.execute('''
    CREATE TABLE IF NOT EXISTS personas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        dni TEXT UNIQUE,
        presente TEXT DEFAULT 'ausente',
        hora_marcado TEXT
    )
''')

# Mostrar las filas (si existen)
cursor.execute("SELECT * FROM personas")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.commit()
conn.close()
