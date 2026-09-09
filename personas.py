import re
import tkinter as tk
from tkinter import ttk, messagebox
import base_datos

CARGOS = ["Docente", "Administrativo", "Personal de Apoyo"]


class ModuloPersonas(tk.Frame):
    def __init__(self, parent, rol="admin"):
        super().__init__(parent, bg="#ffffff", padx=20, pady=20, bd=1, relief="solid")
        self.rol = rol
        self.COLOR_PRIMARY = "#00a8cc"
        self.COLOR_TEXT_DARK = "#333333"

        tk.Label(
            self, text="Personas Registradas", font=("Helvetica", 14, "bold"),
            bg="#ffffff", fg=self.COLOR_TEXT_DARK
        ).pack(anchor="w", pady=(0, 10))

        # --- Buscador ---
        frame_buscador = tk.Frame(self, bg="#f0f2f5", padx=12, pady=10, bd=1, relief="groove")
        frame_buscador.pack(fill="x", pady=(0, 10))

        tk.Label(frame_buscador, text="Buscar por Cédula o Nombre y Apellido:",
                 font=("Helvetica", 9, "bold"), bg="#f0f2f5", fg="#555555").pack(side="left", padx=(0, 8))
        self.ent_buscar = tk.Entry(frame_buscador, font=("Helvetica", 10), width=30)
        self.ent_buscar.pack(side="left", padx=5)
        self.ent_buscar.bind("<KeyRelease>", self._al_escribir_busqueda)
        self.ent_buscar.bind("<Return>", lambda e: self._al_presionar_enter())

        tk.Button(
            frame_buscador, text="Limpiar", font=("Helvetica", 9), bg="#6c757d", fg="#ffffff",
            bd=0, cursor="hand2", padx=10, command=self.limpiar_busqueda
        ).pack(side="left", padx=5)

        # --- Barra de acciones ---
        frame_acciones = tk.Frame(self, bg="#ffffff")
        frame_acciones.pack(fill="x", pady=(0, 10))

        btn_registrar = tk.Button(
            frame_acciones, text="➕ REGISTRAR PERSONA", font=("Helvetica", 9, "bold"),
            bg="#2e7d32", fg="#ffffff", bd=0, cursor="hand2", padx=12, pady=6,
            command=lambda: self.abrir_formulario_persona(None)
        )
        btn_registrar.pack(side="left", padx=(0, 5))

        btn_editar = tk.Button(
            frame_acciones, text="✏️ EDITAR", font=("Helvetica", 9, "bold"),
            bg="#1976d2", fg="#ffffff", bd=0, cursor="hand2", padx=12, pady=6,
            command=self.editar_seleccionada
        )
        btn_editar.pack(side="left", padx=5)

        btn_eliminar = tk.Button(
            frame_acciones, text="🗑️ ELIMINAR", font=("Helvetica", 9, "bold"),
            bg="#c62828", fg="#ffffff", bd=0, cursor="hand2", padx=12, pady=6,
            command=self.eliminar_seleccionada
        )
        btn_eliminar.pack(side="left", padx=5)

        if self.rol == "visualizador":
            btn_registrar.configure(state="disabled")
            btn_editar.configure(state="disabled")
            btn_eliminar.configure(state="disabled")

        # --- Tabla ---
        columnas = ("cedula", "nombre", "telefono", "institucion", "cargo")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings", height=16)
        self.tabla.heading("cedula", text="Cédula")
        self.tabla.heading("nombre", text="Nombre y Apellido")
        self.tabla.heading("telefono", text="Teléfono")
        self.tabla.heading("institucion", text="Institución")
        self.tabla.heading("cargo", text="Cargo")

        self.tabla.column("cedula", width=100)
        self.tabla.column("nombre", width=220)
        self.tabla.column("telefono", width=110)
        self.tabla.column("institucion", width=220)
        self.tabla.column("cargo", width=140)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscroll=scrollbar.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tabla.bind("<Double-1>", lambda e: self.editar_seleccionada())

        self.cargar_lista()

    # ------------------------------------------------------------------

    def cargar_lista(self, texto=None):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for persona in base_datos.obtener_personas(texto):
            self.tabla.insert("", "end", values=persona)

    def _al_escribir_busqueda(self, event=None):
        texto = self.ent_buscar.get().strip()
        self.cargar_lista(texto or None)

    def _al_presionar_enter(self):
        texto = self.ent_buscar.get().strip()
        cedula = re.sub(r"\D", "", texto)
        if cedula and cedula == texto and not base_datos.obtener_beneficiario_por_cedula(cedula):
            # La cédula no existe: se ofrece llevar directamente al registro.
            if messagebox.askyesno(
                "Persona no encontrada",
                f"No hay ninguna persona registrada con la cédula {cedula}.\n\n"
                f"¿Desea registrarla ahora?"
            ):
                self.abrir_formulario_persona(None, cedula_prellenada=cedula)

    def limpiar_busqueda(self):
        self.ent_buscar.delete(0, tk.END)
        self.cargar_lista()

    def obtener_cedula_seleccionada(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return None
        return self.tabla.item(seleccion[0])["values"][0]

    def editar_seleccionada(self):
        if self.rol == "visualizador":
            return
        cedula = self.obtener_cedula_seleccionada()
        if not cedula:
            messagebox.showwarning("Atención", "Seleccione una persona de la lista para editar.")
            return
        persona = base_datos.obtener_beneficiario_por_cedula(str(cedula))
        self.abrir_formulario_persona(persona)

    def eliminar_seleccionada(self):
        if self.rol == "visualizador":
            return
        cedula = self.obtener_cedula_seleccionada()
        if not cedula:
            messagebox.showwarning("Atención", "Seleccione una persona de la lista para eliminar.")
            return

        seleccion = self.tabla.selection()
        nombre = self.tabla.item(seleccion[0])["values"][1]

        if not messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de eliminar a {nombre} (C.I. {cedula})?"):
            return

        resultado = base_datos.eliminar_persona(str(cedula))
        if resultado == "OCULTADA":
            messagebox.showinfo(
                "Persona Eliminada",
                "Esta persona tiene trámites registrados en el historial, por lo que se ocultó "
                "de la lista de Personas pero sus trámites se conservan intactos para consulta y reportes."
            )
        elif resultado == "ELIMINADA":
            messagebox.showinfo("Persona Eliminada", "La persona fue eliminada completamente.")
        self.cargar_lista(self.ent_buscar.get().strip() or None)

    # ------------------------------------------------------------------
    # Formulario de registro / edición
    # ------------------------------------------------------------------

    def abrir_formulario_persona(self, persona_existente, cedula_prellenada=None):
        if self.rol == "visualizador":
            return

        vent = tk.Toplevel(self)
        vent.title("Editar Persona" if persona_existente else "Registrar Persona")
        vent.geometry("440x420")
        vent.configure(bg="#ffffff")
        vent.grab_set()

        tk.Label(
            vent, text="Editar Datos Personales" if persona_existente else "Registrar Nueva Persona",
            font=("Helvetica", 13, "bold"), bg="#ffffff", fg=self.COLOR_PRIMARY
        ).pack(pady=(18, 15))

        frame = tk.Frame(vent, bg="#ffffff", padx=25)
        frame.pack(fill="both", expand=True)

        vcmd_cedula = (vent.register(lambda t: (t.isdigit() or t == "") and len(t) <= 10), '%P')
        vcmd_telefono = (vent.register(lambda t: len(t) <= 13 and re.match(r'^[0-9+\-\s]*$', t) is not None), '%P')

        tk.Label(frame, text="Cédula:", font=("Helvetica", 9, "bold"), bg="#ffffff", anchor="w").grid(row=0, column=0, sticky="w", pady=6)
        ent_cedula = tk.Entry(frame, font=("Helvetica", 10), width=28, validate="key", validatecommand=vcmd_cedula)
        ent_cedula.grid(row=0, column=1, pady=6, padx=10)

        tk.Label(frame, text="Nombre y Apellido:", font=("Helvetica", 9, "bold"), bg="#ffffff", anchor="w").grid(row=1, column=0, sticky="w", pady=6)
        ent_nombre = tk.Entry(frame, font=("Helvetica", 10), width=28)
        ent_nombre.grid(row=1, column=1, pady=6, padx=10)

        tk.Label(frame, text="Teléfono:", font=("Helvetica", 9, "bold"), bg="#ffffff", anchor="w").grid(row=2, column=0, sticky="w", pady=6)
        ent_telefono = tk.Entry(frame, font=("Helvetica", 10), width=28, validate="key", validatecommand=vcmd_telefono)
        ent_telefono.grid(row=2, column=1, pady=6, padx=10)

        tk.Label(frame, text="Institución:", font=("Helvetica", 9, "bold"), bg="#ffffff", anchor="w").grid(row=3, column=0, sticky="w", pady=6)
        ent_institucion = tk.Entry(frame, font=("Helvetica", 10), width=28)
        ent_institucion.grid(row=3, column=1, pady=6, padx=10)

        tk.Label(frame, text="Cargo:", font=("Helvetica", 9, "bold"), bg="#ffffff", anchor="w").grid(row=4, column=0, sticky="w", pady=6)
        cmb_cargo = ttk.Combobox(frame, values=CARGOS, state="readonly", width=25)
        cmb_cargo.grid(row=4, column=1, pady=6, padx=10)
        cmb_cargo.current(0)

        def forzar_mayus(entry):
            texto = entry.get()
            mayus = texto.upper()
            if texto != mayus:
                pos = entry.index(tk.INSERT)
                entry.delete(0, tk.END)
                entry.insert(0, mayus)
                entry.icursor(pos)

        ent_nombre.bind("<KeyRelease>", lambda e: forzar_mayus(ent_nombre))
        ent_institucion.bind("<KeyRelease>", lambda e: forzar_mayus(ent_institucion))

        if persona_existente:
            ent_cedula.insert(0, persona_existente[0])
            ent_cedula.configure(state="disabled")  # la cédula no se reasigna en edición
            ent_nombre.insert(0, persona_existente[1])
            ent_telefono.insert(0, persona_existente[2])
            ent_institucion.insert(0, persona_existente[3])
            if persona_existente[4] in CARGOS:
                cmb_cargo.set(persona_existente[4])
        elif cedula_prellenada:
            ent_cedula.insert(0, cedula_prellenada)

        def guardar():
            cedula = re.sub(r"\D", "", ent_cedula.get().strip())
            nombre = ent_nombre.get().strip().upper()
            telefono = ent_telefono.get().strip()
            institucion = ent_institucion.get().strip().upper()
            cargo = cmb_cargo.get()

            faltantes = []
            if not cedula: faltantes.append("Cédula")
            if not nombre: faltantes.append("Nombre y Apellido")
            if not telefono: faltantes.append("Teléfono")
            if not institucion: faltantes.append("Institución")
            if faltantes:
                messagebox.showwarning("Campos Incompletos", "Complete: " + ", ".join(faltantes))
                return

            if not persona_existente:
                if base_datos.obtener_beneficiario_por_cedula(cedula):
                    messagebox.showerror("Cédula Duplicada", "Ya existe una persona registrada con esa cédula.")
                    return

            base_datos.registrar_o_editar_persona(cedula, nombre, telefono, institucion, cargo)
            messagebox.showinfo("Éxito", "Datos guardados correctamente.")
            vent.destroy()
            self.cargar_lista(self.ent_buscar.get().strip() or None)

        tk.Button(
            vent, text="GUARDAR", font=("Helvetica", 10, "bold"), bg=self.COLOR_PRIMARY, fg="#ffffff",
            bd=0, cursor="hand2", command=guardar
        ).pack(fill="x", padx=25, pady=20, ipady=8)
