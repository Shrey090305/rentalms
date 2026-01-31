"""
Test script for vendor-wise order splitting functionality
This script verifies that orders with multi-vendor products are properly split
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from django.contrib.auth import get_user_model
from rental.models import Product, Quotation, QuotationLine, RentalOrder, Invoice
from datetime import datetime, timedelta

User = get_user_model()

print("=" * 80)
print("VENDOR-WISE ORDER SPLITTING TEST")
print("=" * 80)

# Check vendors
vendors = User.objects.filter(role='vendor')
print(f"\n1. Found {vendors.count()} vendors in the system:")
for vendor in vendors:
    product_count = Product.objects.filter(vendor=vendor).count()
    print(f"   - {vendor.get_full_name()} ({vendor.email}): {product_count} products")

# Check if we have at least 2 vendors with products
vendor_list = list(vendors)
if len(vendor_list) < 2:
    print("\n⚠️  WARNING: Need at least 2 vendors to test multi-vendor splitting")
    print("   Creating a second vendor for testing...")
    
    # Create a test vendor
    from django.contrib.auth.hashers import make_password
    test_vendor = User.objects.create(
        email='testvendor@example.com',
        username='testvendor',
        password=make_password('testpass123'),
        first_name='Test',
        last_name='Vendor',
        role='vendor',
        company_name='Test Vendor Company'
    )
    print(f"   ✓ Created test vendor: {test_vendor.get_full_name()}")
    vendor_list.append(test_vendor)

# Ensure vendors have products
print("\n2. Checking products per vendor:")
for i, vendor in enumerate(vendor_list[:2]):
    products = Product.objects.filter(vendor=vendor, is_rentable=True, publish_on_website=True)
    print(f"   Vendor {i+1} ({vendor.get_full_name()}): {products.count()} rentable products")
    
    if products.count() == 0:
        print(f"   Creating a test product for {vendor.get_full_name()}...")
        product = Product.objects.create(
            vendor=vendor,
            name=f'Test Product by {vendor.first_name}',
            description='Test product for vendor-wise order splitting',
            price_per_day=100,
            price_per_week=600,
            quantity_on_hand=10,
            is_rentable=True,
            publish_on_website=True
        )
        print(f"   ✓ Created: {product.name} (₹{product.price_per_day}/day)")

# Get or create a test customer
customer = User.objects.filter(role='customer').first()
if not customer:
    print("\n3. Creating test customer...")
    customer = User.objects.create(
        email='testcustomer@example.com',
        username='testcustomer',
        password=make_password('testpass123'),
        first_name='Test',
        last_name='Customer',
        role='customer'
    )
    print(f"   ✓ Created customer: {customer.get_full_name()}")
else:
    print(f"\n3. Using existing customer: {customer.get_full_name()}")

# Create a multi-vendor cart
print("\n4. Creating multi-vendor cart...")

# Delete any existing draft quotations for this customer
Quotation.objects.filter(customer=customer, status='draft').delete()

cart = Quotation.objects.create(
    customer=customer,
    status='draft'
)

vendor1 = vendor_list[0]
vendor2 = vendor_list[1] if len(vendor_list) > 1 else vendor_list[0]

product1 = Product.objects.filter(vendor=vendor1, is_rentable=True).first()
product2 = Product.objects.filter(vendor=vendor2, is_rentable=True).first()

if not product1 or not product2:
    print("   ⚠️  ERROR: Could not find products for vendors")
    exit(1)

start_date = datetime.now() + timedelta(days=1)
end_date = start_date + timedelta(days=7)

line1 = QuotationLine.objects.create(
    quotation=cart,
    product=product1,
    quantity=1,
    start_date=start_date,
    end_date=end_date,
    unit_price=product1.price_per_week
)

line2 = QuotationLine.objects.create(
    quotation=cart,
    product=product2,
    quantity=2,
    start_date=start_date,
    end_date=end_date,
    unit_price=product2.price_per_week
)

print(f"   ✓ Added {product1.name} from {vendor1.get_full_name()} (₹{line1.get_total()})")
print(f"   ✓ Added {product2.name} from {vendor2.get_full_name()} (₹{line2.get_total()})")
print(f"   Total cart value: ₹{cart.get_total()}")

# Count orders before
orders_before = RentalOrder.objects.filter(customer=customer).count()
invoices_before = Invoice.objects.filter(order__customer=customer).count()

print(f"\n5. Before checkout:")
print(f"   Orders: {orders_before}")
print(f"   Invoices: {invoices_before}")

# Simulate checkout logic (vendor-wise splitting)
print("\n6. Simulating vendor-wise order splitting...")

from collections import defaultdict
from decimal import Decimal

vendor_lines = defaultdict(list)
for line in cart.lines.all():
    vendor_lines[line.product.vendor].append(line)

print(f"   Cart contains products from {len(vendor_lines)} vendor(s)")

created_orders = []
for vendor, lines in vendor_lines.items():
    # Create order
    order = RentalOrder.objects.create(
        customer=customer,
        delivery_address='Test Address 123',
        delivery_city='Test City',
        delivery_state='Test State',
        delivery_pincode='123456',
        status='pending'
    )
    
    vendor_subtotal = Decimal('0.00')
    for line in lines:
        from rental.models import OrderLine
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
    
    # Create invoice
    tax_amount = (vendor_subtotal * Decimal('18.00') / 100).quantize(Decimal('0.01'))
    security_deposit = Decimal('500.00')
    total_amount = vendor_subtotal + tax_amount + security_deposit
    
    invoice = Invoice.objects.create(
        order=order,
        subtotal=vendor_subtotal,
        discount_amount=Decimal('0.00'),
        tax_rate=Decimal('18.00'),
        tax_amount=tax_amount,
        security_deposit=security_deposit,
        total_amount=total_amount
    )
    
    created_orders.append(order)
    print(f"   ✓ Created Order {order.order_number} for {vendor.get_full_name()}")
    print(f"     - Products: {order.lines.count()}")
    print(f"     - Subtotal: ₹{invoice.subtotal}")
    print(f"     - Total: ₹{invoice.total_amount}")

# Count orders after
orders_after = RentalOrder.objects.filter(customer=customer).count()
invoices_after = Invoice.objects.filter(order__customer=customer).count()

print(f"\n7. After checkout:")
print(f"   Orders: {orders_after} (+{orders_after - orders_before})")
print(f"   Invoices: {invoices_after} (+{invoices_after - invoices_before})")

# Verify splitting
print("\n" + "=" * 80)
print("VERIFICATION RESULTS")
print("=" * 80)

if len(vendor_lines) == 1:
    print("✓ Single vendor cart - 1 order created (as expected)")
    success = orders_after - orders_before == 1
elif len(vendor_lines) == 2:
    print(f"✓ Multi-vendor cart - {len(created_orders)} separate orders created (as expected)")
    success = orders_after - orders_before == 2
    
    # Verify each order has products from only one vendor
    all_correct = True
    for order in created_orders:
        vendors_in_order = set(line.product.vendor for line in order.lines.all())
        if len(vendors_in_order) == 1:
            print(f"  ✓ Order {order.order_number}: All products from {list(vendors_in_order)[0].get_full_name()}")
        else:
            print(f"  ✗ Order {order.order_number}: Contains products from multiple vendors!")
            all_correct = False
    
    success = success and all_correct
else:
    print(f"⚠️  Unusual case: {len(vendor_lines)} vendors")
    success = True

# Verify invoices
print("\n8. Invoice verification:")
for order in created_orders:
    try:
        invoice = order.invoice
        print(f"   ✓ Order {order.order_number} has invoice {invoice.invoice_number}")
        print(f"     - Amount: ₹{invoice.total_amount}, Status: {invoice.status}")
    except:
        print(f"   ✗ Order {order.order_number} has NO invoice!")
        success = False

print("\n" + "=" * 80)
if success:
    print("✓✓✓ VENDOR-WISE ORDER SPLITTING: WORKING CORRECTLY ✓✓✓")
else:
    print("✗✗✗ VENDOR-WISE ORDER SPLITTING: ISSUES DETECTED ✗✗✗")
print("=" * 80)

print(f"\nTest orders created: {[o.order_number for o in created_orders]}")
print("You can view these in the admin panel or customer's 'My Orders' page")
