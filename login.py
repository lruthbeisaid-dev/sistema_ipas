import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk


# Usuarios del sistema: usuario -> (clave, rol)
# rol "admin"        -> acceso completo (registrar, editar, eliminar, renovar, reportes)
# rol "visualizador" -> solo consulta / búsqueda / reportes, sin permisos de modificación
USUARIOS = {
    "admin": {"clave": "1234", "rol": "admin"},
    "visualizador": {"clave": "1234", "rol": "visualizador"},
}


class VentanaLogin:
    def __init__(self, root, al_ingresar_exitoso):
        self.root = root
        self.al_ingresar_exitoso = al_ingresar_exitoso
        
        # Configuración de la Ventana Principal
        self.root.title("IPASME - Inicio de Sesión")
        self.root.geometry("450x550")
        self.root.resizable(False, False)
        self.root.configure(bg="#232943")

        # Contenedor Central
        self.frame_central = tk.Frame(self.root, bg="#232943")
        self.frame_central.pack(expand=True)

        # Cargar Imagen del Logo (IPASME)
        self.cargar_logo()

        # Entrada de Usuario
        self.lbl_usuario = tk.Label(
            self.frame_central, text="Usuario", font=("Helvetica", 10, "bold"), 
            bg="#232943", fg="#b0b5c0", anchor="w"
        )
        self.lbl_usuario.pack(fill="x", pady=(10, 2))

        self.txt_usuario = tk.Entry(
            self.frame_central, font=("Helvetica", 12), bg="#d0d5dd", 
            fg="#1a1a1a", bd=0, relief="flat", insertbackground="black"
        )
        self.txt_usuario.pack(ipady=8, ipadx=10, fill="x")
        self.txt_usuario.bind("<Return>", lambda evento: self.validar_login())

        # Entrada de Contraseña
        self.lbl_clave = tk.Label(
            self.frame_central, text="Contraseña", font=("Helvetica", 10, "bold"), 
            bg="#232943", fg="#b0b5c0", anchor="w"
        )
        self.lbl_clave.pack(fill="x", pady=(15, 2))

        self.txt_clave = tk.Entry(
            self.frame_central, font=("Helvetica", 12), bg="#d0d5dd", 
            fg="#1a1a1a", bd=0, show="*", relief="flat", insertbackground="black"
        )
        self.txt_clave.pack(ipady=8, ipadx=10, fill="x")
        self.txt_clave.bind("<Return>", lambda evento: self.validar_login())

        # Botón de Ingreso
        self.btn_login = tk.Button(
            self.frame_central, text="Ingresar", font=("Helvetica", 11, "bold"),
            bg="#3b4252", fg="#ffffff", activebackground="#4c566a", activeforeground="#ffffff",
            bd=0, cursor="hand2", command=self.validar_login
        )
        self.btn_login.pack(ipady=8, fill="x", pady=(25, 0))

    def cargar_logo(self):
        # Rutas posibles de la imagen del logo
        posibles_rutas = [
            os.path.join("img", "logo_login.png"),
            "logo_login.png",
            os.path.join("img", "logo.webp"),
            os.path.join("img", "logo 2.avif")
        ]
        
        ruta_final = None
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                ruta_final = ruta
                break

        if ruta_final:
            try:
                img_original = Image.open(ruta_final)
                img_resized = img_original.resize((130, 130), Image.Resampling.LANCZOS)
                self.img_logo = ImageTk.PhotoImage(img_resized)
                
                lbl_img = tk.Label(self.frame_central, image=self.img_logo, bg="#232943")
                lbl_img.pack(pady=(0, 15))
            except Exception:
                self.mostrar_texto_logo()
        else:
            self.mostrar_texto_logo()

    def mostrar_texto_logo(self):
        lbl_img = tk.Label(
            self.frame_central, text="[ IPASME ]", 
            font=("Helvetica", 16, "bold"), bg="#232943", fg="#ffffff"
        )
        lbl_img.pack(pady=(0, 20))

    def validar_login(self):
        usuario = self.txt_usuario.get().strip()
        clave = self.txt_clave.get()

        datos_usuario = USUARIOS.get(usuario)

        if datos_usuario and datos_usuario["clave"] == clave:
            self.al_ingresar_exitoso(datos_usuario["rol"])
        else:
            messagebox.showerror("Error de Autenticación", "Usuario o contraseña incorrectos.")