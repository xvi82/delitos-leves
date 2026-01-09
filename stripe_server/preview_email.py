"""
Script para previsualizar el email de licencia en el navegador.
Ejecutar: python preview_email.py
"""

import webbrowser
import tempfile
import os

# Datos de ejemplo para la previsualización
nombre = "Javier Ercilla García"
hw_id = "AD112EE8-83B6-4049-AF0B-7DD5AE9B9011"
license_key = "B52C8DF7925F0E68D1042C94"

# Contenido del email en HTML (copia del email_sender.py)
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 580px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .header {{
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 2px solid #2c3e50;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-size: 24px;
        }}
        .license-box {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #2c3e50;
            border-radius: 10px;
            padding: 25px;
            text-align: center;
            margin: 25px 0;
        }}
        .license-key {{
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            letter-spacing: 2px;
            word-break: break-all;
        }}
        .steps {{
            background: #f8f9fa;
            border-left: 4px solid #2c3e50;
            padding: 15px 20px;
            margin: 20px 0;
        }}
        .steps ol {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .info {{
            font-size: 14px;
            color: #666;
            margin-top: 20px;
        }}
        .contact {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #555;
        }}
        .footer {{
            text-align: center;
            padding-top: 25px;
            margin-top: 25px;
            border-top: 1px solid #eee;
            color: #888;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚖️ Procesador de Delitos Leves</h1>
        </div>
        
        <p>Estimado/a <strong>{nombre}</strong>,</p>
        
        <p>Gracias por adquirir la licencia del Procesador de Delitos Leves.</p>
        
        <div class="license-box">
            <p style="margin: 0 0 10px 0; color: #666;">Su código de activación es:</p>
            <div class="license-key">{license_key}</div>
        </div>
        
        <div class="steps">
            <strong>Para activar su licencia:</strong>
            <ol>
                <li>Abra el Procesador de Delitos Leves</li>
                <li>Vaya a la ventana de Activación</li>
                <li>Introduzca el código anterior</li>
            </ol>
        </div>
        
        <div class="info">
            <p><strong>Este código está vinculado a:</strong></p>
            <ul>
                <li>Nombre: {nombre}</li>
                <li>Equipo: <code>{hw_id}</code></li>
            </ul>
        </div>
        
        <div class="contact">
            <p style="margin: 0;"><strong>¿Tiene alguna duda o problema?</strong></p>
            <p style="margin: 5px 0 0 0;">Escríbanos a: <a href="mailto:jercilla@gmail.com">jercilla@gmail.com</a></p>
        </div>
        
        <div class="footer">
            <p>Un saludo,<br><strong>Procesador de Delitos Leves</strong></p>
        </div>
    </div>
</body>
</html>
"""

# Guardar en archivo temporal y abrir en navegador
temp_file = os.path.join(tempfile.gettempdir(), "email_preview.html")
with open(temp_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print("Abriendo previsualizacion del email...")
print(f"Archivo: {temp_file}")
webbrowser.open(f"file://{temp_file}")

