document.addEventListener('DOMContentLoaded', () => {
    // Función para obtener el rol del usuario actual desde el elemento de encabezado
    function getCurrentUserRole() {
        const userInfoSpan = document.querySelector('.user-info span');
        if (userInfoSpan) {
            const match = userInfoSpan.textContent.match(/\((Admin|Preceptor)\)/i);
            if (match) {
                return match[1].toLowerCase();
            }
        }
        return null; // Si no está logueado o no se encuentra el rol
    }

    let currentUserRole = getCurrentUserRole();
    let currentPreceptorCursos = []; // Para almacenar los cursos del preceptor logueado

    const alumnoForm = document.getElementById('alumno-form');
    const alumnosTableBody = document.querySelector('#alumnos-table tbody');

    // Estas dos constantes solo existirán si el usuario es preceptor en index.html
    const asistenciasTableBody = document.querySelector('#asistencias-table tbody');

    const preceptorForm = document.getElementById('preceptor-form');
    const preceptoresTableBody = document.querySelector('#preceptores-table tbody');

    // Función para cargar los alumnos
    async function cargarAlumnos() {
        try {
            const response = await fetch('/alumnos');
            const alumnos = await response.json();
            alumnosTableBody.innerHTML = '';
            
            let filteredAlumnos = alumnos;

            // Si es preceptor y tiene cursos asignados, filtrar alumnos
            if (currentUserRole === 'preceptor' && currentPreceptorCursos.length > 0) {
                filteredAlumnos = alumnos.filter(alumno => 
                    currentPreceptorCursos.includes(alumno.curso_anio)
                );
            }

            filteredAlumnos.forEach(alumno => {
                const row = alumnosTableBody.insertRow();
                row.insertCell(0).textContent = alumno.id;
                row.insertCell(1).textContent = alumno.nombre;
                row.insertCell(2).textContent = alumno.apellido;
                // Mostrar N/A si fecha_nacimiento es null
                row.insertCell(3).textContent = alumno.fecha_nacimiento ? alumno.fecha_nacimiento : 'N/A';
                row.insertCell(4).textContent = alumno.curso_anio;
                // Mostrar N/A si orientacion es null
                row.insertCell(5).textContent = alumno.orientacion || 'N/A';

                const actionsCell = row.insertCell(6);
                actionsCell.className = 'acciones-col';

                // Botón de Capturar Rostros (Solo Admin)
                if (currentUserRole === 'admin') {
                    const captureBtn = document.createElement('button');
                    captureBtn.textContent = 'Capturar Rostros';
                    captureBtn.onclick = () => capturarRostros(alumno.id);
                    actionsCell.appendChild(captureBtn);
                }
                
                // Botón de Editar
                if (currentUserRole === 'admin' || 
                   (currentUserRole === 'preceptor' && currentPreceptorCursos.includes(alumno.curso_anio))) {
                    const editBtn = document.createElement('button');
                    editBtn.textContent = 'Editar';
                    editBtn.onclick = () => editarAlumno(alumno);
                    actionsCell.appendChild(editBtn);
                }

                // Botón de Eliminar (Solo Admin)
                if (currentUserRole === 'admin') {
                    const deleteBtn = document.createElement('button');
                    deleteBtn.textContent = 'Eliminar';
                    deleteBtn.className = 'delete-btn';
                    deleteBtn.onclick = () => eliminarAlumno(alumno.id);
                    actionsCell.appendChild(deleteBtn);
                }
            });
        } catch (error) {
            console.error('Error al cargar alumnos:', error);
        }
    }

    // Función para guardar o actualizar un alumno
    if (alumnoForm) {
        alumnoForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('alumno-id').value;
            const nombre = document.getElementById('nombre-alumno').value;
            const apellido = document.getElementById('apellido-alumno').value;
            const curso_anio = document.getElementById('curso-anio-alumno').value; // Este campo solo está visible para admin en el formulario de creación

            let alumnoData = {};
            if (currentUserRole === 'admin') {
                // Admin solo envía estos campos al crear
                alumnoData = { nombre, apellido, curso_anio };
            } else if (currentUserRole === 'preceptor') {
                // Preceptor solo edita estos campos
                const fecha_nacimiento = document.getElementById('fecha-nacimiento-alumno').value;
                const orientacion = document.getElementById('orientacion-alumno').value;
                alumnoData = { nombre, apellido, fecha_nacimiento, orientacion: orientacion || null };
            }

            try {
                let response;
                if (id) {
                    // PUT (edición)
                    response = await fetch(`/alumnos/${id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(alumnoData)
                    });
                } else {
                    // POST (creación, solo para admin)
                    if (currentUserRole === 'admin') {
                        response = await fetch('/alumnos', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(alumnoData)
                        });
                    } else {
                        alert('No tienes permiso para crear alumnos.');
                        return;
                    }
                }

                if (response.ok) {
                    alumnoForm.reset();
                    document.getElementById('alumno-id').value = '';
                    // Si el formulario de alumno-form está visible (solo para admin al crear), resetear campos específicos
                    if (currentUserRole === 'admin' && document.getElementById('curso-anio-alumno')) {
                        document.getElementById('curso-anio-alumno').value = '';
                    }
                    alert('Alumno guardado exitosamente');
                    cargarAlumnos();
                } else {
                    const errorData = await response.json();
                    alert('Error al guardar alumno: ' + errorData.error);
                }
            } catch (error) {
                console.error('Error en la solicitud:', error);
                alert('Error en la comunicación con el servidor.');
            }
        });
    }

    // Función para precargar datos de alumno para edición
    function editarAlumno(alumno) {
        document.getElementById('alumno-id').value = alumno.id;
        document.getElementById('nombre-alumno').value = alumno.nombre;
        document.getElementById('apellido-alumno').value = alumno.apellido;
        
        // El formulario de edición para preceptor tiene estos campos, para admin no
        const fechaNacimientoInput = document.getElementById('fecha-nacimiento-alumno');
        const orientacionInput = document.getElementById('orientacion-alumno');
        const cursoAnioInput = document.getElementById('curso-anio-alumno');

        if (currentUserRole === 'preceptor') {
            if (fechaNacimientoInput) fechaNacimientoInput.value = alumno.fecha_nacimiento || '';
            if (orientacionInput) orientacionInput.value = alumno.orientacion || '';
            // Deshabilitar curso_anio para preceptor
            if (cursoAnioInput) cursoAnioInput.disabled = true;
        } else { // Admin
            // Si el admin va a editar, el formulario no tiene fecha_nacimiento ni orientacion
            // y curso_anio debería ser editable (en teoría, aunque el flujo es que preceptor lo completa)
            if (cursoAnioInput) cursoAnioInput.value = alumno.curso_anio;
            if (cursoAnioInput) cursoAnioInput.disabled = false;
        }
    }

    // Función para eliminar un alumno
    async function eliminarAlumno(id) {
        if (!confirm('¿Estás seguro de que quieres eliminar este alumno?')) return;
        try {
            const response = await fetch(`/alumnos/${id}`, { method: 'DELETE' });
            if (response.ok) {
                alert('Alumno eliminado exitosamente');
                cargarAlumnos();
            } else {
                const errorData = await response.json();
                alert('Error al eliminar alumno: ' + errorData.error);
            }
        } catch (error) {
            console.error('Error en la solicitud:', error);
        }
    }

    // --- Funciones para Asistencia (Solo Preceptor) ---

    // Función para cargar las asistencias
    async function cargarAsistencias() {
        if (currentUserRole !== 'preceptor') return; // Solo preceptores ven y cargan asistencias

        try {
            const response = await fetch('/asistencias');
            const asistencias = await response.json();
            if (asistenciasTableBody) { // Asegurarse de que el elemento existe
                asistenciasTableBody.innerHTML = '';
                asistencias.forEach(asistencia => {
                    const row = asistenciasTableBody.insertRow();
                    row.insertCell(0).textContent = asistencia.id;
                    row.insertCell(1).textContent = asistencia.alumno_id;
                    row.insertCell(2).textContent = asistencia.fecha;
                    row.insertCell(3).textContent = asistencia.estado;
                });
            }
        } catch (error) {
            console.error('Error al cargar asistencias:', error);
        }
    }

    // --- Funciones para Preceptores (Admin solo) ---

    // Función para cargar preceptores
    async function cargarPreceptores() {
        if (currentUserRole !== 'admin') return;

        try {
            const response = await fetch('/preceptores');
            const preceptores = await response.json();
            if (preceptoresTableBody) { // Asegurarse de que el elemento existe
                preceptoresTableBody.innerHTML = '';
                preceptores.forEach(preceptor => {
                    const row = preceptoresTableBody.insertRow();
                    row.insertCell(0).textContent = preceptor.id;
                    row.insertCell(1).textContent = preceptor.username;
                    row.insertCell(2).textContent = preceptor.rol;
                    row.insertCell(3).textContent = preceptor.cursos_a_cargo || 'N/A';

                    const actionsCell = row.insertCell(4);
                    const editBtn = document.createElement('button');
                    editBtn.textContent = 'Editar Cursos';
                    editBtn.onclick = () => editarPreceptor(preceptor);
                    actionsCell.appendChild(editBtn);

                    const deleteBtn = document.createElement('button');
                    deleteBtn.textContent = 'Eliminar';
                    deleteBtn.className = 'delete-btn';
                    deleteBtn.onclick = () => eliminarPreceptor(preceptor.id);
                    actionsCell.appendChild(deleteBtn);
                });
            }
        } catch (error) {
            console.error('Error al cargar preceptores:', error);
        }
    }

    // Función para guardar o actualizar un preceptor
    if (preceptorForm) {
        preceptorForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('preceptor-id').value;
            const username = document.getElementById('username-preceptor').value;
            const password = document.getElementById('password-preceptor').value;
            const cursos_a_cargo = document.getElementById('cursos-a-cargo-preceptor').value;

            const preceptorData = { username, password, cursos_a_cargo };

            try {
                let response;
                if (id) {
                    // Si editamos, solo enviamos cursos_a_cargo y el ID
                    response = await fetch(`/preceptores/${id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ cursos_a_cargo: cursos_a_cargo })
                    });
                } else {
                    response = await fetch('/preceptores', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(preceptorData)
                    });
                }

                if (response.ok) {
                    preceptorForm.reset();
                    document.getElementById('preceptor-id').value = '';
                    // Re-habilitar campos si fueron deshabilitados para edición
                    document.getElementById('username-preceptor').disabled = false;
                    document.getElementById('password-preceptor').disabled = false;
                    alert('Preceptor guardado exitosamente');
                    cargarPreceptores();
                } else {
                    const errorData = await response.json();
                    alert('Error al guardar preceptor: ' + errorData.error);
                }
            } catch (error) {
                console.error('Error en la solicitud:', error);
            }
        });
    }

    // Función para precargar datos de preceptor para edición (solo cursos_a_cargo)
    function editarPreceptor(preceptor) {
        document.getElementById('preceptor-id').value = preceptor.id;
        document.getElementById('username-preceptor').value = preceptor.username;
        document.getElementById('password-preceptor').value = ''; // No precargar password
        document.getElementById('cursos-a_cargo-preceptor').value = preceptor.cursos_a_cargo || '';

        // Deshabilitar campos de username y password para edición de cursos
        document.getElementById('username-preceptor').disabled = true;
        document.getElementById('password-preceptor').disabled = true;
    }

    // Función para eliminar un preceptor
    async function eliminarPreceptor(id) {
        if (!confirm('¿Estás seguro de que quieres eliminar este preceptor?')) return;
        try {
            const response = await fetch(`/preceptores/${id}`, { method: 'DELETE' });
            if (response.ok) {
                alert('Preceptor eliminado exitosamente');
                cargarPreceptores();
            } else {
                const errorData = await response.json();
                alert('Error al eliminar preceptor: ' + errorData.error);
            }
        } catch (error) {
            console.error('Error en la solicitud:', error);
        }
    }

    // --- Funciones de Reconocimiento Facial ---

    async function capturarRostros(alumnoId) {
        if (!confirm(`¿Iniciar captura de rostros para el alumno ID ${alumnoId}?`)) return;
        try {
            const response = await fetch(`/alumnos/${alumnoId}/capturar_rostros`, { method: 'POST' });
            const data = await response.json();
            if (response.ok) {
                alert(data.mensaje);
            } else {
                alert('Error al iniciar captura de rostros: ' + data.error);
            }
        } catch (error) {
            console.error('Error en la solicitud:', error);
            alert('Error en la comunicación con el servidor.');
        }
    }

    async function entrenarReconocedor() {
        if (!confirm('¿Deseas entrenar el reconocedor facial? Esto puede tomar un tiempo.')) return;
        try {
            const response = await fetch('/reconocimiento/entrenar', { method: 'POST' });
            const data = await response.json();
            if (response.ok) {
                alert(data.mensaje);
            } else {
                alert('Error al entrenar reconocedor: ' + data.error);
            }
        } catch (error) {
            console.error('Error en la solicitud:', error);
            alert('Error en la comunicación con el servidor.');
        }
    }

    async function iniciarReconocimiento() {
        if (!confirm('¿Deseas iniciar el reconocimiento facial en tiempo real? Se abrirá la cámara.')) return;
        try {
            const response = await fetch('/reconocimiento/iniciar', { method: 'POST' });
            const data = await response.json();
            if (response.ok) {
                alert(data.mensaje);
            } else {
                alert('Error al iniciar reconocimiento: ' + data.error);
            }
        } catch (error) {
            console.error('Error en la solicitud:', error);
            alert('Error en la comunicación con el servidor.');
        }
    }

    // Inicialización al cargar la página
    async function initApp() {
        currentUserRole = getCurrentUserRole(); // Re-obtener el rol por si ha cambiado
        
        if (currentUserRole === 'preceptor') {
            // Si es preceptor, obtener sus cursos a cargo
            try {
                // Fetch al preceptor actual para obtener sus cursos a cargo
                // Asumimos que el username del preceptor está en el span del user-info
                const usernameActual = document.querySelector('.user-info span').textContent.split(' ')[1];
                const response = await fetch('/preceptores'); 
                const preceptores = await response.json();
                const currentPreceptor = preceptores.find(p => p.username === usernameActual);
                if (currentPreceptor && currentPreceptor.cursos_a_cargo) {
                    currentPreceptorCursos = currentPreceptor.cursos_a_cargo.split(',').map(c => c.trim()); // Limpiar espacios
                }
            } catch (error) {
                console.error('Error al obtener cursos del preceptor:', error);
            }
        }
        
        if (document.querySelector('.user-info')) { // Solo si hay un usuario logueado
            cargarAlumnos();
            if (currentUserRole === 'preceptor') {
                cargarAsistencias();
            }
            if (currentUserRole === 'admin') {
                cargarPreceptores();
            }
        }
    }

    initApp();
});