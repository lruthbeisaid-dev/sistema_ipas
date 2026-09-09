import datetime
import re
import tkinter as tk
from tkinter import ttk, messagebox
import base_datos
import feriados

TIPOS_TRAMITE = ["Cuido", "Reposo Regular", "Pre-Natal (61 días)", "Post-Natal (89 días)",
                  "Pre y Post-Natal (150 días)"]

PARENTESCOS = ["Hijo(a)", "Madre", "Padre", "Esposo(a)", "Otro"]

COLORES_ASISTENCIALES = ["Verde claro", "Verde oscuro", "Amarillo", "Naranja", "Rojo",
                          "Azul claro", "Azul oscuro", "rosado", "Fucsia", "Gris", "Negro", "Marron"]

ESPECIALIDADES = [
    "Medicina general", "Medicina crítica", "Medicina familiar",
    "Medicina interna", "Psiquiatria", "Psicología", "Pediatría", "Ginecología",
    "Otorrinolaringología", "Traumatología", "Cardiología", "Odontología"
]


class ModuloFormulario(tk.Frame):
    def __init__(self, parent, al_guardar_callback=None, rol="admin", ir_a_personas_callback=None):
        super().__init__(parent, bg="#ffffff", padx=25, pady=20, bd=1, relief="solid")
        self.al_guardar_callback = al_guardar_callback
        self.rol = rol
        self.ir_a_personas_callback = ir_a_personas_callback
        self.persona_encontrada = None

        self.COLOR_TEXT_DARK = "#333333"
        self.COLOR_PRIMARY = "#00a8cc"

        vcmd_cedula = (self.register(self._validar_cedula), '%P')

        tk.Label(
            self, text="Registro de Permisos (Reposo o Cuido)",
            font=("Helvetica", 14, "bold"), bg="#ffffff", fg=self.COLOR_TEXT_DARK
        ).pack(anchor="w", pady=(0, 15))

        # --- Paso 1: búsqueda de la persona por cédula ---
        frame_busqueda = tk.Frame(self, bg="#f0f2f5", padx=15, pady=12, bd=1, relief="groove")
        frame_busqueda.pack(fill="x", pady=(0, 12))

        tk.Label(frame_busqueda, text="Cédula del Solicitante:", font=("Helvetica", 10, "bold"),
                 bg="#f0f2f5", fg="#555555").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.ent_cedula = tk.Entry(
            frame_busqueda, font=("Helvetica", 11), width=18,
            validate="key", validatecommand=vcmd_cedula
        )
        self.ent_cedula.grid(row=0, column=1, sticky="w")
        self.ent_cedula.bind("<Return>", lambda e: self.buscar_persona())
        self.ent_cedula.bind("<FocusOut>", lambda e: self.buscar_persona())

        tk.Button(
            frame_busqueda, text="🔍 Buscar", font=("Helvetica", 9, "bold"), bg=self.COLOR_PRIMARY,
            fg="#ffffff", bd=0, cursor="hand2", padx=10, command=self.buscar_persona
        ).grid(row=0, column=2, padx=10)

        self.lbl_info_persona = tk.Label(
            frame_busqueda, text="Ingrese la cédula y presione Buscar (o Enter) para continuar.",
            font=("Helvetica", 9, "italic"), bg="#f0f2f5", fg="#666666", justify="left", wraplength=650
        )
        self.lbl_info_persona.grid(row=1, column=0, columnspan=3, sticky="w", pady=(10, 0))

        self.btn_ir_a_registrar = tk.Button(
            frame_busqueda, text="➕ Ir a Registrar Persona", font=("Helvetica", 9, "bold"),
            bg="#f57c00", fg="#ffffff", bd=0, cursor="hand2", padx=10,
            command=self._ir_a_registrar_persona
        )

        # --- Paso 2: datos del trámite (deshabilitados hasta encontrar a la persona) ---
        self.frame_tramite = tk.Frame(self, bg="#ffffff")
        self.frame_tramite.pack(fill="both", expand=True)

        fila = 0

        def nueva_fila():
            nonlocal fila
            f = fila
            fila += 1
            return f

        def crear_etiqueta(texto, r):
            tk.Label(
                self.frame_tramite, text=texto, font=("Helvetica", 10, "bold"),
                bg="#ffffff", fg="#555555"
            ).grid(row=r, column=0, sticky="w", pady=4, padx=5)

        # Tipo de Trámite
        r = nueva_fila()
        crear_etiqueta("Tipo de Trámite:", r)
        self.cmb_tipo = ttk.Combobox(self.frame_tramite, values=TIPOS_TRAMITE, state="readonly")
        self.cmb_tipo.grid(row=r, column=1, sticky="ew", pady=4, padx=10)
        self.cmb_tipo.current(0)

        # Campos exclusivos de Cuido
        r = nueva_fila()
        self.lbl_beneficiario_para = tk.Label(
            self.frame_tramite, text="¿Para quién se solicita el cuido?:", font=("Helvetica", 10, "bold"),
            bg="#ffffff", fg="#555555"
        )
        self.ent_beneficiario_para = tk.Entry(self.frame_tramite, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self._fila_beneficiario_para = r

        r = nueva_fila()
        self.lbl_parentesco = tk.Label(
            self.frame_tramite, text="Parentesco:", font=("Helvetica", 10, "bold"),
            bg="#ffffff", fg="#555555"
        )
        self.cmb_parentesco = ttk.Combobox(self.frame_tramite, values=PARENTESCOS, state="readonly")
        self.cmb_parentesco.current(0)
        self._fila_parentesco = r

        # Días Solicitados
        r = nueva_fila()
        crear_etiqueta("Días Solicitados:", r)
        self.ent_dias = tk.Entry(self.frame_tramite, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_dias.grid(row=r, column=1, sticky="ew", pady=4, padx=10)

        # Fecha Desde
        r = nueva_fila()
        crear_etiqueta("Fecha Desde (DD-MM-AAAA):", r)
        self.ent_fecha_desde = tk.Entry(self.frame_tramite, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_fecha_desde.grid(row=r, column=1, sticky="ew", pady=4, padx=10)

        # Fecha Hasta + botón de reinicio
        r = nueva_fila()
        crear_etiqueta("Fecha Hasta (DD-MM-AAAA):", r)
        frame_hasta = tk.Frame(self.frame_tramite, bg="#ffffff")
        frame_hasta.grid(row=r, column=1, sticky="ew", pady=4, padx=10)
        frame_hasta.columnconfigure(0, weight=1)
        self.ent_fecha_hasta = tk.Entry(frame_hasta, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_fecha_hasta.grid(row=0, column=0, sticky="ew")
        tk.Button(
            frame_hasta, text="🔄 Reiniciar", font=("Helvetica", 8, "bold"),
            bg="#6c757d", fg="#ffffff", bd=0, cursor="hand2", padx=6,
            command=self.reiniciar_dias_y_fechas
        ).grid(row=0, column=1, padx=(6, 0))

        # Médico Tratante
        r = nueva_fila()
        crear_etiqueta("Médico Tratante:", r)
        self.ent_medico = tk.Entry(self.frame_tramite, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_medico.grid(row=r, column=1, sticky="ew", pady=4, padx=10)

        # Código Registro Médico
        r = nueva_fila()
        crear_etiqueta("Código Registro Médico:", r)
        self.ent_codigo_medico = tk.Entry(self.frame_tramite, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_codigo_medico.grid(row=r, column=1, sticky="ew", pady=4, padx=10)

        # Código Coordinación Asistencial
        r = nueva_fila()
        crear_etiqueta("Código Coordinación Asistencial:", r)
        self.ent_codigo_registro = tk.Entry(self.frame_tramite, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_codigo_registro.grid(row=r, column=1, sticky="ew", pady=4, padx=10)

        # Asignación de Código / Color
        r = nueva_fila()
        crear_etiqueta("Asignación de Código / Color:", r)
        self.cmb_seleccion_codigo_asistencial = ttk.Combobox(self.frame_tramite, values=COLORES_ASISTENCIALES, state="readonly")
        self.cmb_seleccion_codigo_asistencial.grid(row=r, column=1, sticky="ew", pady=4, padx=10)
        self.cmb_seleccion_codigo_asistencial.current(0)

        # Especialidad
        r = nueva_fila()
        crear_etiqueta("Especialidad:", r)
        self.cmb_especialidad = ttk.Combobox(self.frame_tramite, values=ESPECIALIDADES, state="readonly", font=("Helvetica", 10))
        self.cmb_especialidad.grid(row=r, column=1, sticky="ew", pady=4, padx=10)
        self.cmb_especialidad.current(0)

        self.frame_tramite.columnconfigure(1, weight=1)

        self.campo_desde_manual = False
        self.campo_hasta_manual = False

        self.ent_dias.bind("<KeyRelease>", self._al_cambiar_dias_o_tipo)
        self.cmb_tipo.bind("<<ComboboxSelected>>", self._al_cambiar_tipo)
        self.ent_fecha_desde.bind("<KeyRelease>", self._al_editar_fecha_desde_manual)
        self.ent_fecha_hasta.bind("<KeyRelease>", self._al_editar_fecha_hasta_manual)

        r = nueva_fila()
        self.btn_guardar = tk.Button(
            self.frame_tramite, text="GUARDAR REGISTRO", font=("Helvetica", 11, "bold"),
            bg=self.COLOR_PRIMARY, fg="#ffffff", activebackground="#0088a3", activeforeground="#ffffff",
            bd=0, cursor="hand2", command=self.procesar_registro
        )
        self.btn_guardar.grid(row=r, column=0, columnspan=2, pady=(15, 0), ipady=8, sticky="ew")

        self._actualizar_visibilidad_cuido()
        self._bloquear_formulario_tramite()

    # ------------------------------------------------------------------

    def _validar_cedula(self, texto):
        return (texto.isdigit() or texto == "") and len(texto) <= 10

    def _bloquear_formulario_tramite(self):
        self._establecer_estado_tramite("disabled")
        self.btn_ir_a_registrar.grid_forget()

    def _establecer_estado_tramite(self, estado):
        estado_combo = "disabled" if estado == "disabled" else "readonly"
        widgets_entry = [self.ent_dias, self.ent_fecha_desde, self.ent_fecha_hasta,
                          self.ent_medico, self.ent_codigo_medico, self.ent_codigo_registro,
                          self.ent_beneficiario_para]
        widgets_combo = [self.cmb_tipo, self.cmb_parentesco, self.cmb_seleccion_codigo_asistencial, self.cmb_especialidad]
        for w in widgets_entry:
            w.configure(state=estado)
        for w in widgets_combo:
            w.configure(state=estado_combo)
        self.btn_guardar.configure(state=("disabled" if estado == "disabled" else "normal"))
        if self.rol == "visualizador":
            self.btn_guardar.configure(state="disabled")

    def buscar_persona(self):
        cedula = re.sub(r"\D", "", self.ent_cedula.get().strip())
        if not cedula:
            return

        beneficiario = base_datos.obtener_beneficiario_por_cedula(cedula)
        if not beneficiario:
            self.persona_encontrada = None
            self.lbl_info_persona.config(
                text=f"⚠ No existe ninguna persona registrada con la cédula {cedula}. "
                     f"Debe registrarla primero en el módulo Personas.",
                fg="#c62828"
            )
            self.btn_ir_a_registrar.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))
            self._bloquear_formulario_tramite()
            return

        self.persona_encontrada = beneficiario
        _, nombre, telefono, institucion, cargo = beneficiario
        self.lbl_info_persona.config(
            text=f"✓ {nombre}  |  Tel: {telefono}  |  {institucion} — {cargo}",
            fg="#2e7d32"
        )
        self.btn_ir_a_registrar.grid_forget()
        if self.rol != "visualizador":
            self._establecer_estado_tramite("normal")

    def _ir_a_registrar_persona(self):
        cedula = re.sub(r"\D", "", self.ent_cedula.get().strip())
        if self.ir_a_personas_callback:
            self.ir_a_personas_callback(cedula)

    # ------------------------------------------------------------------
    # Cuido: mostrar/ocultar campos de "para quién" y "parentesco"
    # ------------------------------------------------------------------

    def _actualizar_visibilidad_cuido(self):
        if self.cmb_tipo.get() == "Cuido":
            self.lbl_beneficiario_para.grid(row=self._fila_beneficiario_para, column=0, sticky="w", pady=4, padx=5)
            self.ent_beneficiario_para.grid(row=self._fila_beneficiario_para, column=1, sticky="ew", pady=4, padx=10)
            self.lbl_parentesco.grid(row=self._fila_parentesco, column=0, sticky="w", pady=4, padx=5)
            self.cmb_parentesco.grid(row=self._fila_parentesco, column=1, sticky="ew", pady=4, padx=10)
        else:
            self.lbl_beneficiario_para.grid_remove()
            self.ent_beneficiario_para.grid_remove()
            self.lbl_parentesco.grid_remove()
            self.cmb_parentesco.grid_remove()

    # ------------------------------------------------------------------
    # Sugerencia automática de fechas / días
    # ------------------------------------------------------------------

    def _al_editar_fecha_desde_manual(self, event=None):
        self.campo_desde_manual = True
        self._recalcular_fecha_hasta()

    def _al_editar_fecha_hasta_manual(self, event=None):
        self.campo_hasta_manual = True

    def _al_cambiar_dias_o_tipo(self, event=None):
        if not self.campo_desde_manual:
            self._sugerir_fecha_desde()
        self._recalcular_fecha_hasta()

    def _al_cambiar_tipo(self, event=None):
        self._actualizar_visibilidad_cuido()

        if self.cmb_tipo.get() == "Pre y Post-Natal (150 días)":
            self.ent_dias.configure(state="normal")
            self.ent_dias.delete(0, tk.END)
            self.ent_dias.insert(0, "150")
            if not self.campo_desde_manual:
                self._sugerir_fecha_desde()
            self.campo_hasta_manual = False
            self._recalcular_fecha_hasta()
            return

        self._al_cambiar_dias_o_tipo()

    def _sugerir_fecha_desde(self):
        hoy = datetime.date.today()
        self.ent_fecha_desde.delete(0, tk.END)
        self.ent_fecha_desde.insert(0, hoy.strftime("%d-%m-%Y"))

    def _recalcular_fecha_hasta(self):
        if self.campo_hasta_manual:
            return

        dias_str = self.ent_dias.get().strip()
        if not dias_str.isdigit() or int(dias_str) <= 0:
            return

        try:
            fecha_desde = datetime.datetime.strptime(self.ent_fecha_desde.get().strip(), "%d-%m-%Y").date()
        except ValueError:
            return

        dias = int(dias_str)
        tipo = self.cmb_tipo.get()

        if tipo == "Cuido":
            fecha_hasta = feriados.sumar_dias_habiles(fecha_desde, dias)
        else:
            fecha_hasta = feriados.sumar_dias_calendario(fecha_desde, dias)

        self.ent_fecha_hasta.delete(0, tk.END)
        self.ent_fecha_hasta.insert(0, fecha_hasta.strftime("%d-%m-%Y"))

    def reiniciar_dias_y_fechas(self):
        self.ent_dias.delete(0, tk.END)
        self.ent_fecha_desde.delete(0, tk.END)
        self.ent_fecha_hasta.delete(0, tk.END)
        self.campo_desde_manual = False
        self.campo_hasta_manual = False

    def prellenar_para_renovacion(self, cedula, tipo, dias_restantes, fecha_inicio_renovacion):
        self.limpiar_campos()
        cedula_limpia = re.sub(r"\D", "", str(cedula))[:10]
        self.ent_cedula.insert(0, cedula_limpia)
        self.buscar_persona()

        if tipo in TIPOS_TRAMITE:
            self.cmb_tipo.set(tipo)
        self._actualizar_visibilidad_cuido()

        self.ent_dias.insert(0, str(dias_restantes))

        if isinstance(fecha_inicio_renovacion, (datetime.date, datetime.datetime)):
            fecha_fmt = fecha_inicio_renovacion.strftime("%d-%m-%Y")
        else:
            try:
                dt = datetime.datetime.strptime(str(fecha_inicio_renovacion), "%Y-%m-%d")
                fecha_fmt = dt.strftime("%d-%m-%Y")
            except ValueError:
                fecha_fmt = str(fecha_inicio_renovacion)

        self.ent_fecha_desde.insert(0, fecha_fmt)
        self.campo_desde_manual = True
        self.campo_hasta_manual = False
        self._recalcular_fecha_hasta()

    def prellenar_cedula(self, cedula):
        """Llamado al volver desde el módulo Personas tras registrar a alguien,
        para retomar el registro del trámite sin volver a escribir la cédula."""
        self.limpiar_campos()
        self.ent_cedula.insert(0, cedula)
        self.buscar_persona()

    # ------------------------------------------------------------------
    # Guardado / validación del registro
    # ------------------------------------------------------------------

    def procesar_registro(self):
        if self.rol == "visualizador":
            messagebox.showerror("Acceso Denegado", "Su rol de Visualizador no tiene permiso para registrar trámites.")
            return

        if not self.persona_encontrada:
            messagebox.showwarning("Atención", "Primero debe buscar y confirmar una persona registrada por su cédula.")
            return

        try:
            cedula = self.persona_encontrada[0]

            tipo = self.cmb_tipo.get()
            dias_str = self.ent_dias.get().strip()
            fecha_desde_str = self.ent_fecha_desde.get().strip()
            fecha_hasta_str = self.ent_fecha_hasta.get().strip()

            codigo_rojo = self.cmb_seleccion_codigo_asistencial.get()
            medico = self.ent_medico.get().strip().upper()
            especialidad = self.cmb_especialidad.get()
            codigo_registro = self.ent_codigo_registro.get().strip()
            codigo_medico = self.ent_codigo_medico.get().strip()

            beneficiario_para = self.ent_beneficiario_para.get().strip().upper() if tipo == "Cuido" else ""
            parentesco = self.cmb_parentesco.get() if tipo == "Cuido" else ""

            campos_vacios = []
            if not dias_str: campos_vacios.append("Días Solicitados")
            if not fecha_desde_str: campos_vacios.append("Fecha Desde")
            if not fecha_hasta_str: campos_vacios.append("Fecha Hasta")
            if not medico: campos_vacios.append("Médico Tratante")
            if not especialidad: campos_vacios.append("Especialidad")
            if not codigo_registro: campos_vacios.append("Código de coordinación asistencial")
            if tipo == "Cuido" and not beneficiario_para: campos_vacios.append("¿Para quién se solicita el cuido?")

            if campos_vacios:
                messagebox.showwarning(
                    "Campos Incompletos",
                    f"Por favor complete los siguientes campos requeridos:\n\n• " + "\n• ".join(campos_vacios)
                )
                return

            if not dias_str.isdigit() or int(dias_str) <= 0:
                messagebox.showerror("Error de Validación", "El campo Días Solicitados debe ser mayor a 0.")
                return
            dias = int(dias_str)

            if codigo_medico and not re.match(r"^[A-Za-z0-9\-]+$", codigo_medico):
                messagebox.showerror("Error de Validación", "El 'Código Registro Médico' solo puede contener letras, números y guiones.")
                return

            try:
                fecha_desde = datetime.datetime.strptime(fecha_desde_str, "%d-%m-%Y").date()
            except ValueError:
                messagebox.showerror("Error de Fecha", "Formato 'Fecha Desde' inválido (debe ser DD-MM-AAAA).")
                return

            try:
                fecha_hasta = datetime.datetime.strptime(fecha_hasta_str, "%d-%m-%Y").date()
            except ValueError:
                messagebox.showerror("Error de Fecha", "Formato 'Fecha Hasta' inválido (debe ser DD-MM-AAAA).")
                return

            if fecha_hasta < fecha_desde:
                messagebox.showerror("Error de Fecha", "'Fecha Hasta' no puede ser anterior a 'Fecha Desde'.")
                return

            tope_tipo = base_datos.TOPES_DIAS.get(tipo)
            if tope_tipo is not None and dias > tope_tipo:
                messagebox.showerror("Límite Superado", f"El trámite '{tipo}' no puede exceder los {tope_tipo} días.")
                return

            if tipo == "Reposo Regular" and especialidad == "Medicina general" and dias > 3:
                continuar = messagebox.askyesno(
                    "Aviso: Medicina General",
                    f"Un reposo por Medicina General normalmente no debe exceder de 3 días "
                    f"(se están solicitando {dias} días).\n\n¿Desea continuar de todas formas?"
                )
                if not continuar:
                    return

            historial = base_datos.buscar_por_cedula(cedula)
            hace_un_ano = fecha_desde - datetime.timedelta(days=365)
            hace_seis_meses = fecha_desde - datetime.timedelta(days=180)

            dias_cuido_acumulados = 0
            dias_reposo_acumulados = 0

            for reg in historial:
                t_reg = reg[6]
                d_reg = reg[7]
                try:
                    f_hasta_reg = datetime.datetime.strptime(reg[9], "%Y-%m-%d").date()
                    f_desde_reg = datetime.datetime.strptime(reg[8], "%Y-%m-%d").date()
                except ValueError:
                    continue

                if fecha_desde < f_hasta_reg:
                    fecha_permitida = (f_hasta_reg + datetime.timedelta(days=1)).strftime("%d-%m-%Y")
                    messagebox.showerror(
                        "Registro Rechazado",
                        f"El solicitante posee un permiso activo vigente hasta el {f_hasta_reg.strftime('%d-%m-%Y')}.\n\n"
                        f"No es posible registrar un nuevo permiso durante el período activo.\n"
                        f"Podrá registrarse a partir del: {fecha_permitida}."
                    )
                    return

                if "Cuido" in t_reg and f_desde_reg >= hace_un_ano:
                    dias_cuido_acumulados += d_reg

                if t_reg == "Reposo Regular" and f_desde_reg >= hace_seis_meses:
                    dias_reposo_acumulados += d_reg

            if tipo == "Cuido" and (dias_cuido_acumulados + dias) > 20:
                messagebox.showerror(
                    "Límite Anual Superado",
                    f"El solicitante ya tiene {dias_cuido_acumulados} días de cuido registrados en el año.\n"
                    f"No puede superar el límite anual de 20 días hábiles."
                )
                return

            if tipo == "Reposo Regular" and (dias_reposo_acumulados + dias) > 84:
                messagebox.showerror(
                    "Límite de 84 Días Superado",
                    f"El solicitante tiene {dias_reposo_acumulados} días acumulados en los últimos 6 meses.\n"
                    f"Supera el límite de 84 días de permisos por semestre."
                )
                return

            datos_reposo = (
                cedula, tipo, dias, str(fecha_desde), str(fecha_hasta),
                codigo_rojo, medico, especialidad, codigo_registro,
                beneficiario_para, parentesco
            )

            base_datos.guardar_registro(datos_reposo)
            messagebox.showinfo("Registro Exitoso", f"Trámite registrado correctamente hasta el {fecha_hasta.strftime('%d-%m-%Y')}.")

            self.limpiar_campos()
            if self.al_guardar_callback:
                self.al_guardar_callback()

        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al intentar guardar:\n{e}")

    def limpiar_campos(self):
        self.ent_cedula.delete(0, tk.END)
        self.persona_encontrada = None
        self.lbl_info_persona.config(text="Ingrese la cédula y presione Buscar (o Enter) para continuar.", fg="#666666")
        self.btn_ir_a_registrar.grid_forget()

        self._establecer_estado_tramite("normal")
        self.ent_dias.delete(0, tk.END)
        self.ent_fecha_desde.delete(0, tk.END)
        self.ent_fecha_hasta.delete(0, tk.END)
        self.ent_medico.delete(0, tk.END)
        self.ent_codigo_registro.delete(0, tk.END)
        self.ent_codigo_medico.delete(0, tk.END)
        self.ent_beneficiario_para.delete(0, tk.END)
        self.cmb_tipo.current(0)
        self.cmb_parentesco.current(0)
        self.cmb_seleccion_codigo_asistencial.current(0)
        self.cmb_especialidad.current(0)
        self.campo_desde_manual = False
        self.campo_hasta_manual = False
        self._actualizar_visibilidad_cuido()
        self._bloquear_formulario_tramite()