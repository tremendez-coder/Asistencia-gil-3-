import cv2
import time

# Cargamos modelos solo una vez
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('recognizer/recognizer.yml')

# Control para evitar múltiples reconocimientos seguidos
ultimo_nombre = None
ultimo_tiempo = 0

def rostro_real(frame, personas):
    global ultimo_nombre, ultimo_tiempo

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    rostros = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(100, 100),  # No detectar caras muy chicas
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    for (x, y, w, h) in rostros:
        rostro = gray[y:y+h, x:x+w]
        id_, conf = recognizer.predict(rostro)

        nombre = personas.get(id_, 'Desconocido') if conf < 60 else 'Desconocido'

        color = (0, 255, 0) if nombre != 'Desconocido' else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, f"{nombre} ({int(conf)})", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # ✅ Solo devolvemos si han pasado 2 segundos desde la última detección
        if nombre != 'Desconocido' and (time.time() - ultimo_tiempo > 2 or nombre != ultimo_nombre):
            ultimo_nombre = nombre
            ultimo_tiempo = time.time()
            return nombre, frame

    return None, frame
