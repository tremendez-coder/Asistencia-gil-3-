''' import cv2
import sqlite3

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('recognizer/recognizer.yml')

detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Conectar a base de datos
conn = sqlite3.connect('recognizer/database.db')
cursor = conn.cursor()
cursor.execute("SELECT id, nombre FROM personas")
personas = dict(cursor.fetchall())
conn.close()

cam = cv2.VideoCapture(0)

while True:
    ret, frame = cam.read()
    if not ret:
        break

    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rostros = detector.detectMultiScale(gris, 1.3, 5)

    for (x, y, w, h) in rostros:
        rostro = gris[y:y+h, x:x+w]
        id_, conf = recognizer.predict(rostro)
        nombre = personas.get(id_, 'Desconocido') if conf < 30 else 'Desconocido'
        color = (0, 255, 0) if nombre != 'Desconocido' else (0, 0, 255)

        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, f"{nombre} ({int(conf)})", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow('Reconociendo...', frame)
    if cv2.waitKey(1) == 27:  # ESC para salir
        break

cam.release()
cv2.destroyAllWindows() ''' 