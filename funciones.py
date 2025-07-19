# funciones.py
import unicodedata
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
import json

def normalize(text: str) -> str:
    """
    Normaliza una cadena: quita acentos, convierte a minúsculas y recorta espacios.
    """
    text = unicodedata.normalize('NFD', text or "")
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    return text.strip().lower()

def update_dataframe_json(stored_json: str, metric: str, value: str, excel_path: str = 'data.xlsx') -> str:
    """
    Dado un JSON serializado de DataFrame, la métrica y el valor,
    actualiza el DataFrame: crea columna si es nueva, añade fila con el valor,
    guarda todo a un archivo Excel, y devuelve el DataFrame re-serializado a JSON.
    """
    # Reconstruye DataFrame
    df = pd.read_json(stored_json, orient='split')

    # Formateo: primera letra mayúscula y resto minúsculas
    m_fmt = metric.strip().title()
    v_fmt = value.strip().title()

    # Si la columna no existe, la creamos con NaN
    if m_fmt not in df.columns:
        df[m_fmt] = pd.NA

    # Prepara la fila nueva
    nueva_fila = {col: (v_fmt if col == m_fmt else pd.NA) for col in df.columns}
    df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)

    # Guarda en Excel
    df.to_excel(excel_path, index=False)

    # Retorna JSON actualizado
    return df.to_json(date_format='iso', orient='split')


# Configuración usando variables de entorno
SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "1Rl88ZQO9S5ye7AlzTd2_ooToH8u6ZLgrRtftYbBpeck")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_credentials():
    """
    Obtiene las credenciales de Google desde variables de entorno.
    """
    # Opción 1: JSON completo en una variable
    credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if credentials_json:
        try:
            credentials_info = json.loads(credentials_json)
            return Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
        except json.JSONDecodeError:
            raise ValueError("Error al decodificar GOOGLE_CREDENTIALS_JSON")
    
    # Opción 2: Variables individuales (más seguro para algunos servicios)
    credentials_dict = {
        "type": os.getenv("GOOGLE_ACCOUNT_TYPE", "service_account"),
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),
        "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("GOOGLE_PRIVATE_KEY", "").replace('\\n', '\n'),
        "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL")
    }
    
    # Verificar que tenemos las variables esenciales
    required_vars = ["project_id", "private_key", "client_email"]
    missing_vars = [var for var in required_vars if not credentials_dict[var]]
    
    if missing_vars:
        raise ValueError(f"Faltan variables de entorno: {', '.join([f'GOOGLE_{var.upper()}' for var in missing_vars])}")
    
    return Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)


def get_sheet():
    """
    Autoriza con gspread y devuelve el worksheet principal.
    """
    creds = get_credentials()
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.sheet1
    return worksheet


def append_to_sheet(metric: str, value: str):
    """
    Inserta el valor en la columna de la métrica correspondiente.
    - Si la columna no existe, la crea en la primera fila.
    - Busca la siguiente fila vacía debajo de esa columna y escribe el valor.
    """
    ws = get_sheet()
    # Formateo Título
    m_fmt = metric.strip().title()
    v_fmt = value.strip().title()

    # Leer encabezados (fila 1)
    headers = ws.row_values(1)
    if m_fmt in headers:
        col = headers.index(m_fmt) + 1
    else:
        # nueva columna al final
        col = len(headers) + 1
        ws.update_cell(1, col, m_fmt)

    # Buscar la siguiente fila vacía debajo de encabezado
    row = 2
    while True:
        cell = ws.cell(row, col).value
        if not cell:
            break
        row += 1

    # Escribir el valor
    ws.update_cell(row, col, v_fmt) 