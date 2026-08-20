import datetime
import re
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import base_datos

# Importaciones de ReportLab para la generación de reportes en PDF
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ModuloHistorial(tk.Frame):
    def __init__(self, parent, callback_renovar=None, rol="admin"):
        super().__init__(parent, bg="#ffffff", padx=20, pady=20, bd=1, relief="solid")
        self.callback_renovar = callback_renovar
        self.rol = rol

        self.COLOR_TEXT_DARK = "#333333"
        self.COLOR_PRIMARY = "#00a8cc"

        # Validación en tiempo real: Solo permite números en el campo Cédula
        self.vcmd_solo_numeros = (self.register(self._validar_entrada_solo_numeros), '%P')

        lbl_t = tk.Label(
            self, 
            text="Histórico y Gestión de Registros", 
            font=("Helvetica", 14, "bold"), 
            bg="#ffffff", 
            fg=self.COLOR_TEXT_DARK
        )
        lbl_t.pack(anchor="w", pady=(0, 10))

        # --- BARRA DE BÚSQUEDA Y CONSULTA ---
        frame_busqueda = tk.Frame(self, bg="#f0f2f5", padx=12, pady=10, bd=1, relief="groove")
        frame_busqueda.pack(fill="x", pady=(0, 10))

        tk.Label(
            frame_busqueda, text="Buscar Cédula:", 
            font=("Helvetica", 10, "bold"), bg="#f0f2f5", fg="#555555"
        ).pack(side="left", padx=(0, 5))

        # Campo con validación estricta de sólo números
        self.ent_buscar_cedula = tk.Entry(
            frame_busqueda, font=("Helvetica", 10), width=18,
            validate="key", validatecommand=self.vcmd_solo_numeros
        )
        self.ent_buscar_cedula.pack(side="left", padx=5)

        btn_buscar = tk.Button(
            frame_busqueda, text="CONSULTAR DÍAS", font=("Helvetica", 9, "bold"),
            bg=self.COLOR_PRIMARY, fg="#ffffff", bd=0, cursor="hand2", padx=10, command=self.consultar_estado_cedula
        )
        btn_buscar.pack(side="left", padx=5)

        btn_mostrar_todo = tk.Button(
            frame_busqueda, text="Mostrar Todos", font=("Helvetica", 9),
            bg="#6c757d", fg="#ffffff", bd=0, cursor="hand2", padx=10, command=self.cargar_tabla_completa
        )
        btn_mostrar_todo.pack(side="left", padx=5)

        self.lbl_info_estado = tk.Label(
            self, text="Seleccione un registro para editar, eliminar, renovar o exportar informe.",
            font=("Helvetica", 9, "italic"), bg="#ffffff", fg="#666666", anchor="w", justify="left"
        )
        self.lbl_info_estado.pack(fill="x", pady=(0, 8))

        # --- BARRA DE ACCIONES (EDITAR, ELIMINAR, RENOVAR, REPORTES) ---
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

        # El rol "visualizador" solo puede consultar, buscar y generar reportes:
        # no tiene permiso para renovar, editar ni eliminar registros.
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
        self.cargar_tabla_completa()

    def _validar_entrada_solo_numeros(self, texto):
        """Impide escribir caracteres distintos a dígitos numéricos en la Cédula."""
        return texto.isdigit() or texto == ""

    def _formatear_fecha(self, fecha):
        """Asegura estrictamente el formato DD-MM-AAAA para visualización."""
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
        """Obtiene un objeto datetime.date tolerando orígenes YYYY-MM-DD o DD-MM-AAAA."""
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

    def cargar_tabla_completa(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        registros = base_datos.obtener_registros()
        for reg in registros:
            tag = "codigo_rojo" if reg[10] == "SI" else ""
            f_desde = self._formatear_fecha(reg[8])
            f_hasta = self._formatear_fecha(reg[9])
            self.tabla.insert("", "end", values=(reg[0], reg[1], reg[2], reg[3], reg[6], reg[7], f_desde, f_hasta, reg[10]), tags=(tag,))
        
        self.lbl_info_estado.config(text="Mostrando la totalidad de registros guardados en el sistema.", fg="#666666")

    def consultar_estado_cedula(self):
        cedula_raw = self.ent_buscar_cedula.get().strip()
        cedula = re.sub(r"\D", "", cedula_raw)

        if not cedula:
            messagebox.showwarning("Atención", "Ingrese un número de cédula válido para consultar.")
            return

        registros = base_datos.buscar_por_cedula(cedula)
        
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        if not registros:
            self.lbl_info_estado.config(text=f"No se encontraron registros previos para la cédula: {cedula}", fg="#d32f2f")
            self.datos_renovacion_actual = None
            return

        for reg in registros:
            tag = "codigo_rojo" if reg[10] == "SI" else ""
            f_desde = self._formatear_fecha(reg[8])
            f_hasta = self._formatear_fecha(reg[9])
            self.tabla.insert("", "end", values=(reg[0], reg[1], reg[2], reg[3], reg[6], reg[7], f_desde, f_hasta, reg[10]), tags=(tag,))

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

            if ("Reposo" in tipo or "Natal" in tipo) and f_desde >= hace_seis_meses:
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
        else:
            dias_disponibles = max(0, 84 - dias_reposo_6meses)

        self.datos_renovacion_actual = {
            "cedula": ultimo_reg[1],
            "nombre": ultimo_reg[2],
            "telefono": ultimo_reg[3],
            "institucion": ultimo_reg[4],
            "cargo": ultimo_reg[5],
            "tipo": ultimo_reg[6],
            "dias_restantes": dias_disponibles,
            "fecha_inicio": fecha_inicio_renovacion,
            "f_hasta_ultimo": f_hasta_ultimo,
            "reposo_activo": reposo_activo
        }

        mensaje_resumen = f"Cédula: {cedula} | "
        if "Cuido" in tipo_ultimo:
            mensaje_resumen += f"CUIDOS: Ha consumido {dias_cuido_ano} de 20 días hábiles (Le quedan {dias_disponibles} días). "
        else:
            mensaje_resumen += f"REPOSOS: Acumula {dias_reposo_6meses} de 84 días (Le quedan {dias_disponibles} días). "

        if reposo_activo and fecha_fin_activo:
            mensaje_resumen += f"\n🚨 PERMISO ACTIVO hasta el {fecha_fin_activo.strftime('%d-%m-%Y')}."

        self.lbl_info_estado.config(text=mensaje_resumen, fg="#1565c0" if not reposo_activo else "#c62828")

        if reposo_activo:
            messagebox.showwarning(
                "Aviso de Permiso Activo - Renovación Bloqueada",
                f"El solicitante {ultimo_reg[2]} (Cédula: {cedula}) posee un permiso ACTIVO vigente hasta el {fecha_fin_activo.strftime('%d-%m-%Y')}.\n\n"
                f"⛔ REGULACIÓN INSTITUCIONAL:\n"
                f"Tiene que cumplirse la totalidad de días solicitados a la institución antes de tramitar una renovación.\n\n"
                f"Podrá renovar los {dias_disponibles} días restantes únicamente a partir del: {fecha_inicio_renovacion.strftime('%d-%m-%Y')} (un día después del vencimiento)."
            )
        elif dias_disponibles > 0:
            respuesta = messagebox.askyesno(
                "Renovación Disponible",
                f"El último permiso de {ultimo_reg[2]} finalizó el {f_hasta_ultimo.strftime('%d-%m-%Y')}.\n\n"
                f"• Días disponibles para renovar: {dias_disponibles} días.\n"
                f"• Fecha sugerida de inicio: {fecha_inicio_renovacion.strftime('%d-%m-%Y')}.\n\n"
                f"¿Desea preparar el formulario para renovar los días restantes ahora?"
            )
            if respuesta:
                self.renovar_dias_restantes()

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
                        elif ("Reposo" in r[6] or "Natal" in r[6]) and f_d >= hace_seis_meses:
                            dias_reposo += r[7]

                f_hasta_ultimo = self._parsear_fecha(reg[9]) or datetime.date.today()
                fecha_inicio_renovacion = f_hasta_ultimo + datetime.timedelta(days=1)

                if "Cuido" in reg[6]:
                    dias_restantes = max(0, 20 - dias_cuido)
                else:
                    dias_restantes = max(0, 84 - dias_reposo)

                self.datos_renovacion_actual = {
                    "cedula": reg[1], "nombre": reg[2], "telefono": reg[3],
                    "institucion": reg[4], "cargo": reg[5], "tipo": reg[6],
                    "dias_restantes": dias_restantes, "fecha_inicio": fecha_inicio_renovacion,
                    "f_hasta_ultimo": f_hasta_ultimo,
                    "reposo_activo": f_hasta_ultimo >= fecha_actual
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
            self.callback_renovar(
                info["cedula"], info["nombre"], info["telefono"],
                info["institucion"], info["cargo"], info["tipo"],
                info["dias_restantes"], info["fecha_inicio"]
            )

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

        confirmacion = messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de eliminar el registro ID #{id_reg} correspondiente a {nombre}?")
        if confirmacion:
            base_datos.eliminar_registro(id_reg)
            messagebox.showinfo("Éxito", "Registro eliminado correctamente.")
            self.cargar_tabla_completa()

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
        if not reg: return

        vent = tk.Toplevel(self)
        vent.title(f"Editar Registro #{id_reg}")
        vent.geometry("500x580")
        vent.configure(bg="#ffffff")
        vent.grab_set()

        vcmd_solo_numeros_edit = (vent.register(self._validar_entrada_solo_numeros), '%P')

        tk.Label(vent, text="Modificar Datos del Registro", font=("Helvetica", 12, "bold"), bg="#ffffff", fg="#00a8cc").pack(pady=10)

        frame = tk.Frame(vent, bg="#ffffff", padx=15, pady=5)
        frame.pack(fill="both", expand=True)

        campos = [
            ("Cédula:", reg[1]), ("Nombre:", reg[2]), ("Teléfono:", reg[3]),
            ("Institución:", reg[4]), ("Cargo:", reg[5]), ("Trámite:", reg[6]),
            ("Días:", str(reg[7])), ("Desde (DD-MM-AAAA):", self._formatear_fecha(reg[8])),
            ("Hasta (DD-MM-AAAA):", self._formatear_fecha(reg[9])), ("Código Rojo:", reg[10]),
            ("Médico:", reg[11]), ("Especialidad:", reg[12]), ("Procesador:", reg[13])
        ]

        entries = {}
        for i, (label_text, val) in enumerate(campos):
            tk.Label(frame, text=label_text, bg="#ffffff", font=("Helvetica", 9, "bold")).grid(row=i, column=0, sticky="w", pady=3)
            
            if label_text == "Cédula:":
                ent = tk.Entry(frame, font=("Helvetica", 9), width=30, validate="key", validatecommand=vcmd_solo_numeros_edit)
            else:
                ent = tk.Entry(frame, font=("Helvetica", 9), width=30)
                
            ent.insert(0, str(val))
            ent.grid(row=i, column=1, pady=3, padx=5)
            entries[label_text] = ent

        def guardar_cambios():
            cedula_editada = re.sub(r"\D", "", entries["Cédula:"].get().strip())
            if not cedula_editada.isdigit():
                messagebox.showerror("Error de Cédula", "La Cédula debe contener únicamente números.")
                return

            nuevos_datos = (
                cedula_editada,
                entries["Nombre:"].get().strip(),
                entries["Teléfono:"].get().strip(),
                entries["Institución:"].get().strip(),
                entries["Cargo:"].get().strip(),
                entries["Trámite:"].get().strip(),
                int(entries["Días:"].get().strip()),
                self._formatear_fecha(entries["Desde (DD-MM-AAAA):"].get().strip()),
                self._formatear_fecha(entries["Hasta (DD-MM-AAAA):"].get().strip()),
                entries["Código Rojo:"].get().strip(),
                entries["Médico:"].get().strip(),
                entries["Especialidad:"].get().strip(),
                entries["Procesador:"].get().strip()
            )
            base_datos.actualizar_registro(id_reg, nuevos_datos)
            messagebox.showinfo("Éxito", "Registro actualizado correctamente.")
            vent.destroy()
            self.cargar_tabla_completa()

        btn = tk.Button(vent, text="GUARDAR CAMBIOS", bg="#00a8cc", fg="#ffffff", font=("Helvetica", 10, "bold"), bd=0, command=guardar_cambios)
        btn.pack(fill="x", padx=20, pady=15)

    def generar_reporte_pdf(self):
        registros = base_datos.obtener_registros()
        if not registros:
            messagebox.showinfo("Reporte Vacío", "No hay registros disponibles para generar el reporte.")
            return

        # Ventana modal para seleccionar la categoría de reporte a exportar
        vent_opciones = tk.Toplevel(self)
        vent_opciones.title("Seleccionar Tipo de Reporte")
        vent_opciones.geometry("400x380")
        vent_opciones.configure(bg="#ffffff")
        vent_opciones.resizable(False, False)
        vent_opciones.grab_set()

        tk.Label(
            vent_opciones, 
            text="Seleccione el Reporte a Exportar", 
            font=("Helvetica", 12, "bold"), 
            bg="#ffffff", 
            fg=self.COLOR_PRIMARY
        ).pack(pady=(15, 10))

        opcion_var = tk.StringVar(value="TODOS")

        opciones = [
            ("📋 Reporte General Completo (Unificado)", "TODOS"),
            ("🟢 Personas ACTIVA por Reposos", "REPOSOS_ACTIVOS"),
            ("🟢 Personas ACTIVAS por Cuidos", "CUIDOS_ACTIVOS"),
            ("🔴 Personas CULMINARON sus Reposos", "REPOSOS_CULMINADOS"),
            ("🔴 Personas CULMINARON sus Cuidos", "CUIDOS_CULMINADOS")
        ]

        frame_radio = tk.Frame(vent_opciones, bg="#ffffff", padx=20)
        frame_radio.pack(fill="both", expand=True)

        for texto, valor in opciones:
            rb = tk.Radiobutton(
                frame_radio, 
                text=texto, 
                value=valor, 
                variable=opcion_var, 
                font=("Helvetica", 10), 
                bg="#ffffff", 
                activebackground="#ffffff", 
                anchor="w"
            )
            rb.pack(fill="x", pady=5)

        def procesar_exportacion():
            tipo_reporte = opcion_var.get()
            vent_opciones.destroy()

            ruta_archivo = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Documento PDF", "*.pdf"), ("Todos los archivos", "*.*")],
                title="Guardar Reporte Institucional PDF"
            )

            if not ruta_archivo:
                return

            fecha_actual = datetime.date.today()

            # Clasificación de registros en memoria
            lista_filtrada = []
            titulo_filtro = ""

            for reg in registros:
                tipo_tramite = str(reg[6])
                es_cuido = "Cuido" in tipo_tramite
                es_reposo = "Reposo" in tipo_tramite or "Natal" in tipo_tramite

                f_hasta = self._parsear_fecha(reg[9])
                if not f_hasta:
                    continue

                esta_activo = f_hasta >= fecha_actual

                if tipo_reporte == "TODOS":
                    lista_filtrada.append((reg, esta_activo))
                    titulo_filtro = "REPORTE GENERAL UNIFICADO DE REPOSOS Y CUIDOS"
                elif tipo_reporte == "REPOSOS_ACTIVOS" and es_reposo and esta_activo:
                    lista_filtrada.append((reg, esta_activo))
                    titulo_filtro = "REPORTE DE PERSONAS ACTIVAS POR REPOSOS / NATALES"
                elif tipo_reporte == "CUIDOS_ACTIVOS" and es_cuido and esta_activo:
                    lista_filtrada.append((reg, esta_activo))
                    titulo_filtro = "REPORTE DE PERSONAS ACTIVAS POR CUIDOS"
                elif tipo_reporte == "REPOSOS_CULMINADOS" and es_reposo and not esta_activo:
                    lista_filtrada.append((reg, esta_activo))
                    titulo_filtro = "REPORTE DE PERSONAS QUE CULMINARON SUS REPOSOS / NATALES"
                elif tipo_reporte == "CUIDOS_CULMINADOS" and es_cuido and not esta_activo:
                    lista_filtrada.append((reg, esta_activo))
                    titulo_filtro = "REPORTE DE PERSONAS QUE CULMINARON SUS CUIDOS"

            if not lista_filtrada:
                messagebox.showinfo("Sin Datos", "No se encontraron registros que coincidan con la categoría seleccionada.")
                return

            try:
                # Construcción del PDF con ReportLab (Orientación Horizontal/Landscape)
                doc = SimpleDocTemplate(
                    ruta_archivo,
                    pagesize=landscape(letter),
                    rightMargin=30, leftMargin=30, topMargin=25, bottomMargin=25
                )
                
                elements = []
                styles = getSampleStyleSheet()

                # --- CONFIGURACIÓN DE ESTILOS EXACTOS DE LA REFERENCIA ---
                mppe_title_left = ParagraphStyle(
                    'MPPETitleLeft',
                    parent=styles['Normal'],
                    fontName='Helvetica',
                    fontSize=11,
                    leading=13,
                    textColor=colors.HexColor('#666666'),
                    alignment=0
                )

                educacion_big_left = ParagraphStyle(
                    'EducacionBigLeft',
                    parent=styles['Normal'],
                    fontName='Helvetica-Bold',
                    fontSize=28,
                    leading=30,
                    textColor=colors.HexColor('#4a6b82'),
                    alignment=0
                )

                umi_rubio_left = ParagraphStyle(
                    'UmiRubioLeft',
                    parent=styles['Normal'],
                    fontName='Helvetica-Bold',
                    fontSize=28,
                    leading=30,
                    textColor=colors.HexColor('#6c8299'),
                    alignment=0
                )

                ipasme_big_right = ParagraphStyle(
                    'IpasmeBigRight',
                    parent=styles['Normal'],
                    fontName='Helvetica-Bold',
                    fontSize=34,
                    leading=36,
                    textColor=colors.HexColor('#5a7894'),
                    alignment=2
                )

                ipasme_sub_right = ParagraphStyle(
                    'IpasmeSubRight',
                    parent=styles['Normal'],
                    fontName='Helvetica',
                    fontSize=8,
                    leading=10,
                    textColor=colors.HexColor('#666666'),
                    alignment=2
                )

                header_blue_title = ParagraphStyle(
                    'HeaderBlueTitle',
                    parent=styles['Heading1'],
                    fontName='Helvetica-Bold',
                    fontSize=11,
                    leading=14,
                    textColor=colors.HexColor('#00a8cc'),
                    alignment=1
                )
                
                header_blue_subtitle = ParagraphStyle(
                    'HeaderBlueSubTitle',
                    parent=styles['Heading2'],
                    fontName='Helvetica-Bold',
                    fontSize=12,
                    leading=15,
                    textColor=colors.HexColor('#00a8cc'),
                    alignment=1
                )

                meta_info_style = ParagraphStyle(
                    'MetaInfoStyle',
                    parent=styles['Normal'],
                    fontName='Helvetica',
                    fontSize=9,
                    leading=12,
                    textColor=colors.HexColor('#333333'),
                    alignment=1
                )

                cell_header_style = ParagraphStyle(
                    'CellHeader',
                    parent=styles['Normal'],
                    fontName='Helvetica-Bold',
                    fontSize=8,
                    leading=10,
                    textColor=colors.white,
                    alignment=1
                )

                cell_center = ParagraphStyle(
                    'CellCenter',
                    parent=styles['Normal'],
                    fontName='Helvetica',
                    fontSize=8,
                    leading=10,
                    alignment=1
                )

                cell_left = ParagraphStyle(
                    'CellLeft',
                    parent=styles['Normal'],
                    fontName='Helvetica',
                    fontSize=8,
                    leading=10,
                    alignment=0
                )

                # --- BANNER / CABECERA SUPERIOR ---
                logo_izq_path = "logo_mppe.png"
                logo_der_path = "logo_ipasme.png"

                # Lado Izquierdo: Imagen o Texto formateado exacto
                if os.path.exists(logo_izq_path):
                    col_izq = Image(logo_izq_path, width=320, height=55)
                else:
                    col_izq = [
                        Paragraph("Ministerio del Poder Popular para la", mppe_title_left),
                        Paragraph("EDUCACIÓN <font fontName='Helvetica-Bold' size=28 color='#6c8299'>U.M.I. Rubio</font>", educacion_big_left)
                    ]

                # Lado Derecho: Imagen o Texto formateado exacto
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

                # --- TÍTULOS DE CABECERA Y METADATOS ---
                elements.append(Paragraph("INSTITUTO DE PREVISIÓN Y ASISTENCIA SOCIAL DEL MINISTERIO DE EDUCACIÓN (IPASME)", header_blue_title))
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(f"<b>{titulo_filtro}</b>", header_blue_subtitle))
                elements.append(Spacer(1, 4))
                
                fecha_fmt = fecha_actual.strftime("%d-%m-%Y")
                elements.append(Paragraph(f"Fecha de emisión: {fecha_fmt} | Total de registros: {len(lista_filtrada)}", meta_info_style))
                elements.append(Spacer(1, 10))

                # --- TABLA DE DATOS (Ajustada a la referencia) ---
                headers = ["Cédula", "Nombre Solicitante", "Teléfono", "Trámite", "Días", "Desde", "Hasta", "Estado", "Cod. Color"]
                data = [[Paragraph(h, cell_header_style) for h in headers]]

                for reg, activo in lista_filtrada:
                    estado_str = "ACTIVO" if activo else "CULMINADO"
                    color_estado = "#2e7d32" if activo else "#c62828"
                    
                    data.append([
                        Paragraph(str(reg[1]), cell_center),
                        Paragraph(str(reg[2]), cell_left),
                        Paragraph(str(reg[3]), cell_center),
                        Paragraph(str(reg[6]), cell_center),
                        Paragraph(str(reg[7]), cell_center),
                        Paragraph(self._formatear_fecha(reg[8]), cell_center),
                        Paragraph(self._formatear_fecha(reg[9]), cell_center),
                        Paragraph(f"<font color='{color_estado}'><b>{estado_str}</b></font>", cell_center),
                        Paragraph(str(reg[10]), cell_center)
                    ])

                # Ancho exacto de columnas para completar los 732pt del ancho utilizable
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

        btn_confirmar = tk.Button(
            vent_opciones, 
            text="EXPORTAR REPORTE PDF", 
            bg=self.COLOR_PRIMARY, 
            fg="#ffffff", 
            font=("Helvetica", 10, "bold"), 
            bd=0, 
            cursor="hand2", 
            command=procesar_exportacion
        )
        btn_confirmar.pack(fill="x", padx=20, pady=15, ipady=5)