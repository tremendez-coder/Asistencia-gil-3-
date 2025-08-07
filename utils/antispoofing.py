import cv2
import time
import os
import numpy as np

class FaceRecognizer:
    """Clase mejorada para reconocimiento facial con mejor gestión de recursos"""
    
    def __init__(self, model_path='recognizer/recognizer.yml'):
        self.model_path = model_path
        self.face_detector = None
        self.recognizer = None
        self.last_detection = {'name': None, 'time': 0, 'confidence': 100}
        self.detection_cooldown = 2.0  # Segundos entre detecciones del mismo rostro
        self.confidence_threshold = 60  # Umbral de confianza
        
        self._init_components()
    
    def _init_components(self):
        """Inicializa los componentes de detección y reconocimiento"""
        try:
            # Detector de rostros
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_detector = cv2.CascadeClassifier(cascade_path)
            
            if self.face_detector.empty():
                raise Exception("No se pudo cargar el detector de rostros")
            
            # Reconocedor
            if os.path.exists(self.model_path):
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
                self.recognizer.read(self.model_path)
                print(f"[INFO] Modelo cargado desde {self.model_path}")
            else:
                print(f"[WARNING] No se encontró modelo entrenado en {self.model_path}")
                
        except Exception as e:
            print(f"[ERROR] Error inicializando componentes: {e}")
            raise
    
    def reload_model(self):
        """Recarga el modelo entrenado (útil después de entrenar)"""
        try:
            if os.path.exists(self.model_path):
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
                self.recognizer.read(self.model_path)
                print(f"[INFO] Modelo recargado exitosamente")
                return True
        except Exception as e:
            print(f"[ERROR] Error recargando modelo: {e}")
        return False
    
    def detect_and_recognize(self, frame, personas_dict):
        """
        Detecta y reconoce rostros en el frame
        Args:
            frame: Frame de video
            personas_dict: Diccionario {id: nombre}
        Returns:
            tuple: (nombre_reconocido o None, frame_procesado)
        """
        if not self.recognizer:
            return None, self._draw_no_model_message(frame)
        
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Mejorar la imagen
            gray = cv2.equalizeHist(gray)
            
            # Detectar rostros
            faces = self.face_detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(80, 80),
                maxSize=(300, 300),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            recognized_name = None
            current_time = time.time()
            
            for (x, y, w, h) in faces:
                # Extraer región del rostro
                face_roi = gray[y:y+h, x:x+w]
                
                try:
                    # Reconocer rostro
                    person_id, confidence = self.recognizer.predict(face_roi)
                    
                    # Determinar nombre basado en confianza
                    if confidence < self.confidence_threshold and person_id in personas_dict:
                        name = personas_dict[person_id]
                        color = (0, 255, 0)  # Verde para reconocido
                        
                        # Control de cooldown para evitar detecciones repetidas
                        if (name != self.last_detection['name'] or 
                            current_time - self.last_detection['time'] > self.detection_cooldown):
                            recognized_name = name
                            self.last_detection = {
                                'name': name,
                                'time': current_time,
                                'confidence': confidence
                            }
                    else:
                        name = 'Desconocido'
                        color = (0, 0, 255)  # Rojo para desconocido
                    
                    # Dibujar rectángulo y etiqueta
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    
                    # Etiqueta con nombre y confianza
                    label = f"{name} ({int(confidence)}%)"
                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    
                    # Fondo para el texto
                    cv2.rectangle(frame, (x, y-30), (x + label_size[0] + 10, y), color, -1)
                    cv2.putText(frame, label, (x + 5, y - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    # Indicador de confianza en el rostro
                    confidence_bar_width = int((confidence / 100) * w)
                    cv2.rectangle(frame, (x, y+h-10), (x + confidence_bar_width, y+h), 
                                 (0, 255-int(confidence*2.55), int(confidence*2.55)), -1)
                
                except Exception as e:
                    print(f"[WARNING] Error reconociendo rostro: {e}")
                    # Dibujar rectángulo de error
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                    cv2.putText(frame, "Error", (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Información de estado en el frame
            self._draw_status_info(frame, len(faces), current_time)
            
            return recognized_name, frame
            
        except Exception as e:
            print(f"[ERROR] Error en detección: {e}")
            return None, self._draw_error_message(frame, str(e))
    
    def _draw_status_info(self, frame, num_faces, current_time):
        """Dibuja información de estado en el frame"""
        h, w = frame.shape[:2]
        
        # Información en la esquina superior izquierda
        info_lines = [
            f"Rostros detectados: {num_faces}",
            f"Modelo: {'✓' if self.recognizer else '✗'}",
            f"Timestamp: {time.strftime('%H:%M:%S')}"
        ]
        
        for i, line in enumerate(info_lines):
            y_pos = 30 + (i * 25)
            cv2.rectangle(frame, (10, y_pos - 20), (300, y_pos + 5), (0, 0, 0), -1)
            cv2.putText(frame, line, (15, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def _draw_no_model_message(self, frame):
        """Dibuja mensaje cuando no hay modelo"""
        h, w = frame.shape[:2]
        message = "No hay modelo entrenado"
        cv2.putText(frame, message, (w//4, h//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return frame
    
    def _draw_error_message(self, frame, error_msg):
        """Dibuja mensaje de error"""
        h, w = frame.shape[:2]
        cv2.putText(frame, f"Error: {error_msg[:30]}", (10, h-30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        return frame

# Instancia global del reconocedor
_face_recognizer = None

def get_face_recognizer():
    """Obtiene la instancia global del reconocedor (patrón singleton)"""
    global _face_recognizer
    if _face_recognizer is None:
        _face_recognizer = FaceRecognizer()
    return _face_recognizer

def rostro_real(frame, personas):
    """
    Función de compatibilidad con el código existente
    Args:
        frame: Frame de video
        personas: Diccionario {id: nombre}
    Returns:
        tuple: (nombre_reconocido o None, frame_procesado)
    """
    recognizer = get_face_recognizer()
    return recognizer.detect_and_recognize(frame, personas)

def reload_recognition_model():
    """Recarga el modelo de reconocimiento"""
    recognizer = get_face_recognizer()
    return recognizer.reload_model()

# Función para validar que el sistema esté configurado correctamente
def validate_recognition_system():
    """Valida que el sistema de reconocimiento esté configurado correctamente"""
    issues = []
    
    try:
        recognizer = get_face_recognizer()
        
        if not recognizer.face_detector or recognizer.face_detector.empty():
            issues.append("Detector de rostros no disponible")
        
        if not recognizer.recognizer:
            issues.append("Modelo de reconocimiento no entrenado")
        
        if not os.path.exists('recognizer/'):
            issues.append("Directorio 'recognizer/' no existe")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        return False, [f"Error de inicialización: {str(e)}"]