from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal
import json


class Category(models.Model):
    """Product categories like Electronics, Furniture, Sports, etc."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'


class ProductAttribute(models.Model):
    """Attributes like Brand, Color, Size, etc."""
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class AttributeValue(models.Model):
    """Values for attributes"""
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"
    
    class Meta:
        unique_together = ['attribute', 'value']
        ordering = ['attribute', 'value']


class Product(models.Model):
    """Main product model"""
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sales_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Rental pricing
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    price_per_week = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    
    # Inventory
    quantity_on_hand = models.IntegerField(default=0)
    
    # Flags
    is_rentable = models.BooleanField(default=True)
    publish_on_website = models.BooleanField(default=True)
    
    # Attributes
    attributes = models.ManyToManyField(AttributeValue, blank=True, related_name='products')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_available_quantity(self, start_date=None, end_date=None):
        """Calculate available quantity for given date range"""
        if not start_date or not end_date:
            return self.quantity_on_hand
        
        # Check overlapping rentals
        overlapping = OrderLine.objects.filter(
            product=self,
            order__status__in=['confirmed', 'picked_up', 'rented'],
            start_date__lt=end_date,
            end_date__gt=start_date
        )
        
        reserved_qty = sum(line.quantity for line in overlapping)
        return max(0, self.quantity_on_hand - reserved_qty)
    
    def calculate_rental_price(self, start_date, end_date):
        """Calculate rental price based on duration"""
        if not start_date or not end_date:
            return Decimal('0.00')
        
        duration = end_date - start_date
        hours = duration.total_seconds() / 3600
        days = duration.days
        weeks = days // 7
        
        # Choose best pricing strategy
        if weeks > 0 and self.price_per_week > 0:
            return self.price_per_week * weeks
        elif days > 0 and self.price_per_day > 0:
            return self.price_per_day * days
        elif hours > 0 and self.price_per_hour > 0:
            return self.price_per_hour * Decimal(str(hours))
        else:
            return self.sales_price
    
    class Meta:
        ordering = ['-created_at']


class ProductVariant(models.Model):
    """Product variants with different pricing/stock"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    
    # Variant-specific pricing (overrides product pricing if set)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_week = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    quantity_on_hand = models.IntegerField(default=0)
    attributes = models.ManyToManyField(AttributeValue, blank=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    def get_price_per_hour(self):
        return self.price_per_hour or self.product.price_per_hour
    
    def get_price_per_day(self):
        return self.price_per_day or self.product.price_per_day
    
    def get_price_per_week(self):
        return self.price_per_week or self.product.price_per_week


class Quotation(models.Model):
    """Cart/Quotation before confirmation"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quotations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Quotation {self.id} - {self.customer.username}"
    
    def get_total(self):
        return sum(line.get_total() for line in self.lines.all())
    
    def get_tax_amount(self, tax_rate=18):
        """Calculate GST"""
        subtotal = self.get_total()
        return subtotal * Decimal(str(tax_rate / 100))
    
    def get_grand_total(self, tax_rate=18):
        return self.get_total() + self.get_tax_amount(tax_rate)


class QuotationLine(models.Model):
    """Line items in quotation"""
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def get_total(self):
        return self.unit_price * self.quantity
    
    def clean(self):
        """Validate availability"""
        if self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date")
        
        available = self.product.get_available_quantity(self.start_date, self.end_date)
        if self.quantity > available:
            raise ValidationError(f"Only {available} units available for selected dates")


class RentalOrder(models.Model):
    """Confirmed rental order"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('picked_up', 'Picked Up'),
        ('rented', 'Rented'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('home_delivery', 'Home Delivery'),
        ('pickup', 'Pickup from Warehouse'),
    ]
    
    quotation = models.OneToOneField(Quotation, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Delivery info
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHOD_CHOICES, default='home_delivery', help_text='How would you like to receive the product?')
    delivery_address = models.TextField(blank=True)
    delivery_city = models.CharField(max_length=100, blank=True)
    delivery_state = models.CharField(max_length=100, blank=True)
    delivery_pincode = models.CharField(max_length=10, blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            import random
            self.order_number = f"RO{timezone.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        super().save(*args, **kwargs)
    
    def get_total(self):
        return sum(line.get_total() for line in self.lines.all())
    
    def get_tax_amount(self, tax_rate=18):
        subtotal = self.get_total()
        return subtotal * Decimal(str(tax_rate / 100))
    
    def get_grand_total(self, tax_rate=18):
        return self.get_total() + self.get_tax_amount(tax_rate)
    
    def get_latest_return_date(self):
        """Get the latest return date from all order lines"""
        return max((line.end_date for line in self.lines.all()), default=None)
    
    def has_approaching_return(self):
        """Check if return date is within 1 day"""
        if self.status not in ['picked_up', 'rented']:
            return False
        
        latest_return = self.get_latest_return_date()
        if not latest_return:
            return False
        
        now = timezone.now()
        time_until_return = latest_return - now
        
        # Check if return is within next 24 hours
        return timezone.timedelta(hours=0) <= time_until_return <= timezone.timedelta(hours=24)
    
    def is_return_overdue(self):
        """Check if return date has passed"""
        if self.status not in ['picked_up', 'rented']:
            return False
        
        latest_return = self.get_latest_return_date()
        if not latest_return:
            return False
        
        return timezone.now() > latest_return
    
    def get_return_status(self):
        """Get return status: 'overdue', 'approaching', 'normal', or 'returned'"""
        if self.status == 'returned':
            return 'returned'
        if self.is_return_overdue():
            return 'overdue'
        if self.has_approaching_return():
            return 'approaching'
        return 'normal'


class OrderLine(models.Model):
    """Line items in rental order"""
    order = models.ForeignKey(RentalOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def get_total(self):
        return self.unit_price * self.quantity
    
    def clean(self):
        """Validate date range and availability"""
        if self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date")
        
        # Check for overlapping reservations (excluding self if updating)
        overlapping = OrderLine.objects.filter(
            product=self.product,
            order__status__in=['confirmed', 'picked_up', 'rented'],
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        ).exclude(id=self.id if self.id else None)
        
        reserved_qty = sum(line.quantity for line in overlapping)
        available = self.product.quantity_on_hand - reserved_qty
        
        if self.quantity > available:
            raise ValidationError(f"Only {available} units available for selected dates. {reserved_qty} already reserved.")


class Pickup(models.Model):
    """Pickup document"""
    order = models.OneToOneField(RentalOrder, on_delete=models.CASCADE, related_name='pickup')
    pickup_date = models.DateTimeField(default=timezone.now)
    picked_by = models.CharField(max_length=200, help_text="Person who picked up")
    id_proof = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Pickup for {self.order.order_number}"


class Return(models.Model):
    """Return document"""
    order = models.OneToOneField(RentalOrder, on_delete=models.CASCADE, related_name='return_doc')
    return_date = models.DateTimeField(default=timezone.now)
    returned_by = models.CharField(max_length=200)
    condition_notes = models.TextField(blank=True, help_text="Condition of returned items")
    
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    damage_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Return for {self.order.order_number}"
    
    def calculate_late_fee(self, daily_rate=100):
        """Calculate late fee if returned after end date"""
        total_late_days = 0
        for line in self.order.lines.all():
            if self.return_date > line.end_date:
                late_duration = self.return_date - line.end_date
                late_days = late_duration.days
                if late_days > 0:
                    total_late_days += late_days
        
        return Decimal(str(daily_rate * total_late_days))


class Invoice(models.Model):
    """Invoice for rental order"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_TERM_CHOICES = [
        ('full_upfront', 'Full Upfront'),
        ('partial_upfront', 'Partial + Security Deposit'),
        ('after_delivery', 'After Delivery'),
    ]
    
    order = models.OneToOneField(RentalOrder, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_term = models.CharField(max_length=30, choices=PAYMENT_TERM_CHOICES, default='full_upfront')
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Coupon discount amount")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)  # GST percentage
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            import random
            self.invoice_number = f"INV{timezone.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        
        # Calculate totals
        if self.order:
            self.subtotal = self.order.get_total()
            # Apply discount first
            subtotal_after_discount = self.subtotal - self.discount_amount
            # Calculate tax on discounted amount
            self.tax_amount = subtotal_after_discount * (self.tax_rate / 100)
            self.total_amount = subtotal_after_discount + self.tax_amount + self.security_deposit + self.late_fee
        
        super().save(*args, **kwargs)
    
    def get_balance(self):
        return self.total_amount - self.amount_paid
    
    def is_fully_paid(self):
        return self.amount_paid >= self.total_amount


class Payment(models.Model):
    """Payment records"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Wallet'),
        ('bank_transfer', 'Bank Transfer'),
        ('mock', 'Mock Payment'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment {self.amount} for {self.invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update invoice paid amount
        total_paid = sum(p.amount for p in self.invoice.payments.all())
        self.invoice.amount_paid = total_paid
        
        # Update status
        if total_paid >= self.invoice.total_amount:
            self.invoice.status = 'paid'
            self.invoice.paid_at = timezone.now()
        elif total_paid > 0:
            self.invoice.status = 'partially_paid'
        
        self.invoice.save()


class SystemSettings(models.Model):
    """System-wide settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.key
    
    @staticmethod
    def get_setting(key, default=''):
        try:
            setting = SystemSettings.objects.get(key=key)
            return setting.value
        except SystemSettings.DoesNotExist:
            return default
    
    @staticmethod
    def set_setting(key, value, description=''):
        setting, created = SystemSettings.objects.get_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        if not created:
            setting.value = value
            if description:
                setting.description = description
            setting.save()
        return setting
    
    class Meta:
        verbose_name_plural = "System Settings"


# Signal handlers for inventory management
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver

@receiver(pre_save, sender=RentalOrder)
def restore_quantity_on_cancel(sender, instance, **kwargs):
    """Restore product quantity when order is cancelled or returned"""
    if instance.pk:  # Only for existing orders
        try:
            old_order = RentalOrder.objects.get(pk=instance.pk)
            # If order status changed to cancelled or returned
            if old_order.status not in ['cancelled', 'returned'] and instance.status in ['cancelled', 'returned']:
                # Restore quantities for all order lines
                for line in instance.lines.all():
                    line.product.quantity_on_hand += line.quantity
                    line.product.save()
        except RentalOrder.DoesNotExist:
            pass

@receiver(post_delete, sender=OrderLine)
def restore_quantity_on_delete(sender, instance, **kwargs):
    """Restore product quantity when order line is deleted"""
    if instance.order.status not in ['cancelled', 'returned']:
        instance.product.quantity_on_hand += instance.quantity
        instance.product.save()
