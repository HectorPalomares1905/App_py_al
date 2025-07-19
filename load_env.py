# load_env.py - Utilitario para cargar variables de entorno

import os
from typing import Dict, Any

def load_env_file(env_path: str = '.env') -> None:
    """
    Carga variables de entorno desde un archivo .env
    """
    if not os.path.exists(env_path):
        print(f"Archivo {env_path} no encontrado. Usando variables del sistema.")
        return
    
    with open(env_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remover comillas si las hay
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                os.environ[key] = value

def check_env_variables() -> Dict[str, Any]:
    """
    Verifica que las variables de entorno necesarias estén configuradas
    """
    required_vars = {
        'GOOGLE_SPREADSHEET_ID': os.getenv('GOOGLE_SPREADSHEET_ID'),
        'GOOGLE_CREDENTIALS_JSON': os.getenv('GOOGLE_CREDENTIALS_JSON'),
    }
    
    # Si no tiene JSON completo, verificar variables individuales
    if not required_vars['GOOGLE_CREDENTIALS_JSON']:
        individual_vars = {
            'GOOGLE_PROJECT_ID': os.getenv('GOOGLE_PROJECT_ID'),
            'GOOGLE_PRIVATE_KEY': os.getenv('GOOGLE_PRIVATE_KEY'),
            'GOOGLE_CLIENT_EMAIL': os.getenv('GOOGLE_CLIENT_EMAIL'),
        }
        required_vars.update(individual_vars)
    
    missing = [var for var, value in required_vars.items() if not value]
    
    if missing:
        print(f"⚠️  Variables de entorno faltantes: {', '.join(missing)}")
        return {'status': 'error', 'missing': missing}
    
    print("✅ Todas las variables de entorno están configuradas")
    return {'status': 'ok', 'variables': list(required_vars.keys())}

# Cargar automáticamente al importar este módulo
load_env_file()

if __name__ == "__main__":
    # Test para verificar configuración
    print("🔍 Verificando configuración de variables de entorno...")
    result = check_env_variables()
    
    if result['status'] == 'ok':
        print("🎉 Configuración correcta!")
        
        # Test de conexión con Google Sheets
        try:
            from funciones import get_sheet
            ws = get_sheet()
            print(f"📊 Conexión exitosa con Google Sheets: {ws.title}")
        except Exception as e:
            print(f"❌ Error al conectar con Google Sheets: {e}")
    else:
        print("❌ Por favor, configura las variables faltantes en el archivo .env")