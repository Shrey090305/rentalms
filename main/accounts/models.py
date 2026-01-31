from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with roles and company information"""
    
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    company_name = models.CharField(max_length=200, blank=True)
    gstin = models.CharField(max_length=15, blank=True, help_text='GST Identification Number')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_customer(self):
        return self.role == 'customer'
    
    def is_vendor(self):
        return self.role == 'vendor'
    
    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser

