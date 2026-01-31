from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import io


def generate_invoice_pdf(invoice):
    """Generate invoice PDF and return as bytes"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=30,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=12,
    )
    
    # Title
    elements.append(Paragraph("RentEase - Rental Management System", title_style))
    elements.append(Spacer(1, 12))
    
    # Invoice Header
    header_data = [
        ['INVOICE', ''],
        [f'Invoice #: {invoice.invoice_number}', ''],
        [f'Date: {invoice.created_at.strftime("%b %d, %Y")}', ''],
        [f'Status: {invoice.get_status_display()}', ''],
    ]
    header_table = Table(header_data, colWidths=[4*inch, 2*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 16),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#0d6efd')),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Customer Details
    elements.append(Paragraph("Bill To:", heading_style))
    customer_info = f"""
    <b>{invoice.order.customer.company_name}</b><br/>
    {invoice.order.customer.username}<br/>
    Email: {invoice.order.customer.email}<br/>
    GSTIN: {invoice.order.customer.gstin}<br/>
    {invoice.order.delivery_address}<br/>
    {invoice.order.delivery_city}, {invoice.order.delivery_state} - {invoice.order.delivery_pincode}
    """
    elements.append(Paragraph(customer_info, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Order Details
    elements.append(Paragraph("Order Details:", heading_style))
    order_info = f"""
    Order #: {invoice.order.order_number}<br/>
    Order Date: {invoice.order.created_at.strftime("%b %d, %Y")}<br/>
    Order Status: {invoice.order.get_status_display()}
    """
    elements.append(Paragraph(order_info, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Items Table
    elements.append(Paragraph("Rental Items:", heading_style))
    
    items_data = [['Item', 'Rental Period', 'Qty', 'Rate', 'Amount']]
    for line in invoice.order.lines.all():
        period = f"{line.start_date.strftime('%b %d, %Y')} to {line.end_date.strftime('%b %d, %Y')}"
        items_data.append([
            line.product.name,
            period,
            str(line.quantity),
            f'Rs. {line.unit_price}',
            f'Rs. {line.get_total()}'
        ])
    
    items_table = Table(items_data, colWidths=[2.2*inch, 1.8*inch, 0.5*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))
    
    # Totals
    totals_data = [
        ['Subtotal:', f'Rs. {invoice.subtotal}'],
        [f'GST ({invoice.tax_rate}%):', f'Rs. {invoice.tax_amount}'],
        ['Security Deposit:', f'Rs. {invoice.security_deposit}'],
    ]
    
    if invoice.late_fee:
        totals_data.append(['Late Fee:', f'Rs. {invoice.late_fee}'])
    
    totals_data.extend([
        ['Total Amount:', f'Rs. {invoice.total_amount}'],
        ['Amount Paid:', f'Rs. {invoice.amount_paid}'],
        ['Balance Due:', f'Rs. {invoice.get_balance()}'],
    ])
    
    totals_table = Table(totals_data, colWidths=[4.2*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -3), (-1, -3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -3), (-1, -3), 12),
        ('BACKGROUND', (0, -3), (-1, -3), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, -3), (-1, -3), colors.whitesmoke),
        ('LINEABOVE', (0, -3), (-1, -3), 2, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 30))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph("Thank you for your business!", footer_style))
    elements.append(Paragraph("For queries: info@rentease.com | +91 1234567890", footer_style))
    
    # Build PDF
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def send_payment_confirmation_email(invoice):
    """Send payment confirmation email with invoice attachment"""
    try:
        customer = invoice.order.customer
        print(f"[EMAIL] Preparing to send email to: {customer.email}")
        
        # Get rental period details
        rental_items = []
        for line in invoice.order.lines.all():
            rental_items.append({
                'product': line.product.name,
                'quantity': line.quantity,
                'start_date': line.start_date.strftime('%B %d, %Y at %I:%M %p'),
                'end_date': line.end_date.strftime('%B %d, %Y at %I:%M %p'),
                'amount': line.get_total(),
            })
        
        print(f"[EMAIL] Found {len(rental_items)} rental items")
        
        # Render email template
        email_subject = f'Payment Successful - Invoice {invoice.invoice_number}'
        email_body = render_to_string('website/email/payment_confirmation.html', {
            'customer': customer,
            'invoice': invoice,
            'rental_items': rental_items,
        })
        
        print(f"[EMAIL] Email template rendered successfully")
        
        # Create email
        email = EmailMessage(
            subject=email_subject,
            body=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer.email],
        )
        email.content_subtype = 'html'
        
        print(f"[EMAIL] Generating PDF invoice...")
        # Generate and attach PDF invoice
        pdf_bytes = generate_invoice_pdf(invoice)
        email.attach(
            filename=f'Invoice_{invoice.invoice_number}.pdf',
            content=pdf_bytes,
            mimetype='application/pdf'
        )
        
        print(f"[EMAIL] PDF attached, sending email...")
        # Send email
        email.send(fail_silently=False)
        print(f"[EMAIL] ✓ Email sent successfully to {customer.email}")
        return True
    
    except Exception as e:
        print(f"[EMAIL] ✗ Error sending email: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
