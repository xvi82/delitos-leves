"""
Servidor Flask para procesamiento de pagos con Stripe
y generación automática de licencias del Procesador de Delitos Leves.
"""

import os
import threading
from datetime import datetime
from flask import Flask, request, redirect, render_template, jsonify
import stripe
from license_generator import generate_license_hash
from email_sender import send_license_email
from invoice_generator import generate_invoice_pdf, generate_invoice_number, generate_invoice_filename
from database import init_database, save_sale, get_all_sales, get_sales_count, get_total_revenue, export_sales_csv

# ============================================================
# Configuración
# ============================================================

app = Flask(__name__)

# Claves de Stripe (se cargan desde variables de entorno)
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
STRIPE_PRICE_ID = os.environ.get('STRIPE_PRICE_ID')

# URL base del servidor (Railway la proporciona automáticamente)
BASE_URL = os.environ.get('RAILWAY_PUBLIC_DOMAIN', os.environ.get('BASE_URL', 'http://localhost:5000'))
if BASE_URL and not BASE_URL.startswith('http'):
    BASE_URL = f'https://{BASE_URL}'

# Contraseña para el panel de administración
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Inicializar base de datos al arrancar
with app.app_context():
    init_database()


# ============================================================
# Rutas principales
# ============================================================

@app.route('/')
def home():
    """Página de inicio - redirige a la web promocional."""
    return redirect('https://xvi82.github.io/delitos-leves/')


@app.route('/crear-sesion-pago', methods=['POST'])
def crear_sesion_pago():
    """
    Crea una sesión de Stripe Checkout y redirige al usuario.
    Recibe: nombre, hw_id, email, juzgado, numero, partido desde el formulario.
    """
    try:
        nombre = request.form.get('nombre', '').strip()
        hw_id = request.form.get('hw_id', '').strip()
        email = request.form.get('email', '').strip()
        
        # Datos del juzgado (opcionales)
        juzgado = request.form.get('juzgado', '').strip()
        numero = request.form.get('numero', '').strip()
        partido = request.form.get('partido', '').strip()
        
        # Validación básica
        if not nombre or not hw_id or not email:
            return render_template('error.html', 
                mensaje="Faltan datos obligatorios. Por favor, complete todos los campos."), 400
        
        # Crear sesión de Stripe Checkout
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': STRIPE_PRICE_ID,
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'{BASE_URL}/exito?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{BASE_URL}/cancelado',
            customer_email=email,
            metadata={
                'nombre': nombre,
                'hw_id': hw_id,
                'juzgado': juzgado,
                'numero_juzgado': numero,
                'partido_judicial': partido,
            },
            # Configuración adicional para mejor UX
            locale='es',
            billing_address_collection='required',
        )
        
        # Redirigir a Stripe Checkout
        return redirect(session.url, code=303)
        
    except stripe.error.StripeError as e:
        print(f"Error de Stripe: {e}")
        return render_template('error.html', 
            mensaje="Error al procesar el pago. Por favor, inténtelo de nuevo."), 500
    except Exception as e:
        print(f"Error inesperado: {e}")
        return render_template('error.html', 
            mensaje="Ha ocurrido un error. Por favor, inténtelo de nuevo."), 500


@app.route('/exito')
def exito():
    """
    Página de éxito tras el pago.
    Muestra la licencia generada al usuario.
    """
    session_id = request.args.get('session_id')
    
    if not session_id:
        return render_template('error.html', 
            mensaje="Sesión no válida."), 400
    
    try:
        # Recuperar datos de la sesión de Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Verificar que el pago fue exitoso
        if session.payment_status != 'paid':
            return render_template('error.html', 
                mensaje="El pago no se ha completado correctamente."), 400
        
        # Extraer datos del metadata
        nombre = session.metadata.get('nombre', '')
        hw_id = session.metadata.get('hw_id', '')
        email = session.customer_email
        
        # Generar la licencia
        license_key = generate_license_hash(hw_id, nombre)
        
        return render_template('exito.html',
            license_key=license_key,
            nombre=nombre,
            email=email)
            
    except stripe.error.StripeError as e:
        print(f"Error recuperando sesión: {e}")
        return render_template('error.html', 
            mensaje="Error al verificar el pago."), 500


@app.route('/cancelado')
def cancelado():
    """Página cuando el usuario cancela el pago."""
    return render_template('cancelado.html')


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook de Stripe para recibir notificaciones de pago.
    Aquí se envía el email automático con la licencia.
    """
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Verificar la firma del webhook
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        print(f"Payload inválido: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        print(f"Firma inválida: {e}")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Procesar el evento
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Solo procesar si el pago fue exitoso
        if session.payment_status == 'paid':
            handle_successful_payment(session)
    
    return jsonify({'status': 'success'}), 200


def handle_successful_payment(session):
    """
    Procesa un pago exitoso:
    1. Genera la licencia
    2. Genera la factura PDF
    3. Guarda la venta en la base de datos
    4. Envía email al cliente con licencia y factura (en segundo plano)
    """
    try:
        nombre = session.metadata.get('nombre', '')
        hw_id = session.metadata.get('hw_id', '')
        email = session.customer_email
        amount = session.amount_total / 100  # Convertir de céntimos a euros
        currency = session.currency.upper()
        session_id = session.id
        fecha_actual = datetime.now()
        
        # Datos del juzgado (del metadata)
        juzgado = session.metadata.get('juzgado', '')
        numero_juzgado = session.metadata.get('numero_juzgado', '')
        partido_judicial = session.metadata.get('partido_judicial', '')
        
        # Datos adicionales de Stripe
        payment_intent = session.payment_intent if hasattr(session, 'payment_intent') else None
        customer_id = session.customer if hasattr(session, 'customer') else None
        
        # Obtener datos de facturación desde los detalles del cliente
        pais_facturacion = None
        direccion_facturacion = None
        try:
            if payment_intent:
                pi = stripe.PaymentIntent.retrieve(payment_intent)
                if pi.charges and pi.charges.data:
                    billing = pi.charges.data[0].billing_details
                    if billing and billing.address:
                        pais_facturacion = billing.address.country
                        # Construir dirección completa para la factura
                        addr = billing.address
                        direccion_parts = []
                        if addr.line1:
                            direccion_parts.append(addr.line1)
                        if addr.line2:
                            direccion_parts.append(addr.line2)
                        if addr.postal_code or addr.city:
                            city_line = f"{addr.postal_code or ''} {addr.city or ''}".strip()
                            if city_line:
                                direccion_parts.append(city_line)
                        if addr.state:
                            direccion_parts.append(addr.state)
                        direccion_facturacion = ', '.join(direccion_parts) if direccion_parts else None
        except Exception as e:
            print(f"⚠️ No se pudo obtener datos de facturación: {e}")
        
        # Generar licencia
        license_key = generate_license_hash(hw_id, nombre)
        
        # Guardar venta en base de datos
        save_sale(
            nombre=nombre,
            email=email,
            hw_id=hw_id,
            license_key=license_key,
            amount=amount,
            currency=currency,
            stripe_session_id=session_id,
            juzgado=juzgado,
            numero_juzgado=numero_juzgado,
            partido_judicial=partido_judicial,
            stripe_payment_intent=payment_intent,
            stripe_customer_id=customer_id,
            pais_facturacion=pais_facturacion
        )
        
        # Generar número de factura y factura PDF
        numero_factura = generate_invoice_number()
        print(f"📄 Generando factura {numero_factura}...")
        
        try:
            invoice_pdf = generate_invoice_pdf(
                nombre_cliente=nombre,
                email_cliente=email,
                amount_total=amount,
                currency=currency,
                fecha=fecha_actual,
                numero_factura=numero_factura,
                pais_cliente=pais_facturacion,
                direccion_cliente=direccion_facturacion
            )
            invoice_filename = generate_invoice_filename(numero_factura)
            print(f"✅ Factura generada: {invoice_filename} ({len(invoice_pdf)} bytes)")
        except Exception as invoice_error:
            print(f"⚠️ Error generando factura: {invoice_error}")
            invoice_pdf = None
            invoice_filename = None
            numero_factura = None
        
        print(f"📧 Iniciando envío de email a {email}...")
        
        # Enviar email en un thread separado para no bloquear el webhook
        def send_email_async():
            try:
                success = send_license_email(
                    to_email=email,
                    nombre=nombre,
                    hw_id=hw_id,
                    license_key=license_key,
                    invoice_pdf=invoice_pdf,
                    invoice_filename=invoice_filename,
                    invoice_number=numero_factura,
                    amount=amount,
                    fecha=fecha_actual
                )
                if success:
                    print(f"✅ Email con factura enviado correctamente a {email}")
                else:
                    print(f"⚠️ No se pudo enviar email a {email}")
            except Exception as email_error:
                print(f"❌ Error enviando email: {email_error}")
        
        # Iniciar thread para enviar email
        email_thread = threading.Thread(target=send_email_async)
        email_thread.daemon = True
        email_thread.start()
        
        print(f"✅ Licencia generada para {nombre}: {license_key[:8]}...")
        
    except Exception as e:
        print(f"❌ Error procesando pago: {e}")
        # En producción, podrías enviar una alerta o reintentarlo


# ============================================================
# Panel de Administración (protegido por contraseña)
# ============================================================

@app.route('/admin')
def admin_panel():
    """Panel de administración para ver las ventas."""
    password = request.args.get('key', '')
    
    if password != ADMIN_PASSWORD:
        return render_template('error.html', 
            mensaje="Acceso no autorizado."), 401
    
    sales = get_all_sales()
    total_count = get_sales_count()
    total_bruto, total_neto, total_comisiones = get_total_revenue()
    
    return render_template('admin.html',
        sales=sales,
        total_count=total_count,
        total_bruto=total_bruto,
        total_neto=total_neto,
        total_comisiones=total_comisiones)


@app.route('/admin/export')
def export_sales():
    """Exporta las ventas en formato JSON."""
    password = request.args.get('key', '')
    
    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Acceso no autorizado'}), 401
    
    sales = get_all_sales()
    
    # Convertir fechas a string para JSON
    for sale in sales:
        if sale.get('created_at'):
            sale['created_at'] = sale['created_at'].isoformat()
    
    total_bruto, total_neto, total_comisiones = get_total_revenue()
    
    return jsonify({
        'total_ventas': len(sales),
        'total_ingresos_brutos': total_bruto,
        'total_comisiones_stripe': total_comisiones,
        'total_ingresos_netos': total_neto,
        'ventas': sales
    })


@app.route('/admin/export-csv')
def export_sales_csv_route():
    """Exporta las ventas en formato CSV (compatible con Excel/Access)."""
    from flask import Response
    from datetime import datetime
    
    password = request.args.get('key', '')
    
    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Acceso no autorizado'}), 401
    
    csv_content = export_sales_csv()
    
    if not csv_content:
        return jsonify({'error': 'No hay ventas para exportar'}), 404
    
    # Nombre del archivo con fecha
    filename = f"ventas_licencias_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    # Añadir BOM para que Excel reconozca UTF-8
    csv_with_bom = '\ufeff' + csv_content
    
    return Response(
        csv_with_bom,
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )


# ============================================================
# Health check para Railway
# ============================================================

@app.route('/health')
def health():
    """Endpoint de salud para Railway."""
    return jsonify({'status': 'healthy'}), 200


# ============================================================
# Ejecutar servidor
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)

