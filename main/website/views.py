from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from decimal import Decimal
from rental.models import Product, Quotation, QuotationLine, RentalOrder, OrderLine
from rental.forms import AddToCartForm, CheckoutForm


def home(request):
    """Homepage"""
    featured_products = Product.objects.filter(
        publish_on_website=True,
        is_rentable=True
    )[:6]
    
    context = {
        'featured_products': featured_products,
    }
    return render(request, 'website/home.html', context)


def product_list(request):
    """Product listing page with search/filter"""
    products = Product.objects.filter(publish_on_website=True, is_rentable=True)
    
    # Search
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    # Price filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price_per_day__gte=min_price)
    if max_price:
        products = products.filter(price_per_day__lte=max_price)
    
    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'website/product_list.html', context)


def product_detail(request, pk):
    """Product detail page"""
    product = get_object_or_404(Product, pk=pk, publish_on_website=True)
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = AddToCartForm(request.POST, product=product)
        if form.is_valid():
            # Get or create cart (draft quotation)
            cart, created = Quotation.objects.get_or_create(
                customer=request.user,
                status='draft'
            )
            
            # Calculate price
            unit_price = product.calculate_rental_price(
                form.cleaned_data['start_date'],
                form.cleaned_data['end_date']
            )
            
            # Add to cart
            QuotationLine.objects.create(
                quotation=cart,
                product=product,
                variant=form.cleaned_data.get('variant'),
                quantity=form.cleaned_data['quantity'],
                start_date=form.cleaned_data['start_date'],
                end_date=form.cleaned_data['end_date'],
                unit_price=unit_price
            )
            
            messages.success(request, f'{product.name} added to cart!')
            return redirect('website:cart')
    else:
        form = AddToCartForm(product=product)
    
    context = {
        'product': product,
        'form': form,
    }
    return render(request, 'website/product_detail.html', context)


@login_required
def cart_view(request):
    """Shopping cart / quotation view"""
    cart = Quotation.objects.filter(
        customer=request.user,
        status='draft'
    ).first()
    
    if not cart:
        messages.info(request, 'Your cart is empty.')
        return redirect('website:product_list')
    
    # Handle line removal
    if request.method == 'POST' and 'remove_line' in request.POST:
        line_id = request.POST.get('line_id')
        QuotationLine.objects.filter(id=line_id, quotation=cart).delete()
        messages.success(request, 'Item removed from cart.')
        return redirect('website:cart')
    
    context = {
        'cart': cart,
        'subtotal': cart.get_total(),
        'tax_amount': cart.get_tax_amount(),
        'grand_total': cart.get_grand_total(),
    }
    return render(request, 'website/cart.html', context)


@login_required
def checkout_view(request):
    """Checkout and create order"""
    cart = get_object_or_404(
        Quotation,
        customer=request.user,
        status='draft'
    )
    
    if not cart.lines.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('website:product_list')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            # Create rental order
            order = form.save(commit=False)
            order.customer = request.user
            order.quotation = cart
            order.status = 'pending'
            order.save()
            
            # Copy quotation lines to order lines
            for line in cart.lines.all():
                OrderLine.objects.create(
                    order=order,
                    product=line.product,
                    variant=line.variant,
                    quantity=line.quantity,
                    start_date=line.start_date,
                    end_date=line.end_date,
                    unit_price=line.unit_price
                )
                
                # Reduce product quantity
                line.product.quantity_on_hand -= line.quantity
                line.product.save()
            
            # Mark quotation as confirmed
            cart.status = 'confirmed'
            cart.save()
            
            # Create invoice
            from rental.models import Invoice
            invoice = Invoice.objects.create(
                order=order,
                subtotal=order.get_total(),
                tax_rate=Decimal('18.00'),
                tax_amount=order.get_tax_amount(),
                security_deposit=Decimal('1000.00'),  # Default security deposit
                total_amount=order.get_grand_total() + Decimal('1000.00')
            )
            
            messages.success(request, f'Order {order.order_number} created successfully!')
            return redirect('website:order_detail', pk=order.pk)
    else:
        form = CheckoutForm(user=request.user)
    
    context = {
        'cart': cart,
        'form': form,
        'subtotal': cart.get_total(),
        'tax_amount': cart.get_tax_amount(),
        'security_deposit': Decimal('1000.00'),
        'grand_total': cart.get_grand_total() + Decimal('1000.00'),
    }
    return render(request, 'website/checkout.html', context)


@login_required
def my_orders(request):
    """Customer's orders list"""
    orders = RentalOrder.objects.filter(customer=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'website/my_orders.html', context)


@login_required
def order_detail(request, pk):
    """Order detail view"""
    order = get_object_or_404(RentalOrder, pk=pk, customer=request.user)
    
    try:
        invoice = order.invoice
    except:
        invoice = None
    
    context = {
        'order': order,
        'invoice': invoice,
    }
    return render(request, 'website/order_detail.html', context)


@login_required
def invoice_view(request, pk):
    """Invoice detail/download"""
    from rental.models import Invoice
    invoice = get_object_or_404(Invoice, pk=pk, order__customer=request.user)
    
    context = {
        'invoice': invoice,
    }
    return render(request, 'website/invoice.html', context)


@login_required
def invoice_pdf_download(request, pk):
    """Download invoice as PDF"""
    from rental.models import Invoice
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    import io
    
    invoice = get_object_or_404(Invoice, pk=pk, order__customer=request.user)
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for PDF elements
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
    elements.append(Paragraph("Items:", heading_style))
    
    items_data = [['Item', 'Period', 'Qty', 'Rate', 'Amount']]
    for line in invoice.order.lines.all():
        period = f"{line.start_date.strftime('%b %d')} - {line.end_date.strftime('%b %d, %Y')}"
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
    
    # Get PDF value and return response
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
    return response


@login_required
def payment_view(request, invoice_id):
    """Razorpay payment page (dummy mode)"""
    from rental.models import Invoice, Payment
    import random
    invoice = get_object_or_404(Invoice, pk=invoice_id, order__customer=request.user)
    
    if request.method == 'POST':
        # Simulate Razorpay payment
        payment_method = request.POST.get('payment_method', 'upi')
        amount = invoice.get_balance()
        
        # Generate dummy Razorpay payment ID
        razorpay_payment_id = f'pay_{random.randint(100000000000, 999999999999)}'
        
        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=payment_method,
            reference_number=razorpay_payment_id,
            notes=f'Razorpay payment via {payment_method.upper()}'
        )
        
        messages.success(request, f'Payment of ₹{amount} successful via Razorpay!')
        
        # Update order status
        if invoice.is_fully_paid():
            order = invoice.order
            order.status = 'confirmed'
            order.save()
        
        return redirect('website:payment_success', invoice_id=invoice.pk)
    
    # Generate dummy Razorpay order ID
    razorpay_order_id = f'order_{random.randint(100000000000, 999999999999)}'
    
    context = {
        'invoice': invoice,
        'amount_to_pay': invoice.get_balance(),
        'razorpay_order_id': razorpay_order_id,
        'razorpay_key': 'rzp_test_dummy123456',  # Dummy key for display
    }
    return render(request, 'website/payment.html', context)


@login_required
def payment_success(request, invoice_id):
    """Payment success page"""
    from rental.models import Invoice
    invoice = get_object_or_404(Invoice, pk=invoice_id, order__customer=request.user)
    
    context = {
        'invoice': invoice,
    }
    return render(request, 'website/payment_success.html', context)

