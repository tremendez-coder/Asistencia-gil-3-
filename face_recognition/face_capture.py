import cv2
import os

def capture_faces(alumno_id, num_fotos=50):
    # Cargar el clasificador de rostros pre-entrenado de OpenCV
    face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Crear la carpeta para el alumno si no existe
    dataset_path = f'./face_recognition/datasets/{alumno_id}'
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    # Inicializar la cámara
    cap = cv2.VideoCapture(0) # 0 para la cámara predeterminada
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara.")
        return False

    print(f"\n[INFO] Capturando {num_fotos} imágenes para el alumno ID: {alumno_id}. Presiona 'q' para salir.")
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error al leer el frame de la cámara.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
            # Solo guardar si se detecta un rostro y no hemos alcanzado el límite de fotos
            if count < num_fotos:
                img_name = f"{dataset_path}/user_{alumno_id}_{count}.jpg"
                cv2.imwrite(img_name, gray[y:y+h, x:x+w])
                count += 1
                print(f"Imagen {count}/{num_fotos} capturada.")

        cv2.imshow('Capturando Rostros', frame)

        k = cv2.waitKey(100) & 0xff # Espera 100ms, si se presiona 'q' sale
        if k == ord('q') or count >= num_fotos:
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n[INFO] Captura de rostros finalizada para el alumno ID: {alumno_id}. Total: {count} imágenes.")
    return True

if __name__ == '__main__':
    # Ejemplo de uso: Capturar 50 fotos para el alumno con ID 1
    # Asegúrate de haber reinicializado la base de datos y tener alumnos registrados.
    # Para ejecutar esto, debes pasar el ID del alumno.
    # Por ejemplo, desde la terminal: python face_recognition/face_capture.py 1
    import sys
    if len(sys.argv) > 1:
        alumno_id_to_capture = sys.argv[1]
        capture_faces(alumno_id_to_capture)
    else:
        print("Uso: python face_recognition/face_capture.py <ID_DEL_ALUMNO>")