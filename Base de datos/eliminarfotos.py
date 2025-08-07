import os

carpeta_faces = 'recognizer/faces'

# Crear carpeta si no existe
if not os.path.exists(carpeta_faces):
    os.makedirs(carpeta_faces)

for archivo in os.listdir(carpeta_faces):
    if archivo.endswith(".jpg"):
        os.remove(os.path.join(carpeta_faces, archivo))

print("[INFO] Se borraron todas las imágenes de entrenamiento.")
