import cv2
import os
import numpy as np
from PIL import Image
import requests # Agregado para hacer peticiones HTTP

# Rutas
datasets_path = './face_recognition/datasets'
trainer_path = './face_recognition/trainer/trainer.yml'

# URL base de la API de Flask
FLASK_API_BASE_URL = "http://127.0.0.1:5000"

def get_images_and_labels(path):
    image_paths = [os.path.join(path, f) for f in os.listdir(path) if not f.startswith('.')]
    face_samples = []
    ids = []
    for image_path in image_paths:
        PIL_img = Image.open(image_path).convert('L') # Convertir a escala de grises
        img_numpy = np.array(PIL_img, 'uint8')
        # Extraer el ID del alumno del nombre del archivo (user_ID_numero.jpg)
        id = int(os.path.split(image_path)[-1].split('_')[1])
        face_samples.append(img_numpy)
        ids.append(id)
    return face_samples, ids

def train_recognizer():
    # Crear el entrenador LBPH
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    # Asegurarse de que el directorio del entrenador exista
    trainer_dir = os.path.dirname(trainer_path)
    if not os.path.exists(trainer_dir):
        os.makedirs(trainer_dir)

    print("\n[INFO] Entrenando rostros. Esto puede tomar unos segundos...")
    
    all_face_samples = []
    all_ids = []

    # Recorrer todos los subdirectorios (IDs de alumnos) en datasets_path
    if not os.path.exists(datasets_path):
        print(f"[INFO] El directorio de datasets '{datasets_path}' no existe. Asegúrate de capturar rostros primero.")
        return False

    for alumno_id_dir in os.listdir(datasets_path):
        current_alumno_path = os.path.join(datasets_path, alumno_id_dir)
        if os.path.isdir(current_alumno_path): # Asegurarse de que sea un directorio
            print(f"Cargando imágenes para el alumno ID: {alumno_id_dir}")
            faces, ids = get_images_and_labels(current_alumno_path)
            all_face_samples.extend(faces)
            all_ids.extend(ids)

    if not all_face_samples:
        print("[INFO] No hay datos para entrenar. Asegúrate de haber capturado rostros.")
        return False

    # Entrenar el reconocedor
    recognizer.train(all_face_samples, np.array(all_ids))

    # Guardar el modelo entrenado
    recognizer.write(trainer_path) # Guarda el modelo

    print(f"\n[INFO] {len(np.unique(all_ids))} rostros entrenados. Modelo guardado en {trainer_path}")
    return True

def register_attendance(alumno_id, estado="Presente"):
    """
    Envía una solicitud POST a la API de Flask para registrar la asistencia.
    """
    url = f"{FLASK_API_BASE_URL}/asistencias/registrar"
    data = {'alumno_id': alumno_id, 'estado': estado}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status() # Lanza un error para códigos de estado HTTP erróneos
        print(f"Asistencia registrada para el alumno ID {alumno_id}: {response.json().get('mensaje', 'Éxito')}")
    except requests.exceptions.RequestException as e:
        print(f"Error al registrar asistencia para el alumno ID {alumno_id}: {e}")

def recognize_face(alumno_id_map, threshold=60):
    # Cargar el clasificador de rostros pre-entrenado de OpenCV
    face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Cargar el reconocedor entrenado
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    try:
        recognizer.read(trainer_path)
    except cv2.error:
        print("Error: No se pudo cargar el modelo de entrenamiento. Asegúrate de que ha sido entrenado.")
        return

    # Inicializar la cámara
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara.")
        return

    print("\n[INFO] Iniciando reconocimiento facial. Presiona 'q' para salir.")
    # Usaremos una variable para controlar si ya registramos la asistencia para un alumno en el ciclo actual
    last_recognized_id = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error al leer el frame de la cámara.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 5)

        current_recognized_id = None # Reiniciar por cada frame
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            id_predicted, confidence = recognizer.predict(gray[y:y+h, x:x+w])

            if confidence < threshold:
                name = alumno_id_map.get(str(id_predicted), "Desconocido")
                confidence_text = f"  {round(100 - confidence)}%"
                
                # Si reconocemos a un alumno y no es el mismo que el último reconocido
                if name != "Desconocido" and id_predicted != last_recognized_id:
                    register_attendance(id_predicted) # Registrar asistencia
                    current_recognized_id = id_predicted # Marcar como reconocido en este frame
                    last_recognized_id = id_predicted # Actualizar el último ID reconocido
                elif name != "Desconocido" and id_predicted == last_recognized_id:
                    current_recognized_id = id_predicted # Sigue siendo el mismo alumno
            else:
                name = "Desconocido"
                confidence_text = f"  {round(100 - confidence)}%"

            cv2.putText(frame, str(name), (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, str(confidence_text), (x + 5, y + h + 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 1)

        # Si no se reconoce a nadie en el frame actual, resetear last_recognized_id
        if current_recognized_id is None:
            last_recognized_id = None

        cv2.imshow('Reconocimiento Facial', frame)

        k = cv2.waitKey(1) & 0xff # Espera 1ms
        if k == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n[INFO] Reconocimiento facial finalizado.")