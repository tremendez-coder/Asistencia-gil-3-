from flask import Flask, render_template, Response, send_file, request, redirect, url_for, flash
import cv2
import sqlite3
import datetime
import os
import threading

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Cambiar en producción

# Variables globales para manejo de cámara
camera = None
camera_lock = threading.Lock()

# Cargar reconocedor
recognizer = cv2.face.LBPHFaceRecognizer_create()
if os.path.exists('recognizer/recognizer.yml'):
    recognizer.read('recognizer/recognizer.yml')
    print("[INFO] Modelo cargado")
else:
    print("[WARNING] No hay modelo entrenado")

detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def get_camera():
    """Obtiene la instancia de cámara de forma thread-safe"""
    global camera
    with camera_lock:
        if camera is None:
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                raise Exception("No se pudo abrir la cámara")
    return camera

def release_camera():
    """Libera la cámara de forma segura"""
    global camera
    with camera_lock:
        if camera is not None:
            camera.release()
            camera = None

def get_personas():
    """Obtiene personas de la base de datos"""
    try:
        conn = sqlite3.connect('recognizer/database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM personas")
        personas = dict(cursor.fetchall())
        conn.close()
        return personas
    except Exception as e:
        print(f"Error obteniendo personas: {e}")
        return {}

def update_attendance(person_id, person_name):
    """Actualiza la asistencia de una persona"""
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect('recognizer/database.db')
        cursor = conn.cursor()
        
        # Verificar si ya fue marcado hoy
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT hora_marcado FROM personas 
            WHERE id = ? AND DATE(hora_marcado) = ?
        """, (person_id, today))
        
        if cursor.fetchone() is None:  # No marcado hoy
            cursor.execute("""
                UPDATE personas 
                SET presente = 'presente', hora_marcado = ? 
                WHERE id = ?
            """, (now, person_id))
            conn.commit()
            print(f"Asistencia registrada para {person_name} a las {now}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error actualizando asistencia: {e}")
        return False

# Resetear estado al iniciar
try:
    conn = sqlite3.connect('recognizer/database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE personas SET presente = 'ausente', hora_marcado = NULL")
    conn.commit()
    conn.close()
except Exception as e:
    print(f"Error reseteando estado: {e}")

def gen_frames():
    """Genera frames de video con reconocimiento facial"""
    personas = get_personas()
    cam = get_camera()
    
    try:
        while True:
            ret, frame = cam.read()
            if not ret:
                print("Error leyendo frame de la cámara")
                break
            
            gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rostros = detector.detectMultiScale(gris, 1.3, 5)
            
            for (x, y, w, h) in rostros:
                rostro = gris[y:y+h, x:x+w]
                
                if os.path.exists('recognizer/recognizer.yml'):
                    id_, conf = recognizer.predict(rostro)
                    nombre = personas.get(id_, 'Desconocido') if conf < 70 else 'Desconocido'
                    color = (0, 255, 0) if nombre != 'Desconocido' else (0, 0, 255)
                    
                    # Si se reconoció alguien, actualizar asistencia
                    if nombre != 'Desconocido':
                        update_attendance(id_, nombre)
                else:
                    nombre = 'Sin modelo'
                    color = (0, 255, 255)
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, nombre, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Codificar frame para streaming
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
    except Exception as e:
        print(f"Error en gen_frames: {e}")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Aquí agregarías la lógica para guardar el usuario
        # Por ejemplo, en la base de datos
        
        flash(f'Usuario {name} registrado exitosamente!', 'success')
        return redirect(url_for('index'))
    
    return render_template('signup_form.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/presentes')
def presentes():
    try:
        conn = sqlite3.connect('recognizer/database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, presente, hora_marcado FROM personas ORDER BY nombre")
        data = cursor.fetchall()
        conn.close()
        return render_template('tabla.html', personas=data)
    except Exception as e:
        flash(f'Error cargando datos: {e}', 'error')
        return render_template('tabla.html', personas=[])

@app.route('/descargar_excel')
def descargar_excel():
    try:
        conn = sqlite3.connect('recognizer/database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, presente, hora_marcado FROM personas ORDER BY nombre")
        data = cursor.fetchall()
        conn.close()

        # Usar openpyxl básico si no tienes excel.py
        try:
            from excel import generar_excel_lindo
            output = generar_excel_lindo(data)
        except ImportError:
            import openpyxl
            from io import BytesIO
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Asistencia"
            ws.append(["Nombre", "Estado", "Hora de reconocimiento"])
            
            for row in data:
                ws.append(row)
            
            output = BytesIO()
            wb.save(output)
            output.seek(0)
        
        filename = f"asistencia_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return send_file(output, download_name=filename, as_attachment=True)
    
    except Exception as e:
        flash(f'Error generando Excel: {e}', 'error')
        return redirect(url_for('presentes'))

@app.route('/capturar', methods=['GET', 'POST'])
def capturar():
    """Ruta para capturar rostros de nuevas personas"""
    if request.method == 'GET':
        return '''
        <h2>Capturar Rostros</h2>
        <form method="POST">
            <label>Nombre: <input name="nombre" required></label><br><br>
            <button type="submit">Capturar</button>
        </form>
        <a href="/">Volver</a>
        '''
    
    try:
        nombre = request.form.get('nombre', '').strip()
        if not nombre:
            flash('Debe ingresar un nombre', 'error')
            return redirect(url_for('capturar'))
        
        # Insertar nueva persona
        conn = sqlite3.connect('recognizer/database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO personas (nombre) VALUES (?)", (nombre,))
        person_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        flash(f'Persona {nombre} agregada. Usa capturando.py para tomar fotos.', 'success')
            
    except Exception as e:
        flash(f'Error: {e}', 'error')
    
    return redirect(url_for('capturar'))

@app.route('/entrenar', methods=['POST'])
def entrenar():
    """Ruta para entrenar el modelo"""
    try:
        flash('Usa entreno.py para entrenar el modelo.', 'info')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    
    return redirect(url_for('index'))

# Cleanup al cerrar la aplicación
import atexit

def cleanup():
    release_camera()
    print("[INFO] Recursos liberados")

atexit.register(cleanup)

if __name__ == '__main__':
    print("[INFO] Iniciando aplicación...")
    app.run(debug=True, threaded=True)