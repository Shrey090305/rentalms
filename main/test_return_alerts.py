"""
Test script for return date alerts functionality
Creates test orders with different return dates to verify filtering
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rental.models import Product, RentalOrder, OrderLine
from decimal import Decimal

User = get_user_model()

print("=" * 80)
print("TESTING RETURN DATE ALERTS FUNCTIONALITY")
print("=" * 80)

# Get vendor and customer
vendor = User.objects.filter(role='vendor').first()
customer = User.objects.filter(role='customer').first()

if not vendor or not customer:
    print("✗ ERROR: Need at least one vendor and one customer")
    exit(1)

# Get a product
product = Product.objects.filter(vendor=vendor, is_rentable=True).first()

if not product:
    print("✗ ERROR: No rentable products found")
    exit(1)

print(f"\n1. Test Setup:")
print(f"   Vendor: {vendor.get_full_name()}")
print(f"   Customer: {customer.get_full_name()}")
print(f"   Product: {product.name}")

# Create test orders with different return dates
print("\n2. Creating test orders...")

now = timezone.now()

# Test Case 1: Order with return date 2 hours ago (OVERDUE)
order1 = RentalOrder.objects.create(
    customer=customer,
    delivery_address="Test Address",
    delivery_city="Test City",
    delivery_state="Test State",
    delivery_pincode="123456",
    status='rented'
)
OrderLine.objects.create(
    order=order1,
    product=product,
    quantity=1,
    start_date=now - timedelta(days=3),
    end_date=now - timedelta(hours=2),  # 2 hours ago
    unit_price=Decimal('100.00')
)
print(f"   ✓ Order 1 ({order1.order_number}): OVERDUE (2 hours past return)")

# Test Case 2: Order with return date in 12 hours (APPROACHING)
order2 = RentalOrder.objects.create(
    customer=customer,
    delivery_address="Test Address",
    delivery_city="Test City",
    delivery_state="Test State",
    delivery_pincode="123456",
    status='rented'
)
OrderLine.objects.create(
    order=order2,
    product=product,
    quantity=1,
    start_date=now - timedelta(days=2),
    end_date=now + timedelta(hours=12),  # 12 hours from now
    unit_price=Decimal('100.00')
)
print(f"   ✓ Order 2 ({order2.order_number}): APPROACHING (12 hours until return)")

# Test Case 3: Order with return date in 2 days (NORMAL)
order3 = RentalOrder.objects.create(
    customer=customer,
    delivery_address="Test Address",
    delivery_city="Test City",
    delivery_state="Test State",
    delivery_pincode="123456",
    status='rented'
)
OrderLine.objects.create(
    order=order3,
    product=product,
    quantity=1,
    start_date=now,
    end_date=now + timedelta(days=2),  # 2 days from now
    unit_price=Decimal('100.00')
)
print(f"   ✓ Order 3 ({order3.order_number}): NORMAL (2 days until return)")

# Test Case 4: Already returned order (RETURNED)
order4 = RentalOrder.objects.create(
    customer=customer,
    delivery_address="Test Address",
    delivery_city="Test City",
    delivery_state="Test State",
    delivery_pincode="123456",
    status='returned'
)
OrderLine.objects.create(
    order=order4,
    product=product,
    quantity=1,
    start_date=now - timedelta(days=5),
    end_date=now - timedelta(days=2),
    unit_price=Decimal('100.00')
)
print(f"   ✓ Order 4 ({order4.order_number}): RETURNED (already returned)")

# Test the model methods
print("\n3. Testing model methods:")

print(f"\n   Order 1 (OVERDUE):")
print(f"     - Latest return date: {order1.get_latest_return_date()}")
print(f"     - Has approaching return: {order1.has_approaching_return()}")
print(f"     - Is return overdue: {order1.is_return_overdue()}")
print(f"     - Return status: {order1.get_return_status()}")

print(f"\n   Order 2 (APPROACHING):")
print(f"     - Latest return date: {order2.get_latest_return_date()}")
print(f"     - Has approaching return: {order2.has_approaching_return()}")
print(f"     - Is return overdue: {order2.is_return_overdue()}")
print(f"     - Return status: {order2.get_return_status()}")

print(f"\n   Order 3 (NORMAL):")
print(f"     - Latest return date: {order3.get_latest_return_date()}")
print(f"     - Has approaching return: {order3.has_approaching_return()}")
print(f"     - Is return overdue: {order3.is_return_overdue()}")
print(f"     - Return status: {order3.get_return_status()}")

print(f"\n   Order 4 (RETURNED):")
print(f"     - Latest return date: {order4.get_latest_return_date()}")
print(f"     - Has approaching return: {order4.has_approaching_return()}")
print(f"     - Is return overdue: {order4.is_return_overdue()}")
print(f"     - Return status: {order4.get_return_status()}")

# Test filtering
print("\n4. Testing filtering logic:")

from django.db import models

active_orders = RentalOrder.objects.filter(status__in=['picked_up', 'rented'])
print(f"   Total active orders: {active_orders.count()}")

within_24h = now + timedelta(hours=24)

overdue = active_orders.filter(lines__end_date__lt=now).distinct()
print(f"   Overdue orders: {overdue.count()}")
for o in overdue:
    print(f"     - {o.order_number}")

approaching = active_orders.filter(
    lines__end_date__gte=now,
    lines__end_date__lte=within_24h
).distinct()
print(f"   Approaching orders (within 24h): {approaching.count()}")
for o in approaching:
    print(f"     - {o.order_number}")

urgent = active_orders.filter(
    models.Q(lines__end_date__lt=now) | 
    models.Q(lines__end_date__lte=within_24h, lines__end_date__gte=now)
).distinct()
print(f"   Urgent orders (approaching + overdue): {urgent.count()}")
for o in urgent:
    print(f"     - {o.order_number}")

print("\n" + "=" * 80)
print("VERIFICATION RESULTS")
print("=" * 80)

# Verify expectations
success = True

if not order1.is_return_overdue():
    print("✗ FAIL: Order 1 should be overdue")
    success = False
else:
    print("✓ PASS: Order 1 is correctly identified as overdue")

if not order2.has_approaching_return():
    print("✗ FAIL: Order 2 should have approaching return")
    success = False
else:
    print("✓ PASS: Order 2 is correctly identified as approaching")

if order3.has_approaching_return() or order3.is_return_overdue():
    print("✗ FAIL: Order 3 should be normal (neither approaching nor overdue)")
    success = False
else:
    print("✓ PASS: Order 3 is correctly identified as normal")

if order4.get_return_status() != 'returned':
    print("✗ FAIL: Order 4 should be marked as returned")
    success = False
else:
    print("✓ PASS: Order 4 is correctly identified as returned")

if urgent.count() < 2:
    print(f"✗ FAIL: Expected at least 2 urgent orders, found {urgent.count()}")
    success = False
else:
    print(f"✓ PASS: Found {urgent.count()} urgent orders")

print("\n" + "=" * 80)
if success:
    print("✓✓✓ RETURN DATE ALERTS: WORKING CORRECTLY ✓✓✓")
else:
    print("✗✗✗ RETURN DATE ALERTS: ISSUES DETECTED ✗✗✗")
print("=" * 80)

print(f"\nTest orders created: {[o.order_number for o in [order1, order2, order3, order4]]}")
print("\nYou can now:")
print("1. Visit /rental/orders/ to see order list with filters")
print("2. Click 'Urgent Returns' button to see overdue/approaching orders")
print("3. Check dashboard for urgent returns alert")
print("4. Use return_status filter: ?return_status=urgent")
