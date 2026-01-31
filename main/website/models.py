from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Coupon(models.Model):
    """Discount coupon codes"""
    code = models.CharField(max_length=50, unique=True, help_text="Coupon code (e.g., SAVE10)")
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=10.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage (0-100)"
    )
    is_active = models.BooleanField(default=True, help_text="Is this coupon currently active?")
    max_uses = models.IntegerField(default=0, help_text="Maximum total uses (0 = unlimited)")
    times_used = models.IntegerField(default=0, help_text="Number of times this coupon has been used")
    
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True, help_text="Leave blank for no expiration")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code} - {self.discount_percentage}% off"
    
    def is_valid(self):
        """Check if coupon is currently valid"""
        if not self.is_active:
            return False, "This coupon is inactive"
        
        now = timezone.now()
        if now < self.valid_from:
            return False, "This coupon is not yet valid"
        
        if self.valid_until and now > self.valid_until:
            return False, "This coupon has expired"
        
        if self.max_uses > 0 and self.times_used >= self.max_uses:
            return False, "This coupon has reached its usage limit"
        
        return True, "Coupon is valid"
    
    def can_be_used_by(self, user):
        """Check if a specific user can use this coupon"""
        # Check if coupon is valid
        is_valid, message = self.is_valid()
        if not is_valid:
            return False, message
        
        # Check if user has already used this coupon
        if CouponUsage.objects.filter(coupon=self, user=user).exists():
            return False, "You have already used this coupon"
        
        return True, "Coupon can be applied"
    
    class Meta:
        ordering = ['-created_at']


class CouponUsage(models.Model):
    """Track which users have used which coupons"""
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupon_usages')
    order = models.ForeignKey('rental.RentalOrder', on_delete=models.CASCADE, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    used_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} used {self.coupon.code}"
    
    class Meta:
        ordering = ['-used_at']
        unique_together = ['coupon', 'user']
