import datetime
import re
import tkinter as tk
from tkinter import ttk, messagebox
import base_datos
import feriados

class ModuloFormulario(tk.Frame):
    def __init__(self, parent, al_guardar_callback=None, rol="admin"):
        super().__init__(parent, bg="#ffffff", padx=25, pady=20, bd=1, relief="solid")
        self.al_guardar_callback = al_guardar_callback
        self.rol = rol

        self.COLOR_TEXT_DARK = "#333333"
        self.COLOR_PRIMARY = "#00a8cc"

        # Validación en tiempo real: Solo permite dígitos numéricos en el Entry de la Cédula
        vcmd_solo_numeros = (self.register(self._validar_entrada_solo_numeros), '%P')

        lbl_t = tk.Label(
            self, 
            text="Formulario de Registro de Reposo o Cuido", 
            font=("Helvetica", 14, "bold"), 
            bg="#ffffff", 
            fg=self.COLOR_TEXT_DARK
        )
        lbl_t.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # --- ORDEN ESTRICTAMENTE VERTICAL HACIA ABAJO ---
        fields_order = [
            ("Nombre y Apellido:", 1),
            ("Cédula:", 2),
            ("Teléfono:", 3),
            ("Cargo:", 4),
            ("Institución:", 5),
            ("Tipo de Trámite:", 6),
            ("Días Solicitados:", 7),
            ("Fecha Desde (DD-MM-AAAA):", 8),
            ("Fecha Hasta (DD-MM-AAAA):", 9),
            ("Médico Tratante:", 10),
            ("Código Registro Médico:", 11),
            ("Código Coordinación Asistencial:", 12),
            ("Asignación de Código / Color:", 13),
            ("Especialidad:", 14)
        ]

        for text, r in fields_order:
            tk.Label(
                self, text=text, font=("Helvetica", 10, "bold"), 
                bg="#ffffff", fg="#555555"
            ).grid(row=r, column=0, sticky="w", pady=4, padx=5)

        # 1. Nombre y Apellido
        self.ent_nombre = tk.Entry(self, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_nombre.grid(row=1, column=1, sticky="ew", pady=4, padx=10)

        # 2. Cédula (Bloqueado para ingresar SOLO números)
        self.ent_cedula = tk.Entry(
            self, font=("Helvetica", 10), bg="#f0f2f5", bd=1,
            validate="key", validatecommand=vcmd_solo_numeros
        )
        self.ent_cedula.grid(row=2, column=1, sticky="ew", pady=4, padx=10)

        # 3. Teléfono
        self.ent_telefono = tk.Entry(self, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_telefono.grid(row=3, column=1, sticky="ew", pady=4, padx=10)

        # 4. Cargo
        self.cmb_cargo = ttk.Combobox(self, values=["Docente", "Administrativo", "Personal de Apoyo"], state="readonly")
        self.cmb_cargo.grid(row=4, column=1, sticky="ew", pady=4, padx=10)
        self.cmb_cargo.current(0)

        # 5. Institución
        self.ent_institucion = tk.Entry(self, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_institucion.grid(row=5, column=1, sticky="ew", pady=4, padx=10)

        # 6. Tipo de Trámite
        self.cmb_tipo = ttk.Combobox(self, values=["Cuido", "Reposo Regular", "Pre-Natal (61 días)", "Post-Natal (89 días)"], state="readonly")
        self.cmb_tipo.grid(row=6, column=1, sticky="ew", pady=4, padx=10)
        self.cmb_tipo.current(0)

        # 7. Días Solicitados
        self.ent_dias = tk.Entry(self, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_dias.grid(row=7, column=1, sticky="ew", pady=4, padx=10)

        # 8. Fecha Desde (DD-MM-AAAA)
        self.ent_fecha_desde = tk.Entry(self, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_fecha_desde.grid(row=8, column=1, sticky="ew", pady=4, padx=10)

        # 9. Fecha Hasta (DD-MM-AAAA)
        self.ent_fecha_hasta = tk.Entry(self, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_fecha_hasta.grid(row=9, column=1, sticky="ew", pady=4, padx=10)

        # 10. Médico Tratante
        self.ent_medico = tk.Entry(self, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_medico.grid(row=10, column=1, sticky="ew", pady=4, padx=10)

        # 11. Código Registro Médico
        self.ent_codigo_medico = tk.Entry(self, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_codigo_medico.grid(row=11, column=1, sticky="ew", pady=4, padx=10)

        # 12. Código Coordinación Asistencial
        self.ent_codigo_registro = tk.Entry(self, font=("Helvetica", 10), bg="#f0f2f5", bd=1)
        self.ent_codigo_registro.grid(row=12, column=1, sticky="ew", pady=4, padx=10)

        # 13. Asignación de Código / Color
        self.cmb_seleccion_codigo_asistencial = ttk.Combobox(self, values=["Verde claro","Verde oscuro","Amarillo", "Naranja", "Rojo", "Azul claro","Azul oscuro","rosado", "fuxia","Gris", "Negro", "Marron"], state="readonly")
        self.cmb_seleccion_codigo_asistencial.grid(row=13, column=1, sticky="ew", pady=4, padx=10)
        self.cmb_seleccion_codigo_asistencial.current(0)

        # 14. Especialidad
        lista_especialidades = [
            "Medicina general", "Medicina crítica", "Medicina familiar", 
            "Medicina interna", "Psiquiatria", "Pediatría", "Ginecología", 
            "Otorrinolaringología", "Traumatología", "Cardiología", "Odontología"
        ]
        self.cmb_especialidad = ttk.Combobox(self, values=lista_especialidades, state="readonly", font=("Helvetica", 10))
        self.cmb_especialidad.grid(row=14, column=1, sticky="ew", pady=4, padx=10)
        self.cmb_especialidad.current(0)

        self.columnconfigure(1, weight=1)

        # --- Autocompletado y sugerencia automática de fechas ---
        self.campo_desde_manual = False
        self.campo_hasta_manual = False

        self.ent_cedula.bind("<FocusOut>", self._autocompletar_beneficiario)
        self.ent_dias.bind("<KeyRelease>", self._al_cambiar_dias_o_tipo)
        self.cmb_tipo.bind("<<ComboboxSelected>>", self._al_cambiar_dias_o_tipo)
        self.ent_fecha_desde.bind("<KeyRelease>", self._al_editar_fecha_desde_manual)
        self.ent_fecha_hasta.bind("<KeyRelease>", self._al_editar_fecha_hasta_manual)

        # Botón de guardar
        btn_guardar = tk.Button(
            self, text="GUARDAR REGISTRO", font=("Helvetica", 11, "bold"),
            bg=self.COLOR_PRIMARY, fg="#ffffff", activebackground="#0088a3", activeforeground="#ffffff",
            bd=0, cursor="hand2", command=self.procesar_registro
        )
        btn_guardar.grid(row=15, column=0, columnspan=2, pady=(15, 0), ipady=8, sticky="ew")

        # El rol "visualizador" no tiene permiso para registrar reposos/cuidos
        if self.rol == "visualizador":
            btn_guardar.configure(state="disabled")

    def _validar_entrada_solo_numeros(self, texto):
        """Impide escribir caracteres distintos a dígitos numéricos en la Cédula."""
        return texto.isdigit() or texto == ""

    def _autocompletar_beneficiario(self, event=None):
        """Al salir del campo Cédula, si el beneficiario ya está registrado,
        rellena sus datos personales automáticamente (campos vacíos únicamente)."""
        cedula = re.sub(r"\D", "", self.ent_cedula.get().strip())
        if not cedula:
            return

        beneficiario = base_datos.obtener_beneficiario_por_cedula(cedula)
        if not beneficiario:
            return

        _, nombre, telefono, institucion, cargo = beneficiario

        if not self.ent_nombre.get().strip():
            self.ent_nombre.insert(0, nombre)
        if not self.ent_telefono.get().strip():
            self.ent_telefono.insert(0, telefono)
        if not self.ent_institucion.get().strip():
            self.ent_institucion.insert(0, institucion)
        if cargo in self.cmb_cargo["values"]:
            self.cmb_cargo.set(cargo)

    def _al_editar_fecha_desde_manual(self, event=None):
        self.campo_desde_manual = True
        self._recalcular_fecha_hasta()

    def _al_editar_fecha_hasta_manual(self, event=None):
        self.campo_hasta_manual = True

    def _al_cambiar_dias_o_tipo(self, event=None):
        if not self.campo_desde_manual:
            self._sugerir_fecha_desde()
        self._recalcular_fecha_hasta()

    def _sugerir_fecha_desde(self):
        hoy = datetime.date.today()
        self.ent_fecha_desde.delete(0, tk.END)
        self.ent_fecha_desde.insert(0, hoy.strftime("%d-%m-%Y"))

    def _recalcular_fecha_hasta(self):
        """Sugiere la 'Fecha Hasta' según los días solicitados y el tipo de trámite:
        para Reposos cuentan todos los días corridos, para Cuidos solo días hábiles
        (sin sábados, domingos ni feriados de Venezuela). El usuario puede modificarla."""
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

    def prellenar_para_renovacion(self, cedula, nombre, telefono, institucion, cargo, tipo, dias_restantes, fecha_inicio_renovacion):
        self.limpiar_campos()
        cedula_limpia = re.sub(r"\D", "", str(cedula))
        self.ent_cedula.insert(0, cedula_limpia)
        self.ent_telefono.insert(0, str(telefono))
        self.ent_nombre.insert(0, str(nombre))
        self.ent_institucion.insert(0, str(institucion))
        
        if cargo in ["Docente", "Administrativo", "Personal de Apoyo"]:
            self.cmb_cargo.set(cargo)

        if tipo in ["Cuido", "Reposo Regular", "Pre-Natal (61 días)", "Post-Natal (89 días)"]:
            self.cmb_tipo.set(tipo)

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

        # La fecha desde ya fue fijada intencionalmente por la renovación;
        # se sugiere la fecha hasta en base a esta, pero sigue siendo editable.
        self.campo_desde_manual = True
        self.campo_hasta_manual = False
        self._recalcular_fecha_hasta()

    def procesar_registro(self):
        if self.rol == "visualizador":
            messagebox.showerror("Acceso Denegado", "Su rol de Visualizador no tiene permiso para registrar trámites.")
            return
        try:
            cedula_raw = self.ent_cedula.get().strip()
            cedula = re.sub(r"\D", "", cedula_raw)

            telefono = self.ent_telefono.get().strip()
            nombre = self.ent_nombre.get().strip()
            institucion = self.ent_institucion.get().strip()
            cargo = self.cmb_cargo.get()
            tipo = self.cmb_tipo.get()
            dias_str = self.ent_dias.get().strip()
            fecha_desde_str = self.ent_fecha_desde.get().strip()
            fecha_hasta_str = self.ent_fecha_hasta.get().strip()
            
            codigo_rojo = self.cmb_seleccion_codigo_asistencial.get()
            medico = self.ent_medico.get().strip()
            especialidad = self.cmb_especialidad.get()
            codigo_registro = self.ent_codigo_registro.get().strip()
            codigo_medico = self.ent_codigo_medico.get().strip()

            campos_vacios = []
            if not cedula: campos_vacios.append("Cédula")
            if not telefono: campos_vacios.append("Teléfono")
            if not nombre: campos_vacios.append("Nombre y Apellido")
            if not institucion: campos_vacios.append("Institución")
            if not dias_str: campos_vacios.append("Días Solicitados")
            if not fecha_desde_str: campos_vacios.append("Fecha Desde")
            if not fecha_hasta_str: campos_vacios.append("Fecha Hasta")
            if not medico: campos_vacios.append("Médico Tratante")
            if not especialidad: campos_vacios.append("Especialidad")
            if not codigo_registro: campos_vacios.append("Código de coordinación asistencial")

            if campos_vacios:
                messagebox.showwarning(
                    "Campos Incompletos", 
                    f"Por favor complete los siguientes campos requeridos:\n\n• " + "\n• ".join(campos_vacios)
                )
                return

            if not cedula.isdigit():
                messagebox.showerror("Error de Validación", "La Cédula debe contener únicamente números sin puntos ni caracteres.")
                return

            telefono_limpio = telefono.replace("-", "").replace(" ", "").replace("+", "")
            if not telefono_limpio.isdigit() or len(telefono_limpio) < 7:
                messagebox.showerror("Error de Validación", "Ingrese un número de Teléfono válido.")
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

            if tipo == "Cuido" and dias > 20:
                messagebox.showerror("Límite Superado", "Los permisos de Cuido no pueden exceder los 20 días hábiles.")
                return
            elif tipo == "Reposo Regular" and dias > 21:
                messagebox.showerror("Límite Superado", "Un reposo individual no puede exceder de 21 días.")
                return
            elif tipo == "Pre-Natal (61 días)" and dias > 61:
                messagebox.showerror("Límite Superado", "El Pre-Natal no puede exceder 61 días.")
                return
            elif tipo == "Post-Natal (89 días)" and dias > 89:
                messagebox.showerror("Límite Superado", "El Post-Natal no puede exceder 89 días.")
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

                if ("Reposo" in t_reg or "Natal" in t_reg) and f_desde_reg >= hace_seis_meses:
                    dias_reposo_acumulados += d_reg

            if tipo == "Cuido" and (dias_cuido_acumulados + dias) > 20:
                messagebox.showerror(
                    "Límite Anual Superado",
                    f"El solicitante ya tiene {dias_cuido_acumulados} días de cuido registrados en el año.\n"
                    f"No puede superar el límite anual de 20 días hábiles."
                )
                return

            if ("Reposo" in tipo or "Natal" in tipo) and (dias_reposo_acumulados + dias) > 84:
                messagebox.showerror(
                    "Límite de 84 Días Superado",
                    f"El solicitante tiene {dias_reposo_acumulados} días acumulados en los últimos 6 meses.\n"
                    f"Supera el límite de 84 días de permisos por semestre."
                )
                return

            datos_beneficiario = (cedula, nombre, telefono, institucion, cargo)
            datos_reposo = (
                cedula, tipo, dias, str(fecha_desde), str(fecha_hasta),
                codigo_rojo, medico, especialidad, codigo_registro
            )

            base_datos.guardar_registro(datos_beneficiario, datos_reposo)
            messagebox.showinfo("Registro Exitoso", f"Trámite registrado correctamente hasta el {fecha_hasta.strftime('%d-%m-%Y')}.")
            
            self.limpiar_campos()
            if self.al_guardar_callback:
                self.al_guardar_callback()

        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al intentar guardar:\n{e}")

    def limpiar_campos(self):
        self.ent_cedula.delete(0, tk.END)
        self.ent_telefono.delete(0, tk.END)
        self.ent_nombre.delete(0, tk.END)
        self.ent_institucion.delete(0, tk.END)
        self.ent_dias.delete(0, tk.END)
        self.ent_fecha_desde.delete(0, tk.END)
        self.ent_fecha_hasta.delete(0, tk.END)
        self.ent_medico.delete(0, tk.END)
        self.ent_codigo_registro.delete(0, tk.END)
        self.ent_codigo_medico.delete(0, tk.END)
        self.cmb_cargo.current(0)
        self.cmb_tipo.current(0)
        self.cmb_seleccion_codigo_asistencial.current(0)
        self.cmb_especialidad.current(0)
        self.campo_desde_manual = False
        self.campo_hasta_manual = False