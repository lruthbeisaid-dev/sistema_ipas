import tkinter as tk
import datetime
import base_datos
from formulario import ModuloFormulario
from historial import ModuloHistorial

class VentanaDashboard:
    def __init__(self, root):
        self.root = root
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

        self.topbar = tk.Frame(self.root, bg=self.COLOR_TOPBAR, height=50)
        self.topbar.pack(side="top", fill="x")

        lbl_logo_top = tk.Label(
            self.topbar, text=" IPASME | Sistema de Gestión", 
            font=("Helvetica", 13, "bold"), bg=self.COLOR_TOPBAR, fg="#ffffff"
        )
        lbl_logo_top.pack(side="left", padx=15, pady=10)

        self.sidebar = tk.Frame(self.root, bg=self.COLOR_SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        lbl_menu = tk.Label(
            self.sidebar, text="MÓDULOS", font=("Helvetica", 9, "bold"), 
            bg=self.COLOR_SIDEBAR, fg="#7e8a9b", anchor="w"
        )
        lbl_menu.pack(fill="x", padx=15, pady=(20, 10))

        self.btn_nav_dash = self.crear_boton_nav(" Dashboard", self.mostrar_modulo_dash)
        self.btn_nav_nuevo = self.crear_boton_nav(" Registrar Permiso", self.mostrar_modulo_nuevo)
        self.btn_nav_tabla = self.crear_boton_nav(" Consultas / Histórico", self.mostrar_modulo_tabla)

        self.area_trabajo = tk.Frame(self.root, bg=self.COLOR_BG)
        self.area_trabajo.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        self.frame_dash = tk.Frame(self.area_trabajo, bg=self.COLOR_BG)

        self.modulo_form = ModuloFormulario(self.area_trabajo, al_guardar_callback=self.actualizar_metricas)
        self.modulo_historial = ModuloHistorial(self.area_trabajo, callback_renovar=self.iniciar_renovacion_desde_historial)

        self.construir_modulo_dash()
        self.mostrar_modulo_dash()

    def crear_boton_nav(self, texto, comando):
        btn = tk.Button(
            self.sidebar, text=texto, font=("Helvetica", 10, "bold"),
            bg=self.COLOR_SIDEBAR, fg="#d0d5dd", activebackground=self.COLOR_SIDEBAR_BTN,
            activeforeground="#ffffff", bd=0, anchor="w", padx=15, cursor="hand2", command=comando
        )
        btn.pack(fill="x", ipady=10, pady=2)
        return btn

    def resaltar_boton(self, btn_activo):
        for btn in [self.btn_nav_dash, self.btn_nav_nuevo, self.btn_nav_tabla]:
            btn.configure(bg=self.COLOR_SIDEBAR, fg="#d0d5dd")
        btn_activo.configure(bg=self.COLOR_SIDEBAR_ACTIVE, fg="#ffffff")

    def ocultar_modulos(self):
        self.frame_dash.pack_forget()
        if hasattr(self, 'modulo_form'):
            self.modulo_form.pack_forget()
        if hasattr(self, 'modulo_historial'):
            self.modulo_historial.pack_forget()

    def mostrar_modulo_dash(self):
        self.ocultar_modulos()
        self.resaltar_boton(self.btn_nav_dash)
        self.actualizar_metricas()
        self.frame_dash.pack(fill="both", expand=True)

    def construir_modulo_dash(self):
        lbl_titulo = tk.Label(
            self.frame_dash, text="Resumen General del Sistema", 
            font=("Helvetica", 16, "bold"), bg=self.COLOR_BG, fg=self.COLOR_TEXT_DARK
        )
        lbl_titulo.pack(anchor="w", pady=(0, 15))

        frame_cards = tk.Frame(self.frame_dash, bg=self.COLOR_BG)
        frame_cards.pack(fill="x", pady=10)

        # Ajuste de títulos y variables de tarjetas
        self.card_total_reposos = self.crear_tarjeta(frame_cards, "TOTAL REPOSOS", "0", "#00a8cc")
        self.card_total_cuidos = self.crear_tarjeta(frame_cards, "TOTAL CUIDOS", "0", "#e53935")
        self.card_cuidos_activos = self.crear_tarjeta(frame_cards, "CUIDOS ACTIVOS", "0", "#ffb300")
        self.card_reposos_activos = self.crear_tarjeta(frame_cards, "REPOSOS ACTIVOS", "0", "#43a047")

    def crear_tarjeta(self, padre, titulo, valor_inicial, color_borde):
        card = tk.Frame(padre, bg=self.COLOR_CARD, bd=1, relief="solid", highlightthickness=2, highlightbackground=color_borde)
        card.pack(side="left", fill="both", expand=True, padx=8, ipady=15)

        lbl_t = tk.Label(card, text=titulo, font=("Helvetica", 9, "bold"), bg=self.COLOR_CARD, fg="#707070")
        lbl_t.pack(pady=(10, 5))

        lbl_val = tk.Label(card, text=valor_inicial, font=("Helvetica", 22, "bold"), bg=self.COLOR_CARD, fg=color_borde)
        lbl_val.pack()
        return lbl_val

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

            # Verificación de vigencia por fecha
            esta_activo = False
            if fecha_hasta_str:
                try:
                    fecha_hasta = datetime.datetime.strptime(fecha_hasta_str, "%Y-%m-%d").date()
                    if fecha_hasta >= fecha_actual:
                        esta_activo = True
                except ValueError:
                    pass

            # Conteo Totales (Histórico completo)
            if es_reposo:
                total_reposos += 1
            elif es_cuido:
                total_cuidos += 1

            # Conteo de Activos (Solo vigentes)
            if esta_activo:
                if es_cuido:
                    cuidos_activos += 1
                elif es_reposo:
                    reposos_activos += 1

        self.card_total_reposos.config(text=str(total_reposos))
        self.card_total_cuidos.config(text=str(total_cuidos))
        self.card_cuidos_activos.config(text=str(cuidos_activos))
        self.card_reposos_activos.config(text=str(reposos_activos))

    def mostrar_modulo_nuevo(self):
        self.ocultar_modulos()
        self.resaltar_boton(self.btn_nav_nuevo)
        self.modulo_form.pack(fill="both", expand=True)

    def mostrar_modulo_tabla(self):
        self.ocultar_modulos()
        self.resaltar_boton(self.btn_nav_tabla)
        self.modulo_historial.cargar_tabla_completa()
        self.modulo_historial.pack(fill="both", expand=True)

    def iniciar_renovacion_desde_historial(self, cedula, nombre, telefono, institucion, cargo, tipo, dias_restantes, fecha_inicio):
        self.mostrar_modulo_nuevo()
        self.modulo_form.prellenar_para_renovacion(
            cedula, nombre, telefono, institucion, cargo, tipo, dias_restantes, fecha_inicio
        )