import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from rental.models import Product

# Update Laptop Computer
laptop = Product.objects.filter(name__icontains='laptop').first()
if laptop:
    laptop.image = 'products/laptop_computer.jpg'
    laptop.save()
    print(f'✓ Updated {laptop.name} with laptop_computer.jpg')
else:
    print('✗ Laptop Computer not found')

# Update Sound System
sound = Product.objects.filter(name__icontains='sound').first()
if sound:
    sound.image = 'products/sound_system.jpg'
    sound.save()
    print(f'✓ Updated {sound.name} with sound_system.jpg')
else:
    print('✗ Sound System not found')

print('\nUpdated products:')
print('-' * 60)
for p in Product.objects.filter(id__in=[3, 4]):
    print(f'ID: {p.id}, Name: {p.name}, Image: {p.image.name if p.image else "None"}')
print('-' * 60)
