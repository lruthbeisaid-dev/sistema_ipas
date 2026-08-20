"""
Cálculo de feriados y días hábiles/no laborables en Venezuela.

Se usa para sugerir automáticamente la 'Fecha Hasta' de los permisos de tipo
Cuido, en los que solo cuentan los días hábiles (no sábados, domingos ni
feriados nacionales).
"""

import datetime


def _domingo_de_pascua(anio):
    """Calcula la fecha del Domingo de Pascua (Algoritmo de Meeus/Jones/Butcher)."""
    a = anio % 19
    b = anio // 100
    c = anio % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(anio, mes, dia)


def feriados_venezuela(anio):
    """Devuelve el conjunto de fechas feriadas/no laborables oficiales de Venezuela para un año dado."""
    pascua = _domingo_de_pascua(anio)

    return {
        datetime.date(anio, 1, 1),                                  # Año Nuevo
        pascua - datetime.timedelta(days=48),                       # Lunes de Carnaval
        pascua - datetime.timedelta(days=47),                       # Martes de Carnaval
        pascua - datetime.timedelta(days=3),                        # Jueves Santo
        pascua - datetime.timedelta(days=2),                        # Viernes Santo
        datetime.date(anio, 4, 19),                                 # Declaración de la Independencia
        datetime.date(anio, 5, 1),                                  # Día del Trabajador
        datetime.date(anio, 6, 24),                                 # Batalla de Carabobo
        datetime.date(anio, 7, 5),                                  # Día de la Independencia
        datetime.date(anio, 7, 24),                                 # Natalicio de Simón Bolívar
        datetime.date(anio, 10, 12),                                # Día de la Resistencia Indígena
        datetime.date(anio, 12, 24),                                # Nochebuena
        datetime.date(anio, 12, 25),                                # Navidad
        datetime.date(anio, 12, 31),                                # Fin de Año
    }


def es_dia_habil(fecha):
    """True si la fecha es un día hábil en Venezuela (no sábado, domingo ni feriado)."""
    if fecha.weekday() >= 5:  # 5 = sábado, 6 = domingo
        return False
    return fecha not in feriados_venezuela(fecha.year)


def sumar_dias_calendario(fecha_inicio, cantidad_dias):
    """Fecha final contando TODOS los días de la semana de forma corrida (para Reposos)."""
    return fecha_inicio + datetime.timedelta(days=cantidad_dias - 1)


def sumar_dias_habiles(fecha_inicio, cantidad_dias):
    """Fecha final contando solo días hábiles (para Cuidos), a partir de fecha_inicio inclusive."""
    fecha = fecha_inicio
    dias_contados = 0
    while True:
        if es_dia_habil(fecha):
            dias_contados += 1
            if dias_contados == cantidad_dias:
                return fecha
        fecha += datetime.timedelta(days=1)