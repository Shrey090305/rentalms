from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
from .models import (
    Product, RentalOrder, OrderLine, Invoice, Payment,
    Pickup, Return
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
    
    orders = orders.order_by('-created_at')
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
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

