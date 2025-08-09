from fpdf import FPDF
import os
from datetime import datetime

def generate_money_order_pdf(order):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', size=12)

    pdf.cell(200, 10, txt=order['shop_url'], ln=True, align='C')
    pdf.cell(200, 10, txt=f"Order: {order['name']}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Customer: {order['customer_name']}", ln=True, align='L')
    pdf.cell(200, 10, txt=f"Address: {order['address1'] or ''} {order['address2'] or ''}", ln=True, align='L')
    pdf.cell(200, 10, txt=f"{order['city'] or ''}, {order['province'] or ''} {order['postal_code'] or ''}", ln=True, align='L')
    pdf.cell(200, 10, txt=f"{order['country'] or ''}", ln=True, align='L')
    pdf.cell(200, 10, txt=f"Amount: {order['total_price']} {order['currency']}", ln=True, align='L')
    pdf.cell(200, 10, txt=f"Date: {order['created_at_utc']}", ln=True, align='L')
    pdf.cell(200, 10, txt="COD - No tracking", ln=True, align='L')
    pdf.cell(200, 20, txt="Signature: ____________________________", ln=True, align='L')

    output_dir = '/tmp' if os.path.exists('/tmp') else '/var/tmp'
    pdf_path = f"{output_dir}/money_order_{order['id']}.pdf"
    pdf.output(pdf_path)
    return pdf_path