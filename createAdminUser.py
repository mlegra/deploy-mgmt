# Agrega esto al final de tu app.py, ejecútalo una vez y luego bórralo o comenta
from model import create_user

try:
    create_user('admin', 'admin123', 'admin')
    print("Usuario admin creado: usuario=admin, contraseña=admin123")
except Exception as e:
    print("Ya existe el usuario admin o error:", e)