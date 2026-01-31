from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from decimal import Decimal
from rental.models import Product, Quotation, QuotationLine, RentalOrder, OrderLine
from rental.forms import AddToCartForm, CheckoutForm
from .models import Coupon, CouponUsage


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
    from rental.models import Category
    
    products = Product.objects.filter(publish_on_website=True, is_rentable=True)
    categories = Category.objects.filter(is_active=True)
    
    # Category filter
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        try:
            selected_category = Category.objects.get(slug=category_slug, is_active=True)
            products = products.filter(category=selected_category)
        except Category.DoesNotExist:
            pass
    
    # Search - only search in name by default for more accurate results
    query = request.GET.get('q', '').strip()
    if query:
        # Primary search: exact name matches or starts with query
        products = products.filter(name__icontains=query)
    
    # Price filter
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    
    if min_price:
        try:
            products = products.filter(price_per_day__gte=Decimal(min_price))
        except (ValueError, TypeError):
            pass
    
    if max_price:
        try:
            products = products.filter(price_per_day__lte=Decimal(max_price))
        except (ValueError, TypeError):
            pass
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'query': query,
    }
    return render(request, 'website/product_list.html', context)


def product_detail(request, pk):
    """Product detail page"""
    product = get_object_or_404(Product, pk=pk, publish_on_website=True)
    
    if request.method == 'POST' and request.user.is_authenticated and request.user.role == 'customer':
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
    # Only customers can access cart
    if request.user.role != 'customer':
        messages.error(request, 'Only customers can rent products.')
        return redirect('website:home')
    
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
    # Only customers can checkout
    if request.user.role != 'customer':
        messages.error(request, 'Only customers can rent products.')
        return redirect('website:home')
    
    cart = get_object_or_404(
        Quotation,
        customer=request.user,
        status='draft'
    )
    
    if not cart.lines.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('website:product_list')
    
    # Initialize discount variables
    discount_amount = Decimal('0.00')
    applied_coupon = None
    
    # Check if coupon is in session
    if 'applied_coupon_code' in request.session:
        try:
            coupon = Coupon.objects.get(code=request.session['applied_coupon_code'])
            can_use, message = coupon.can_be_used_by(request.user)
            if can_use:
                applied_coupon = coupon
                subtotal = cart.get_total()
                discount_amount = (subtotal * coupon.discount_percentage / 100).quantize(Decimal('0.01'))
        except Coupon.DoesNotExist:
            del request.session['applied_coupon_code']
    
    # Calculate totals with discount
    subtotal = cart.get_total()
    subtotal_after_discount = subtotal - discount_amount
    tax_amount = (subtotal_after_discount * Decimal('18.00') / 100).quantize(Decimal('0.01'))
    security_deposit = Decimal('1000.00')
    grand_total = subtotal_after_discount + tax_amount + security_deposit
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            # Group cart lines by vendor
            from collections import defaultdict
            vendor_lines = defaultdict(list)
            for line in cart.lines.all():
                vendor_lines[line.product.vendor].append(line)
            
            created_orders = []
            total_discount_distributed = Decimal('0.00')
            
            # Calculate discount per vendor proportionally
            if discount_amount > 0:
                vendor_subtotals = {}
                for vendor, lines in vendor_lines.items():
                    vendor_subtotal = sum(line.get_total() for line in lines)
                    vendor_subtotals[vendor] = vendor_subtotal
            
            # Create separate order and invoice for each vendor
            for vendor, lines in vendor_lines.items():
                # Create rental order for this vendor
                order = RentalOrder()
                order.customer = request.user
                order.quotation = None  # Will link to original cart in first order only
                order.status = 'pending'
                order.delivery_method = form.cleaned_data['delivery_method']
                order.delivery_address = form.cleaned_data.get('delivery_address', '')
                order.delivery_city = form.cleaned_data.get('delivery_city', '')
                order.delivery_state = form.cleaned_data.get('delivery_state', '')
                order.delivery_pincode = form.cleaned_data.get('delivery_pincode', '')
                order.notes = form.cleaned_data.get('notes', '')
                order.save()
                
                # Copy quotation lines to order lines for this vendor
                vendor_subtotal = Decimal('0.00')
                for line in lines:
                    OrderLine.objects.create(
                        order=order,
                        product=line.product,
                        variant=line.variant,
                        quantity=line.quantity,
                        start_date=line.start_date,
                        end_date=line.end_date,
                        unit_price=line.unit_price
                    )
                    vendor_subtotal += line.get_total()
                    
                    # Reduce product quantity
                    line.product.quantity_on_hand -= line.quantity
                    line.product.save()
                
                # Calculate proportional discount for this vendor
                vendor_discount = Decimal('0.00')
                if discount_amount > 0 and subtotal > 0:
                    discount_ratio = vendor_subtotal / subtotal
                    vendor_discount = (discount_amount * discount_ratio).quantize(Decimal('0.01'))
                    total_discount_distributed += vendor_discount
                
                # Adjust last vendor's discount to account for rounding
                if vendor == list(vendor_lines.keys())[-1]:
                    vendor_discount += (discount_amount - total_discount_distributed)
                
                # Calculate vendor-specific amounts
                vendor_subtotal_after_discount = vendor_subtotal - vendor_discount
                vendor_tax = (vendor_subtotal_after_discount * Decimal('18.00') / 100).quantize(Decimal('0.01'))
                
                # Security deposit split proportionally
                vendor_security_deposit = Decimal('0.00')
                if security_deposit > 0 and subtotal > 0:
                    deposit_ratio = vendor_subtotal / subtotal
                    vendor_security_deposit = (security_deposit * deposit_ratio).quantize(Decimal('0.01'))
                
                vendor_total = vendor_subtotal_after_discount + vendor_tax + vendor_security_deposit
                
                # Create invoice for this vendor's order
                from rental.models import Invoice
                invoice = Invoice.objects.create(
                    order=order,
                    subtotal=vendor_subtotal,
                    discount_amount=vendor_discount,
                    tax_rate=Decimal('18.00'),
                    tax_amount=vendor_tax,
                    security_deposit=vendor_security_deposit,
                    total_amount=vendor_total
                )
                
                created_orders.append(order)
            
            # Link first order to quotation
            if created_orders:
                created_orders[0].quotation = cart
                created_orders[0].save()
            
            # Mark quotation as confirmed
            cart.status = 'confirmed'
            cart.save()
            
            # Record coupon usage if applied (link to first order)
            if applied_coupon and created_orders:
                CouponUsage.objects.create(
                    coupon=applied_coupon,
                    user=request.user,
                    order=created_orders[0],
                    discount_amount=discount_amount
                )
                applied_coupon.times_used += 1
                applied_coupon.save()
                # Clear coupon from session
                del request.session['applied_coupon_code']
            
            # Store order IDs and invoice IDs in session for confirmation page
            request.session['created_order_ids'] = [order.id for order in created_orders]
            
            if len(created_orders) == 1:
                messages.success(request, f'Order {created_orders[0].order_number} created successfully!')
            else:
                order_numbers = ', '.join([o.order_number for o in created_orders])
                messages.success(request, f'{len(created_orders)} orders created successfully: {order_numbers}')
            
            # Redirect to payment page for first invoice
            first_invoice = created_orders[0].invoice
            return redirect('website:payment', invoice_id=first_invoice.pk)
    else:
        form = CheckoutForm(user=request.user)
    
    context = {
        'cart': cart,
        'form': form,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'applied_coupon': applied_coupon,
        'subtotal_after_discount': subtotal_after_discount,
        'tax_amount': tax_amount,
        'security_deposit': security_deposit,
        'grand_total': grand_total,
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
def order_success(request):
    """Order success page showing all created orders"""
    order_ids = request.session.get('created_order_ids', [])
    
    if not order_ids:
        messages.info(request, 'No recent orders found.')
        return redirect('website:my_orders')
    
    orders = RentalOrder.objects.filter(id__in=order_ids, customer=request.user)
    
    # Clear session
    if 'created_order_ids' in request.session:
        del request.session['created_order_ids']
    
    context = {
        'orders': orders,
    }
    return render(request, 'website/order_success.html', context)


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
    """Download invoice as PDF with vendor logo"""
    from rental.models import Invoice
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    import io
    import os
    from django.conf import settings
    
    invoice = get_object_or_404(Invoice, pk=pk, order__customer=request.user)
    
    # Get vendor from first product in order
    vendor = None
    first_line = invoice.order.lines.first()
    if first_line and first_line.product:
        vendor = first_line.product.vendor
    
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
    
    # Add vendor logo if available
    if vendor and vendor.company_logo:
        try:
            logo_path = os.path.join(settings.MEDIA_ROOT, str(vendor.company_logo))
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=2*inch, height=0.8*inch, kind='proportional')
                logo.hAlign = 'LEFT'
                elements.append(logo)
                elements.append(Spacer(1, 12))
        except Exception as e:
            pass  # Continue without logo if there's an error
    
    # Vendor Company Name or RentEase title
    if vendor and vendor.company_name:
        vendor_title_style = ParagraphStyle(
            'VendorTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#0d6efd'),
            spaceAfter=12,
        )
        elements.append(Paragraph(vendor.company_name, vendor_title_style))
    else:
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
    
    # Delivery method display
    delivery_method_display = "Home Delivery" if invoice.order.delivery_method == 'home_delivery' else "Pickup from Warehouse"
    
    order_info = f"""
    Order #: {invoice.order.order_number}<br/>
    Order Date: {invoice.order.created_at.strftime("%b %d, %Y")}<br/>
    Delivery Method: <b>{delivery_method_display}</b><br/>
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
    from .email_utils import send_payment_confirmation_email
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
            
            # Send confirmation email with invoice
            email_sent = send_payment_confirmation_email(invoice)
            if email_sent:
                messages.success(request, 'Confirmation email sent to your registered email address.')
        
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
    
    # Check for other unpaid invoices from the same checkout session
    created_order_ids = request.session.get('created_order_ids', [])
    other_invoices = []
    if created_order_ids:
        from rental.models import RentalOrder
        for order_id in created_order_ids:
            try:
                order = RentalOrder.objects.get(pk=order_id, customer=request.user)
                if hasattr(order, 'invoice') and order.invoice.pk != invoice.pk:
                    if not order.invoice.is_fully_paid():
                        other_invoices.append(order.invoice)
            except RentalOrder.DoesNotExist:
                pass
    
    context = {
        'invoice': invoice,
        'other_invoices': other_invoices,
    }
    return render(request, 'website/payment_success.html', context)


@login_required
def validate_coupon(request):
    """AJAX endpoint to validate and apply coupon"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    if request.user.role != 'customer':
        return JsonResponse({'success': False, 'message': 'Only customers can use coupons'})
    
    coupon_code = request.POST.get('coupon_code', '').strip().upper()
    
    if not coupon_code:
        return JsonResponse({'success': False, 'message': 'Please enter a coupon code'})
    
    try:
        coupon = Coupon.objects.get(code=coupon_code)
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon code'})
    
    # Check if user can use this coupon
    can_use, message = coupon.can_be_used_by(request.user)
    
    if not can_use:
        return JsonResponse({'success': False, 'message': message})
    
    # Get cart to calculate discount
    try:
        cart = Quotation.objects.get(customer=request.user, status='draft')
        subtotal = cart.get_total()
        discount_amount = (subtotal * coupon.discount_percentage / 100).quantize(Decimal('0.01'))
        subtotal_after_discount = subtotal - discount_amount
        tax_amount = (subtotal_after_discount * Decimal('18.00') / 100).quantize(Decimal('0.01'))
        security_deposit = Decimal('1000.00')
        grand_total = subtotal_after_discount + tax_amount + security_deposit
        
        # Store coupon in session
        request.session['applied_coupon_code'] = coupon_code
        
        return JsonResponse({
            'success': True,
            'message': f'Coupon {coupon_code} applied successfully! You saved ₹{discount_amount}',
            'discount_amount': str(discount_amount),
            'discount_percentage': str(coupon.discount_percentage),
            'subtotal': str(subtotal),
            'subtotal_after_discount': str(subtotal_after_discount),
            'tax_amount': str(tax_amount),
            'grand_total': str(grand_total),
        })
    except Quotation.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'No cart found'})


@login_required
def remove_coupon(request):
    """AJAX endpoint to remove applied coupon"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    if 'applied_coupon_code' in request.session:
        del request.session['applied_coupon_code']
    
    # Recalculate totals without coupon
    try:
        cart = Quotation.objects.get(customer=request.user, status='draft')
        subtotal = cart.get_total()
        tax_amount = (subtotal * Decimal('18.00') / 100).quantize(Decimal('0.01'))
        security_deposit = Decimal('1000.00')
        grand_total = subtotal + tax_amount + security_deposit
        
        return JsonResponse({
            'success': True,
            'message': 'Coupon removed',
            'subtotal': str(subtotal),
            'subtotal_after_discount': str(subtotal),
            'discount_amount': '0.00',
            'tax_amount': str(tax_amount),
            'grand_total': str(grand_total),
        })
    except Quotation.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'No cart found'})


def about(request):
    """About Us page"""
    return render(request, 'website/about.html')


def terms(request):
    """Terms and Conditions page"""
    return render(request, 'website/terms.html')
