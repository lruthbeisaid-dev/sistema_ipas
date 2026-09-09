import tkinter as tk
from tkinter import messagebox, filedialog
import datetime
import os
import base_datos

TIEMPO_INACTIVIDAD_MS = 10 * 60 * 1000  # 10 minutos


class VentanaDashboard:
    def __init__(self, root, rol="admin", al_cerrar_sesion=None, usuario="admin"):
        self.root = root
        self.rol = rol
        self.usuario = usuario
        self.al_cerrar_sesion = al_cerrar_sesion
        self.root.title("IPASME - Sistema de Gestión de Reposos y Cuidos")
        self.root.geometry("1150x700")
        self.root.configure(bg="#f4f6f8")

        self.COLOR_TOPBAR = "#00a8cc"
        self.COLOR_SIDEBAR = "#222831"
        self.COLOR_SIDEBAR_BTN = "#2d343f"
        self.COLOR_SIDEBAR_ACTIVE = "#00a8cc"
        self.COLOR_BG = "#f4f6f8"
        self.COLOR_CARD = "#ffffff"
        self.COLOR_TEXT_DARK = "#333333"
        self.COLOR_PRIMARY = "#00a8cc"

        # Los módulos se crean de forma perezosa (solo al navegar a ellos por
        # primera vez), para no reservar memoria de widgets que tal vez el
        # usuario nunca visite en la sesión — importante en equipos con 2 GB de RAM.
        self.modulo_form = None
        self.modulo_historial = None
        self.modulo_personas = None
        self.modulo_auditoria = None

        self.topbar = tk.Frame(self.root, bg=self.COLOR_TOPBAR, height=50)
        self.topbar.pack(side="top", fill="x")

        tk.Label(
            self.topbar, text=" IPASME | Sistema de Gestión",
            font=("Helvetica", 13, "bold"), bg=self.COLOR_TOPBAR, fg="#ffffff"
        ).pack(side="left", padx=15, pady=10)

        texto_rol = "Administrador" if self.rol == "admin" else "Visualizador (solo lectura)"
        tk.Label(
            self.topbar, text=f"{texto_rol} ({self.usuario})",
            font=("Helvetica", 10, "bold"), bg=self.COLOR_TOPBAR, fg="#ffffff"
        ).pack(side="right", padx=15, pady=10)

        if self.rol == "admin":
            tk.Button(
                self.topbar, text="🔑 Cambiar Clave", font=("Helvetica", 9, "bold"),
                bg=self.COLOR_TOPBAR, fg="#ffffff", activebackground="#0088a3",
                bd=0, cursor="hand2", command=self.abrir_cambio_clave
            ).pack(side="right", padx=10)

        self.sidebar = tk.Frame(self.root, bg=self.COLOR_SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar, text="MÓDULOS", font=("Helvetica", 9, "bold"),
            bg=self.COLOR_SIDEBAR, fg="#7e8a9b", anchor="w"
        ).pack(fill="x", padx=15, pady=(20, 10))

        self.btn_nav_dash = self.crear_boton_nav(" Inicio", self.mostrar_modulo_dash)
        self.btn_nav_personas = self.crear_boton_nav(" Personas", self.mostrar_modulo_personas)
        self.btn_nav_nuevo = self.crear_boton_nav(" Registro de Permisos", self.mostrar_modulo_nuevo)
        self.btn_nav_tabla = self.crear_boton_nav(" Consultas / Histórico", self.mostrar_modulo_tabla)
        self.btn_nav_auditoria = self.crear_boton_nav(" Auditoría", self.mostrar_modulo_auditoria)

        tk.Button(
            self.sidebar, text=" 🔒 Cerrar Sesión", font=("Helvetica", 10, "bold"),
            bg=self.COLOR_SIDEBAR, fg="#e57373", activebackground="#c62828",
            activeforeground="#ffffff", bd=0, anchor="w", padx=15, cursor="hand2",
            command=self.cerrar_sesion
        ).pack(side="bottom", fill="x", ipady=12, pady=15)

        self.area_trabajo = tk.Frame(self.root, bg=self.COLOR_BG)
        self.area_trabajo.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        self.frame_dash = tk.Frame(self.area_trabajo, bg=self.COLOR_BG)

        self.construir_modulo_dash()

        if self.rol == "visualizador":
            self.btn_nav_auditoria.pack_forget()

        self.mostrar_modulo_dash()

        self._id_temporizador_inactividad = None
        for evento in ("<Motion>", "<KeyPress>", "<Button>"):
            self.root.bind_all(evento, self._reiniciar_temporizador_inactividad, add="+")
        self._reiniciar_temporizador_inactividad()

        self._actualizar_reloj()

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------

    def crear_boton_nav(self, texto, comando):
        btn = tk.Button(
            self.sidebar, text=texto, font=("Helvetica", 10, "bold"),
            bg=self.COLOR_SIDEBAR, fg="#d0d5dd", activebackground=self.COLOR_SIDEBAR_BTN,
            activeforeground="#ffffff", bd=0, anchor="w", padx=15, cursor="hand2", command=comando
        )
        btn.pack(fill="x", ipady=10, pady=2)
        return btn

    def resaltar_boton(self, btn_activo):
        for btn in [self.btn_nav_dash, self.btn_nav_personas, self.btn_nav_nuevo, self.btn_nav_tabla, self.btn_nav_auditoria]:
            btn.configure(bg=self.COLOR_SIDEBAR, fg="#d0d5dd")
        btn_activo.configure(bg=self.COLOR_SIDEBAR_ACTIVE, fg="#ffffff")

    def ocultar_modulos(self):
        self.frame_dash.pack_forget()
        for modulo in (self.modulo_form, self.modulo_historial, self.modulo_personas, self.modulo_auditoria):
            if modulo is not None:
                modulo.pack_forget()

    def mostrar_modulo_dash(self):
        self.ocultar_modulos()
        self.resaltar_boton(self.btn_nav_dash)
        self.actualizar_metricas()
        self.refrescar_alertas()
        self.frame_dash.pack(fill="both", expand=True)

    def mostrar_modulo_personas(self):
        self.ocultar_modulos()
        self.resaltar_boton(self.btn_nav_personas)
        if self.modulo_personas is None:
            from personas import ModuloPersonas
            self.modulo_personas = ModuloPersonas(self.area_trabajo, rol=self.rol)
        else:
            self.modulo_personas.cargar_lista()
        self.modulo_personas.pack(fill="both", expand=True)

    def mostrar_modulo_nuevo(self):
        if self.rol == "visualizador":
            return
        self.ocultar_modulos()
        self.resaltar_boton(self.btn_nav_nuevo)
        if self.modulo_form is None:
            from formulario import ModuloFormulario
            self.modulo_form = ModuloFormulario(
                self.area_trabajo, al_guardar_callback=self.actualizar_metricas, rol=self.rol,
                ir_a_personas_callback=self._ir_a_personas_desde_formulario
            )
        self.modulo_form.pack(fill="both", expand=True)

    def mostrar_modulo_tabla(self):
        self.ocultar_modulos()
        self.resaltar_boton(self.btn_nav_tabla)
        if self.modulo_historial is None:
            from historial import ModuloHistorial
            self.modulo_historial = ModuloHistorial(
                self.area_trabajo, callback_renovar=self.iniciar_renovacion_desde_historial, rol=self.rol
            )
        else:
            self.modulo_historial.cargar_tabla_completa()
        self.modulo_historial.pack(fill="both", expand=True)

    def mostrar_modulo_auditoria(self):
        if self.rol == "visualizador":
            return
        self.ocultar_modulos()
        self.resaltar_boton(self.btn_nav_auditoria)
        if self.modulo_auditoria is None:
            from auditoria import ModuloAuditoria
            self.modulo_auditoria = ModuloAuditoria(self.area_trabajo, rol=self.rol)
        else:
            self.modulo_auditoria.cargar_auditoria()
        self.modulo_auditoria.pack(fill="both", expand=True)

    def _ir_a_personas_desde_formulario(self, cedula):
        self.mostrar_modulo_personas()
        self.modulo_personas.abrir_formulario_persona(None, cedula_prellenada=cedula)

    def iniciar_renovacion_desde_historial(self, cedula, tipo, dias_restantes, fecha_inicio):
        self.mostrar_modulo_nuevo()
        self.modulo_form.prellenar_para_renovacion(cedula, tipo, dias_restantes, fecha_inicio)

    # ------------------------------------------------------------------
    # Construcción del módulo "Inicio"
    # ------------------------------------------------------------------

    def construir_modulo_dash(self):
        canvas_scroll = tk.Canvas(self.frame_dash, bg=self.COLOR_BG, highlightthickness=0)
        scrollbar_dash = tk.Scrollbar(self.frame_dash, orient="vertical", command=canvas_scroll.yview)
        contenido = tk.Frame(canvas_scroll, bg=self.COLOR_BG)

        contenido.bind("<Configure>", lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all")))
        canvas_scroll.create_window((0, 0), window=contenido, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar_dash.set)

        canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar_dash.pack(side="right", fill="y")

        tk.Label(
            contenido, text="Resumen General del Sistema",
            font=("Helvetica", 16, "bold"), bg=self.COLOR_BG, fg=self.COLOR_TEXT_DARK
        ).pack(anchor="w", pady=(0, 15))

        # Fila superior: tarjetas de conteo (izquierda) + reloj/fecha (derecha)
        frame_fila_superior = tk.Frame(contenido, bg=self.COLOR_BG)
        frame_fila_superior.pack(fill="x", pady=10)

        frame_cards = tk.Frame(frame_fila_superior, bg=self.COLOR_BG)
        frame_cards.pack(side="left", fill="both", expand=True)

        self.card_total_reposos = self.crear_tarjeta(frame_cards, "TOTAL REPOSOS", "0", "#00a8cc")
        self.card_total_cuidos = self.crear_tarjeta(frame_cards, "TOTAL CUIDOS", "0", "#e53935")
        self.card_cuidos_activos = self.crear_tarjeta(frame_cards, "CUIDOS ACTIVOS", "0", "#ffb300")
        self.card_reposos_activos = self.crear_tarjeta(frame_cards, "REPOSOS ACTIVOS", "0", "#43a047")

        # Panel de fecha y hora (llena el espacio en blanco a la derecha de las tarjetas)
        frame_reloj = tk.Frame(frame_fila_superior, bg="#263544", width=190)
        frame_reloj.pack(side="left", fill="y", padx=(12, 0), ipady=15)
        frame_reloj.pack_propagate(False)

        tk.Label(frame_reloj, text="🕐", font=("Helvetica", 20), bg="#263544", fg="#ffffff").pack(pady=(8, 2))
        self.lbl_hora = tk.Label(frame_reloj, text="--:--:--", font=("Helvetica", 18, "bold"), bg="#263544", fg="#ffffff")
        self.lbl_hora.pack()
        self.lbl_fecha = tk.Label(frame_reloj, text="---", font=("Helvetica", 11), bg="#263544", fg="#9fd7e6", wraplength=170, justify="center")
        self.lbl_fecha.pack(pady=(4, 0))

        # Reportes rápidos
        frame_reportes = tk.Frame(contenido, bg=self.COLOR_CARD, bd=1, relief="solid", padx=15, pady=12)
        frame_reportes.pack(fill="x", pady=(20, 10))

        tk.Label(frame_reportes, text="Reportes Rápidos", font=("Helvetica", 12, "bold"),
                 bg=self.COLOR_CARD, fg=self.COLOR_TEXT_DARK).pack(anchor="w", pady=(0, 8))

        frame_botones_reportes = tk.Frame(frame_reportes, bg=self.COLOR_CARD)
        frame_botones_reportes.pack(fill="x")

        tk.Button(
            frame_botones_reportes, text="📄 Resumen Diario (PDF)", font=("Helvetica", 9, "bold"),
            bg="#f57c00", fg="#ffffff", bd=0, cursor="hand2", padx=10, pady=6,
            command=lambda: self.exportar_resumen_pdf("HOY")
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            frame_botones_reportes, text="📄 Reporte del Mes (PDF)", font=("Helvetica", 9, "bold"),
            bg="#f57c00", fg="#ffffff", bd=0, cursor="hand2", padx=10, pady=6,
            command=lambda: self.exportar_resumen_pdf("MES")
        ).pack(side="left", padx=8)

        tk.Button(
            frame_botones_reportes, text="📊 Reporte del Mes (Excel)", font=("Helvetica", 9, "bold"),
            bg="#2e7d32", fg="#ffffff", bd=0, cursor="hand2", padx=10, pady=6,
            command=self.exportar_mes_excel
        ).pack(side="left", padx=8)

        # Panel de alertas
        frame_alertas = tk.Frame(contenido, bg=self.COLOR_CARD, bd=1, relief="solid", padx=15, pady=12)
        frame_alertas.pack(fill="x", pady=10)

        tk.Label(frame_alertas, text="📌 Panel de Alertas / Recordatorios", font=("Helvetica", 12, "bold"),
                 bg=self.COLOR_CARD, fg=self.COLOR_TEXT_DARK).pack(anchor="w", pady=(0, 8))

        frame_nueva_alerta = tk.Frame(frame_alertas, bg=self.COLOR_CARD)
        frame_nueva_alerta.pack(fill="x", pady=(0, 8))

        self.ent_nueva_alerta = tk.Entry(frame_nueva_alerta, font=("Helvetica", 10))
        self.ent_nueva_alerta.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.ent_nueva_alerta.bind("<Return>", lambda e: self.agregar_alerta())

        tk.Button(
            frame_nueva_alerta, text="+ Agregar", font=("Helvetica", 9, "bold"),
            bg=self.COLOR_PRIMARY, fg="#ffffff", bd=0, cursor="hand2", padx=10, command=self.agregar_alerta
        ).pack(side="left")

        self.frame_lista_alertas = tk.Frame(frame_alertas, bg=self.COLOR_CARD)
        self.frame_lista_alertas.pack(fill="x")

    def crear_tarjeta(self, padre, titulo, valor_inicial, color_borde):
        card = tk.Frame(padre, bg=self.COLOR_CARD, bd=1, relief="solid", highlightthickness=2, highlightbackground=color_borde)
        card.pack(side="left", fill="both", expand=True, padx=8, ipady=15)

        tk.Label(card, text=titulo, font=("Helvetica", 9, "bold"), bg=self.COLOR_CARD, fg="#707070").pack(pady=(10, 5))
        lbl_val = tk.Label(card, text=valor_inicial, font=("Helvetica", 22, "bold"), bg=self.COLOR_CARD, fg=color_borde)
        lbl_val.pack()
        return lbl_val

    def _actualizar_reloj(self):
        ahora = datetime.datetime.now()
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                 "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        texto_fecha = f"{dias[ahora.weekday()]}, {ahora.day} de {meses[ahora.month - 1]} de {ahora.year}"
        if hasattr(self, "lbl_hora"):
            self.lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
            self.lbl_fecha.config(text=texto_fecha)
        self.root.after(1000, self._actualizar_reloj)

    def actualizar_metricas(self):
        registros = base_datos.obtener_registros()
        fecha_actual = datetime.date.today()

        total_reposos = 0
        total_cuidos = 0
        cuidos_activos = 0
        reposos_activos = 0

        for r in registros:
            tipo_tramite = str(r[6]) if len(r) > 6 and r[6] else ""
            fecha_hasta_str = str(r[9]) if len(r) > 9 and r[9] else ""

            es_cuido = "Cuido" in tipo_tramite
            es_reposo = "Reposo" in tipo_tramite or "Natal" in tipo_tramite

            esta_activo = False
            if fecha_hasta_str:
                try:
                    fecha_hasta = datetime.datetime.strptime(fecha_hasta_str, "%Y-%m-%d").date()
                    if fecha_hasta >= fecha_actual:
                        esta_activo = True
                except ValueError:
                    pass

            if es_reposo:
                total_reposos += 1
            elif es_cuido:
                total_cuidos += 1

            if esta_activo:
                if es_cuido:
                    cuidos_activos += 1
                elif es_reposo:
                    reposos_activos += 1

        self.card_total_reposos.config(text=str(total_reposos))
        self.card_total_cuidos.config(text=str(total_cuidos))
        self.card_cuidos_activos.config(text=str(cuidos_activos))
        self.card_reposos_activos.config(text=str(reposos_activos))

    # ------------------------------------------------------------------
    # Panel de alertas
    # ------------------------------------------------------------------

    def refrescar_alertas(self):
        for widget in self.frame_lista_alertas.winfo_children():
            widget.destroy()

        alertas = base_datos.obtener_alertas()
        if not alertas:
            tk.Label(self.frame_lista_alertas, text="No hay alertas pendientes.",
                     font=("Helvetica", 9, "italic"), bg=self.COLOR_CARD, fg="#999999").pack(anchor="w")
            return

        for id_alerta, texto, fecha_creacion in alertas:
            fila = tk.Frame(self.frame_lista_alertas, bg="#fff8e1", pady=4, padx=8)
            fila.pack(fill="x", pady=2)
            tk.Label(fila, text=f"• {texto}", font=("Helvetica", 9), bg="#fff8e1", fg="#5d4037", anchor="w").pack(side="left", fill="x", expand=True)
            tk.Button(
                fila, text="✕", font=("Helvetica", 8, "bold"), bg="#fff8e1", fg="#c62828", bd=0,
                cursor="hand2", command=lambda i=id_alerta: self.quitar_alerta(i)
            ).pack(side="right")

    def agregar_alerta(self):
        texto = self.ent_nueva_alerta.get().strip()
        if not texto:
            return
        base_datos.crear_alerta(texto)
        self.ent_nueva_alerta.delete(0, tk.END)
        self.refrescar_alertas()

    def quitar_alerta(self, id_alerta):
        base_datos.eliminar_alerta(id_alerta)
        self.refrescar_alertas()

    # ------------------------------------------------------------------
    # Reportes rápidos (PDF / Excel) — reutilizan el generador del histórico
    # ------------------------------------------------------------------

    def exportar_resumen_pdf(self, modo):
        registros = base_datos.obtener_registros()
        if not registros:
            messagebox.showinfo("Sin Datos", "No hay registros disponibles para generar el reporte.")
            return

        fecha_actual = datetime.date.today()
        lista_filtrada = []
        for reg in registros:
            try:
                f_desde = datetime.datetime.strptime(reg[8], "%Y-%m-%d").date()
                f_hasta = datetime.datetime.strptime(reg[9], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            if modo == "HOY" and f_desde != fecha_actual:
                continue
            if modo == "MES" and (f_desde.year != fecha_actual.year or f_desde.month != fecha_actual.month):
                continue
            lista_filtrada.append((reg, f_hasta >= fecha_actual))

        if not lista_filtrada:
            messagebox.showinfo("Sin Datos", "No hay trámites en ese período para generar el reporte.")
            return

        titulo = f"RESUMEN DIARIO — {fecha_actual.strftime('%d-%m-%Y')}" if modo == "HOY" \
            else f"RESUMEN DEL MES — {fecha_actual.strftime('%m-%Y')}"

        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf"), ("Todos los archivos", "*.*")],
            title="Guardar Reporte PDF"
        )
        if not ruta_archivo:
            return

        # Se instancia el módulo de histórico solo para reutilizar su generador
        # de PDF (carga perezosa de ReportLab incluida).
        if self.modulo_historial is None:
            self.mostrar_modulo_tabla()
            self.mostrar_modulo_dash()
        self.modulo_historial._construir_pdf(ruta_archivo, lista_filtrada, titulo)

    def exportar_mes_excel(self):
        registros = base_datos.obtener_registros()
        fecha_actual = datetime.date.today()
        filas_mes = []
        for reg in registros:
            try:
                f_desde = datetime.datetime.strptime(reg[8], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            if f_desde.year == fecha_actual.year and f_desde.month == fecha_actual.month:
                filas_mes.append(reg)

        if not filas_mes:
            messagebox.showinfo("Sin Datos", "No hay trámites registrados este mes.")
            return

        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Libro de Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
            title="Guardar Reporte del Mes en Excel"
        )
        if not ruta_archivo:
            return

        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Reporte del Mes"
            encabezados = ["ID", "Cédula", "Nombre", "Teléfono", "Institución", "Cargo",
                           "Trámite", "Días", "Desde", "Hasta", "Cod. Color", "Médico", "Especialidad"]
            ws.append(encabezados)
            for reg in filas_mes:
                ws.append([reg[0], reg[1], reg[2], reg[3], reg[4], reg[5], reg[6],
                           reg[7], reg[8], reg[9], reg[10], reg[11], reg[12]])
            wb.save(ruta_archivo)
            messagebox.showinfo("Reporte Generado", f"El reporte Excel fue generado correctamente en:\n{ruta_archivo}")
        except ImportError:
            import csv
            ruta_csv = os.path.splitext(ruta_archivo)[0] + ".csv"
            with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Cédula", "Nombre", "Teléfono", "Institución", "Cargo",
                                  "Trámite", "Días", "Desde", "Hasta", "Cod. Color", "Médico", "Especialidad"])
                for reg in filas_mes:
                    writer.writerow(reg[:13])
            messagebox.showinfo(
                "Reporte Generado (CSV)",
                f"El paquete 'openpyxl' no está instalado; se generó en formato CSV, "
                f"compatible con Excel, en:\n{ruta_csv}"
            )
        except Exception as e:
            messagebox.showerror("Error al Generar Excel", f"Ocurrió un problema al exportar:\n{e}")

    # ------------------------------------------------------------------
    # Cambio de clave: asistente de 2 pasos
    #   Paso 1: verificar contraseña actual + pregunta de seguridad
    #   Paso 2: definir la nueva contraseña (se pide 2 veces)
    # ------------------------------------------------------------------

    def abrir_cambio_clave(self):
        vent = tk.Toplevel(self.root)
        vent.title("Cambiar Contraseña")
        vent.geometry("420x460")
        vent.configure(bg="#ffffff")
        vent.resizable(False, False)
        vent.grab_set()

        contenedor = tk.Frame(vent, bg="#ffffff")
        contenedor.pack(fill="both", expand=True)

        pregunta1, pregunta2 = base_datos.obtener_preguntas_seguridad(self.usuario)

        self._paso1_a_paso2(contenedor, vent, pregunta1, pregunta2)

    def _paso1_a_paso2(self, contenedor, vent, pregunta1, pregunta2):
        for w in contenedor.winfo_children():
            w.destroy()

        tk.Label(contenedor, text="Paso 1 de 2 — Verificar Identidad", font=("Helvetica", 12, "bold"),
                 bg="#ffffff", fg="#00a8cc").pack(pady=(20, 15))

        tk.Label(contenedor, text="Contraseña actual:", bg="#ffffff", font=("Helvetica", 9, "bold")).pack(pady=(0, 2))
        ent_actual = tk.Entry(contenedor, font=("Helvetica", 10), width=32, show="*")
        ent_actual.pack()

        ent_respuesta1 = None
        if pregunta1:
            tk.Label(contenedor, text=pregunta1, bg="#ffffff", font=("Helvetica", 9, "bold"),
                     wraplength=340, justify="center").pack(pady=(14, 2))
            ent_respuesta1 = tk.Entry(contenedor, font=("Helvetica", 10), width=32)
            ent_respuesta1.pack()
        else:
            tk.Label(contenedor, text="(No hay pregunta de seguridad configurada todavía;\n"
                                       "podrá definirla en el siguiente paso.)",
                     bg="#ffffff", font=("Helvetica", 8, "italic"), fg="#888888", justify="center").pack(pady=(10, 0))

        def continuar():
            clave_actual = ent_actual.get()
            respuesta1 = ent_respuesta1.get().strip() if ent_respuesta1 else ""

            if not clave_actual:
                messagebox.showwarning("Atención", "Ingrese su contraseña actual.")
                return
            if base_datos.verificar_credenciales(self.usuario, clave_actual) is None:
                messagebox.showerror("Error", "La contraseña actual es incorrecta.")
                return
            if pregunta1 and not base_datos.verificar_respuesta_seguridad(self.usuario, respuesta1):
                messagebox.showerror("Error", "La respuesta de seguridad es incorrecta.")
                return

            self._mostrar_paso2(contenedor, vent, pregunta1, pregunta2)

        tk.Button(contenedor, text="CONTINUAR", bg="#00a8cc", fg="#ffffff", font=("Helvetica", 10, "bold"),
                  bd=0, cursor="hand2", command=continuar).pack(fill="x", padx=30, pady=25, ipady=7)

    def _mostrar_paso2(self, contenedor, vent, pregunta1, pregunta2):
        for w in contenedor.winfo_children():
            w.destroy()

        tk.Label(contenedor, text="Paso 2 de 2 — Nueva Contraseña", font=("Helvetica", 12, "bold"),
                 bg="#ffffff", fg="#00a8cc").pack(pady=(15, 12))

        tk.Label(contenedor, text="Nueva contraseña:", bg="#ffffff", font=("Helvetica", 9, "bold")).pack(pady=(0, 2))
        ent_nueva = tk.Entry(contenedor, font=("Helvetica", 10), width=32, show="*")
        ent_nueva.pack()

        tk.Label(contenedor, text="Confirmar nueva contraseña:", bg="#ffffff", font=("Helvetica", 9, "bold")).pack(pady=(10, 2))
        ent_confirmar = tk.Entry(contenedor, font=("Helvetica", 10), width=32, show="*")
        ent_confirmar.pack()

        tk.Label(contenedor, text="Preguntas de seguridad (opcional, 1 o 2):", bg="#ffffff",
                 font=("Helvetica", 9, "bold")).pack(pady=(16, 2))

        tk.Label(contenedor, text="Pregunta 1:", bg="#ffffff", font=("Helvetica", 8)).pack()
        ent_pregunta1 = tk.Entry(contenedor, font=("Helvetica", 9), width=32)
        ent_pregunta1.insert(0, pregunta1 or "")
        ent_pregunta1.pack()
        ent_respuesta1 = tk.Entry(contenedor, font=("Helvetica", 9), width=32)
        ent_respuesta1.pack(pady=(2, 8))
        ent_respuesta1.insert(0, "")

        tk.Label(contenedor, text="Pregunta 2 (opcional):", bg="#ffffff", font=("Helvetica", 8)).pack()
        ent_pregunta2 = tk.Entry(contenedor, font=("Helvetica", 9), width=32)
        ent_pregunta2.insert(0, pregunta2 or "")
        ent_pregunta2.pack()
        ent_respuesta2 = tk.Entry(contenedor, font=("Helvetica", 9), width=32)
        ent_respuesta2.pack(pady=(2, 4))

        tk.Label(contenedor, text="Deje la respuesta en blanco para no modificar esa pregunta.",
                 bg="#ffffff", font=("Helvetica", 7, "italic"), fg="#888888").pack()

        def guardar():
            nueva = ent_nueva.get()
            confirmar = ent_confirmar.get()

            if not nueva or not confirmar:
                messagebox.showwarning("Atención", "Complete la nueva contraseña y su confirmación.")
                return
            if nueva != confirmar:
                messagebox.showerror("Error", "Las dos contraseñas ingresadas no coinciden.")
                return
            if len(nueva) < 4:
                messagebox.showerror("Error", "La nueva contraseña debe tener al menos 4 caracteres.")
                return

            base_datos.cambiar_clave(self.usuario, nueva)

            p1 = ent_pregunta1.get().strip()
            r1 = ent_respuesta1.get().strip()
            if p1 and r1:
                base_datos.actualizar_pregunta_individual(self.usuario, 1, p1, r1)

            p2 = ent_pregunta2.get().strip()
            r2 = ent_respuesta2.get().strip()
            if p2 and r2:
                base_datos.actualizar_pregunta_individual(self.usuario, 2, p2, r2)

            messagebox.showinfo("Éxito", "Contraseña actualizada correctamente.")
            vent.destroy()

        tk.Button(contenedor, text="GUARDAR CONTRASEÑA", bg="#00a8cc", fg="#ffffff", font=("Helvetica", 10, "bold"),
                  bd=0, cursor="hand2", command=guardar).pack(fill="x", padx=30, pady=18, ipady=7)

    # ------------------------------------------------------------------
    # Cierre de sesión (manual y por inactividad)
    # ------------------------------------------------------------------

    def _reiniciar_temporizador_inactividad(self, event=None):
        if self._id_temporizador_inactividad is not None:
            self.root.after_cancel(self._id_temporizador_inactividad)
        self._id_temporizador_inactividad = self.root.after(TIEMPO_INACTIVIDAD_MS, self._cerrar_por_inactividad)

    def _cerrar_por_inactividad(self):
        messagebox.showinfo("Sesión Cerrada", "Su sesión se cerró automáticamente por inactividad.")
        self.root.destroy()
        if self.al_cerrar_sesion:
            self.al_cerrar_sesion()

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Está seguro de que desea cerrar la sesión?"):
            self.root.destroy()
            if self.al_cerrar_sesion:
                self.al_cerrar_sesion()