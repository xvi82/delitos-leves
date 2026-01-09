"""
Módulo para gestión de base de datos PostgreSQL.
Guarda el registro de todas las ventas de licencias.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# URL de conexión a PostgreSQL (proporcionada por Railway)
DATABASE_URL = os.environ.get('DATABASE_URL', '')


def get_connection():
    """Obtiene una conexión a la base de datos."""
    if not DATABASE_URL:
        print("⚠️ DATABASE_URL no configurada")
        return None
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return None


def init_database():
    """Crea las tablas necesarias si no existen."""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Crear tabla de ventas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                hw_id VARCHAR(100) NOT NULL,
                license_key VARCHAR(50) NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                currency VARCHAR(10) DEFAULT 'EUR',
                stripe_session_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                -- Datos del juzgado
                juzgado VARCHAR(100),
                numero_juzgado VARCHAR(20),
                partido_judicial VARCHAR(100),
                -- Datos adicionales de Stripe
                stripe_payment_intent VARCHAR(255),
                stripe_customer_id VARCHAR(255),
                pais_facturacion VARCHAR(50)
            )
        """)
        
        # Añadir columnas si no existen (para migraciones)
        columnas_nuevas = [
            ("juzgado", "VARCHAR(100)"),
            ("numero_juzgado", "VARCHAR(20)"),
            ("partido_judicial", "VARCHAR(100)"),
            ("stripe_payment_intent", "VARCHAR(255)"),
            ("stripe_customer_id", "VARCHAR(255)"),
            ("pais_facturacion", "VARCHAR(50)")
        ]
        
        for columna, tipo in columnas_nuevas:
            try:
                cursor.execute(f"""
                    ALTER TABLE ventas ADD COLUMN IF NOT EXISTS {columna} {tipo}
                """)
            except Exception:
                pass  # La columna ya existe
        
        # Crear índice para búsquedas rápidas
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ventas_email ON ventas(email)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ventas_hw_id ON ventas(hw_id)
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False


def save_sale(nombre: str, email: str, hw_id: str, license_key: str, 
              amount: float, currency: str = 'EUR', stripe_session_id: str = None,
              juzgado: str = None, numero_juzgado: str = None, partido_judicial: str = None,
              stripe_payment_intent: str = None, stripe_customer_id: str = None,
              pais_facturacion: str = None) -> bool:
    """
    Guarda una venta en la base de datos.
    
    Returns:
        True si se guardó correctamente, False en caso contrario
    """
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ventas (
                nombre, email, hw_id, license_key, amount, currency, stripe_session_id,
                juzgado, numero_juzgado, partido_judicial,
                stripe_payment_intent, stripe_customer_id, pais_facturacion
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (nombre, email, hw_id, license_key, amount, currency, stripe_session_id,
              juzgado, numero_juzgado, partido_judicial,
              stripe_payment_intent, stripe_customer_id, pais_facturacion))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"💾 Venta guardada: {nombre} - {email}")
        return True
        
    except Exception as e:
        print(f"❌ Error guardando venta: {e}")
        return False


def get_all_sales() -> list:
    """
    Obtiene todas las ventas ordenadas por fecha (más recientes primero).
    
    Returns:
        Lista de diccionarios con los datos de las ventas
    """
    conn = get_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, nombre, email, hw_id, license_key, amount, currency, 
                   stripe_session_id, created_at,
                   juzgado, numero_juzgado, partido_judicial,
                   stripe_payment_intent, stripe_customer_id, pais_facturacion
            FROM ventas
            ORDER BY created_at DESC
        """)
        
        sales = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [dict(sale) for sale in sales]
        
    except Exception as e:
        print(f"❌ Error obteniendo ventas: {e}")
        return []


def get_sales_count() -> int:
    """Obtiene el número total de ventas."""
    conn = get_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ventas")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except:
        return 0


def get_total_revenue() -> tuple:
    """
    Obtiene el total de ingresos brutos y netos.
    Comisión Stripe España: 1,5% + 0,25€ por transacción.
    
    Returns:
        Tupla (ingresos_brutos, ingresos_netos, total_comisiones)
    """
    conn = get_connection()
    if not conn:
        return 0.0, 0.0, 0.0
    
    try:
        cursor = conn.cursor()
        # Obtener suma total y número de transacciones
        cursor.execute("SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM ventas")
        result = cursor.fetchone()
        total_bruto = float(result[0])
        num_ventas = int(result[1])
        cursor.close()
        conn.close()
        
        # Calcular comisiones: 1,5% + 0,25€ por transacción
        total_comisiones = (total_bruto * 0.015) + (num_ventas * 0.25)
        total_neto = total_bruto - total_comisiones
        
        return total_bruto, total_neto, total_comisiones
    except:
        return 0.0, 0.0, 0.0


def export_sales_csv() -> str:
    """
    Exporta todas las ventas en formato CSV (compatible con Excel/Access).
    
    Returns:
        String con el contenido CSV
    """
    import csv
    import io
    
    sales = get_all_sales()
    
    if not sales:
        return ""
    
    # Crear el CSV en memoria
    output = io.StringIO()
    
    # Cabeceras en español para Excel
    fieldnames = [
        'ID', 'Fecha', 'Nombre', 'Email', 'Hardware_ID', 'Licencia',
        'Importe_Bruto', 'Comision_Stripe', 'Importe_Neto', 'Moneda',
        'Juzgado', 'Numero', 'Partido_Judicial',
        'Stripe_Session', 'Stripe_Payment', 'Stripe_Customer', 'Pais'
    ]
    
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(fieldnames)
    
    for sale in sales:
        fecha = sale.get('created_at')
        if fecha:
            fecha = fecha.strftime('%d/%m/%Y %H:%M')
        
        # Calcular comisión Stripe: 1,5% + 0,25€
        importe_bruto = float(sale.get('amount', 0))
        comision = round(importe_bruto * 0.015 + 0.25, 2)
        importe_neto = round(importe_bruto - comision, 2)
        
        writer.writerow([
            sale.get('id', ''),
            fecha or '',
            sale.get('nombre', ''),
            sale.get('email', ''),
            sale.get('hw_id', ''),
            sale.get('license_key', ''),
            str(importe_bruto).replace('.', ','),  # Formato español
            str(comision).replace('.', ','),
            str(importe_neto).replace('.', ','),
            sale.get('currency', 'EUR'),
            sale.get('juzgado', '') or '',
            sale.get('numero_juzgado', '') or '',
            sale.get('partido_judicial', '') or '',
            sale.get('stripe_session_id', '') or '',
            sale.get('stripe_payment_intent', '') or '',
            sale.get('stripe_customer_id', '') or '',
            sale.get('pais_facturacion', '') or ''
        ])
    
    return output.getvalue()




