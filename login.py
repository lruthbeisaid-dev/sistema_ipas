import os
import tkinter as tk
from tkinter import messagebox
import base_datos


class VentanaLogin:
    def __init__(self, root, al_ingresar_exitoso):
        self.root = root
        self.al_ingresar_exitoso = al_ingresar_exitoso

        self.root.title("IPASME - Inicio de Sesión")
        self.root.configure(bg="#151b2e")

        # Pantalla completa, con Escape como salida de emergencia (no cierra
        # la app, solo restaura la ventana por si el usuario lo necesita).
        try:
            self.root.attributes("-fullscreen", True)
        except tk.TclError:
            self.root.state("zoomed")
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))

        # --- Panel izquierdo: identidad institucional ---
        self.panel_izq = tk.Frame(self.root, bg="#0f3d4a")
        self.panel_izq.place(relx=0, rely=0, relwidth=0.5, relheight=1)

        self.frame_marca = tk.Frame(self.panel_izq, bg="#0f3d4a")
        self.frame_marca.place(relx=0.5, rely=0.5, anchor="center")

        self.cargar_logo()

        tk.Label(
            self.frame_marca, text="IPASME", font=("Helvetica", 40, "bold"),
            bg="#0f3d4a", fg="#ffffff"
        ).pack(pady=(15, 0))

        tk.Label(
            self.frame_marca, text="Sistema de Gestión de Reposos y Cuidos",
            font=("Helvetica", 13), bg="#0f3d4a", fg="#8fd3e8"
        ).pack(pady=(5, 0))

        tk.Frame(self.frame_marca, bg="#00a8cc", height=3, width=120).pack(pady=18)

        tk.Label(
            self.frame_marca,
            text="Instituto de Previsión y Asistencia Social\npara el Personal del Ministerio de Educación",
            font=("Helvetica", 10), bg="#0f3d4a", fg="#6fa9b8", justify="center"
        ).pack()

        # --- Panel derecho: formulario de acceso ---
        self.panel_der = tk.Frame(self.root, bg="#151b2e")
        self.panel_der.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)

        self.frame_central = tk.Frame(self.panel_der, bg="#1e2540", padx=45, pady=40)
        self.frame_central.place(relx=0.5, rely=0.5, anchor="center", width=380)

        tk.Label(
            self.frame_central, text="Iniciar Sesión", font=("Helvetica", 18, "bold"),
            bg="#1e2540", fg="#ffffff"
        ).pack(anchor="w", pady=(0, 25))

        self.lbl_usuario = tk.Label(
            self.frame_central, text="Usuario", font=("Helvetica", 10, "bold"),
            bg="#1e2540", fg="#9aa3c2", anchor="w"
        )
        self.lbl_usuario.pack(fill="x", pady=(0, 4))

        self.txt_usuario = tk.Entry(
            self.frame_central, font=("Helvetica", 12), bg="#2a3357",
            fg="#ffffff", bd=0, relief="flat", insertbackground="white"
        )
        self.txt_usuario.pack(ipady=9, ipadx=10, fill="x")
        self.txt_usuario.bind("<Return>", lambda evento: self.validar_login())

        self.lbl_clave = tk.Label(
            self.frame_central, text="Contraseña", font=("Helvetica", 10, "bold"),
            bg="#1e2540", fg="#9aa3c2", anchor="w"
        )
        self.lbl_clave.pack(fill="x", pady=(18, 4))

        self.txt_clave = tk.Entry(
            self.frame_central, font=("Helvetica", 12), bg="#2a3357",
            fg="#ffffff", bd=0, show="•", relief="flat", insertbackground="white"
        )
        self.txt_clave.pack(ipady=9, ipadx=10, fill="x")
        self.txt_clave.bind("<Return>", lambda evento: self.validar_login())

        self.btn_login = tk.Button(
            self.frame_central, text="INGRESAR", font=("Helvetica", 11, "bold"),
            bg="#00a8cc", fg="#ffffff", activebackground="#0088a3", activeforeground="#ffffff",
            bd=0, cursor="hand2", command=self.validar_login
        )
        self.btn_login.pack(ipady=10, fill="x", pady=(28, 5))

        self.lbl_olvido = tk.Label(
            self.frame_central, text="¿Olvidó su contraseña?", font=("Helvetica", 9, "underline"),
            bg="#1e2540", fg="#7e8db0", cursor="hand2"
        )
        self.lbl_olvido.pack(pady=(14, 0))
        self.lbl_olvido.bind("<Button-1>", lambda evento: self.abrir_recuperar_clave())

        self.txt_usuario.focus_set()

    def cargar_logo(self):
        # PIL solo se importa si realmente hace falta mostrar una imagen,
        # para no cargar esa librería en memoria cuando no se usa.
        posibles_rutas = [
            os.path.join("img", "logo_login.png"),
            "logo_login.png",
            os.path.join("img", "logo.webp"),
            os.path.join("img", "logo 2.avif")
        ]
        ruta_final = next((r for r in posibles_rutas if os.path.exists(r)), None)

        if ruta_final:
            try:
                from PIL import Image, ImageTk
                img_original = Image.open(ruta_final)
                img_resized = img_original.resize((150, 150), Image.Resampling.LANCZOS)
                self.img_logo = ImageTk.PhotoImage(img_resized)
                tk.Label(self.frame_marca, image=self.img_logo, bg="#0f3d4a").pack()
                return
            except Exception:
                pass

        tk.Label(
            self.frame_marca, text="🏥", font=("Helvetica", 60), bg="#0f3d4a", fg="#ffffff"
        ).pack()

    def validar_login(self):
        usuario = self.txt_usuario.get().strip()
        clave = self.txt_clave.get()

        rol = base_datos.verificar_credenciales(usuario, clave)

        if rol:
            self.root.attributes("-fullscreen", False)
            self.al_ingresar_exitoso(rol, usuario)
        else:
            messagebox.showerror("Error de Autenticación", "Usuario o contraseña incorrectos.")
            self.txt_clave.delete(0, tk.END)

    # ------------------------------------------------------------------
    # Recuperación de contraseña (usuario admin) mediante preguntas de seguridad
    # ------------------------------------------------------------------

    def abrir_recuperar_clave(self):
        vent = tk.Toplevel(self.root)
        vent.title("Recuperar Contraseña")
        vent.geometry("420x480")
        vent.configure(bg="#ffffff")
        vent.resizable(False, False)
        vent.grab_set()

        pregunta1, pregunta2 = base_datos.obtener_preguntas_seguridad("admin")
        if not pregunta1 and not pregunta2:
            tk.Label(vent, text="El usuario admin no tiene preguntas\nde seguridad configuradas todavía.",
                     bg="#ffffff", font=("Helvetica", 10), justify="center").pack(pady=40)
            return

        tk.Label(vent, text="Recuperación de Contraseña", font=("Helvetica", 13, "bold"),
                 bg="#ffffff", fg="#00a8cc").pack(pady=(20, 10))
        tk.Label(vent, text="Usuario: admin", bg="#ffffff", font=("Helvetica", 9, "bold")).pack(pady=(0, 15))

        ent_respuesta1 = None
        ent_respuesta2 = None

        if pregunta1:
            tk.Label(vent, text=pregunta1, bg="#ffffff", font=("Helvetica", 10),
                     wraplength=360, justify="center").pack(pady=(0, 4))
            ent_respuesta1 = tk.Entry(vent, font=("Helvetica", 10), width=38)
            ent_respuesta1.pack(pady=(0, 12))

        if pregunta2:
            tk.Label(vent, text=pregunta2, bg="#ffffff", font=("Helvetica", 10),
                     wraplength=360, justify="center").pack(pady=(0, 4))
            ent_respuesta2 = tk.Entry(vent, font=("Helvetica", 10), width=38)
            ent_respuesta2.pack(pady=(0, 12))

        tk.Label(vent, text="Nueva contraseña:", bg="#ffffff", font=("Helvetica", 9, "bold")).pack(pady=(8, 2))
        ent_nueva = tk.Entry(vent, font=("Helvetica", 10), width=38, show="*")
        ent_nueva.pack(pady=(0, 8))

        tk.Label(vent, text="Confirmar nueva contraseña:", bg="#ffffff", font=("Helvetica", 9, "bold")).pack(pady=(0, 2))
        ent_confirmar = tk.Entry(vent, font=("Helvetica", 10), width=38, show="*")
        ent_confirmar.pack(pady=(0, 8))

        def procesar():
            respuesta1 = ent_respuesta1.get().strip() if ent_respuesta1 else ""
            respuesta2 = ent_respuesta2.get().strip() if ent_respuesta2 else ""
            nueva = ent_nueva.get().strip()
            confirmar = ent_confirmar.get().strip()

            if (pregunta1 and not respuesta1) or (pregunta2 and not respuesta2):
                messagebox.showwarning("Atención", "Responda todas las preguntas de seguridad.")
                return
            if not nueva or not confirmar:
                messagebox.showwarning("Atención", "Complete la nueva contraseña y su confirmación.")
                return
            if nueva != confirmar:
                messagebox.showerror("Error", "Las dos contraseñas ingresadas no coinciden.")
                return
            if len(nueva) < 4:
                messagebox.showwarning("Atención", "La nueva contraseña debe tener al menos 4 caracteres.")
                return

            if not base_datos.verificar_respuesta_seguridad("admin", respuesta1, respuesta2):
                messagebox.showerror("Error", "Una o más respuestas de seguridad son incorrectas.")
                return

            base_datos.cambiar_clave("admin", nueva)
            messagebox.showinfo("Éxito", "Contraseña actualizada correctamente. Ya puede iniciar sesión.")
            vent.destroy()

        tk.Button(vent, text="RESTABLECER CONTRASEÑA", bg="#00a8cc", fg="#ffffff",
                  font=("Helvetica", 10, "bold"), bd=0, cursor="hand2",
                  command=procesar).pack(fill="x", padx=25, pady=18, ipady=6)