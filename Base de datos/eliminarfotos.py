import os

carpeta_faces = 'recognizer/faces'

for archivo in os.listdir(carpeta_faces):
    if archivo.endswith(".jpg"):
        os.remove(os.path.join(carpeta_faces, archivo))

print("[INFO] Se borraron todas las imágenes de entrenamiento.")
