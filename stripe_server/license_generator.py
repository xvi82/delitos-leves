"""
Generador de licencias para el Procesador de Delitos Leves.
Este módulo contiene la lógica para generar claves de activación
basadas en el Hardware ID y el nombre del usuario.

⚠️ IMPORTANTE: La SECRET_KEY debe coincidir exactamente con la
del archivo license_manager.py de la aplicación principal.
"""

import hashlib
import os

# La clave secreta se carga desde variable de entorno por seguridad
# En producción, NUNCA hardcodees esta clave en el código
SECRET_KEY = os.environ.get('LICENSE_SECRET_KEY', '')


def generate_license_hash(hardware_id: str, user_name: str) -> str:
    """
    Genera el hash de la licencia vinculando Hardware + Nombre + Clave Secreta.
    
    Args:
        hardware_id: UUID único del hardware del usuario
        user_name: Nombre del usuario (tal como aparece en la app)
    
    Returns:
        Clave de licencia de 24 caracteres en mayúsculas
    """
    if not SECRET_KEY:
        raise ValueError("LICENSE_SECRET_KEY no está configurada")
    
    # Normalizamos el nombre (mayúsculas, sin espacios extra)
    clean_name = user_name.strip().upper()
    clean_hwid = hardware_id.strip()
    
    # Creamos la cadena única
    raw_data = f"{clean_hwid}|{clean_name}|{SECRET_KEY}"
    
    # Generamos el hash
    return hashlib.sha256(raw_data.encode()).hexdigest()[:24].upper()


def verify_license(key: str, hardware_id: str, user_name: str) -> bool:
    """
    Verifica si una clave de licencia es válida.
    
    Args:
        key: Clave proporcionada por el usuario
        hardware_id: UUID del hardware
        user_name: Nombre del usuario
    
    Returns:
        True si la clave es válida, False en caso contrario
    """
    expected_key = generate_license_hash(hardware_id, user_name)
    return key.strip().upper() == expected_key





