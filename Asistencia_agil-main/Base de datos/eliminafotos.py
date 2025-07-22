#eliminafotos.py
import os
import shutil

carpeta = 'recognizer/faces'
if os.path.exists(carpeta):
    shutil.rmtree(carpeta)
    os.makedirs(carpeta)
    print("[INFO] Se borraron todas las imágenes de entrenamiento.")
else:
    print("[ERROR] La carpeta no existe.")