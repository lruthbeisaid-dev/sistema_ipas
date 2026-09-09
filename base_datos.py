import sqlite3
import datetime
import hashlib
import atexit

# Topes máximos de días por tipo de trámite (usado para validaciones y reportes)
TOPES_DIAS = {
    "Cuido": 20,
    "Reposo Regular": 84,
    "Pre-Natal (61 días)": 61,
    "Post-Natal (89 días)": 89,
    "Pre y Post-Natal (150 días)": 150,
}

# Etiquetas legibles de cada campo del trámite, usadas para describir los
# cambios en el módulo de Auditoría.
CAMPOS_TRAMITE = [
    ("tipo_tramite", "Tipo de trámite"),
    ("dias", "Días"),
    ("fecha_desde", "Fecha Desde"),
    ("fecha_hasta", "Fecha Hasta"),
    ("codigo_rojo", "Código/Color"),
    ("medico", "Médico"),
    ("especialidad", "Especialidad"),
    ("codigo_registro", "Código de registro"),
    ("beneficiario_para", "Para quién (cuido)"),
    ("parentesco", "Parentesco"),
]

CAMPOS_PERSONA = [
    ("nombre", "Nombre"),
    ("telefono", "Teléfono"),
    ("institucion", "Institución"),
    ("cargo", "Cargo"),
]

_SELECCION_REGISTRO = '''
    SELECT r.id, r.cedula, b.nombre, b.telefono, b.institucion, b.cargo,
           r.tipo_tramite, r.dias, r.fecha_desde, r.fecha_hasta,
           r.codigo_rojo, r.medico, r.especialidad, r.codigo_registro,
           r.beneficiario_para, r.parentesco
    FROM reposos r
    JOIN beneficiarios b ON b.cedula = r.cedula
    WHERE r.eliminado = 0
'''

# ---------------------------------------------------------------------------
# Conexión: se mantiene UNA sola conexión abierta durante toda la sesión de
# la aplicación (en vez de abrir/cerrar el archivo en cada consulta), y se
# limita explícitamente la memoria caché de SQLite. En un equipo con solo
# 2 GB de RAM esto reduce notablemente el consumo de recursos del backend.
# ---------------------------------------------------------------------------
_conexion_global = None


def conectar_bd():
    global _conexion_global
    if _conexion_global is None:
        _conexion_global = sqlite3.connect("reposos.db", check_same_thread=False)
        _conexion_global.execute("PRAGMA foreign_keys = ON")
        _conexion_global.execute("PRAGMA journal_mode = WAL")
        _conexion_global.execute("PRAGMA synchronous = NORMAL")
        _conexion_global.execute("PRAGMA cache_size = -2000")   # ~2 MB de caché máx.
        _conexion_global.execute("PRAGMA temp_store = MEMORY")
        atexit.register(cerrar_bd)
    return _conexion_global


def cerrar_bd():
    global _conexion_global
    if _conexion_global is not None:
        try:
            _conexion_global.commit()
            _conexion_global.close()
        except sqlite3.Error:
            pass
        _conexion_global = None


def _hash(texto):
    return hashlib.sha256((texto or "").strip().lower().encode("utf-8")).hexdigest()


def inicializar_bd():
    conexion = conectar_bd()
    cursor = conexion.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS beneficiarios (
            cedula TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL DEFAULT '',
            institucion TEXT NOT NULL,
            cargo TEXT NOT NULL
        )
    ''')

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_reposo INTEGER,
            accion TEXT NOT NULL,
            cedula TEXT,
            nombre TEXT,
            tipo_tramite TEXT,
            codigo_registro TEXT,
            fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            detalle TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY,
            clave_hash TEXT NOT NULL,
            rol TEXT NOT NULL,
            pregunta1 TEXT DEFAULT '',
            respuesta1_hash TEXT DEFAULT '',
            pregunta2 TEXT DEFAULT '',
            respuesta2_hash TEXT DEFAULT ''
        )
    ''')

    _migrar_esquema_anterior(cursor)
    _migrar_columnas_reposo(cursor)
    _migrar_columnas_beneficiario(cursor)
    _migrar_columnas_auditoria(cursor)
    _migrar_columnas_usuarios(cursor)
    _sembrar_usuarios_por_defecto(cursor)

    conexion.commit()

    purgar_registros_vencidos()


def _migrar_esquema_anterior(cursor):
    """Migra bases de datos creadas con el esquema original de una sola tabla."""
    cursor.execute("PRAGMA table_info(reposos)")
    columnas = [col[1] for col in cursor.fetchall()]

    if "tipo" in columnas and "tipo_tramite" not in columnas:
        cursor.execute("ALTER TABLE reposos RENAME COLUMN tipo TO tipo_tramite")
        columnas = [c if c != "tipo" else "tipo_tramite" for c in columnas]

    if "nombre" not in columnas:
        return

    cursor.execute('SELECT DISTINCT cedula, nombre, telefono, institucion, cargo FROM reposos')
    for cedula, nombre, telefono, institucion, cargo in cursor.fetchall():
        cursor.execute('''
            INSERT OR IGNORE INTO beneficiarios (cedula, nombre, telefono, institucion, cargo)
            VALUES (?, ?, ?, ?, ?)
        ''', (cedula, nombre, telefono, institucion, cargo))

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


def _migrar_columnas_reposo(cursor):
    cursor.execute("PRAGMA table_info(reposos)")
    columnas = [col[1] for col in cursor.fetchall()]
    columnas_nuevas = {
        "beneficiario_para": "TEXT NOT NULL DEFAULT ''",
        "parentesco": "TEXT NOT NULL DEFAULT ''",
        "eliminado": "INTEGER NOT NULL DEFAULT 0",
        "fecha_eliminacion": "TIMESTAMP",
    }
    for nombre_col, definicion in columnas_nuevas.items():
        if nombre_col not in columnas:
            cursor.execute(f"ALTER TABLE reposos ADD COLUMN {nombre_col} {definicion}")


def _migrar_columnas_beneficiario(cursor):
    cursor.execute("PRAGMA table_info(beneficiarios)")
    columnas = [col[1] for col in cursor.fetchall()]
    columnas_nuevas = {
        "eliminado": "INTEGER NOT NULL DEFAULT 0",
        "fecha_eliminacion": "TIMESTAMP",
    }
    for nombre_col, definicion in columnas_nuevas.items():
        if nombre_col not in columnas:
            cursor.execute(f"ALTER TABLE beneficiarios ADD COLUMN {nombre_col} {definicion}")


def _migrar_columnas_auditoria(cursor):
    cursor.execute("PRAGMA table_info(auditoria)")
    info = cursor.fetchall()
    columnas = [col[1] for col in info]

    # Una versión previa tenía 'usuario TEXT NOT NULL'; como ya no se registra
    # el usuario (solo el admin puede editar), se reconstruye la tabla sin esa
    # restricción para que las nuevas inserciones (sin 'usuario') no fallen.
    tiene_usuario_not_null = any(col[1] == "usuario" and col[3] == 1 for col in info)
    if tiene_usuario_not_null:
        cursor.execute("ALTER TABLE auditoria RENAME TO auditoria_legacy")
        cursor.execute('''
            CREATE TABLE auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_reposo INTEGER,
                accion TEXT NOT NULL,
                cedula TEXT,
                nombre TEXT,
                tipo_tramite TEXT,
                codigo_registro TEXT,
                fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                detalle TEXT
            )
        ''')
        columnas_legacy = [c[1] for c in info]
        cols_comunes = [c for c in ("id", "id_reposo", "accion", "fecha_hora", "detalle") if c in columnas_legacy]
        lista_columnas = ", ".join(cols_comunes)
        cursor.execute(f"INSERT INTO auditoria ({lista_columnas}) SELECT {lista_columnas} FROM auditoria_legacy")
        cursor.execute("DROP TABLE auditoria_legacy")
        return

    columnas_nuevas = {
        "cedula": "TEXT",
        "nombre": "TEXT",
        "tipo_tramite": "TEXT",
        "codigo_registro": "TEXT",
    }
    for nombre_col, definicion in columnas_nuevas.items():
        if nombre_col not in columnas:
            cursor.execute(f"ALTER TABLE auditoria ADD COLUMN {nombre_col} {definicion}")


def _migrar_columnas_usuarios(cursor):
    cursor.execute("PRAGMA table_info(usuarios)")
    columnas = [col[1] for col in cursor.fetchall()]

    # Compatibilidad con una versión previa que solo tenía una pregunta de seguridad.
    if "pregunta_seguridad" in columnas and "pregunta1" not in columnas:
        cursor.execute("ALTER TABLE usuarios RENAME COLUMN pregunta_seguridad TO pregunta1")
        cursor.execute("ALTER TABLE usuarios RENAME COLUMN respuesta_hash TO respuesta1_hash")
        columnas = [c for c in columnas if c not in ("pregunta_seguridad", "respuesta_hash")]
        columnas += ["pregunta1", "respuesta1_hash"]

    columnas_nuevas = {
        "pregunta1": "TEXT DEFAULT ''",
        "respuesta1_hash": "TEXT DEFAULT ''",
        "pregunta2": "TEXT DEFAULT ''",
        "respuesta2_hash": "TEXT DEFAULT ''",
    }
    for nombre_col, definicion in columnas_nuevas.items():
        if nombre_col not in columnas:
            cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {nombre_col} {definicion}")


def _sembrar_usuarios_por_defecto(cursor):
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] > 0:
        return
    cursor.execute('''
        INSERT INTO usuarios (usuario, clave_hash, rol, pregunta1, respuesta1_hash, pregunta2, respuesta2_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ("admin", _hash("1234"), "admin",
          "¿Cuál es el nombre de la institución donde trabaja?", _hash("ipasme"),
          "¿En qué ciudad se encuentra la oficina principal?", _hash("rubio")))
    cursor.execute('''
        INSERT INTO usuarios (usuario, clave_hash, rol) VALUES (?, ?, ?)
    ''', ("visualizador", _hash("1234"), "visualizador"))


# ---------------------------------------------------------------------------
# Utilidad de comparación de cambios (para el módulo de Auditoría)
# ---------------------------------------------------------------------------

def _describir_cambios(valores_anteriores, valores_nuevos, mapeo_campos):
    """valores_anteriores / valores_nuevos: diccionarios {campo: valor}.
    mapeo_campos: lista de tuplas (campo, etiqueta_legible).
    Devuelve una cadena legible con los campos que cambiaron, o None si no hubo cambios."""
    cambios = []
    for campo, etiqueta in mapeo_campos:
        antes = valores_anteriores.get(campo, "")
        despues = valores_nuevos.get(campo, "")
        if str(antes) != str(despues):
            cambios.append(f"{etiqueta}: '{antes}' → '{despues}'")
    if not cambios:
        return None
    return "; ".join(cambios)


# ---------------------------------------------------------------------------
# Personas (beneficiarios) — módulo "Personas"
# ---------------------------------------------------------------------------

def guardar_beneficiario(cedula, nombre, telefono, institucion, cargo):
    """Inserta o actualiza los datos personales de un beneficiario (upsert por cédula).
    Si la persona había sido eliminada lógicamente, la reactiva."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT INTO beneficiarios (cedula, nombre, telefono, institucion, cargo, eliminado)
        VALUES (?, ?, ?, ?, ?, 0)
        ON CONFLICT(cedula) DO UPDATE SET
            nombre = excluded.nombre,
            telefono = excluded.telefono,
            institucion = excluded.institucion,
            cargo = excluded.cargo,
            eliminado = 0
    ''', (cedula, nombre, telefono, institucion, cargo))
    conexion.commit()


def registrar_o_editar_persona(cedula, nombre, telefono, institucion, cargo):
    """Guarda una persona y registra el evento correspondiente en Auditoría
    (CREACION_PERSONA si es nueva, EDICION_PERSONA si ya existía, con el detalle de los cambios)."""
    existente = obtener_beneficiario_por_cedula(cedula)
    guardar_beneficiario(cedula, nombre, telefono, institucion, cargo)

    nuevos = {"nombre": nombre, "telefono": telefono, "institucion": institucion, "cargo": cargo}

    if existente is None:
        registrar_auditoria("CREACION_PERSONA", cedula=cedula, nombre=nombre,
                             detalle=f"Persona registrada: {nombre} — {institucion} ({cargo})")
    else:
        anteriores = {"nombre": existente[1], "telefono": existente[2],
                      "institucion": existente[3], "cargo": existente[4]}
        detalle = _describir_cambios(anteriores, nuevos, CAMPOS_PERSONA)
        if detalle:
            registrar_auditoria("EDICION_PERSONA", cedula=cedula, nombre=nombre, detalle=detalle)


def obtener_beneficiario_por_cedula(cedula):
    """Devuelve (cedula, nombre, telefono, institucion, cargo) o None si no existe
    (independientemente de si está oculta/eliminada lógicamente)."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT cedula, nombre, telefono, institucion, cargo
        FROM beneficiarios WHERE cedula = ?
    ''', (cedula,))
    return cursor.fetchone()


def obtener_personas(texto=None):
    """Lista de personas activas (no eliminadas), opcionalmente filtradas por
    cédula o nombre (búsqueda parcial, sin distinguir mayúsculas)."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    if texto:
        comodin_cedula = f"%{texto}%"
        comodin_nombre = f"%{texto.upper()}%"
        cursor.execute('''
            SELECT cedula, nombre, telefono, institucion, cargo FROM beneficiarios
            WHERE eliminado = 0 AND (cedula LIKE ? OR UPPER(nombre) LIKE ?)
            ORDER BY nombre ASC
        ''', (comodin_cedula, comodin_nombre))
    else:
        cursor.execute('''
            SELECT cedula, nombre, telefono, institucion, cargo FROM beneficiarios
            WHERE eliminado = 0 ORDER BY nombre ASC
        ''')
    return cursor.fetchall()


def persona_tiene_tramites(cedula):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('SELECT COUNT(*) FROM reposos WHERE cedula = ?', (cedula,))
    return cursor.fetchone()[0] > 0


def eliminar_persona(cedula):
    """Elimina a una persona. Si no tiene ningún trámite asociado (ni siquiera
    eliminado), se borra por completo; si tiene historial, se oculta
    (eliminación lógica) para no perder la trazabilidad de sus trámites.
    Devuelve 'ELIMINADA', 'OCULTADA' o 'NO_EXISTE'."""
    beneficiario = obtener_beneficiario_por_cedula(cedula)
    if not beneficiario:
        return "NO_EXISTE"

    conexion = conectar_bd()
    cursor = conexion.cursor()

    if persona_tiene_tramites(cedula):
        cursor.execute('''
            UPDATE beneficiarios SET eliminado = 1, fecha_eliminacion = CURRENT_TIMESTAMP
            WHERE cedula = ?
        ''', (cedula,))
        conexion.commit()
        registrar_auditoria("ELIMINACION_PERSONA", cedula=cedula, nombre=beneficiario[1],
                             detalle="Persona ocultada (conserva historial de trámites asociados)")
        return "OCULTADA"

    cursor.execute('DELETE FROM beneficiarios WHERE cedula = ?', (cedula,))
    conexion.commit()
    registrar_auditoria("ELIMINACION_PERSONA", cedula=cedula, nombre=beneficiario[1],
                         detalle="Persona eliminada completamente (sin trámites asociados)")
    return "ELIMINADA"


# ---------------------------------------------------------------------------
# Registros (reposos / cuidos) — módulo "Registro de Permisos"
# ---------------------------------------------------------------------------

def guardar_registro(datos_reposo):
    """
    datos_reposo: (cedula, tipo_tramite, dias, fecha_desde, fecha_hasta,
                   codigo_rojo, medico, especialidad, codigo_registro,
                   beneficiario_para, parentesco)
    La cédula debe corresponder a una persona ya registrada en 'Personas'
    (este módulo ya NO crea ni edita datos personales).
    """
    datos_reposo = tuple(datos_reposo)
    if len(datos_reposo) == 9:
        datos_reposo = datos_reposo + ("", "")

    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT INTO reposos (
            cedula, tipo_tramite, dias, fecha_desde, fecha_hasta,
            codigo_rojo, medico, especialidad, codigo_registro,
            beneficiario_para, parentesco
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', datos_reposo)
    id_nuevo = cursor.lastrowid
    conexion.commit()

    beneficiario = obtener_beneficiario_por_cedula(datos_reposo[0])
    nombre = beneficiario[1] if beneficiario else ""
    registrar_auditoria(
        "CREACION_TRAMITE", id_reposo=id_nuevo, cedula=datos_reposo[0], nombre=nombre,
        tipo_tramite=datos_reposo[1], codigo_registro=datos_reposo[8],
        detalle=f"Trámite registrado: {datos_reposo[1]} ({datos_reposo[2]} días, {datos_reposo[3]} a {datos_reposo[4]})"
    )
    return id_nuevo


def obtener_registros():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute(_SELECCION_REGISTRO + ' ORDER BY r.id DESC')
    return cursor.fetchall()


def buscar_por_cedula(cedula):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute(_SELECCION_REGISTRO + ' AND r.cedula = ? ORDER BY r.id DESC', (cedula,))
    return cursor.fetchall()


def obtener_registro_por_id(id_reg):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute(_SELECCION_REGISTRO + ' AND r.id = ?', (id_reg,))
    return cursor.fetchone()


def buscar_registros_filtrados(texto=None, tipo=None, estado=None,
                                fecha_desde=None, fecha_hasta=None, color=None):
    conexion = conectar_bd()
    cursor = conexion.cursor()

    condiciones = []
    parametros = []

    if texto:
        condiciones.append("(r.cedula LIKE ? OR UPPER(b.nombre) LIKE ?)")
        parametros.extend([f"%{texto}%", f"%{texto.upper()}%"])

    if tipo and tipo != "Todos":
        condiciones.append("r.tipo_tramite = ?")
        parametros.append(tipo)

    if color and color != "Todos":
        condiciones.append("r.codigo_rojo = ?")
        parametros.append(color)

    if fecha_desde:
        condiciones.append("r.fecha_desde >= ?")
        parametros.append(fecha_desde)

    if fecha_hasta:
        condiciones.append("r.fecha_desde <= ?")
        parametros.append(fecha_hasta)

    consulta = _SELECCION_REGISTRO
    if condiciones:
        consulta += " AND " + " AND ".join(condiciones)
    consulta += " ORDER BY r.id DESC"

    cursor.execute(consulta, parametros)
    filas = cursor.fetchall()

    if estado in ("VIGENTE", "VENCIDO"):
        hoy = datetime.date.today()
        filtradas = []
        for f in filas:
            try:
                f_hasta = datetime.datetime.strptime(f[9], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            activo = f_hasta >= hoy
            if (estado == "VIGENTE" and activo) or (estado == "VENCIDO" and not activo):
                filtradas.append(f)
        return filtradas

    return filas


def eliminar_registro(id_reg):
    """Eliminación lógica de un trámite. NO afecta los datos personales de
    la persona (solo desaparece el trámite de las consultas normales)."""
    reg = obtener_registro_por_id(id_reg)
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE reposos SET eliminado = 1, fecha_eliminacion = CURRENT_TIMESTAMP WHERE id = ?
    ''', (id_reg,))
    conexion.commit()

    if reg:
        detalle = (f"Trámite eliminado: {reg[6]} | Código de registro: {reg[13]} | "
                   f"Código/Color: {reg[10]} | Días: {reg[7]} | Vigencia: {reg[8]} a {reg[9]}")
        registrar_auditoria("ELIMINACION_TRAMITE", id_reposo=id_reg, cedula=reg[1], nombre=reg[2],
                             tipo_tramite=reg[6], codigo_registro=reg[13], detalle=detalle)


def actualizar_registro(id_reg, datos):
    """
    datos: (tipo_tramite, dias, fecha_desde, fecha_hasta, codigo_rojo, medico,
            especialidad, codigo_registro, beneficiario_para, parentesco)
    Actualiza ÚNICAMENTE los datos del trámite (la cédula/persona no se modifica
    desde aquí; para eso está el módulo Personas).
    """
    reg_anterior = obtener_registro_por_id(id_reg)
    if not reg_anterior:
        return

    (tipo_tramite, dias, fecha_desde, fecha_hasta, codigo_rojo, medico,
     especialidad, codigo_registro, beneficiario_para, parentesco) = datos

    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE reposos SET
            tipo_tramite = ?, dias = ?, fecha_desde = ?, fecha_hasta = ?,
            codigo_rojo = ?, medico = ?, especialidad = ?, codigo_registro = ?,
            beneficiario_para = ?, parentesco = ?
        WHERE id = ?
    ''', (tipo_tramite, dias, fecha_desde, fecha_hasta, codigo_rojo, medico,
          especialidad, codigo_registro, beneficiario_para, parentesco, id_reg))
    conexion.commit()

    anteriores = {
        "tipo_tramite": reg_anterior[6], "dias": reg_anterior[7], "fecha_desde": reg_anterior[8],
        "fecha_hasta": reg_anterior[9], "codigo_rojo": reg_anterior[10], "medico": reg_anterior[11],
        "especialidad": reg_anterior[12], "codigo_registro": reg_anterior[13],
        "beneficiario_para": reg_anterior[14], "parentesco": reg_anterior[15],
    }
    nuevos = {
        "tipo_tramite": tipo_tramite, "dias": dias, "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta, "codigo_rojo": codigo_rojo, "medico": medico,
        "especialidad": especialidad, "codigo_registro": codigo_registro,
        "beneficiario_para": beneficiario_para, "parentesco": parentesco,
    }
    detalle = _describir_cambios(anteriores, nuevos, CAMPOS_TRAMITE) or "Sin cambios detectados"
    registrar_auditoria("EDICION_TRAMITE", id_reposo=id_reg, cedula=reg_anterior[1], nombre=reg_anterior[2],
                         tipo_tramite=tipo_tramite, codigo_registro=codigo_registro, detalle=detalle)


def purgar_registros_vencidos(anios=10):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    limite = (datetime.date.today() - datetime.timedelta(days=365 * anios)).isoformat()
    cursor.execute("SELECT id, cedula, tipo_tramite, codigo_registro FROM reposos WHERE fecha_hasta < ?", (limite,))
    filas = cursor.fetchall()
    ids = [f[0] for f in filas]
    if ids:
        cursor.executemany("DELETE FROM reposos WHERE id = ?", [(i,) for i in ids])
        conexion.commit()
    for id_reg, cedula, tipo_tramite, codigo_registro in filas:
        registrar_auditoria("PURGA_AUTOMATICA", id_reposo=id_reg, cedula=cedula, tipo_tramite=tipo_tramite,
                             codigo_registro=codigo_registro,
                             detalle=f"Registro eliminado automáticamente por antigüedad superior a {anios} años")
    return len(ids)


# ---------------------------------------------------------------------------
# Auditoría
# ---------------------------------------------------------------------------

def registrar_auditoria(accion, id_reposo=None, cedula=None, nombre=None,
                         tipo_tramite=None, codigo_registro=None, detalle=""):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT INTO auditoria (id_reposo, accion, cedula, nombre, tipo_tramite, codigo_registro, detalle)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (id_reposo, accion, cedula, nombre, tipo_tramite, codigo_registro, detalle))
    conexion.commit()


def obtener_auditoria(cedula=None, limite=1000):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    if cedula:
        cursor.execute('''
            SELECT id, accion, cedula, nombre, tipo_tramite, codigo_registro, fecha_hora, detalle
            FROM auditoria WHERE cedula = ? ORDER BY fecha_hora DESC LIMIT ?
        ''', (cedula, limite))
    else:
        cursor.execute('''
            SELECT id, accion, cedula, nombre, tipo_tramite, codigo_registro, fecha_hora, detalle
            FROM auditoria ORDER BY fecha_hora DESC LIMIT ?
        ''', (limite,))
    return cursor.fetchall()


# ---------------------------------------------------------------------------
# Alertas / recordatorios del dashboard
# ---------------------------------------------------------------------------

def crear_alerta(texto):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO alertas (texto) VALUES (?)", (texto,))
    conexion.commit()


def obtener_alertas():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, texto, fecha_creacion FROM alertas ORDER BY id DESC")
    return cursor.fetchall()


def eliminar_alerta(id_alerta):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM alertas WHERE id = ?", (id_alerta,))
    conexion.commit()


# ---------------------------------------------------------------------------
# Usuarios / autenticación / preguntas de seguridad (hasta 2 por usuario)
# ---------------------------------------------------------------------------

def verificar_credenciales(usuario, clave):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT clave_hash, rol FROM usuarios WHERE usuario = ?", (usuario,))
    fila = cursor.fetchone()
    if fila and fila[0] == _hash(clave):
        return fila[1]
    return None


def cambiar_clave(usuario, clave_nueva):
    """Actualiza la clave directamente (usar solo después de haber verificado
    identidad por otro medio: clave actual, preguntas de seguridad, etc.)."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("UPDATE usuarios SET clave_hash = ? WHERE usuario = ?", (_hash(clave_nueva), usuario))
    conexion.commit()


def obtener_preguntas_seguridad(usuario):
    """Devuelve (pregunta1, pregunta2). Cadena vacía si no está configurada."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT pregunta1, pregunta2 FROM usuarios WHERE usuario = ?", (usuario,))
    fila = cursor.fetchone()
    if not fila:
        return ("", "")
    return (fila[0] or "", fila[1] or "")


def verificar_respuesta_seguridad(usuario, respuesta1, respuesta2=None):
    """Verifica la(s) respuesta(s) configuradas. Si solo hay una pregunta
    configurada, basta con responderla correctamente; si hay dos, ambas
    deben ser correctas."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT pregunta1, respuesta1_hash, pregunta2, respuesta2_hash FROM usuarios WHERE usuario = ?", (usuario,))
    fila = cursor.fetchone()
    if not fila:
        return False
    pregunta1, resp1_hash, pregunta2, resp2_hash = fila

    if not pregunta1 and not pregunta2:
        return False

    if pregunta1 and resp1_hash != _hash(respuesta1 or ""):
        return False

    if pregunta2 and resp2_hash != _hash(respuesta2 or ""):
        return False

    return True


def actualizar_pregunta_individual(usuario, numero, pregunta, respuesta):
    """Actualiza solo la pregunta de seguridad 1 o 2, dejando la otra intacta."""
    campo_p = "pregunta1" if numero == 1 else "pregunta2"
    campo_r = "respuesta1_hash" if numero == 1 else "respuesta2_hash"
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute(f"UPDATE usuarios SET {campo_p} = ?, {campo_r} = ? WHERE usuario = ?",
                   (pregunta, _hash(respuesta), usuario))
    conexion.commit()


def establecer_preguntas_seguridad(usuario, pregunta1, respuesta1, pregunta2="", respuesta2=""):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE usuarios SET pregunta1 = ?, respuesta1_hash = ?, pregunta2 = ?, respuesta2_hash = ?
        WHERE usuario = ?
    ''', (pregunta1, _hash(respuesta1) if respuesta1 else "",
          pregunta2, _hash(respuesta2) if respuesta2 else "", usuario))
    conexion.commit()