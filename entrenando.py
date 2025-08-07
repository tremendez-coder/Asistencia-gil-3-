import cv2
import numpy as np
from PIL import Image
import os

ruta = 'recognizer/faces'
recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def obtener_imagenes_y_labels(ruta):
    imagenes = []
    ids = []
    for archivo in os.listdir(ruta):
        if archivo.endswith(".jpg"):
            path_completo = os.path.join(ruta, archivo)
            imagen = Image.open(path_completo).convert('L')  # Escala de grises
            imagen_np = np.array(imagen, 'uint8')
            id_ = int(archivo.split('.')[1])
            rostros = detector.detectMultiScale(imagen_np)
            for (x, y, w, h) in rostros:
                imagenes.append(imagen_np[y:y+h, x:x+w])
                ids.append(id_)
    return imagenes, ids

print("[INFO] Entrenando el modelo...")
faces, ids = obtener_imagenes_y_labels(ruta)
recognizer.train(faces, np.array(ids))

if not os.path.exists('recognizer'):
    os.makedirs('recognizer')

recognizer.save('recognizer/recognizer.yml')
print("[INFO] Modelo entrenado y guardado en 'recognizer/recognizer.yml'")
