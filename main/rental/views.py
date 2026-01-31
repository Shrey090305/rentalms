from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, Avg
from django.utils import timezone
from django.db import models
from decimal import Decimal
from .models import (
    Product, RentalOrder, OrderLine, Invoice, Payment,
    Pickup, Return, Category
)
from .forms import (
    ProductForm, OrderStatusUpdateForm, PickupForm,
    ReturnForm, PaymentForm
)


def is_vendor_or_admin(user):
    """Check if user is vendor or admin"""
    return user.is_authenticated and (user.is_vendor() or user.is_admin_user())


@login_required
@user_passes_test(is_vendor_or_admin)
def dashboard(request):
    """Vendor/Admin dashboard with statistics"""
    # Get user's products if vendor
    if request.user.is_vendor():
        products = Product.objects.filter(vendor=request.user)
        orders = RentalOrder.objects.filter(lines__product__vendor=request.user).distinct()
    else:
        products = Product.objects.all()
        orders = RentalOrder.objects.all()
    
    # Statistics
    total_products = products.count()
    total_orders = orders.count()
    active_rentals = orders.filter(status='rented').count()
    
    # Revenue calculation
    invoices = Invoice.objects.filter(order__in=orders)
    total_revenue = invoices.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    pending_revenue = invoices.filter(status__in=['draft', 'sent']).aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    # Urgent returns (approaching or overdue)
    from django.utils import timezone
    from datetime import timedelta
    now = timezone.now()
    within_24h = now + timedelta(hours=24)
    
    urgent_returns = orders.filter(
        status__in=['picked_up', 'rented']
    ).filter(
        models.Q(lines__end_date__lt=now) | 
        models.Q(lines__end_date__lte=within_24h, lines__end_date__gte=now)
    ).distinct()
    
    urgent_returns_count = urgent_returns.count()
    overdue_count = urgent_returns.filter(lines__end_date__lt=now).distinct().count()
    approaching_count = urgent_returns.filter(
        lines__end_date__lte=within_24h, 
        lines__end_date__gte=now
    ).distinct().count()
    
    # Most rented products
    most_rented = OrderLine.objects.filter(
        order__in=orders,
        order__status__in=['confirmed', 'picked_up', 'rented', 'returned']
    ).values('product__name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('unit_price')
    ).order_by('-total_qty')[:5]
    
    # Recent orders
    recent_orders = orders.order_by('-created_at')[:10]
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'active_rentals': active_rentals,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'urgent_returns_count': urgent_returns_count,
        'overdue_count': overdue_count,
        'approaching_count': approaching_count,
        'urgent_returns': urgent_returns[:5],  # Show top 5 on dashboard
        'most_rented': most_rented,
        'recent_orders': recent_orders,
    }
    return render(request, 'rental/dashboard.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def product_manage(request):
    """Manage products list"""
    if request.user.is_vendor():
        products = Product.objects.filter(vendor=request.user)
    else:
        products = Product.objects.all()
    
    products = products.order_by('-created_at')
    
    context = {
        'products': products,
    }
    return render(request, 'rental/product_manage.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def product_create(request):
    """Create new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user
            product.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('rental:product_manage')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    return render(request, 'rental/product_form.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def product_edit(request, pk):
    """Edit product"""
    product = get_object_or_404(Product, pk=pk)
    
    # Check permission
    if request.user.is_vendor() and product.vendor != request.user:
        messages.error(request, 'You do not have permission to edit this product.')
        return redirect('rental:product_manage')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('rental:product_manage')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'action': 'Edit',
    }
    return render(request, 'rental/product_form.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def product_delete(request, pk):
    """Delete product"""
    product = get_object_or_404(Product, pk=pk)
    
    # Check permission
    if request.user.is_vendor() and product.vendor != request.user:
        messages.error(request, 'You do not have permission to delete this product.')
        return redirect('rental:product_manage')
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('rental:product_manage')
    
    context = {
        'product': product,
    }
    return render(request, 'rental/product_delete.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def order_manage(request):
    """Manage orders list"""
    if request.user.is_vendor():
        orders = RentalOrder.objects.filter(
            lines__product__vendor=request.user
        ).distinct()
    else:
        orders = RentalOrder.objects.all()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Filter by return date urgency
    return_filter = request.GET.get('return_status')
    if return_filter == 'approaching':
        # Orders with return dates within 24 hours
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        within_24h = now + timedelta(hours=24)
        orders = orders.filter(
            status__in=['picked_up', 'rented'],
            lines__end_date__gte=now,
            lines__end_date__lte=within_24h
        ).distinct()
    elif return_filter == 'overdue':
        # Orders with passed return dates
        from django.utils import timezone
        orders = orders.filter(
            status__in=['picked_up', 'rented'],
            lines__end_date__lt=timezone.now()
        ).distinct()
    elif return_filter == 'urgent':
        # Combined: approaching or overdue
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        within_24h = now + timedelta(hours=24)
        orders = orders.filter(
            status__in=['picked_up', 'rented']
        ).filter(
            models.Q(lines__end_date__lt=now) | 
            models.Q(lines__end_date__lte=within_24h, lines__end_date__gte=now)
        ).distinct()
    
    orders = orders.order_by('-created_at')
    
    # Count urgent returns for badge
    if request.user.is_vendor():
        urgent_orders = RentalOrder.objects.filter(
            lines__product__vendor=request.user,
            status__in=['picked_up', 'rented']
        ).distinct()
    else:
        urgent_orders = RentalOrder.objects.filter(
            status__in=['picked_up', 'rented']
        )
    
    from django.utils import timezone
    from datetime import timedelta
    now = timezone.now()
    within_24h = now + timedelta(hours=24)
    
    urgent_count = urgent_orders.filter(
        models.Q(lines__end_date__lt=now) | 
        models.Q(lines__end_date__lte=within_24h, lines__end_date__gte=now)
    ).distinct().count()
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'return_filter': return_filter,
        'urgent_count': urgent_count,
    }
    return render(request, 'rental/order_manage.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def order_detail_manage(request, pk):
    """Order detail for management"""
    order = get_object_or_404(RentalOrder, pk=pk)
    
    # Check permission for vendors
    if request.user.is_vendor():
        # Vendor can only see orders containing their products
        if not order.lines.filter(product__vendor=request.user).exists():
            messages.error(request, 'You do not have permission to view this order.')
            return redirect('rental:order_manage')
    
    try:
        invoice = order.invoice
    except:
        invoice = None
    
    try:
        pickup = order.pickup
    except:
        pickup = None
    
    try:
        return_doc = order.return_doc
    except:
        return_doc = None
    
    context = {
        'order': order,
        'invoice': invoice,
        'pickup': pickup,
        'return_doc': return_doc,
    }
    return render(request, 'rental/order_detail_manage.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def order_update_status(request, pk):
    """Update order status"""
    order = get_object_or_404(RentalOrder, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        old_status = order.status
        order.status = new_status
        
        if new_status == 'confirmed' and old_status != 'confirmed':
            order.confirmed_at = timezone.now()
        
        order.save()
        messages.success(request, f'Order status updated to {order.get_status_display()}')
        
        return redirect('rental:order_detail_manage', pk=order.pk)
    
    return redirect('rental:order_manage')


@login_required
@user_passes_test(is_vendor_or_admin)
def record_pickup(request, order_id):
    """Record pickup for order"""
    order = get_object_or_404(RentalOrder, pk=order_id)
    
    if request.method == 'POST':
        form = PickupForm(request.POST)
        if form.is_valid():
            pickup = Pickup.objects.create(
                order=order,
                pickup_date=form.cleaned_data['pickup_date'],
                picked_by=form.cleaned_data['picked_by'],
                id_proof=form.cleaned_data.get('id_proof', ''),
                notes=form.cleaned_data.get('notes', '')
            )
            
            # Update order status
            order.status = 'picked_up'
            order.save()
            
            messages.success(request, 'Pickup recorded successfully!')
            return redirect('rental:order_detail_manage', pk=order.pk)
    else:
        form = PickupForm()
    
    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'rental/pickup_form.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def record_return(request, order_id):
    """Record return for order"""
    order = get_object_or_404(RentalOrder, pk=order_id)
    
    if request.method == 'POST':
        form = ReturnForm(request.POST)
        if form.is_valid():
            return_doc = form.save(commit=False)
            return_doc.order = order
            
            # Calculate late fee
            return_doc.late_fee = return_doc.calculate_late_fee()
            return_doc.save()
            
            # Update order status
            order.status = 'returned'
            order.save()
            
            # Update invoice with late fee if any
            try:
                invoice = order.invoice
                invoice.late_fee = return_doc.late_fee + return_doc.damage_fee
                invoice.save()
            except:
                pass
            
            messages.success(request, f'Return recorded successfully! Late fee: ₹{return_doc.late_fee}')
            return redirect('rental:order_detail_manage', pk=order.pk)
    else:
        form = ReturnForm()
    
    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'rental/return_form.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def invoice_manage(request, order_id):
    """View/manage invoice"""
    order = get_object_or_404(RentalOrder, pk=order_id)
    
    try:
        invoice = order.invoice
    except:
        # Create invoice if not exists
        invoice = Invoice.objects.create(
            order=order,
            subtotal=order.get_total(),
            tax_rate=Decimal('18.00'),
            tax_amount=order.get_tax_amount(),
            security_deposit=Decimal('1000.00'),
            total_amount=order.get_grand_total() + Decimal('1000.00')
        )
        messages.success(request, 'Invoice created!')
    
    context = {
        'invoice': invoice,
        'order': order,
    }
    return render(request, 'rental/invoice_manage.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def record_payment(request, invoice_id):
    """Record payment for invoice"""
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, invoice=invoice)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()
            
            messages.success(request, f'Payment of ₹{payment.amount} recorded successfully!')
            return redirect('rental:invoice_manage', order_id=invoice.order.pk)
    else:
        form = PaymentForm(invoice=invoice)
    
    context = {
        'form': form,
        'invoice': invoice,
    }
    return render(request, 'rental/payment_form.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def reports_dashboard(request):
    """Main reports dashboard"""
    from django.db.models import Sum
    
    # Get quick overview stats
    if request.user.is_vendor():
        orders = RentalOrder.objects.filter(lines__product__vendor=request.user).distinct()
        products = Product.objects.filter(vendor=request.user, is_rentable=True)
    else:
        orders = RentalOrder.objects.all()
        products = Product.objects.filter(is_rentable=True)
    
    total_orders = orders.count()
    total_revenue = orders.aggregate(total=Sum('invoice__total_amount'))['total'] or Decimal('0.00')
    active_customers = orders.values('customer').distinct().count()
    active_products = products.count()
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'active_customers': active_customers,
        'active_products': active_products,
    }
    return render(request, 'rental/reports_dashboard.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def sales_report(request):
    """Sales report with filtering"""
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Avg
    
    # Get date range from request or default to last 30 days
    end_date = request.GET.get('end_date')
    start_date = request.GET.get('start_date')
    
    if not end_date:
        end_date = timezone.now()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        end_date = timezone.make_aware(end_date)
    
    if not start_date:
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        start_date = timezone.make_aware(start_date)
    
    # Filter orders by user role
    if request.user.is_vendor():
        orders = RentalOrder.objects.filter(
            lines__product__vendor=request.user,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).distinct()
    else:
        orders = RentalOrder.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
    
    # Calculate metrics
    total_orders = orders.count()
    total_revenue = orders.aggregate(total=Sum('invoice__total_amount'))['total'] or Decimal('0.00')
    avg_order_value = orders.aggregate(avg=Avg('invoice__total_amount'))['avg'] or Decimal('0.00')
    
    # Orders by status
    orders_by_status = orders.values('status').annotate(
        count=Count('id'),
        revenue=Sum('invoice__total_amount')
    ).order_by('-count')
    
    # Daily sales trend
    from django.db.models.functions import TruncDate
    daily_sales = orders.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        orders_count=Count('id'),
        revenue=Sum('invoice__total_amount')
    ).order_by('date')
    
    # Top customers
    top_customers = orders.values(
        'customer__first_name', 
        'customer__last_name',
        'customer__email'
    ).annotate(
        order_count=Count('id'),
        total_spent=Sum('invoice__total_amount')
    ).order_by('-total_spent')[:10]
    
    # Get unique customers count
    unique_customers = orders.values('customer').distinct().count()
    
    # Calculate percentages for order status
    for status in orders_by_status:
        status['percentage'] = (status['count'] / total_orders * 100) if total_orders > 0 else 0
    
    # Prepare data for charts
    import json
    daily_sales_labels = json.dumps([str(item['date']) for item in daily_sales])
    daily_sales_revenue = json.dumps([float(item['revenue'] or 0) for item in daily_sales])
    daily_sales_orders = json.dumps([item['orders_count'] for item in daily_sales])
    
    status_labels = json.dumps([item['status'] or 'Pending' for item in orders_by_status])
    status_counts = json.dumps([item['count'] for item in orders_by_status])
    
    # Rename customer field keys for template
    top_customers_list = []
    for customer in top_customers:
        top_customers_list.append({
            'user__first_name': customer['customer__first_name'],
            'user__last_name': customer['customer__last_name'],
            'user__email': customer['customer__email'],
            'order_count': customer['order_count'],
            'total_spent': customer['total_spent']
        })
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'unique_customers': unique_customers,
        'orders_by_status': orders_by_status,
        'daily_sales': daily_sales,
        'top_customers': top_customers_list,
        'daily_sales_labels': daily_sales_labels,
        'daily_sales_revenue': daily_sales_revenue,
        'daily_sales_orders': daily_sales_orders,
        'status_labels': status_labels,
        'status_counts': status_counts,
    }
    return render(request, 'rental/sales_report.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def product_report(request):
    """Product performance report"""
    from django.db.models import Sum, Count, F, Q
    from datetime import timedelta
    import json
    
    # Filter products by user role
    if request.user.is_vendor():
        products = Product.objects.filter(vendor=request.user)
        order_lines = OrderLine.objects.filter(product__vendor=request.user)
    else:
        products = Product.objects.all()
        order_lines = OrderLine.objects.all()
    
    # Most rented products - need to join with product details
    most_rented_data = order_lines.filter(
        order__status__in=['confirmed', 'picked_up', 'rented', 'returned']
    ).values(
        'product__id',
        'product__name',
        'product__category__name',
        'product__quantity_on_hand'
    ).annotate(
        rental_count=Count('id'),
        rental_revenue=Sum(F('unit_price') * F('quantity'))
    ).order_by('-rental_count')[:20]
    
    # Get product objects for most rented
    most_rented = []
    for item in most_rented_data:
        product = products.filter(id=item['product__id']).first()
        if product:
            most_rented.append({
                'name': item['product__name'],
                'category': type('obj', (object,), {'name': item['product__category__name']})() if item['product__category__name'] else None,
                'rental_count': item['rental_count'],
                'rental_revenue': item['rental_revenue'] or Decimal('0.00'),
                'stock': item['product__quantity_on_hand']
            })
    
    # Category breakdown - rentals by category
    category_breakdown = order_lines.filter(
        order__status__in=['confirmed', 'picked_up', 'rented', 'returned']
    ).values(
        'product__category__name'
    ).annotate(
        rental_count=Count('id'),
        revenue=Sum(F('unit_price') * F('quantity'))
    ).order_by('-rental_count')
    
    # Low stock products with recent rentals
    thirty_days_ago = timezone.now() - timedelta(days=30)
    low_stock = []
    for product in products.filter(quantity_on_hand__lte=5, is_rentable=True).order_by('quantity_on_hand')[:10]:
        recent_rentals = order_lines.filter(
            product=product,
            order__created_at__gte=thirty_days_ago
        ).count()
        low_stock.append({
            'name': product.name,
            'category': product.category,
            'stock': product.quantity_on_hand,
            'recent_rentals': recent_rentals
        })
    
    # Product utilization (simple version - currently rented)
    utilization = []
    for product in products.filter(is_rentable=True)[:10]:
        currently_rented = order_lines.filter(
            product=product,
            order__status__in=['picked_up', 'rented']
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        if product.quantity_on_hand > 0:
            utilization_rate = (currently_rented / product.quantity_on_hand) * 100
        else:
            utilization_rate = 0
            
        utilization.append({
            'name': product.name,
            'utilization_rate': utilization_rate
        })
    
    # Sort by utilization rate
    utilization = sorted(utilization, key=lambda x: x['utilization_rate'], reverse=True)
    
    # Prepare chart data
    most_rented_labels = json.dumps([item['name'][:30] for item in most_rented][:10])
    most_rented_counts = json.dumps([item['rental_count'] for item in most_rented][:10])
    
    category_labels = json.dumps([item['product__category__name'] or 'Uncategorized' for item in category_breakdown][:10])
    category_counts = json.dumps([item['rental_count'] for item in category_breakdown][:10])
    
    context = {
        'total_products': products.count(),
        'rentable_products': products.filter(is_rentable=True).count(),
        'most_rented': most_rented,
        'category_breakdown': category_breakdown,
        'low_stock': low_stock,
        'utilization': utilization,
        'most_rented_labels': most_rented_labels,
        'most_rented_counts': most_rented_counts,
        'category_labels': category_labels,
        'category_counts': category_counts,
    }
    return render(request, 'rental/product_report.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def revenue_report(request):
    """Revenue and financial report"""
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Q
    from django.db.models.functions import TruncMonth
    
    # Filter invoices by user role
    if request.user.is_vendor():
        invoices = Invoice.objects.filter(order__lines__product__vendor=request.user).distinct()
    else:
        invoices = Invoice.objects.all()
    
    # Total revenue metrics
    total_invoiced = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_paid = invoices.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    total_pending = total_invoiced - total_paid
    
    # Payment status breakdown
    payment_status = invoices.values('status').annotate(
        count=Count('id'),
        amount=Sum('total_amount')
    ).order_by('status')
    
    # Monthly revenue trend (last 12 months)
    twelve_months_ago = timezone.now() - timedelta(days=365)
    monthly_revenue = invoices.filter(
        created_at__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        invoiced=Sum('total_amount'),
        paid=Sum('amount_paid'),
        invoice_count=Count('id')
    ).order_by('month')
    
    # Payment method breakdown
    payments = Payment.objects.all()
    if request.user.is_vendor():
        payments = payments.filter(invoice__order__lines__product__vendor=request.user).distinct()
    
    payment_methods = payments.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')
    
    # Revenue by product category
    if request.user.is_vendor():
        order_lines = OrderLine.objects.filter(product__vendor=request.user)
    else:
        order_lines = OrderLine.objects.all()
    
    category_revenue = order_lines.filter(
        order__status__in=['confirmed', 'picked_up', 'rented', 'returned']
    ).values(
        'product__category__name'
    ).annotate(
        revenue=Sum(F('unit_price') * F('quantity')),
        order_count=Count('order', distinct=True),
        avg_value=Avg(F('unit_price') * F('quantity'))
    ).order_by('-revenue')
    
    # Calculate collection rate
    collection_rate = (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
    
    # Prepare chart data
    import json
    monthly_labels = json.dumps([item['month'].strftime('%b %Y') for item in monthly_revenue])
    monthly_invoiced = json.dumps([float(item['invoiced'] or 0) for item in monthly_revenue])
    monthly_paid = json.dumps([float(item['paid'] or 0) for item in monthly_revenue])
    
    payment_method_labels = json.dumps([item['payment_method'] or 'Pending' for item in payment_methods])
    payment_method_amounts = json.dumps([float(item['total'] or 0) for item in payment_methods])
    
    category_revenue_labels = json.dumps([item['product__category__name'] or 'Uncategorized' for item in category_revenue][:10])
    category_revenue_amounts = json.dumps([float(item['revenue'] or 0) for item in category_revenue][:10])
    
    context = {
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'collection_rate': collection_rate,
        'payment_status': payment_status,
        'monthly_revenue': monthly_revenue,
        'payment_methods': payment_methods,
        'category_revenue': category_revenue,
        'monthly_labels': monthly_labels,
        'monthly_invoiced': monthly_invoiced,
        'monthly_paid': monthly_paid,
        'payment_method_labels': payment_method_labels,
        'payment_method_amounts': payment_method_amounts,
        'category_revenue_labels': category_revenue_labels,
        'category_revenue_amounts': category_revenue_amounts,
    }
    return render(request, 'rental/revenue_report.html', context)


@login_required
@user_passes_test(is_vendor_or_admin)
def customer_report(request):
    """Customer analytics report"""
    from django.db.models import Sum, Count, Avg, Max, Case, When
    from datetime import timedelta
    import json
    
    # Filter customers based on orders
    if request.user.is_vendor():
        orders = RentalOrder.objects.filter(lines__product__vendor=request.user).distinct()
    else:
        orders = RentalOrder.objects.all()
    
    # Top customers
    customer_stats = orders.values(
        'customer__id',
        'customer__first_name',
        'customer__last_name',
        'customer__email'
    ).annotate(
        order_count=Count('id'),
        total_spent=Sum('invoice__total_amount'),
        avg_order_value=Avg('invoice__total_amount')
    ).order_by('-total_spent')[:50]
    
    # Convert to list for template
    top_customers = []
    for customer in customer_stats:
        top_customers.append({
            'user__first_name': customer['customer__first_name'],
            'user__last_name': customer['customer__last_name'],
            'user__email': customer['customer__email'],
            'order_count': customer['order_count'],
            'total_spent': customer['total_spent'] or Decimal('0.00'),
            'avg_order_value': customer['avg_order_value'] or Decimal('0.00')
        })
    
    # New vs returning customers
    all_customers = orders.values('customer').annotate(
        order_count=Count('id')
    )
    
    new_customers = all_customers.filter(order_count=1).count()
    returning_customers = all_customers.filter(order_count__gt=1).count()
    total_customers = new_customers + returning_customers
    
    new_customer_percentage = (new_customers / total_customers * 100) if total_customers > 0 else 0
    returning_customer_percentage = (returning_customers / total_customers * 100) if total_customers > 0 else 0
    
    # Order frequency distribution
    order_frequency_data = all_customers.annotate(
        order_range=Case(
            When(order_count=1, then=models.Value('1')),
            When(order_count__gte=2, order_count__lte=3, then=models.Value('2-3')),
            When(order_count__gte=4, order_count__lte=5, then=models.Value('4-5')),
            default=models.Value('6+'),
            output_field=models.CharField()
        )
    ).values('order_range').annotate(
        customer_count=Count('customer')
    )
    
    # Calculate percentages
    order_frequency = []
    for item in order_frequency_data:
        percentage = (item['customer_count'] / total_customers * 100) if total_customers > 0 else 0
        order_frequency.append({
            'order_range': item['order_range'],
            'customer_count': item['customer_count'],
            'percentage': percentage
        })
    
    # Average orders per customer
    avg_orders_per_customer = all_customers.aggregate(avg=Avg('order_count'))['avg'] or 0
    
    # Prepare chart data
    frequency_labels = json.dumps([item['order_range'] for item in order_frequency])
    frequency_counts = json.dumps([item['customer_count'] for item in order_frequency])
    
    context = {
        'total_customers': total_customers,
        'new_customers': new_customers,
        'returning_customers': returning_customers,
        'new_customer_percentage': new_customer_percentage,
        'returning_customer_percentage': returning_customer_percentage,
        'avg_orders_per_customer': avg_orders_per_customer,
        'top_customers': top_customers,
        'order_frequency': order_frequency,
        'frequency_labels': frequency_labels,
        'frequency_counts': frequency_counts,
    }
    return render(request, 'rental/customer_report.html', context)

