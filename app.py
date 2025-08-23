import os
from datetime import date
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask.cli import with_appcontext
import click

# Importar los módulos de reconocimiento facial
from face_recognition.face_capture import capture_faces
from face_recognition.face_recognizer import train_recognizer, recognize_face

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here' # ¡Cambia esto por una clave segura!
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- Modelos de la Base de Datos ---

class Alumno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True) # Ahora puede ser nulo inicialmente
    curso_anio = db.Column(db.String(50), nullable=False) # Ej: '1er año CB', '3er año CS - IPP'
    orientacion = db.Column(db.String(50), nullable=True) # Ej: 'IPP', 'GAO', 'TEP'. Nullable para ciclo basico
    asistencias = db.relationship('Asistencia', backref='alumno', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'fecha_nacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            'curso_anio': self.curso_anio,
            'orientacion': self.orientacion
        }

class Asistencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alumno_id = db.Column(db.Integer, db.ForeignKey('alumno.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    estado = db.Column(db.String(50), nullable=False) # Ej: 'Presente', 'Ausente', 'Tarde'

    def to_dict(self):
        return {
            'id': self.id,
            'alumno_id': self.alumno_id,
            'fecha': self.fecha.isoformat(),
            'estado': self.estado
        }

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(50), nullable=False) # 'admin' o 'preceptor'
    cursos_a_cargo = db.Column(db.String(500), nullable=True, default='') # Nueva columna para preceptores

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- Rutas de Autenticación ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña inválidos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('login'))

# --- Rutas de Gestión de Alumnos ---

@app.route('/')
@login_required
def index():
    return render_template('index.html', current_user=current_user)

@app.route('/alumnos', methods=['GET', 'POST'])
@login_required
def gestionar_alumnos():
    if request.method == 'POST':
        if current_user.rol != 'admin':
            return jsonify({'error': 'No autorizado'}), 403
        data = request.get_json()
        try:
            new_alumno = Alumno(
                nombre=data['nombre'],
                apellido=data['apellido'],
                curso_anio=data['curso_anio'],
                fecha_nacimiento=None, # El admin no provee esto inicialmente
                orientacion=None      # El admin no provee esto inicialmente
            )
            db.session.add(new_alumno)
            db.session.commit()
            return jsonify(new_alumno.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    else: # GET
        # Si es preceptor, filtrar alumnos por sus cursos
        if current_user.rol == 'preceptor':
            cursos_preceptor = current_user.cursos_a_cargo.split(',')
            alumnos = Alumno.query.filter(Alumno.curso_anio.in_(cursos_preceptor)).all()
        else: # Admin, ver todos los alumnos (sin fecha_nacimiento ni orientacion si no han sido rellenados)
            alumnos = Alumno.query.all()
        return jsonify([a.to_dict() for a in alumnos])

@app.route('/alumnos/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def alumno_detalle(id):
    alumno = Alumno.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify(alumno.to_dict())
    elif request.method == 'PUT':
        # Permitir que los preceptores editen los datos de los alumnos de sus cursos
        if current_user.rol == 'preceptor':
            if alumno.curso_anio not in current_user.cursos_a_cargo.split(','):
                return jsonify({'error': 'No autorizado para editar alumnos fuera de sus cursos asignados'}), 403
            
            data = request.get_json()
            try:
                # El preceptor solo puede editar nombre, apellido, fecha_nacimiento, orientacion (si aplica)
                alumno.nombre = data.get('nombre', alumno.nombre)
                alumno.apellido = data.get('apellido', alumno.apellido)
                if 'fecha_nacimiento' in data and data['fecha_nacimiento']: # Solo actualizar si se provee y no es vacío
                    alumno.fecha_nacimiento = date.fromisoformat(data['fecha_nacimiento'])
                if 'orientacion' in data:
                    alumno.orientacion = data['orientacion']
                
                db.session.commit()
                return jsonify(alumno.to_dict())
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 400

        # Admin puede editar todos los campos, pero siguiendo la nueva lógica si edita solo algunos.
        # Por ahora, para simplificar y alinear con el frontend, asumimos que el admin solo crea.
        # Si se necesita que admin edite, se requeriría un formulario específico para admin con todos los campos.
        # Dejamos la restricción de admin en el frontend.
        if current_user.rol == 'admin':
            data = request.get_json()
            try:
                alumno.nombre = data.get('nombre', alumno.nombre)
                alumno.apellido = data.get('apellido', alumno.apellido)
                alumno.curso_anio = data.get('curso_anio', alumno.curso_anio) # Admin puede cambiar esto si se necesita
                
                # Admin no debe editar fecha_nacimiento ni orientacion desde esta ruta PUT simple si no los provee.
                # Si se requiere edición completa por admin, se debe manejar de forma más robusta.
                if 'fecha_nacimiento' in data and data['fecha_nacimiento']:
                    alumno.fecha_nacimiento = date.fromisoformat(data['fecha_nacimiento'])
                if 'orientacion' in data:
                    alumno.orientacion = data['orientacion']
                
                db.session.commit()
                return jsonify(alumno.to_dict())
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 400
        else:
            return jsonify({'error': 'No autorizado'}), 403

    else: # DELETE
        if current_user.rol != 'admin':
            return jsonify({'error': 'No autorizado'}), 403
        db.session.delete(alumno)
        db.session.commit()
        return jsonify({'mensaje': 'Alumno eliminado'}), 204

# --- Rutas de Gestión de Asistencia ---

@app.route('/asistencias', methods=['GET']) # Solo GET, no POST manual
@login_required
def gestionar_asistencias():
    # El Admin no ve el listado de asistencias. Solo el preceptor.
    if current_user.rol != 'preceptor':
        return jsonify({'error': 'No autorizado'}), 403

    # Si es preceptor, filtrar asistencias por sus cursos
    cursos_preceptor = current_user.cursos_a_cargo.split(',')
    alumnos_en_cursos = Alumno.query.filter(Alumno.curso_anio.in_(cursos_preceptor)).all()
    alumno_ids = [a.id for a in alumnos_en_cursos]
    asistencias = Asistencia.query.filter(Asistencia.alumno_id.in_(alumno_ids)).all()
    
    return jsonify([a.to_dict() for a in asistencias])

@app.route('/asistencias/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def asistencia_detalle(id):
    if current_user.rol != 'admin': # Solo Admin puede editar/eliminar asistencias
        return jsonify({'error': 'No autorizado'}), 403
    
    asistencia = Asistencia.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify(asistencia.to_dict())
    elif request.method == 'PUT':
        data = request.get_json()
        try:
            asistencia.alumno_id = data['alumno_id']
            asistencia.fecha = date.fromisoformat(data['fecha'])
            asistencia.estado = data['estado']
            db.session.commit()
            return jsonify(asistencia.to_dict())
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    else: # DELETE
        db.session.delete(asistencia)
        db.session.commit()
        return jsonify({'mensaje': 'Asistencia eliminada'}), 204

@app.route('/asistencias/registrar', methods=['POST'])
def registrar_asistencia_api():
    """
    Ruta para que el módulo de reconocimiento facial registre la asistencia automáticamente.
    No requiere autenticación ya que la solicitud proviene de un proceso interno.
    """
    data = request.get_json()
    alumno_id = data.get('alumno_id')
    estado = data.get('estado', 'Presente') # Por defecto 'Presente'

    if not alumno_id:
        return jsonify({'error': 'ID de alumno es requerido'}), 400

    alumno = Alumno.query.get(alumno_id)
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404

    # Verificar si ya existe una asistencia para este alumno en el día de hoy
    existing_asistencia = Asistencia.query.filter_by(
        alumno_id=alumno_id,
        fecha=date.today()
    ).first()

    if existing_asistencia:
        # Actualizar estado si es necesario o simplemente indicar que ya está registrado
        if existing_asistencia.estado != estado:
            existing_asistencia.estado = estado
            db.session.commit()
            return jsonify({'mensaje': f'Asistencia de alumno {alumno_id} actualizada a {estado} para hoy.'}), 200
        else:
            return jsonify({'mensaje': f'Asistencia de alumno {alumno_id} ya registrada como {estado} para hoy.'}), 200
    else:
        try:
            new_asistencia = Asistencia(alumno_id=alumno_id, fecha=date.today(), estado=estado)
            db.session.add(new_asistencia)
            db.session.commit()
            return jsonify({'mensaje': f'Asistencia registrada para el alumno {alumno_id} como {estado}.'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Error al registrar asistencia: {str(e)}'}), 500


# --- Rutas de Gestión de Preceptores (Admin solo) ---

@app.route('/preceptores', methods=['GET', 'POST'])
@login_required
def gestionar_preceptores():
    if current_user.rol != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        # cursos_a_cargo es opcional al crear, se puede asignar después
        cursos_a_cargo_str = data.get('cursos_a_cargo', '') 

        if not username or not password:
            return jsonify({'error': 'Username y password son requeridos'}), 400
        
        if Usuario.query.filter_by(username=username).first():
            return jsonify({'error': 'El nombre de usuario ya existe'}), 409

        new_preceptor = Usuario(username=username, rol='preceptor', cursos_a_cargo=cursos_a_cargo_str)
        new_preceptor.set_password(password)
        db.session.add(new_preceptor)
        db.session.commit()
        return jsonify({'id': new_preceptor.id, 'username': new_preceptor.username, 'rol': new_preceptor.rol, 'cursos_a_cargo': new_preceptor.cursos_a_cargo}), 201
    else: # GET
        preceptores = Usuario.query.filter_by(rol='preceptor').all()
        return jsonify([{'id': p.id, 'username': p.username, 'rol': p.rol, 'cursos_a_cargo': p.cursos_a_cargo} for p in preceptores])

@app.route('/preceptores/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def detalle_preceptor(id):
    if current_user.rol != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    preceptor = Usuario.query.get_or_404(id)

    if request.method == 'GET':
        return jsonify({'id': preceptor.id, 'username': preceptor.username, 'rol': preceptor.rol, 'cursos_a_cargo': preceptor.cursos_a_cargo})
    elif request.method == 'PUT':
        data = request.get_json()
        # Solo permitir actualizar cursos_a_cargo
        if 'cursos_a_cargo' in data:
            preceptor.cursos_a_cargo = data['cursos_a_cargo']
            db.session.commit()
            return jsonify({'id': preceptor.id, 'username': preceptor.username, 'rol': preceptor.rol, 'cursos_a_cargo': preceptor.cursos_a_cargo})
        return jsonify({'error': 'Solo se puede actualizar la propiedad cursos_a_cargo'}), 400
    else: # DELETE
        if preceptor.rol == 'admin': # No permitir eliminar al propio admin
            return jsonify({'error': 'No se puede eliminar un usuario admin'}), 403
        db.session.delete(preceptor)
        db.session.commit()
        return jsonify({'mensaje': 'Preceptor eliminado'}), 204


# --- Rutas de Reconocimiento Facial (Admin y Preceptor) ---

@app.route('/alumnos/<int:id>/capturar_rostros', methods=['POST'])
@login_required
def capturar_rostros_alumno(id):
    if current_user.rol != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404
    
    print(f"Iniciando captura de rostros para el alumno ID: {id} ({alumno.nombre} {alumno.apellido})")
    try:
        capture_faces(id)
        return jsonify({'mensaje': f'Captura de rostros iniciada para el alumno {id}. Revisa la consola para el progreso.'}), 202
    except Exception as e:
        return jsonify({'error': f'Error al iniciar captura de rostros: {str(e)}'}), 500

@app.route('/reconocimiento/entrenar', methods=['POST'])
@login_required
def entrenar_reconocedor():
    if current_user.rol != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    print("Iniciando entrenamiento del reconocedor facial...")
    try:
        success = train_recognizer()
        if success:
            return jsonify({'mensaje': 'Entrenamiento del reconocedor facial completado.'}), 200
        else:
            return jsonify({'mensaje': 'Entrenamiento del reconocedor facial no completado. Posiblemente no hay datos de rostros.'}), 200
    except Exception as e:
        return jsonify({'error': f'Error durante el entrenamiento: {str(e)}'}), 500

@app.route('/reconocimiento/iniciar', methods=['POST'])
@login_required
def iniciar_reconocimiento():
    # Permitir que el admin o el preceptor inicien el reconocimiento
    if current_user.rol not in ['admin', 'preceptor']:
        return jsonify({'error': 'No autorizado'}), 403
    
    print("Iniciando reconocimiento facial en tiempo real...")
    try:
        # Obtener un mapa de alumno_id a nombre completo para mostrar en el feed de la cámara
        alumnos = Alumno.query.all()
        alumno_id_map = {str(a.id): f"{a.nombre} {a.apellido}" for a in alumnos}
        
        recognize_face(alumno_id_map)
        return jsonify({'mensaje': 'Reconocimiento facial iniciado. Revisa la ventana de la cámara.'}), 202
    except Exception as e:
        return jsonify({'error': f'Error al iniciar reconocimiento facial: {str(e)}'}), 500

# --- Comandos de CLI Personalizados ---

@app.cli.command('init-db')
@with_appcontext
def init_db_command():
    """Inicializa la base de datos."""
    db.create_all()
    click.echo('Base de datos inicializada.')

@app.cli.command('crear-admin')
@click.argument('username')
@click.argument('password')
@with_appcontext
def crear_admin_command(username, password):
    """Crea un usuario administrador."""
    if Usuario.query.filter_by(username=username).first():
        click.echo(f'El usuario {username} ya existe.')
        return
    admin_user = Usuario(username=username, rol='admin', cursos_a_cargo='') # Admin no tiene cursos_a_cargo
    admin_user.set_password(password)
    db.session.add(admin_user)
    db.session.commit()
    click.echo(f'Usuario administrador "{username}" creado exitosamente.')

if __name__ == '__main__':
    # No ejecutar app.run() directamente cuando se usa Flask CLI
    # La aplicación se ejecuta con 'flask run'
    pass