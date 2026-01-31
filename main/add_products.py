import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from accounts.models import User
from rental.models import Product
from decimal import Decimal

# Get or create a vendor user
vendor = User.objects.filter(role='vendor').first()
if not vendor:
    vendor = User.objects.create_user(
        username='vendor1',
        email='vendor@rentease.com',
        password='vendor123',
        role='vendor',
        company_name='Equipment Rentals Inc.',
    )
    print("Created vendor user: vendor1")

# Products data
products_data = [
    {
        'name': 'Professional Camera',
        'description': 'High-quality DSLR camera perfect for events and photography',
        'cost_price': Decimal('50000.00'),
        'sales_price': Decimal('75000.00'),
        'price_per_hour': Decimal('500.00'),
        'price_per_day': Decimal('3000.00'),
        'price_per_week': Decimal('18000.00'),
        'quantity_on_hand': 5,
    },
    {
        'name': 'Video Projector',
        'description': 'HD projector for presentations and events',
        'cost_price': Decimal('30000.00'),
        'sales_price': Decimal('45000.00'),
        'price_per_hour': Decimal('300.00'),
        'price_per_day': Decimal('2000.00'),
        'price_per_week': Decimal('12000.00'),
        'quantity_on_hand': 8,
    },
    {
        'name': 'Laptop Computer',
        'description': 'High-performance laptop for business use',
        'cost_price': Decimal('40000.00'),
        'sales_price': Decimal('60000.00'),
        'price_per_hour': Decimal('200.00'),
        'price_per_day': Decimal('1500.00'),
        'price_per_week': Decimal('9000.00'),
        'quantity_on_hand': 10,
    },
    {
        'name': 'Sound System',
        'description': 'Professional PA system for events',
        'cost_price': Decimal('80000.00'),
        'sales_price': Decimal('120000.00'),
        'price_per_hour': Decimal('800.00'),
        'price_per_day': Decimal('5000.00'),
        'price_per_week': Decimal('30000.00'),
        'quantity_on_hand': 3,
    },
    {
        'name': 'LED Lights',
        'description': 'Professional lighting equipment for photo/video shoots',
        'cost_price': Decimal('25000.00'),
        'sales_price': Decimal('35000.00'),
        'price_per_hour': Decimal('400.00'),
        'price_per_day': Decimal('2500.00'),
        'price_per_week': Decimal('15000.00'),
        'quantity_on_hand': 12,
    },
]

# Create products
created_count = 0
for product_data in products_data:
    product, created = Product.objects.get_or_create(
        name=product_data['name'],
        vendor=vendor,
        defaults=product_data
    )
    if created:
        print(f"✓ Created: {product.name}")
        created_count += 1
    else:
        print(f"Already exists: {product.name}")

print(f"\n{'='*50}")
print(f"Total products created: {created_count}")
print(f"Total products in database: {Product.objects.count()}")
print(f"{'='*50}")
