import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from website.models import Coupon

print("=" * 60)
print("AVAILABLE COUPON CODES")
print("=" * 60)

coupons = Coupon.objects.all()
print(f"\nTotal Coupons: {coupons.count()}\n")

for coupon in coupons:
    print(f"Code: {coupon.code}")
    print(f"Discount: {coupon.discount_percentage}%")
    print(f"Max Uses: {coupon.max_uses} (Used: {coupon.times_used} times)")
    print(f"Active: {'✓ Yes' if coupon.is_active else '✗ No'}")
    print(f"Valid From: {coupon.valid_from.strftime('%Y-%m-%d %H:%M')}")
    print(f"Valid Until: {coupon.valid_until.strftime('%Y-%m-%d %H:%M') if coupon.valid_until else 'No expiration'}")
    
    # Check if currently valid
    is_valid, message = coupon.is_valid()
    print(f"Status: {'✓ VALID' if is_valid else f'✗ {message}'}")
    print("=" * 60)
