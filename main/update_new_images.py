import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from rental.models import Product

# Update Professional Camera
camera = Product.objects.filter(name__icontains='camera').first()
if camera:
    camera.image = 'products/professional_camera.jpg'
    camera.save()
    print(f'✓ Updated {camera.name} with professional_camera.jpg')
else:
    print('✗ Professional Camera not found')

# Update Video Projector
projector = Product.objects.filter(name__icontains='projector').first()
if projector:
    projector.image = 'products/video_projector.jpg'
    projector.save()
    print(f'✓ Updated {projector.name} with video_projector.jpg')
else:
    print('✗ Video Projector not found')

print('\nAll products status:')
print('-' * 60)
for p in Product.objects.all().order_by('id'):
    image_status = '✓' if p.image else '✗'
    print(f'{image_status} ID: {p.id}, Name: {p.name}, Image: {p.image.name if p.image else "None"}')
print('-' * 60)
