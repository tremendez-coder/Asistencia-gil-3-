import sqlite3

conn = sqlite3.connect('recognizer/database.db')
cursor = conn.cursor()

cursor.execute("DELETE FROM personas")
conn.commit()
conn.close()

print("[INFO] Tabla 'personas' vaciada correctamente.")
