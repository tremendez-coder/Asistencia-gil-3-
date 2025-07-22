from flask import Flask, render_template, Response, send_file, request, redirect, url_for
import cv2
import sqlite3
import datetime
import time
import os
from utils.antispoofing import rostro_real
from utils.excel import generar_excel_lindo
from capturando import capturar_rostro  # asegúrate de que esta función exista

app = Flask(__name__)

def get_personas():
    conn = sqlite3.connect('recognizer/database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM personas")
    personas = dict(cursor.fetchall())
    conn.close()
    return personas

# Reset de estado al iniciar
with sqlite3.connect('recognizer/database.db') as conn:
    cursor = conn.cursor()
    cursor.execute("UPDATE personas SET presente = 'ausente', hora_marcado = NULL")
    conn.commit()

cam = cv2.VideoCapture(0)
personas = get_personas()

def gen_frames():
    while True:
        ret, frame = cam.read()
        if not ret:
            break

        nombre_detectado, frame_mostrado = rostro_real(frame, personas)

        if nombre_detectado:
            ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with sqlite3.connect('recognizer/database.db') as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE personas SET presente = 'presente', hora_marcado = ? WHERE nombre = ?", (ahora, nombre_detectado))
                conn.commit()

        _, buffer = cv2.imencode('.jpg', frame_mostrado)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        time.sleep(0.03)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/presentes')
def presentes():
    with sqlite3.connect('recognizer/database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, presente, hora_marcado FROM personas")
        data = cursor.fetchall()
    return render_template('tabla.html', personas=data)

@app.route('/descargar_excel')
def descargar_excel():
    with sqlite3.connect('recognizer/database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, presente, hora_marcado FROM personas")
        data = cursor.fetchall()

    output = generar_excel_lindo(data)
    return send_file(output, download_name="asistencia.xlsx", as_attachment=True)

@app.route('/capturar', methods=['GET', 'POST'])
def capturar():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        if nombre:
            capturar_rostro(nombre)  # Guarda imágenes en recognizer/faces/{nombre}
            with sqlite3.connect('recognizer/database.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR IGNORE INTO personas (nombre, presente, hora_marcado) VALUES (?, 'ausente', NULL)", (nombre,))
                conn.commit()
            return redirect(url_for('index'))
    return render_template('captura.html')  # formulario para ingresar nombre

if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        cam.release()
