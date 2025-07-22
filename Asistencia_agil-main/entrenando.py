import cv2
import numpy as np
from PIL import Image
import os

# Rutas
faces_dir = os.path.join('recognizer', 'faces')
model_path = os.path.join('recognizer', 'recognizer.yml')

# Crear el reconocedor
recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def obtener_imagenes_y_labels(ruta):
    imagenes = []
    ids = []
    for archivo in os.listdir(ruta):
        if archivo.endswith(".jpg"):
            path_completo = os.path.join(ruta, archivo)
            imagen = Image.open(path_completo).convert('L')
            imagen_np = np.array(imagen, 'uint8')
            id_ = int(archivo.split('.')[1])
            rostros = detector.detectMultiScale(imagen_np)
            for (x, y, w, h) in rostros:
                imagenes.append(imagen_np[y:y+h, x:x+w])
                ids.append(id_)
    return imagenes, ids

# Entrenamiento del modelo
print("[INFO] Entrenando el modelo...")
faces, ids = obtener_imagenes_y_labels(faces_dir)
recognizer.train(faces, np.array(ids))  
recognizer.save(model_path)
print(f"[INFO] Modelo entrenado y guardado en '{model_path}'")
