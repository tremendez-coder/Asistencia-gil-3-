import cv2
import os
import sqlite3

# Crear carpeta de rostros si no existe
faces_dir = os.path.join('recognizer', 'faces')
os.makedirs(faces_dir, exist_ok=True)

# Conexión a la base de datos
conn = sqlite3.connect(os.path.join('recognizer', 'database.db'))
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

# Ingreso de nombre
while True:
    nombre = input("Ingrese el nombre del alumno: ").strip()
    if nombre:
        break
    print("El nombre no puede estar vacío.")

cursor.execute("INSERT INTO personas (nombre) VALUES (?)", (nombre,))
id_persona = cursor.lastrowid
conn.commit()
conn.close()

# Captura de rostro
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
        filename = f'usuario.{id_persona}.{count}.jpg'
        cv2.imwrite(os.path.join(faces_dir, filename), rostro)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    cv2.imshow('Capturando rostros', frame)
    if cv2.waitKey(1) == 27 or count >= 500:
        break

cam.release()
cv2.destroyAllWindows()
print(f"[INFO] Se capturaron {count} imágenes para {nombre}")
