import tkinter as tk
from tkinter import ttk
import base_datos

ETIQUETAS_ACCION = {
    "CREACION_TRAMITE": ("Trámite Creado", "#2e7d32"),
    "EDICION_TRAMITE": ("Trámite Editado", "#1976d2"),
    "ELIMINACION_TRAMITE": ("Trámite Eliminado", "#c62828"),
    "PURGA_AUTOMATICA": ("Purga Automática (+10 años)", "#6a1b9a"),
    "CREACION_PERSONA": ("Persona Registrada", "#2e7d32"),
    "EDICION_PERSONA": ("Persona Editada", "#1976d2"),
    "ELIMINACION_PERSONA": ("Persona Eliminada", "#c62828"),
}


class ModuloAuditoria(tk.Frame):
    def __init__(self, parent, rol="admin"):
        super().__init__(parent, bg="#ffffff", padx=20, pady=20, bd=1, relief="solid")
        self.rol = rol
        self.COLOR_PRIMARY = "#00a8cc"
        self.COLOR_TEXT_DARK = "#333333"

        tk.Label(
            self, text="Auditoría del Sistema", font=("Helvetica", 14, "bold"),
            bg="#ffffff", fg=self.COLOR_TEXT_DARK
        ).pack(anchor="w", pady=(0, 5))

        tk.Label(
            self, text="Historial completo de creaciones, ediciones y eliminaciones de personas y trámites.",
            font=("Helvetica", 9, "italic"), bg="#ffffff", fg="#666666"
        ).pack(anchor="w", pady=(0, 12))

        frame_filtro = tk.Frame(self, bg="#f0f2f5", padx=12, pady=10, bd=1, relief="groove")
        frame_filtro.pack(fill="x", pady=(0, 10))

        tk.Label(frame_filtro, text="Filtrar por Cédula:", font=("Helvetica", 9, "bold"),
                 bg="#f0f2f5", fg="#555555").pack(side="left", padx=(0, 8))
        self.ent_cedula = tk.Entry(frame_filtro, font=("Helvetica", 10), width=18)
        self.ent_cedula.pack(side="left", padx=5)
        self.ent_cedula.bind("<KeyRelease>", lambda e: self.cargar_auditoria())

        tk.Button(
            frame_filtro, text="Limpiar", font=("Helvetica", 9), bg="#6c757d", fg="#ffffff",
            bd=0, cursor="hand2", padx=10, command=self.limpiar_filtro
        ).pack(side="left", padx=5)

        tk.Button(
            frame_filtro, text="🔄 Actualizar", font=("Helvetica", 9, "bold"), bg=self.COLOR_PRIMARY, fg="#ffffff",
            bd=0, cursor="hand2", padx=10, command=self.cargar_auditoria
        ).pack(side="left", padx=5)

        columnas = ("accion", "cedula", "nombre", "tramite", "codigo", "fecha_hora", "detalle")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings", height=20)
        self.tabla.heading("accion", text="Acción")
        self.tabla.heading("cedula", text="Cédula")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("tramite", text="Tipo Trámite")
        self.tabla.heading("codigo", text="Código Registro")
        self.tabla.heading("fecha_hora", text="Fecha y Hora")
        self.tabla.heading("detalle", text="Cambios Realizados")

        self.tabla.column("accion", width=140)
        self.tabla.column("cedula", width=85, anchor="center")
        self.tabla.column("nombre", width=150)
        self.tabla.column("tramite", width=130)
        self.tabla.column("codigo", width=100, anchor="center")
        self.tabla.column("fecha_hora", width=135, anchor="center")
        self.tabla.column("detalle", width=350)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscroll=scrollbar.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.cargar_auditoria()

    def limpiar_filtro(self):
        self.ent_cedula.delete(0, tk.END)
        self.cargar_auditoria()

    def cargar_auditoria(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        cedula = self.ent_cedula.get().strip() or None
        eventos = base_datos.obtener_auditoria(cedula=cedula)

        for id_ev, accion, cedula_ev, nombre, tipo_tramite, codigo_registro, fecha_hora, detalle in eventos:
            etiqueta, color = ETIQUETAS_ACCION.get(accion, (accion, "#333333"))
            tag = accion
            self.tabla.tag_configure(tag, foreground=color)
            self.tabla.insert(
                "", "end",
                values=(etiqueta, cedula_ev or "", nombre or "", tipo_tramite or "-", codigo_registro or "-",
                        fecha_hora, detalle or ""),
                tags=(tag,)
            )
