import os
import glob

# Carpeta donde están las fotos
carpeta_faces = 'recognizer/faces'

# Ingresar el ID del usuario
id_usuario = input("Ingresá el ID del usuario para eliminar sus fotos (ej: 8): ")

# Buscar archivos que coincidan con 'usuario.ID.*.jpg'
patron = os.path.join(carpeta_faces, f'usuario.{id_usuario}.*.jpg')
fotos_encontradas = glob.glob(patron)

# Mostrar los archivos encontrados
if not fotos_encontradas:
    print("No se encontraron fotos para ese usuario.")
else:
    print(f"Se encontraron {len(fotos_encontradas)} fotos. Eliminando...")

    for foto in fotos_encontradas:
        os.remove(foto)
        print(f"Eliminado: {foto}")

    print("✅ Todas las fotos del usuario fueron eliminadas.")
