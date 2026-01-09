"""
Generador de Facturas PDF para el Procesador de Delitos Leves.
Genera facturas profesionales con todos los requisitos legales españoles.
"""

import os
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# ============================================================
# Configuración del Vendedor (datos fiscales)
# ============================================================

SELLER_NAME = os.environ.get('SELLER_NAME', 'Javier Ercilla Garcia')
SELLER_NIF = os.environ.get('SELLER_NIF', '75775047Y')
SELLER_ADDRESS = os.environ.get('SELLER_ADDRESS', 'Avda. Federico Garcia Lorca 3, 1-D-Dcha')
SELLER_CITY = os.environ.get('SELLER_CITY', 'Las Palmas de Gran Canaria, 35011')
SELLER_EMAIL = os.environ.get('SELLER_EMAIL', 'jercilla@gmail.com')

# IVA aplicable (21% en España para software)
IVA_PERCENT = float(os.environ.get('IVA_PERCENT', '21'))


class InvoicePDF(FPDF):
    """Clase personalizada para generar facturas PDF."""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        """Cabecera de la factura."""
        # Color de fondo del header
        self.set_fill_color(44, 62, 80)  # Azul oscuro profesional
        self.rect(0, 0, 210, 45, 'F')
        
        # Título
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(255, 255, 255)
        self.set_xy(15, 15)
        self.cell(0, 10, 'FACTURA', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Subtítulo
        self.set_font('Helvetica', '', 11)
        self.set_xy(15, 28)
        self.cell(0, 6, 'Procesador de Delitos Leves', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Resetear color de texto
        self.set_text_color(0, 0, 0)
        self.ln(25)

    def footer(self):
        """Pie de página."""
        self.set_y(-25)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, f'Factura generada electronicamente - {SELLER_NAME}', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 5, f'Email: {SELLER_EMAIL}', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')


def generate_invoice_number(sale_id: int = None) -> str:
    """
    Genera un número de factura único.
    Formato: YYYY-MMDD-XXXX (Año-MesDía-ID)
    """
    now = datetime.now()
    year = now.strftime('%Y')
    month_day = now.strftime('%m%d')
    
    if sale_id:
        return f"{year}-{month_day}-{sale_id:04d}"
    else:
        # Si no hay ID, usamos timestamp
        timestamp = now.strftime('%H%M%S')
        return f"{year}-{month_day}-{timestamp}"


def generate_invoice_pdf(
    nombre_cliente: str,
    email_cliente: str,
    amount_total: float,
    currency: str = 'EUR',
    fecha: datetime = None,
    numero_factura: str = None,
    pais_cliente: str = None,
    direccion_cliente: str = None,
    nif_cliente: str = None,
    sale_id: int = None
) -> bytes:
    """
    Genera una factura PDF completa.
    
    Args:
        nombre_cliente: Nombre completo del cliente
        email_cliente: Email del cliente
        amount_total: Importe TOTAL cobrado (incluye IVA)
        currency: Moneda (EUR por defecto)
        fecha: Fecha de la factura (hoy si no se especifica)
        numero_factura: Número de factura (se genera si no se especifica)
        pais_cliente: País del cliente (opcional)
        direccion_cliente: Dirección del cliente (opcional)
        nif_cliente: NIF/CIF del cliente (opcional)
        sale_id: ID de la venta en la base de datos (para número factura)
    
    Returns:
        bytes: Contenido del PDF
    """
    if fecha is None:
        fecha = datetime.now()
    
    if numero_factura is None:
        numero_factura = generate_invoice_number(sale_id)
    
    # Calcular desglose de precios
    # El amount_total es lo que cobró Stripe (IVA incluido)
    # Base imponible = Total / (1 + IVA/100)
    base_imponible = round(amount_total / (1 + IVA_PERCENT / 100), 2)
    iva_amount = round(amount_total - base_imponible, 2)
    
    # Crear PDF
    pdf = InvoicePDF()
    pdf.add_page()
    
    # ============================================================
    # Información de la factura (derecha superior)
    # ============================================================
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_xy(120, 55)
    pdf.cell(75, 7, f'Factura N: {numero_factura}', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_x(120)
    pdf.cell(75, 6, f'Fecha: {fecha.strftime("%d/%m/%Y")}', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    
    # ============================================================
    # Datos del Vendedor
    # ============================================================
    pdf.set_xy(15, 55)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(90, 7, 'DATOS DEL VENDEDOR', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    
    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(15)
    pdf.cell(90, 5, SELLER_NAME, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(15)
    pdf.cell(90, 5, f'NIF: {SELLER_NIF}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(15)
    pdf.multi_cell(90, 5, SELLER_ADDRESS)
    pdf.set_x(15)
    pdf.cell(90, 5, SELLER_CITY, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(15)
    pdf.cell(90, 5, f'Email: {SELLER_EMAIL}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # ============================================================
    # Datos del Cliente
    # ============================================================
    pdf.ln(5)
    pdf.set_x(15)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(90, 7, 'DATOS DEL CLIENTE', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    
    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(15)
    pdf.cell(90, 5, nombre_cliente, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    if nif_cliente:
        pdf.set_x(15)
        pdf.cell(90, 5, f'NIF/CIF: {nif_cliente}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    if direccion_cliente:
        pdf.set_x(15)
        pdf.multi_cell(90, 5, direccion_cliente)
    
    if pais_cliente:
        pdf.set_x(15)
        pdf.cell(90, 5, f'Pais: {pais_cliente}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_x(15)
    pdf.cell(90, 5, f'Email: {email_cliente}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # ============================================================
    # Tabla de Conceptos
    # ============================================================
    pdf.ln(15)
    
    # Cabecera de la tabla
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 10)
    
    # Columnas: Concepto | Cantidad | Precio Unit. | Total
    pdf.set_x(15)
    pdf.cell(95, 10, 'CONCEPTO', 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C', fill=True)
    pdf.cell(25, 10, 'CANT.', 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C', fill=True)
    pdf.cell(30, 10, 'PRECIO', 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C', fill=True)
    pdf.cell(30, 10, 'TOTAL', 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C', fill=True)
    
    # Contenido de la tabla
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 9)
    
    # Fila del producto
    pdf.set_x(15)
    pdf.cell(95, 10, 'Licencia Procesador de Delitos Leves', 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')
    pdf.cell(25, 10, '1', 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')
    pdf.cell(30, 10, f'{base_imponible:.2f} {currency}', 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(30, 10, f'{base_imponible:.2f} {currency}', 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    
    # ============================================================
    # Resumen de Totales
    # ============================================================
    pdf.ln(5)
    
    # Alinear a la derecha
    x_label = 120
    width_label = 45
    width_value = 30
    
    # Base imponible
    pdf.set_font('Helvetica', '', 10)
    pdf.set_x(x_label)
    pdf.cell(width_label, 8, 'Base Imponible:', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(width_value, 8, f'{base_imponible:.2f} {currency}', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    
    # IVA
    pdf.set_x(x_label)
    pdf.cell(width_label, 8, f'IVA ({IVA_PERCENT:.0f}%):', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(width_value, 8, f'{iva_amount:.2f} {currency}', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    
    # Línea separadora
    pdf.set_x(x_label)
    pdf.line(x_label, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(2)
    
    # Total
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_x(x_label)
    pdf.cell(width_label, 10, 'TOTAL:', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(width_value, 10, f'{amount_total:.2f} {currency}', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    
    # ============================================================
    # Notas y Forma de Pago
    # ============================================================
    pdf.ln(15)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_x(15)
    pdf.cell(0, 6, 'INFORMACION ADICIONAL', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Formatear fecha en español
    meses = {
        'January': 'enero', 'February': 'febrero', 'March': 'marzo',
        'April': 'abril', 'May': 'mayo', 'June': 'junio',
        'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
        'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
    }
    fecha_str = fecha.strftime("%d de %B de %Y")
    for eng, esp in meses.items():
        fecha_str = fecha_str.replace(eng, esp)
    
    pdf.set_font('Helvetica', '', 8)
    pdf.set_x(15)
    pdf.multi_cell(180, 4, 
        f'Forma de pago: Tarjeta de credito/debito (Stripe)\n'
        f'La licencia adquirida es de uso personal e intransferible.\n'
        f'Esta factura se ha generado electronicamente y es valida sin firma.\n'
        f'Factura emitida el {fecha_str}.'
    )
    
    # ============================================================
    # Generar bytes del PDF
    # ============================================================
    return bytes(pdf.output())


def generate_invoice_filename(numero_factura: str) -> str:
    """Genera el nombre del archivo de la factura."""
    # Limpiar caracteres no válidos para nombres de archivo
    safe_number = numero_factura.replace('/', '-').replace('\\', '-')
    return f"Factura_{safe_number}.pdf"


# ============================================================
# Función de prueba
# ============================================================

if __name__ == '__main__':
    # Generar factura de prueba
    pdf_bytes = generate_invoice_pdf(
        nombre_cliente="Juan Garcia Lopez",
        email_cliente="juan@ejemplo.com",
        amount_total=300.00,  # Precio con IVA incluido (Base: 247.93 + IVA: 52.07)
        currency="EUR",
        pais_cliente="Espana",
        sale_id=1
    )
    
    # Guardar archivo de prueba
    with open("factura_prueba.pdf", "wb") as f:
        f.write(pdf_bytes)
    
    print("Factura de prueba generada: factura_prueba.pdf")
    print(f"Tamano: {len(pdf_bytes)} bytes")
