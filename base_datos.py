import sqlite3

def conectar_bd():
    return sqlite3.connect("reposos.db")

def inicializar_bd():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    # Crear la tabla con la estructura exacta
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reposos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT NOT NULL,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL DEFAULT '',
            institucion TEXT NOT NULL,
            cargo TEXT NOT NULL,
            tipo_tramite TEXT NOT NULL,
            dias INTEGER NOT NULL,
            fecha_desde TEXT NOT NULL,
            fecha_hasta TEXT NOT NULL,
            codigo_rojo TEXT NOT NULL,
            medico TEXT NOT NULL,
            especialidad TEXT NOT NULL,
            codigo_registro TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Verificación y migración segura de columnas existentes
    cursor.execute("PRAGMA table_info(reposos)")
    columnas_existentes = [col[1] for col in cursor.fetchall()]
    
    if "telefono" not in columnas_existentes:
        try:
            cursor.execute("ALTER TABLE reposos ADD COLUMN telefono TEXT NOT NULL DEFAULT ''")
        except sqlite3.OperationalError:
            pass

    if "tipo" in columnas_existentes and "tipo_tramite" not in columnas_existentes:
        try:
            cursor.execute("ALTER TABLE reposos RENAME COLUMN tipo TO tipo_tramite")
        except sqlite3.OperationalError:
            pass

    conexion.commit()
    conexion.close()

def guardar_registro(datos):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT INTO reposos (
            cedula, nombre, telefono, institucion, cargo, tipo_tramite, 
            dias, fecha_desde, fecha_hasta, codigo_rojo, 
            medico, especialidad, codigo_registro
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', datos)
    conexion.commit()
    conexion.close()

def obtener_registros():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    # Consulta explícita por nombre de columna para evitar desfases de índices
    cursor.execute('''
        SELECT id, cedula, nombre, telefono, institucion, cargo, 
               tipo_tramite, dias, fecha_desde, fecha_hasta, 
               codigo_rojo, medico, especialidad, codigo_registro 
        FROM reposos ORDER BY id DESC
    ''')
    filas = cursor.fetchall()
    conexion.close()
    return filas

def buscar_por_cedula(cedula):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT id, cedula, nombre, telefono, institucion, cargo, 
               tipo_tramite, dias, fecha_desde, fecha_hasta, 
               codigo_rojo, medico, especialidad, codigo_registro 
        FROM reposos WHERE cedula = ? ORDER BY id DESC
    ''', (cedula,))
    filas = cursor.fetchall()
    conexion.close()
    return filas

def obtener_registro_por_id(id_reg):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT id, cedula, nombre, telefono, institucion, cargo, 
               tipo_tramite, dias, fecha_desde, fecha_hasta, 
               codigo_rojo, medico, especialidad, codigo_registro 
        FROM reposos WHERE id = ?
    ''', (id_reg,))
    fila = cursor.fetchone()
    conexion.close()
    return fila

def eliminar_registro(id_reg):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM reposos WHERE id = ?', (id_reg,))
    conexion.commit()
    conexion.close()

def actualizar_registro(id_reg, datos):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE reposos SET
            cedula = ?,
            nombre = ?,
            telefono = ?,
            institucion = ?,
            cargo = ?,
            tipo_tramite = ?,
            dias = ?,
            fecha_desde = ?,
            fecha_hasta = ?,
            codigo_rojo = ?,
            medico = ?,
            especialidad = ?,
            codigo_registro = ?
        WHERE id = ?
    ''', (*datos, id_reg))
    conexion.commit()
    conexion.close()