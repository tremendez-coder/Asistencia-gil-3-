import sqlite3

# Conexión a la base de datos
conn = sqlite3.connect('recognizer/database.db')
cursor = conn.cursor()

# Elegir modo de eliminación
modo = input("¿Querés eliminar por (1) ID o (2) nombre? Ingresá 1 o 2: ")

if modo == "1":
    try:
        id_persona = int(input("Ingresá el ID de la persona a eliminar: "))
        cursor.execute("SELECT nombre FROM personas WHERE id = ?", (id_persona,))
        resultado = cursor.fetchone()
        if resultado:
            confirm = input(f"¿Estás seguro de que querés eliminar a '{resultado[0]}'? (s/n): ")
            if confirm.lower() == 's':
                cursor.execute("DELETE FROM personas WHERE id = ?", (id_persona,))
                print("Persona eliminada con éxito.")
            else:
                print("Cancelado.")
        else:
            print("No se encontró una persona con ese ID.")
    except ValueError:
        print("ID inválido.")

elif modo == "2":
    nombre = input("Ingresá el nombre de la persona a eliminar: ").strip()
    cursor.execute("SELECT id FROM personas WHERE nombre = ?", (nombre,))
    resultado = cursor.fetchone()
    if resultado:
        confirm = input(f"¿Estás seguro de que querés eliminar a '{nombre}'? (s/n): ")
        if confirm.lower() == 's':
            cursor.execute("DELETE FROM personas WHERE nombre = ?", (nombre,))
            print("Persona eliminada con éxito.")
        else:
            print("Cancelado.")
    else:
        print("No se encontró una persona con ese nombre.")

else:
    print("Opción inválida.")

conn.commit()
conn.close()
