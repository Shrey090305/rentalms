import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from rental.models import Product
from django.db.models import Q

search_term = 'sh'
print(f"Searching for: '{search_term}'")
print("=" * 80)

products = Product.objects.filter(
    Q(name__icontains=search_term) | 
    Q(description__icontains=search_term) |
    Q(vendor__company_name__icontains=search_term),
    publish_on_website=True,
    is_rentable=True
)

print(f"\nFound {products.count()} products:\n")

for p in products:
    print(f"Product: {p.name}")
    
    # Check where the match is
    if search_term.lower() in p.name.lower():
        print(f"  ✓ Matched in NAME: '{p.name}'")
    
    if search_term.lower() in p.description.lower():
        # Find the context around the match
        desc_lower = p.description.lower()
        idx = desc_lower.find(search_term.lower())
        start = max(0, idx - 20)
        end = min(len(p.description), idx + len(search_term) + 20)
        context = p.description[start:end]
        print(f"  ✓ Matched in DESCRIPTION: '...{context}...'")
    
    if search_term.lower() in p.vendor.company_name.lower():
        print(f"  ✓ Matched in VENDOR: '{p.vendor.company_name}'")
    
    print("-" * 80)
