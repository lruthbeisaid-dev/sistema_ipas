import datetime
import re
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import base_datos

TIPOS_FILTRO = ["Todos", "Cuido", "Reposo Regular", "Pre-Natal (61 días)",
                "Post-Natal (89 días)", "Pre y Post-Natal (150 días)"]
ESTADOS_FILTRO = ["Todos", "Vigentes", "Vencidos"]
COLORES_FILTRO = ["Todos", "Verde claro", "Verde oscuro", "Amarillo", "Naranja", "Rojo",
                   "Azul claro", "Azul oscuro", "rosado", "Fucsia", "Gris", "Negro", "Marron"]


class ModuloHistorial(tk.Frame):
    def __init__(self, parent, callback_renovar=None, rol="admin"):
        super().__init__(parent, bg="#ffffff", padx=20, pady=20, bd=1, relief="solid")
        self.callback_renovar = callback_renovar
        self.rol = rol

        self.COLOR_TEXT_DARK = "#333333"
        self.COLOR_PRIMARY = "#00a8cc"

        lbl_t = tk.Label(
            self,
            text="Histórico y Gestión de Registros",
            font=("Helvetica", 14, "bold"),
            bg="#ffffff",
            fg=self.COLOR_TEXT_DARK
        )
        lbl_t.pack(anchor="w", pady=(0, 10))

        # --- BARRA DE FILTROS ---
        frame_filtros = tk.Frame(self, bg="#f0f2f5", padx=12, pady=10, bd=1, relief="groove")
        frame_filtros.pack(fill="x", pady=(0, 8))

        fila1 = tk.Frame(frame_filtros, bg="#f0f2f5")
        fila1.pack(fill="x", pady=(0, 6))

        tk.Label(fila1, text="Buscar (Cédula o Nombre):", font=("Helvetica", 9, "bold"),
                 bg="#f0f2f5", fg="#555555").pack(side="left", padx=(0, 5))
        self.ent_buscar = tk.Entry(fila1, font=("Helvetica", 10), width=22)
        self.ent_buscar.pack(side="left", padx=5)
        self.ent_buscar.bind("<KeyRelease>", self._al_escribir_busqueda)

        tk.Label(fila1, text="Tipo:", font=("Helvetica", 9, "bold"),
                 bg="#f0f2f5", fg="#555555").pack(side="left", padx=(15, 5))
        self.cmb_filtro_tipo = ttk.Combobox(fila1, values=TIPOS_FILTRO, state="readonly", width=20)
        self.cmb_filtro_tipo.current(0)
        self.cmb_filtro_tipo.pack(side="left", padx=5)
        self.cmb_filtro_tipo.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros())

        tk.Label(fila1, text="Estatus:", font=("Helvetica", 9, "bold"),
                 bg="#f0f2f5", fg="#555555").pack(side="left", padx=(15, 5))
        self.cmb_filtro_estado = ttk.Combobox(fila1, values=ESTADOS_FILTRO, state="readonly", width=12)
        self.cmb_filtro_estado.current(0)
        self.cmb_filtro_estado.pack(side="left", padx=5)
        self.cmb_filtro_estado.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros())

        tk.Label(fila1, text="Color:", font=("Helvetica", 9, "bold"),
                 bg="#f0f2f5", fg="#555555").pack(side="left", padx=(15, 5))
        self.cmb_filtro_color = ttk.Combobox(fila1, values=COLORES_FILTRO, state="readonly", width=12)
        self.cmb_filtro_color.current(0)
        self.cmb_filtro_color.pack(side="left", padx=5)
        self.cmb_filtro_color.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros())

        fila2 = tk.Frame(frame_filtros, bg="#f0f2f5")
        fila2.pack(fill="x")

        tk.Label(fila2, text="Rango Fecha Desde:", font=("Helvetica", 9, "bold"),
                 bg="#f0f2f5", fg="#555555").pack(side="left", padx=(0, 5))
        self.ent_rango_desde = tk.Entry(fila2, font=("Helvetica", 10), width=12)
        self.ent_rango_desde.pack(side="left", padx=5)
        tk.Label(fila2, text="hasta", font=("Helvetica", 9), bg="#f0f2f5", fg="#555555").pack(side="left", padx=3)
        self.ent_rango_hasta = tk.Entry(fila2, font=("Helvetica", 10), width=12)
        self.ent_rango_hasta.pack(side="left", padx=5)
        tk.Label(fila2, text="(DD-MM-AAAA)", font=("Helvetica", 8, "italic"),
                 bg="#f0f2f5", fg="#888888").pack(side="left", padx=(2, 10))

        tk.Button(
            fila2, text="APLICAR FILTROS", font=("Helvetica", 9, "bold"),
            bg=self.COLOR_PRIMARY, fg="#ffffff", bd=0, cursor="hand2", padx=10, command=self.aplicar_filtros
        ).pack(side="left", padx=5)

        tk.Button(
            fila2, text="Limpiar Filtros", font=("Helvetica", 9),
            bg="#6c757d", fg="#ffffff", bd=0, cursor="hand2", padx=10, command=self.limpiar_filtros
        ).pack(side="left", padx=5)

        self.lbl_info_estado = tk.Label(
            self, text="Seleccione un registro para editar, eliminar, renovar o incluirlo en el reporte.",
            font=("Helvetica", 9, "italic"), bg="#ffffff", fg="#666666", anchor="w", justify="left"
        )
        self.lbl_info_estado.pack(fill="x", pady=(0, 8))

        # --- BARRA DE ACCIONES ---
        frame_acciones = tk.Frame(self, bg="#ffffff")
        frame_acciones.pack(fill="x", pady=(0, 10))

        btn_renovar = tk.Button(
            frame_acciones, text="🔄 RENOVAR DÍAS RESTANTES", font=("Helvetica", 9, "bold"),
            bg="#2e7d32", fg="#ffffff", bd=0, cursor="hand2", padx=12, pady=6, command=self.renovar_dias_restantes
        )
        btn_renovar.pack(side="left", padx=(0, 5))

        btn_editar = tk.Button(
            frame_acciones, text="✏️ EDITAR REGISTRO", font=("Helvetica", 9, "bold"),
            bg="#1976d2", fg="#ffffff", bd=0, cursor="hand2", padx=12, pady=6, command=self.abrir_ventana_editar
        )
        btn_editar.pack(side="left", padx=5)

        btn_eliminar = tk.Button(
            frame_acciones, text="🗑️ ELIMINAR", font=("Helvetica", 9, "bold"),
            bg="#c62828", fg="#ffffff", bd=0, cursor="hand2", padx=12, pady=6, command=self.eliminar_registro_seleccionado
        )
        btn_eliminar.pack(side="left", padx=5)

        btn_reporte = tk.Button(
            frame_acciones, text="📄 GENERAR REPORTE", font=("Helvetica", 9, "bold"),
            bg="#f57c00", fg="#ffffff", bd=0, cursor="hand2", padx=12, pady=6, command=self.generar_reporte_pdf
        )
        btn_reporte.pack(side="right", padx=5)

        if self.rol == "visualizador":
            btn_renovar.configure(state="disabled")
            btn_editar.configure(state="disabled")
            btn_eliminar.configure(state="disabled")

        # --- TABLA DE REGISTROS ---
        columnas = ("id", "cedula", "nombre", "telefono", "tipo", "dias", "desde", "hasta", "rojo")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings", height=13)

        self.tabla.heading("id", text="ID")
        self.tabla.heading("cedula", text="Cédula")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("telefono", text="Teléfono")
        self.tabla.heading("tipo", text="Trámite")
        self.tabla.heading("dias", text="Días")
        self.tabla.heading("desde", text="Desde")
        self.tabla.heading("hasta", text="Hasta")
        self.tabla.heading("rojo", text="Cod. color")

        self.tabla.column("id", width=35, anchor="center")
        self.tabla.column("cedula", width=90)
        self.tabla.column("nombre", width=140)
        self.tabla.column("telefono", width=95)
        self.tabla.column("tipo", width=110)
        self.tabla.column("dias", width=45, anchor="center")
        self.tabla.column("desde", width=90, anchor="center")
        self.tabla.column("hasta", width=90, anchor="center")
        self.tabla.column("rojo", width=70, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscroll=scrollbar.set)

        self.tabla.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tabla.tag_configure("codigo_rojo", background="#ffebee", foreground="#c62828")

        self.datos_renovacion_actual = None
        self._ultima_lista_mostrada = []
        self.cargar_tabla_completa()

    # ------------------------------------------------------------------
    # Utilidades de fecha
    # ------------------------------------------------------------------

    def _formatear_fecha(self, fecha):
        if not fecha:
            return ""
        if isinstance(fecha, (datetime.date, datetime.datetime)):
            return fecha.strftime("%d-%m-%Y")
        fecha_str = str(fecha).strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.datetime.strptime(fecha_str, fmt).strftime("%d-%m-%Y")
            except ValueError:
                pass
        return fecha_str

    def _parsear_fecha(self, fecha):
        if not fecha:
            return None
        if isinstance(fecha, datetime.datetime):
            return fecha.date()
        if isinstance(fecha, datetime.date):
            return fecha
        fecha_str = str(fecha).strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.datetime.strptime(fecha_str, fmt).date()
            except ValueError:
                pass
        return None

    def _fecha_iso_desde_campo(self, texto):
        texto = texto.strip()
        if not texto:
            return None
        try:
            return datetime.datetime.strptime(texto, "%d-%m-%Y").date().isoformat()
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Carga y filtros de la tabla
    # ------------------------------------------------------------------

    def _llenar_tabla(self, registros):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for reg in registros:
            tag = "codigo_rojo" if reg[10] == "Rojo" else ""
            f_desde = self._formatear_fecha(reg[8])
            f_hasta = self._formatear_fecha(reg[9])
            self.tabla.insert("", "end", values=(reg[0], reg[1], reg[2], reg[3], reg[6], reg[7], f_desde, f_hasta, reg[10]), tags=(tag,))
        self._ultima_lista_mostrada = registros

    def cargar_tabla_completa(self):
        registros = base_datos.obtener_registros()
        self._llenar_tabla(registros)
        self.lbl_info_estado.config(text="Mostrando la totalidad de registros guardados en el sistema.", fg="#666666")
        self._filtros_activos_descripcion = "Todos los registros"

    def _al_escribir_busqueda(self, event=None):
        self.aplicar_filtros()

    def aplicar_filtros(self):
        texto = self.ent_buscar.get().strip()
        tipo = self.cmb_filtro_tipo.get()
        estado_ui = self.cmb_filtro_estado.get()
        color = self.cmb_filtro_color.get()

        estado = None
        if estado_ui == "Vigentes":
            estado = "VIGENTE"
        elif estado_ui == "Vencidos":
            estado = "VENCIDO"

        fecha_desde_iso = self._fecha_iso_desde_campo(self.ent_rango_desde.get())
        fecha_hasta_iso = self._fecha_iso_desde_campo(self.ent_rango_hasta.get())

        if self.ent_rango_desde.get().strip() and not fecha_desde_iso:
            messagebox.showwarning("Fecha inválida", "El campo 'Rango Fecha Desde' debe tener formato DD-MM-AAAA.")
            return
        if self.ent_rango_hasta.get().strip() and not fecha_hasta_iso:
            messagebox.showwarning("Fecha inválida", "El campo 'Rango Fecha hasta' debe tener formato DD-MM-AAAA.")
            return

        registros = base_datos.buscar_registros_filtrados(
            texto=texto or None, tipo=tipo, estado=estado,
            fecha_desde=fecha_desde_iso, fecha_hasta=fecha_hasta_iso, color=color
        )
        self._llenar_tabla(registros)

        descripcion = []
        if texto: descripcion.append(f"búsqueda '{texto}'")
        if tipo != "Todos": descripcion.append(f"tipo {tipo}")
        if estado_ui != "Todos": descripcion.append(estado_ui.lower())
        if color != "Todos": descripcion.append(f"color {color}")
        if fecha_desde_iso or fecha_hasta_iso: descripcion.append("rango de fechas")
        self._filtros_activos_descripcion = ", ".join(descripcion) if descripcion else "Todos los registros"

        if registros:
            self.lbl_info_estado.config(text=f"{len(registros)} registro(s) encontrados con los filtros aplicados.", fg="#1565c0")
        else:
            self.lbl_info_estado.config(text="No se encontraron registros que coincidan con los filtros.", fg="#d32f2f")

        cedula_num = re.sub(r"\D", "", texto)
        if cedula_num and cedula_num == texto:
            self._calcular_resumen_cedula(cedula_num, registros)

    def limpiar_filtros(self):
        self.ent_buscar.delete(0, tk.END)
        self.cmb_filtro_tipo.current(0)
        self.cmb_filtro_estado.current(0)
        self.cmb_filtro_color.current(0)
        self.ent_rango_desde.delete(0, tk.END)
        self.ent_rango_hasta.delete(0, tk.END)
        self.cargar_tabla_completa()

    def _tiene_filtros_activos(self):
        return bool(
            self.ent_buscar.get().strip() or self.cmb_filtro_tipo.get() != "Todos" or
            self.cmb_filtro_estado.get() != "Todos" or self.cmb_filtro_color.get() != "Todos" or
            self.ent_rango_desde.get().strip() or self.ent_rango_hasta.get().strip()
        )

    def _recargar_tabla_actual(self):
        self.aplicar_filtros() if self._tiene_filtros_activos() else self.cargar_tabla_completa()

    # ------------------------------------------------------------------
    # Resumen de días disponibles / renovación
    # ------------------------------------------------------------------

    def _calcular_resumen_cedula(self, cedula, registros):
        if not registros:
            return

        fecha_actual = datetime.date.today()
        hace_un_ano = fecha_actual - datetime.timedelta(days=365)
        hace_seis_meses = fecha_actual - datetime.timedelta(days=180)

        dias_cuido_ano = 0
        dias_reposo_6meses = 0
        reposo_activo = False
        fecha_fin_activo = None
        ultimo_reg = registros[0]

        for reg in registros:
            tipo = reg[6]
            dias = reg[7]
            f_desde = self._parsear_fecha(reg[8])
            f_hasta = self._parsear_fecha(reg[9])
            if not f_desde or not f_hasta:
                continue

            if "Cuido" in tipo and f_desde >= hace_un_ano:
                dias_cuido_ano += dias

            if tipo == "Reposo Regular" and f_desde >= hace_seis_meses:
                dias_reposo_6meses += dias

            if f_hasta >= fecha_actual:
                reposo_activo = True
                if fecha_fin_activo is None or f_hasta > fecha_fin_activo:
                    fecha_fin_activo = f_hasta

        tipo_ultimo = ultimo_reg[6]
        f_hasta_ultimo = self._parsear_fecha(ultimo_reg[9]) or datetime.date.today()
        fecha_inicio_renovacion = f_hasta_ultimo + datetime.timedelta(days=1)

        if "Cuido" in tipo_ultimo:
            dias_disponibles = max(0, 20 - dias_cuido_ano)
        elif tipo_ultimo == "Reposo Regular":
            dias_disponibles = max(0, 84 - dias_reposo_6meses)
        else:
            tope = base_datos.TOPES_DIAS.get(tipo_ultimo, 0)
            dias_disponibles = max(0, tope - ultimo_reg[7])

        self.datos_renovacion_actual = {
            "cedula": ultimo_reg[1], "tipo": ultimo_reg[6],
            "dias_restantes": dias_disponibles, "fecha_inicio": fecha_inicio_renovacion,
            "f_hasta_ultimo": f_hasta_ultimo, "reposo_activo": reposo_activo
        }

        mensaje_resumen = f"Cédula: {cedula} | "
        if "Cuido" in tipo_ultimo:
            mensaje_resumen += f"CUIDOS: Ha consumido {dias_cuido_ano} de 20 días hábiles (Le quedan {dias_disponibles} días). "
        elif tipo_ultimo == "Reposo Regular":
            mensaje_resumen += f"REPOSOS: Acumula {dias_reposo_6meses} de 84 días (Le quedan {dias_disponibles} días). "
        else:
            mensaje_resumen += f"{tipo_ultimo}: Le quedan {dias_disponibles} días respecto al tope de este trámite. "

        if reposo_activo and fecha_fin_activo:
            mensaje_resumen += f"\n🚨 PERMISO ACTIVO hasta el {fecha_fin_activo.strftime('%d-%m-%Y')}."

        self.lbl_info_estado.config(text=mensaje_resumen, fg="#1565c0" if not reposo_activo else "#c62828")

    def renovar_dias_restantes(self):
        if self.rol == "visualizador":
            messagebox.showerror("Acceso Denegado", "Su rol de Visualizador no tiene permiso para renovar registros.")
            return
        seleccion = self.tabla.selection()
        if seleccion:
            item = self.tabla.item(seleccion[0])
            id_reg = item["values"][0]
            reg = base_datos.obtener_registro_por_id(id_reg)
            if reg:
                cedula = reg[1]
                registros = base_datos.buscar_por_cedula(cedula)
                fecha_actual = datetime.date.today()
                hace_un_ano = fecha_actual - datetime.timedelta(days=365)
                hace_seis_meses = fecha_actual - datetime.timedelta(days=180)

                dias_cuido = 0
                dias_reposo = 0
                for r in registros:
                    f_d = self._parsear_fecha(r[8])
                    if f_d:
                        if "Cuido" in r[6] and f_d >= hace_un_ano:
                            dias_cuido += r[7]
                        elif r[6] == "Reposo Regular" and f_d >= hace_seis_meses:
                            dias_reposo += r[7]

                f_hasta_ultimo = self._parsear_fecha(reg[9]) or datetime.date.today()
                fecha_inicio_renovacion = f_hasta_ultimo + datetime.timedelta(days=1)

                if "Cuido" in reg[6]:
                    dias_restantes = max(0, 20 - dias_cuido)
                elif reg[6] == "Reposo Regular":
                    dias_restantes = max(0, 84 - dias_reposo)
                else:
                    tope = base_datos.TOPES_DIAS.get(reg[6], 0)
                    dias_restantes = max(0, tope - reg[7])

                self.datos_renovacion_actual = {
                    "cedula": reg[1], "tipo": reg[6],
                    "dias_restantes": dias_restantes, "fecha_inicio": fecha_inicio_renovacion,
                    "f_hasta_ultimo": f_hasta_ultimo, "reposo_activo": f_hasta_ultimo >= fecha_actual
                }

        if not self.datos_renovacion_actual:
            messagebox.showwarning("Atención", "Consulte una cédula o seleccione una fila de la tabla para renovar.")
            return

        info = self.datos_renovacion_actual
        fecha_actual = datetime.date.today()

        if info.get("reposo_activo") or (info.get("f_hasta_ultimo") and info["f_hasta_ultimo"] >= fecha_actual):
            messagebox.showerror(
                "Renovación No Permitida",
                f"El solicitante posee un permiso ACTIVO vigente hasta el {info['f_hasta_ultimo'].strftime('%d-%m-%Y')}.\n\n"
                f"Según la normativa institucional, NO se puede renovar hasta cumplirse la fecha final estipulada.\n\n"
                f"Podrá realizar la renovación únicamente a partir del {info['fecha_inicio'].strftime('%d-%m-%Y')}."
            )
            return

        if info["dias_restantes"] <= 0:
            messagebox.showerror("Límite Alcanzado", "El solicitante ya consumió el máximo total de días permitidos para su trámite.")
            return

        if self.callback_renovar:
            self.callback_renovar(info["cedula"], info["tipo"], info["dias_restantes"], info["fecha_inicio"])

    def eliminar_registro_seleccionado(self):
        if self.rol == "visualizador":
            messagebox.showerror("Acceso Denegado", "Su rol de Visualizador no tiene permiso para eliminar registros.")
            return
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione una fila de la tabla para eliminar.")
            return

        item = self.tabla.item(seleccion[0])
        id_reg = item["values"][0]
        nombre = item["values"][2]

        confirmacion = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar el trámite ID #{id_reg} correspondiente a {nombre}?\n\n"
            f"Solo se eliminará este trámite; los datos personales de {nombre} se conservan en 'Personas'.\n"
            f"El evento quedará registrado en el módulo de Auditoría."
        )
        if confirmacion:
            base_datos.eliminar_registro(id_reg)
            messagebox.showinfo("Éxito", "Trámite eliminado correctamente.")
            self._recargar_tabla_actual()

    def abrir_ventana_editar(self):
        if self.rol == "visualizador":
            messagebox.showerror("Acceso Denegado", "Su rol de Visualizador no tiene permiso para editar registros.")
            return
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un registro de la tabla para editar.")
            return

        id_reg = self.tabla.item(seleccion[0])["values"][0]
        reg = base_datos.obtener_registro_por_id(id_reg)
        if not reg:
            return

        vent = tk.Toplevel(self)
        vent.title(f"Editar Trámite #{id_reg}")
        vent.geometry("460x560")
        vent.configure(bg="#ffffff")
        vent.grab_set()

        tk.Label(vent, text="Modificar Datos del Trámite", font=("Helvetica", 12, "bold"), bg="#ffffff", fg="#00a8cc").pack(pady=10)
        tk.Label(vent, text=f"Persona: {reg[2]}  (C.I. {reg[1]})", font=("Helvetica", 9, "italic"),
                 bg="#ffffff", fg="#666666").pack(pady=(0, 10))

        frame = tk.Frame(vent, bg="#ffffff", padx=15, pady=5)
        frame.pack(fill="both", expand=True)

        campos = [
            ("Trámite:", reg[6]), ("Días:", str(reg[7])),
            ("Desde (DD-MM-AAAA):", self._formatear_fecha(reg[8])), ("Hasta (DD-MM-AAAA):", self._formatear_fecha(reg[9])),
            ("Código/Color:", reg[10]), ("Médico:", reg[11]), ("Especialidad:", reg[12]),
            ("Código Registro:", reg[13]), ("Para quién (cuido):", reg[14] if len(reg) > 14 else ""),
            ("Parentesco:", reg[15] if len(reg) > 15 else "")
        ]

        entries = {}
        for i, (label_text, val) in enumerate(campos):
            tk.Label(frame, text=label_text, bg="#ffffff", font=("Helvetica", 9, "bold")).grid(row=i, column=0, sticky="w", pady=3)
            ent = tk.Entry(frame, font=("Helvetica", 9), width=30)
            ent.insert(0, str(val))
            ent.grid(row=i, column=1, pady=3, padx=5)
            entries[label_text] = ent

        def guardar_cambios():
            try:
                dias_editados = int(entries["Días:"].get().strip())
            except ValueError:
                messagebox.showerror("Error", "El campo Días debe ser un número entero.")
                return

            nuevos_datos = (
                entries["Trámite:"].get().strip(),
                dias_editados,
                self._formatear_fecha(entries["Desde (DD-MM-AAAA):"].get().strip()),
                self._formatear_fecha(entries["Hasta (DD-MM-AAAA):"].get().strip()),
                entries["Código/Color:"].get().strip(),
                entries["Médico:"].get().strip().upper(),
                entries["Especialidad:"].get().strip(),
                entries["Código Registro:"].get().strip(),
                entries["Para quién (cuido):"].get().strip().upper(),
                entries["Parentesco:"].get().strip()
            )
            base_datos.actualizar_registro(id_reg, nuevos_datos)
            messagebox.showinfo("Éxito", "Trámite actualizado correctamente. Los cambios quedaron en Auditoría.")
            vent.destroy()
            self._recargar_tabla_actual()

        btn = tk.Button(vent, text="GUARDAR CAMBIOS", bg="#00a8cc", fg="#ffffff", font=("Helvetica", 10, "bold"), bd=0, command=guardar_cambios)
        btn.pack(fill="x", padx=20, pady=15)

    # ------------------------------------------------------------------
    # Reporte PDF unificado (respeta filtros aplicados o selección puntual)
    # ------------------------------------------------------------------

    def generar_reporte_pdf(self):
        """Un único botón de reporte: si hay una fila seleccionada, exporta
        solamente el historial de esa persona; si no, exporta exactamente lo
        que la tabla está mostrando en este momento (según los filtros aplicados)."""
        seleccion = self.tabla.selection()

        if seleccion:
            cedula = str(self.tabla.item(seleccion[0])["values"][1])
            nombre = self.tabla.item(seleccion[0])["values"][2]
            registros = base_datos.buscar_por_cedula(cedula)
            titulo_filtro = f"HISTORIAL INDIVIDUAL — {nombre} (C.I. {cedula})"
        else:
            registros = self._ultima_lista_mostrada
            if not registros:
                messagebox.showinfo("Reporte Vacío", "No hay registros para incluir en el reporte con los filtros actuales.")
                return
            filtros_desc = getattr(self, "_filtros_activos_descripcion", "Todos los registros")
            titulo_filtro = f"REPORTE DE HISTÓRICO — {filtros_desc}"

        if not registros:
            messagebox.showinfo("Reporte Vacío", "No hay registros disponibles para generar el reporte.")
            return

        fecha_actual = datetime.date.today()
        lista_filtrada = []
        for reg in registros:
            f_hasta = self._parsear_fecha(reg[9])
            activo = bool(f_hasta and f_hasta >= fecha_actual)
            lista_filtrada.append((reg, activo))

        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf"), ("Todos los archivos", "*.*")],
            title="Guardar Reporte PDF"
        )
        if not ruta_archivo:
            return

        self._construir_pdf(ruta_archivo, lista_filtrada, titulo_filtro)

    def _construir_pdf(self, ruta_archivo, lista_filtrada, titulo_filtro):
        """Construye y guarda el documento PDF institucional. Las librerías de
        ReportLab se importan aquí (no al inicio del módulo) para no cargarlas
        en memoria durante toda la sesión si nunca se genera un reporte."""
        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors

            fecha_actual = datetime.date.today()

            doc = SimpleDocTemplate(
                ruta_archivo,
                pagesize=landscape(letter),
                rightMargin=30, leftMargin=30, topMargin=25, bottomMargin=25
            )

            elements = []
            styles = getSampleStyleSheet()

            mppe_title_left = ParagraphStyle(
                'MPPETitleLeft', parent=styles['Normal'], fontName='Helvetica',
                fontSize=11, leading=13, textColor=colors.HexColor('#666666'), alignment=0
            )
            educacion_big_left = ParagraphStyle(
                'EducacionBigLeft', parent=styles['Normal'], fontName='Helvetica-Bold',
                fontSize=28, leading=30, textColor=colors.HexColor('#4a6b82'), alignment=0
            )
            ipasme_big_right = ParagraphStyle(
                'IpasmeBigRight', parent=styles['Normal'], fontName='Helvetica-Bold',
                fontSize=34, leading=36, textColor=colors.HexColor('#5a7894'), alignment=2
            )
            ipasme_sub_right = ParagraphStyle(
                'IpasmeSubRight', parent=styles['Normal'], fontName='Helvetica',
                fontSize=8, leading=10, textColor=colors.HexColor('#666666'), alignment=2
            )
            header_blue_title = ParagraphStyle(
                'HeaderBlueTitle', parent=styles['Heading1'], fontName='Helvetica-Bold',
                fontSize=11, leading=14, textColor=colors.HexColor('#00a8cc'), alignment=1
            )
            header_blue_subtitle = ParagraphStyle(
                'HeaderBlueSubTitle', parent=styles['Heading2'], fontName='Helvetica-Bold',
                fontSize=12, leading=15, textColor=colors.HexColor('#00a8cc'), alignment=1
            )
            meta_info_style = ParagraphStyle(
                'MetaInfoStyle', parent=styles['Normal'], fontName='Helvetica',
                fontSize=9, leading=12, textColor=colors.HexColor('#333333'), alignment=1
            )
            cell_header_style = ParagraphStyle(
                'CellHeader', parent=styles['Normal'], fontName='Helvetica-Bold',
                fontSize=8, leading=10, textColor=colors.white, alignment=1
            )
            cell_center = ParagraphStyle(
                'CellCenter', parent=styles['Normal'], fontName='Helvetica',
                fontSize=8, leading=10, alignment=1
            )

            logo_izq_path = "logo_mppe.png"
            logo_der_path = "logo_ipasme.png"

            if os.path.exists(logo_izq_path):
                col_izq = Image(logo_izq_path, width=320, height=55)
            else:
                col_izq = [
                    Paragraph("Ministerio del Poder Popular para la", mppe_title_left),
                    Paragraph("EDUCACIÓN <font fontName='Helvetica-Bold' size=28 color='#6c8299'>U.M.I. Rubio</font>", educacion_big_left)
                ]

            if os.path.exists(logo_der_path):
                col_der = Image(logo_der_path, width=220, height=55)
            else:
                col_der = [
                    Paragraph("IPASME", ipasme_big_right),
                    Paragraph("Instituto de Previsión y Asistencia Social<br/>para el personal del Ministerio de Educación", ipasme_sub_right)
                ]

            header_table = Table([[col_izq, col_der]], colWidths=[450, 282])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
            ]))

            elements.append(header_table)
            elements.append(Spacer(1, 8))

            elements.append(Paragraph("INSTITUTO DE PREVISIÓN Y ASISTENCIA SOCIAL DEL MINISTERIO DE EDUCACIÓN (IPASME)", header_blue_title))
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(f"<b>{titulo_filtro}</b>", header_blue_subtitle))
            elements.append(Spacer(1, 4))

            fecha_fmt = fecha_actual.strftime("%d-%m-%Y")
            elements.append(Paragraph(f"Fecha de emisión: {fecha_fmt} | Total de registros: {len(lista_filtrada)}", meta_info_style))
            elements.append(Spacer(1, 10))

            headers = ["Cédula", "Nombre Solicitante", "Teléfono", "Trámite", "Días", "Desde", "Hasta", "Estado", "Cod. Color"]
            data = [[Paragraph(h, cell_header_style) for h in headers]]

            for reg, activo in lista_filtrada:
                estado_str = "ACTIVO" if activo else "CULMINADO"
                color_estado = "#2e7d32" if activo else "#c62828"

                data.append([
                    Paragraph(str(reg[1]), cell_center),
                    Paragraph(str(reg[2]), cell_center),
                    Paragraph(str(reg[3]), cell_center),
                    Paragraph(str(reg[6]), cell_center),
                    Paragraph(str(reg[7]), cell_center),
                    Paragraph(self._formatear_fecha(reg[8]), cell_center),
                    Paragraph(self._formatear_fecha(reg[9]), cell_center),
                    Paragraph(f"<font color='{color_estado}'><b>{estado_str}</b></font>", cell_center),
                    Paragraph(str(reg[10]), cell_center)
                ])

            col_widths = [55, 110, 75, 80, 35, 70, 70, 60, 55]
            t = Table(data, colWidths=col_widths, repeatRows=1)

            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00a8cc')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#80d8ff')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.white])
            ]))

            elements.append(t)
            doc.build(elements)

            messagebox.showinfo("Reporte Generado", f"El reporte PDF fue generado correctamente en:\n{ruta_archivo}")

        except Exception as e:
            messagebox.showerror("Error al Generar PDF", f"Ocurrió un detalle al exportar el PDF:\n{str(e)}")