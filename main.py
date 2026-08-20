import tkinter as tk
from base_datos import inicializar_bd
from login import VentanaLogin
from dashboard import VentanaDashboard


def iniciar_sesion():
    root_login = tk.Tk()
    VentanaLogin(root_login, al_ingresar_exitoso=lambda rol: abrir_dashboard(root_login, rol))
    root_login.mainloop()


def abrir_dashboard(root_login, rol):
    root_login.destroy()

    root_principal = tk.Tk()
    VentanaDashboard(root_principal, rol, al_cerrar_sesion=iniciar_sesion)
    root_principal.mainloop()


if __name__ == "__main__":
    inicializar_bd()
    iniciar_sesion()