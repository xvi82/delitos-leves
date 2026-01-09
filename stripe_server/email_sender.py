"""
Módulo para envío de emails con la licencia y factura.
Utiliza Brevo API (HTTP) para enviar emails a cualquier destinatario.
"""

import os
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime

# Configuración de Brevo (desde variables de entorno)
BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'jercilla@gmail.com')
FROM_NAME = os.environ.get('FROM_NAME', 'Procesador de Delitos Leves')


def send_license_email(
    to_email: str, 
    nombre: str, 
    hw_id: str, 
    license_key: str,
    invoice_pdf: bytes = None,
    invoice_filename: str = None,
    invoice_number: str = None,
    amount: float = None,
    fecha: datetime = None
) -> bool:
    """
    Envía un email con la clave de licencia y factura al cliente usando Brevo API.
    
    Args:
        to_email: Dirección de correo del cliente
        nombre: Nombre del cliente
        hw_id: Hardware ID del equipo
        license_key: Clave de licencia generada
        invoice_pdf: Bytes del PDF de la factura (opcional)
        invoice_filename: Nombre del archivo de la factura (opcional)
        invoice_number: Número de factura para mostrar en el email (opcional)
        amount: Importe total de la factura (opcional)
        fecha: Fecha de la factura (opcional)
    
    Returns:
        True si el email se envió correctamente, False en caso contrario
    """
    if not BREVO_API_KEY:
        print("⚠️ BREVO_API_KEY no configurada. Email no enviado.")
        return False
    
    # Preparar sección de factura para el email (si hay factura)
    invoice_section = ""
    if invoice_pdf and invoice_number:
        fecha_str = fecha.strftime("%d/%m/%Y") if fecha else datetime.now().strftime("%d/%m/%Y")
        amount_str = f"{amount:.2f} €" if amount else "Ver factura adjunta"
        
        invoice_section = f"""
        <div class="invoice-box">
            <p style="margin: 0 0 10px 0; color: #666;">📄 Factura adjunta:</p>
            <p style="margin: 0; font-size: 14px;">
                <strong>N° Factura:</strong> {invoice_number}<br>
                <strong>Fecha:</strong> {fecha_str}<br>
                <strong>Importe:</strong> {amount_str}
            </p>
        </div>
        """
    
    # Contenido del email en HTML
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
        .invoice-box {{
            background: #e8f4f8;
            border: 1px solid #b8daff;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
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
        
        {invoice_section}
        
        <div class="steps">
            <strong>Para activar su licencia:</strong>
            <ol>
                <li>Abra el Procesador de Delitos Leves</li>
                <li>En la ventana de activación, localice el campo "Introducir clave de activación"</li>
                <li>Copie y pegue el código de activación en dicho campo</li>
                <li>Pulse el botón "Activar"</li>
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
            <p style="margin: 5px 0 0 0;">Simplemente responda a este correo o contacte a través de <a href="mailto:jercilla@gmail.com">jercilla@gmail.com</a></p>
        </div>
        
        <div class="footer">
            <p>Un saludo,<br><strong>Procesador de Delitos Leves</strong></p>
        </div>
    </div>
</body>
</html>
"""
    
    # Datos para la API de Brevo
    email_data = {
        "sender": {
            "name": FROM_NAME,
            "email": FROM_EMAIL
        },
        "to": [
            {
                "email": to_email,
                "name": nombre
            }
        ],
        "replyTo": {
            "email": "jercilla@gmail.com",
            "name": "Soporte - Procesador de Delitos Leves"
        },
        "subject": "🔑 Su licencia del Procesador de Delitos Leves",
        "htmlContent": html_content
    }
    
    # Añadir factura como adjunto si existe
    if invoice_pdf and invoice_filename:
        # Codificar el PDF en base64 para la API de Brevo
        pdf_base64 = base64.b64encode(invoice_pdf).decode('utf-8')
        
        email_data["attachment"] = [
            {
                "content": pdf_base64,
                "name": invoice_filename
            }
        ]
        
        # Actualizar el asunto para indicar que incluye factura
        email_data["subject"] = "🔑 Su licencia y factura - Procesador de Delitos Leves"
    
    try:
        print(f"📧 Enviando email via Brevo a {to_email}...")
        if invoice_pdf:
            print(f"📎 Adjuntando factura: {invoice_filename}")
        
        # Preparar la petición HTTP
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = json.dumps(email_data).encode('utf-8')
        
        request = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        # Enviar la petición
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Email enviado correctamente. MessageId: {result.get('messageId', 'N/A')}")
            return True
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'Sin detalles'
        print(f"❌ Error HTTP {e.code}: {error_body}")
        return False
    except urllib.error.URLError as e:
        print(f"❌ Error de conexión: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Error enviando email: {type(e).__name__}: {e}")
        return False
