import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from website.models import Coupon, CouponUsage
from accounts.models import User

print("=" * 60)
print("TESTING COUPON VALIDATION")
print("=" * 60)

# Get a customer user
try:
    customer = User.objects.filter(role='customer').first()
    if not customer:
        print("❌ No customer users found!")
        exit(1)
    
    print(f"\n✓ Testing with customer: {customer.username}")
    
    # Test each coupon
    coupons = Coupon.objects.filter(is_active=True)
    print(f"\n✓ Found {coupons.count()} active coupons\n")
    
    for coupon in coupons:
        print(f"Testing: {coupon.code}")
        
        # Check if coupon is valid
        is_valid, message = coupon.is_valid()
        print(f"  Valid: {is_valid} - {message}")
        
        # Check if user can use it
        can_use, user_message = coupon.can_be_used_by(customer)
        print(f"  Can use: {can_use} - {user_message}")
        
        # Check usage history
        usage_count = CouponUsage.objects.filter(coupon=coupon, user=customer).count()
        print(f"  Usage count for {customer.username}: {usage_count}")
        
        print("-" * 60)
    
    print("\n✓ All coupons tested successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
