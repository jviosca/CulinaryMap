import json
from cryptography.fernet import Fernet

# Clave para cifrar y descifrar JSON (guardar en un lugar seguro en producción)
SECRET_KEY = b'my_secret_key_here'  # Generar con Fernet.generate_key()
cipher = Fernet(SECRET_KEY)

# Cargar datos desde JSON cifrado
def load_data():
    try:
        with open("sitios.json", "rb") as f:
            encrypted_data = f.read()
        decrypted_data = json.loads(cipher.decrypt(encrypted_data).decode())
    except:
        decrypted_data = []  # Si no hay datos, inicializar vacío
    return decrypted_data

# Guardar datos en JSON cifrado
def save_data(data):
    encrypted_data = cipher.encrypt(json.dumps(data).encode())
    with open("sitios.json", "wb") as f:
        f.write(encrypted_data)
