"""
Test script for verifying the reporting module functionality
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from django.contrib.auth import get_user_model
from rental.models import Product, RentalOrder, OrderLine, Invoice
from decimal import Decimal

User = get_user_model()

def test_reports():
    print("=" * 60)
    print("TESTING REPORTING MODULE")
    print("=" * 60)
    
    # Get a vendor user
    vendor = User.objects.filter(role='vendor').first()
    if not vendor:
        print("❌ No vendor user found. Please create a vendor user first.")
        return
    
    print(f"\n✅ Testing with vendor: {vendor.username}")
    
    # Get vendor's products
    products = Product.objects.filter(vendor=vendor)
    print(f"✅ Vendor has {products.count()} products")
    
    # Get vendor's orders
    orders = RentalOrder.objects.filter(lines__product__vendor=vendor).distinct()
    print(f"✅ Vendor has {orders.count()} orders")
    
    # Test sales metrics
    print("\n" + "-" * 60)
    print("SALES REPORT METRICS")
    print("-" * 60)
    
    total_orders = orders.count()
    total_revenue = sum(order.invoice.total_amount for order in orders if hasattr(order, 'invoice'))
    print(f"Total Orders: {total_orders}")
    print(f"Total Revenue: ₹{total_revenue}")
    
    if total_orders > 0:
        avg_order_value = total_revenue / total_orders
        print(f"Average Order Value: ₹{avg_order_value:.2f}")
    
    # Test product metrics
    print("\n" + "-" * 60)
    print("PRODUCT REPORT METRICS")
    print("-" * 60)
    
    rentable_products = products.filter(is_rentable=True).count()
    print(f"Total Products: {products.count()}")
    print(f"Rentable Products: {rentable_products}")
    
    # Count rentals per product
    from django.db.models import Count
    order_lines = OrderLine.objects.filter(product__vendor=vendor)
    product_rentals = order_lines.values('product__name').annotate(
        rental_count=Count('id')
    ).order_by('-rental_count')[:5]
    
    print("\nTop 5 Most Rented Products:")
    for i, item in enumerate(product_rentals, 1):
        print(f"  {i}. {item['product__name']}: {item['rental_count']} rentals")
    
    # Test low stock
    low_stock = products.filter(stock__lte=5, is_rentable=True)
    print(f"\n⚠️  Low Stock Products (≤5 units): {low_stock.count()}")
    for product in low_stock[:3]:
        print(f"  - {product.name}: {product.stock} units")
    
    # Test revenue metrics
    print("\n" + "-" * 60)
    print("REVENUE REPORT METRICS")
    print("-" * 60)
    
    invoices = Invoice.objects.filter(order__lines__product__vendor=vendor).distinct()
    total_invoiced = sum(inv.total_amount for inv in invoices)
    total_paid = sum(inv.amount_paid for inv in invoices)
    total_pending = total_invoiced - total_paid
    
    print(f"Total Invoiced: ₹{total_invoiced}")
    print(f"Total Paid: ₹{total_paid}")
    print(f"Total Pending: ₹{total_pending}")
    
    if total_invoiced > 0:
        collection_rate = (total_paid / total_invoiced) * 100
        print(f"Collection Rate: {collection_rate:.1f}%")
    
    # Test customer metrics
    print("\n" + "-" * 60)
    print("CUSTOMER REPORT METRICS")
    print("-" * 60)
    
    unique_customers = orders.values('customer').distinct().count()
    print(f"Total Unique Customers: {unique_customers}")
    
    # New vs returning customers
    from django.db.models import Count
    customer_orders = orders.values('customer').annotate(
        order_count=Count('id')
    )
    
    new_customers = customer_orders.filter(order_count=1).count()
    returning_customers = customer_orders.filter(order_count__gt=1).count()
    
    print(f"New Customers (1 order): {new_customers}")
    print(f"Returning Customers (2+ orders): {returning_customers}")
    
    if unique_customers > 0:
        retention_rate = (returning_customers / unique_customers) * 100
        print(f"Customer Retention Rate: {retention_rate:.1f}%")
    
    print("\n" + "=" * 60)
    print("✅ REPORTING MODULE TEST COMPLETED")
    print("=" * 60)
    print("\nTo view the reports:")
    print("1. Login as a vendor or admin user")
    print("2. Click on 'Reports' in the navigation menu")
    print("3. Explore the 4 different reports:")
    print("   - Sales Report (orders, revenue, trends)")
    print("   - Product Report (most rented, categories, stock)")
    print("   - Revenue Report (financial overview, payments)")
    print("   - Customer Report (spending, retention)")
    print("=" * 60)

if __name__ == '__main__':
    test_reports()
