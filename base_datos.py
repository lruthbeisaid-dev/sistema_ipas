import sqlite3

_SELECCION_REGISTRO = '''
    SELECT r.id, r.cedula, b.nombre, b.telefono, b.institucion, b.cargo,
           r.tipo_tramite, r.dias, r.fecha_desde, r.fecha_hasta,
           r.codigo_rojo, r.medico, r.especialidad, r.codigo_registro
    FROM reposos r
    JOIN beneficiarios b ON b.cedula = r.cedula
'''


def conectar_bd():
    conexion = sqlite3.connect("reposos.db")
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar_bd():
    conexion = conectar_bd()
    cursor = conexion.cursor()

    # Tabla de beneficiarios: datos personales, independientes del trámite
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS beneficiarios (
            cedula TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL DEFAULT '',
            institucion TEXT NOT NULL,
            cargo TEXT NOT NULL
        )
    ''')

    # Tabla de reposos/cuidos: solo datos del trámite, referenciando al beneficiario
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reposos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT NOT NULL,
            tipo_tramite TEXT NOT NULL,
            dias INTEGER NOT NULL,
            fecha_desde TEXT NOT NULL,
            fecha_hasta TEXT NOT NULL,
            codigo_rojo TEXT NOT NULL,
            medico TEXT NOT NULL,
            especialidad TEXT NOT NULL,
            codigo_registro TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cedula) REFERENCES beneficiarios(cedula)
        )
    ''')

    _migrar_esquema_anterior(cursor)

    conexion.commit()
    conexion.close()


def _migrar_esquema_anterior(cursor):
    """Migra bases de datos creadas con el esquema anterior (una sola tabla
    'reposos' que incluía nombre/teléfono/institución/cargo en cada fila)
    hacia el nuevo modelo separado de 'beneficiarios' + 'reposos'."""
    cursor.execute("PRAGMA table_info(reposos)")
    columnas = [col[1] for col in cursor.fetchall()]

    if "tipo" in columnas and "tipo_tramite" not in columnas:
        cursor.execute("ALTER TABLE reposos RENAME COLUMN tipo TO tipo_tramite")
        columnas = [c if c != "tipo" else "tipo_tramite" for c in columnas]

    if "nombre" not in columnas:
        return  # ya está en el esquema nuevo, no hay nada que migrar

    # 1. Extraer los beneficiarios únicos de los registros antiguos
    cursor.execute('SELECT DISTINCT cedula, nombre, telefono, institucion, cargo FROM reposos')
    for cedula, nombre, telefono, institucion, cargo in cursor.fetchall():
        cursor.execute('''
            INSERT OR IGNORE INTO beneficiarios (cedula, nombre, telefono, institucion, cargo)
            VALUES (?, ?, ?, ?, ?)
        ''', (cedula, nombre, telefono, institucion, cargo))

    # 2. Reconstruir la tabla reposos sin las columnas de datos personales
    cursor.execute('ALTER TABLE reposos RENAME TO reposos_legacy')
    cursor.execute('''
        CREATE TABLE reposos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT NOT NULL,
            tipo_tramite TEXT NOT NULL,
            dias INTEGER NOT NULL,
            fecha_desde TEXT NOT NULL,
            fecha_hasta TEXT NOT NULL,
            codigo_rojo TEXT NOT NULL,
            medico TEXT NOT NULL,
            especialidad TEXT NOT NULL,
            codigo_registro TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cedula) REFERENCES beneficiarios(cedula)
        )
    ''')

    columnas_compartidas = ["id", "cedula", "tipo_tramite", "dias", "fecha_desde", "fecha_hasta",
                             "codigo_rojo", "medico", "especialidad", "codigo_registro"]
    if "fecha_registro" in columnas:
        columnas_compartidas.append("fecha_registro")
    lista_columnas = ", ".join(columnas_compartidas)

    cursor.execute(f'''
        INSERT INTO reposos ({lista_columnas})
        SELECT {lista_columnas} FROM reposos_legacy
    ''')
    cursor.execute('DROP TABLE reposos_legacy')


def guardar_beneficiario(cedula, nombre, telefono, institucion, cargo):
    """Inserta o actualiza los datos personales de un beneficiario (upsert por cédula)."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT INTO beneficiarios (cedula, nombre, telefono, institucion, cargo)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(cedula) DO UPDATE SET
            nombre = excluded.nombre,
            telefono = excluded.telefono,
            institucion = excluded.institucion,
            cargo = excluded.cargo
    ''', (cedula, nombre, telefono, institucion, cargo))
    conexion.commit()
    conexion.close()


def obtener_beneficiario_por_cedula(cedula):
    """Devuelve (cedula, nombre, telefono, institucion, cargo) o None si no existe."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT cedula, nombre, telefono, institucion, cargo
        FROM beneficiarios WHERE cedula = ?
    ''', (cedula,))
    fila = cursor.fetchone()
    conexion.close()
    return fila


def guardar_registro(datos_beneficiario, datos_reposo):
    """
    datos_beneficiario: (cedula, nombre, telefono, institucion, cargo)
    datos_reposo: (cedula, tipo_tramite, dias, fecha_desde, fecha_hasta,
                   codigo_rojo, medico, especialidad, codigo_registro)
    """
    guardar_beneficiario(*datos_beneficiario)

    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT INTO reposos (
            cedula, tipo_tramite, dias, fecha_desde, fecha_hasta,
            codigo_rojo, medico, especialidad, codigo_registro
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', datos_reposo)
    conexion.commit()
    conexion.close()


def obtener_registros():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute(_SELECCION_REGISTRO + ' ORDER BY r.id DESC')
    filas = cursor.fetchall()
    conexion.close()
    return filas


def buscar_por_cedula(cedula):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute(_SELECCION_REGISTRO + ' WHERE r.cedula = ? ORDER BY r.id DESC', (cedula,))
    filas = cursor.fetchall()
    conexion.close()
    return filas


def obtener_registro_por_id(id_reg):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute(_SELECCION_REGISTRO + ' WHERE r.id = ?', (id_reg,))
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
    """
    datos: (cedula, nombre, telefono, institucion, cargo, tipo_tramite, dias,
            fecha_desde, fecha_hasta, codigo_rojo, medico, especialidad, codigo_registro)
    Actualiza tanto los datos del beneficiario como los del trámite.
    """
    (cedula, nombre, telefono, institucion, cargo, tipo_tramite, dias,
     fecha_desde, fecha_hasta, codigo_rojo, medico, especialidad, codigo_registro) = datos

    guardar_beneficiario(cedula, nombre, telefono, institucion, cargo)

    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE reposos SET
            cedula = ?,
            tipo_tramite = ?,
            dias = ?,
            fecha_desde = ?,
            fecha_hasta = ?,
            codigo_rojo = ?,
            medico = ?,
            especialidad = ?,
            codigo_registro = ?
        WHERE id = ?
    ''', (cedula, tipo_tramite, dias, fecha_desde, fecha_hasta,
          codigo_rojo, medico, especialidad, codigo_registro, id_reg))
    conexion.commit()
    conexion.close()