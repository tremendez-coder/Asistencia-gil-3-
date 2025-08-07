import cv2
import os
import sqlite3

# Crear carpeta si no existe
if not os.path.exists('recognizer/faces'):
    os.makedirs('recognizer/faces')

# Conectar a la base de datos
conn = sqlite3.connect('recognizer/database.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS personas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        presente TEXT DEFAULT 'ausente'
    )
''')
conn.commit()

# Pedir nombre
nombre = input("Ingrese el nombre del alumno: ")

# Insertar en la base
cursor.execute("INSERT INTO personas (nombre) VALUES (?)", (nombre,))
id_persona = cursor.lastrowid
conn.commit()
conn.close()

# Capturar video
cam = cv2.VideoCapture(0)
detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
count = 0

while True:
    ret, frame = cam.read()
    if not ret:
        break
    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rostros = detector.detectMultiScale(gris, 1.3, 5)

    for (x, y, w, h) in rostros:
        count += 1
        rostro = gris[y:y+h, x:x+w]
        cv2.imwrite(f'recognizer/faces/usuario.{id_persona}.{count}.jpg', rostro)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    cv2.imshow('Capturando rostros', frame)
    if cv2.waitKey(1) == 27 or count >= 700:  # ESC para salir
        break

cam.release()
cv2.destroyAllWindows()
print(f"[INFO] Se capturaron {count} imágenes para {nombre}")
