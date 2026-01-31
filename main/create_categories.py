"""
Script to create initial product categories
Based on common rental product types
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from rental.models import Category

print("=" * 80)
print("CREATING PRODUCT CATEGORIES")
print("=" * 80)

# Categories as mentioned in SVG diagram (e.g., Electronics, Furniture, etc.)
categories_data = [
    {
        'name': 'Electronics',
        'description': 'Electronic devices, gadgets, and equipment for rent including cameras, laptops, audio systems, etc.'
    },
    {
        'name': 'Furniture',
        'description': 'Furniture items for events, offices, and homes including chairs, tables, sofas, etc.'
    },
    {
        'name': 'Sports Equipment',
        'description': 'Sports and fitness equipment including bikes, gym equipment, outdoor gear, etc.'
    },
    {
        'name': 'Event Equipment',
        'description': 'Event and party equipment including decorations, tents, lighting, sound systems, etc.'
    },
    {
        'name': 'Vehicles',
        'description': 'Transportation rentals including cars, bikes, scooters, etc.'
    },
    {
        'name': 'Tools & Machinery',
        'description': 'Power tools, construction equipment, and machinery for rent'
    },
    {
        'name': 'Photography & Video',
        'description': 'Professional photography and videography equipment including cameras, lenses, lighting, etc.'
    },
    {
        'name': 'Musical Instruments',
        'description': 'Musical instruments for rent including guitars, keyboards, drums, etc.'
    },
    {
        'name': 'Party Supplies',
        'description': 'Party decorations, costumes, games, and entertainment equipment'
    },
    {
        'name': 'Camping & Outdoor',
        'description': 'Camping gear, hiking equipment, and outdoor adventure supplies'
    },
    {
        'name': 'Home Appliances',
        'description': 'Home appliances for temporary use including refrigerators, washing machines, etc.'
    },
    {
        'name': 'Office Equipment',
        'description': 'Office furniture, electronics, and supplies for rent'
    },
]

created_count = 0
updated_count = 0
skipped_count = 0

for cat_data in categories_data:
    category, created = Category.objects.get_or_create(
        name=cat_data['name'],
        defaults={
            'description': cat_data['description'],
            'is_active': True
        }
    )
    
    if created:
        print(f"✓ Created: {category.name} (slug: {category.slug})")
        created_count += 1
    else:
        # Update description if it changed
        if category.description != cat_data['description']:
            category.description = cat_data['description']
            category.save()
            print(f"↻ Updated: {category.name}")
            updated_count += 1
        else:
            print(f"- Skipped: {category.name} (already exists)")
            skipped_count += 1

print("\n" + "=" * 80)
print("CATEGORY CREATION SUMMARY")
print("=" * 80)
print(f"Created: {created_count}")
print(f"Updated: {updated_count}")
print(f"Skipped: {skipped_count}")
print(f"Total categories: {Category.objects.count()}")
print("=" * 80)

# Show all categories
print("\nAll Categories:")
for cat in Category.objects.all().order_by('name'):
    product_count = cat.products.count()
    print(f"  - {cat.name} ({product_count} products)")

print("\n✓ Categories are now available for product assignment!")
print("  You can:")
print("  1. Assign categories to products in Django admin")
print("  2. Filter products by category on the website")
print("  3. Manage categories in admin panel")
