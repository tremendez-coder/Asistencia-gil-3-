'''
#reconociendo.py 
Sirve para hacer las pruebas dentro del sistema sin necesidad del entorno web
'''
import cv2
import sqlite3
import datetime
from utils.antispoofing import rostro_real

cam = cv2.VideoCapture(0)

conn = sqlite3.connect('recognizer/database.db')
cursor = conn.cursor()
cursor.execute("SELECT id, nombre FROM personas")
personas = dict(cursor.fetchall())
conn.close()

while True:
    ret, frame = cam.read()
    if not ret:
        break

    nombre_detectado, frame_mostrado = rostro_real(frame, personas)

    if nombre_detectado:
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect('recognizer/database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE personas SET presente = 'presente', hora_marcado = ? WHERE nombre = ?", (ahora, nombre_detectado))
            conn.commit()

    cv2.imshow("Reconocimiento", frame_mostrado)
    if cv2.waitKey(1) == 27:
        break

cam.release()
cv2.destroyAllWindows()
print("[INFO] Reconocimiento finalizado")