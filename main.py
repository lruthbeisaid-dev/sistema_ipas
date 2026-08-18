import tkinter as tk
from base_datos import inicializar_bd
from login import VentanaLogin
from dashboard import VentanaDashboard

def abrir_dashboard():
    root_login.destroy()
    
    root_principal = tk.Tk()
    app = VentanaDashboard(root_principal)
    root_principal.mainloop()

if __name__ == "__main__":
    inicializar_bd()

    root_login = tk.Tk()
    app_login = VentanaLogin(root_login, al_ingresar_exitoso=abrir_dashboard)
    root_login.mainloop()