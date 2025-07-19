import dash
from dash import html, dcc, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import os
import json

# Cargar variables de entorno
import load_env  # Esto cargará automáticamente las variables
from funciones import append_to_sheet, get_sheet, normalize

external_stylesheets = ['assets/styles.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# Configuración de usuarios desde variables de entorno
def get_user_credentials():
    """
    Obtiene las credenciales de usuario desde variables de entorno
    """
    try:
        # Opción 1: JSON con usuarios y contraseñas
        users_json = os.getenv('APP_USERS_JSON')
        if users_json:
            return json.loads(users_json)
        
        # Opción 2: Variables individuales (fallback)
        users_str = os.getenv('APP_USERS', 'Usuario1,Usuario2,Usuario3')
        passwords_str = os.getenv('APP_PASSWORDS', 'Contraseña1,Contraseña2,Contraseña3')
        
        users = [u.strip() for u in users_str.split(',')]
        passwords = [p.strip() for p in passwords_str.split(',')]
        
        return [users, passwords]
        
    except Exception as e:
        print(f"Error al cargar credenciales: {e}")
        # Valores por defecto solo para desarrollo
        return [
            ['demo', 'test', 'admin'],
            ['demo123', 'test123', 'admin123']
        ]

# Cargar credenciales
ACCESOS = get_user_credentials()

app.index_string = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {%css%}
    <title>App Celular</title>
  </head>
  <body>
    {%app_entry%}
    <footer>
      {%config%}
      {%scripts%}
      {%renderer%}
    </footer>
  </body>
</html>
"""

app.layout = html.Div([

    # Splash
    html.Div(
        id='page-splash', className='phone-container',
        style={'display':'flex','flexDirection':'column'},
        children=[
            html.Div("Bienvenido", className='welcome-text'),
            dcc.Interval(id='splash-interval', interval=5000, n_intervals=0, max_intervals=1)
        ]
    ),

    # Login
    html.Div(
        id='page-login', className='phone-container',
        style={'display':'none'},
        children=[
            html.Div(className='input-container', children=[
                html.Div("Nombre de Usuario", className='input-label'),
                dcc.Input(id='username', type='text', className='input-box'),
                html.Div("Contraseña", className='input-label'),
                dcc.Input(id='password', type='password', className='input-box'),
            ]),
            html.Button("Acceder", id='login-button', className='login-button'),
            # Mensaje de error de login
            html.Div(id='login-error', style={'color':'red','margin-top':'10px','display':'none'})
        ]
    ),

    # Home
    html.Div(
        id='page-home', className='phone-container',
        style={'display':'none'},
        children=[
            html.Div(className='menu-icon', children=[
                html.Div(className='bar'), html.Div(className='bar'), html.Div(className='bar')
            ]),
            html.Button(id='add-button', className='add-button', children=[
                html.Div(className='plus horizontal'),
                html.Div(className='plus vertical')
            ])
        ]
    ),

    # Add
    html.Div(
        id='page-add', className='phone-container',
        style={'display':'none'},
        children=[
            html.Div(className='menu-icon', children=[
                html.Div(className='bar'), html.Div(className='bar'), html.Div(className='bar')
            ]),
            html.Div(className='input-container', children=[
                html.Div("Métrica", className='input-label'),
                dcc.Input(id='metrica', type='text', className='input-box'),
                html.Div(className='input-label-check', children=[
                    html.Span("Verifique la Métrica"),
                    html.Img(id='check-icon-metrica', src=app.get_asset_url('verde.png'), className='check-icon')
                ]),
                dcc.Input(id='verificar-metrica', type='text', className='input-box'),
                html.Div("Valores", className='input-label'),
                dcc.Input(id='valores', type='text', className='input-box'),
                html.Div(className='input-label-check', children=[
                    html.Span("Verifique los Valores"),
                    html.Img(id='check-icon-valores', src=app.get_asset_url('verde.png'), className='check-icon')
                ]),
                dcc.Input(id='verificar-valores', type='text', className='input-box'),
            ]),
            html.Button("Guardar", id='guardar-button', className='save-button'),
            html.Button(
                html.Img(
                    src=app.get_asset_url('atras.png'),
                    style={'width': '40px', 'height': 'auto'}
                ),
                id='back-button',
                className='arrow-left',
                n_clicks=0
            ),
            html.Div([
                html.Img(src=app.get_asset_url('verde.png'),
                         style={'width':'48px','margin-bottom':'8px'}),
                html.Div("Se ha Guardado", style={'color':'white','fontSize':'18px'})
            ], id='save-modal', style={'display':'none'}),
            # Modal de error
            html.Div([
                html.Img(src=app.get_asset_url('rojo.png'),
                         style={'width':'48px','margin-bottom':'8px'}),
                html.Div("Error al Guardar", style={'color':'white','fontSize':'18px'})
            ], id='error-modal', style={'display':'none'}),
            dcc.Interval(id='modal-interval', interval=5000, n_intervals=0, disabled=True, max_intervals=1)
        ]
    ),

])

# Navegación única entre pantallas
@app.callback(
    Output('page-splash','style'),
    Output('page-login','style'),
    Output('page-home','style'),
    Output('page-add','style'),
    Output('login-error','children'),
    Output('login-error','style'),
    Input('splash-interval','n_intervals'),
    Input('login-button','n_clicks'),
    Input('add-button','n_clicks'),
    Input('back-button','n_clicks'),
    State('username','value'),
    State('password','value')
)
def navigate(splash_n, login_n, add_n, back_n, usr, pwd):
    ctx = callback_context
    if not ctx.triggered:
        # Inicio
        return {'display':'flex'},{'display':'none'},{'display':'none'},{'display':'none'},'',{'display':'none'}
    trig = ctx.triggered[0]['prop_id'].split('.')[0]

    # Splash termina → Login
    if trig == 'splash-interval':
        return {'display':'none'},{'display':'flex'},{'display':'none'},{'display':'none'},'',{'display':'none'}

    # Login → Home solo si credenciales correctas
    if trig == 'login-button' and login_n:
        if not usr or not pwd:
            return no_update, {'display':'flex'},{'display':'none'},{'display':'none'},'Por favor, complete todos los campos',{'display':'block'}
        
        # Compara usr/pwd contra ACCESOS
        users, pwds = ACCESOS
        if usr in users:
            idx = users.index(usr)
            if pwd == pwds[idx]:
                return {'display':'none'},{'display':'none'},{'display':'flex'},{'display':'none'},'',{'display':'none'}
        
        # Credenciales incorrectas
        return no_update, {'display':'flex'},{'display':'none'},{'display':'none'},'Usuario o contraseña incorrectos',{'display':'block'}

    # Home → Add
    if trig == 'add-button' and add_n:
        return {'display':'none'},{'display':'none'},{'display':'none'},{'display':'flex'},'',{'display':'none'}

    # Add → Home
    if trig == 'back-button' and back_n:
        return {'display':'none'},{'display':'none'},{'display':'flex'},{'display':'none'},'',{'display':'none'}

    # Fallback sin cambios
    return no_update, no_update, no_update, no_update, no_update, no_update

# Checks de validación
@app.callback(Output('check-icon-metrica','style'),
              Input('metrica','value'), Input('verificar-metrica','value'))
def show_check_metrica(m, vm):
    if not m or not vm: return {'display':'none'}
    return {'display':'inline-block'} if normalize(m)==normalize(vm) else {'display':'none'}

@app.callback(Output('check-icon-valores','style'),
              Input('valores','value'), Input('verificar-valores','value'))
def show_check_valores(v, vv):
    if not v or not vv: return {'display':'none'}
    return {'display':'inline-block'} if normalize(v)==normalize(vv) else {'display':'none'}

@app.callback(Output('guardar-button','style'),
              Input('metrica','value'), Input('verificar-metrica','value'),
              Input('valores','value'), Input('verificar-valores','value'))
def toggle_save_button(m, vm, v, vv):
    ok_m = bool(m and vm and normalize(m)==normalize(vm))
    ok_v = bool(v and vv and normalize(v)==normalize(vv))
    return {'display':'inline-block'} if ok_m and ok_v else {'display':'none'}

# Guardado y modal
@app.callback(
    Output('save-modal','style'),
    Output('error-modal','style'),
    Output('modal-interval','disabled'),
    Output('modal-interval','n_intervals'),
    Input('guardar-button','n_clicks'),
    Input('modal-interval','n_intervals'),
    State('metrica','value'),
    State('valores','value')
)
def handle_save_and_hide(save_n, interval_n, metric, value):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trig = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trig=='guardar-button' and save_n:
        try:
            append_to_sheet(metric, value)
            return {'display':'flex'}, {'display':'none'}, False, 0
        except Exception as e:
            print(f"Error al guardar: {e}")
            return {'display':'none'}, {'display':'flex'}, False, 0
    
    if trig=='modal-interval':
        return {'display':'none'}, {'display':'none'}, True, dash.no_update
    
    raise PreventUpdate

# Verificación inicial de configuración
def check_app_config():
    """Verifica que la aplicación esté correctamente configurada"""
    try:
        # Verificar conexión con Google Sheets
        ws = get_sheet()
        print(f"✅ Conexión exitosa con Google Sheets: {ws.title}")
        return True
    except Exception as e:
        print(f"❌ Error de configuración: {e}")
        print("💡 Verifica tus variables de entorno en el archivo .env")
        return False

if __name__ == '__main__':
    print("🚀 Iniciando aplicación...")
    
    # Verificar configuración antes de iniciar
    if check_app_config():
        print("✅ Configuración correcta. Iniciando servidor...")
        app.run_server(debug=os.getenv('DASH_DEBUG', 'True').lower() == 'true')
    else:
        print("❌ Error en la configuración. Revisa las variables de entorno.")
        print("📖 Consulta el archivo README.md para instrucciones de configuración.")