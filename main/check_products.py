import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from rental.models import Product

products = Product.objects.all()
print('\nProducts in database:')
print('-' * 60)
for p in products:
    image_name = p.image.name if p.image else 'None'
    print(f'ID: {p.id}, Name: {p.name}, Image: {image_name}')
print('-' * 60)
