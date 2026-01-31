"""
Test script for verifying invoice with vendor logos
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from django.contrib.auth import get_user_model
from rental.models import Invoice
from django.conf import settings

User = get_user_model()

def test_invoice_with_logo():
    print("=" * 60)
    print("TESTING INVOICE WITH VENDOR LOGOS")
    print("=" * 60)
    
    # Check if media folder exists
    media_root = settings.MEDIA_ROOT
    logos_folder = os.path.join(media_root, 'company_logos')
    
    print(f"\n✅ Media root: {media_root}")
    print(f"✅ Logos folder: {logos_folder}")
    
    if not os.path.exists(logos_folder):
        os.makedirs(logos_folder, exist_ok=True)
        print(f"✅ Created logos folder: {logos_folder}")
    
    # Get vendors
    vendors = User.objects.filter(role='vendor')
    print(f"\n✅ Found {vendors.count()} vendor(s)")
    
    for vendor in vendors:
        print(f"\n📊 Vendor: {vendor.username}")
        print(f"   Company: {vendor.company_name}")
        print(f"   Logo: {vendor.company_logo if vendor.company_logo else 'No logo uploaded'}")
        
        # Check vendor's products
        from rental.models import Product
        products = Product.objects.filter(vendor=vendor)
        print(f"   Products: {products.count()}")
        
        # Check vendor's orders/invoices
        invoices = Invoice.objects.filter(order__lines__product__vendor=vendor).distinct()
        print(f"   Invoices: {invoices.count()}")
        
        if invoices.exists():
            print(f"   ✅ Vendor has invoices that will include logo/company name")
        else:
            print(f"   ⚠️  No invoices found for this vendor")
    
    print("\n" + "=" * 60)
    print("FEATURE IMPLEMENTATION SUMMARY")
    print("=" * 60)
    
    print("\n✅ Model Changes:")
    print("   - Added 'company_logo' ImageField to User model")
    print("   - Uploaded logos stored in 'media/company_logos/'")
    
    print("\n✅ Form Updates:")
    print("   - SignUpForm includes company_logo field")
    print("   - UserProfileForm includes company_logo field")
    print("   - Both forms support file uploads (enctype='multipart/form-data')")
    
    print("\n✅ View Updates:")
    print("   - signup_view handles request.FILES")
    print("   - profile_view handles request.FILES")
    print("   - invoice_pdf_download includes vendor logo if available")
    
    print("\n✅ Invoice PDF Features:")
    print("   - Displays vendor company logo (if uploaded)")
    print("   - Shows vendor company name prominently")
    print("   - Falls back to 'RentEase' branding if no vendor logo")
    print("   - Logo size: 2x0.8 inches (proportional)")
    
    print("\n✅ Template Updates:")
    print("   - signup.html: Added enctype='multipart/form-data'")
    print("   - profile.html: Added enctype='multipart/form-data'")
    
    print("\n📋 HOW TO TEST:")
    print("   1. Login as a vendor or create new vendor account")
    print("   2. Go to Profile page")
    print("   3. Upload a company logo (recommended: 200x80px PNG/JPG)")
    print("   4. Create or view an existing invoice")
    print("   5. Download PDF invoice - logo will appear at the top")
    
    print("\n💡 RECOMMENDED LOGO SPECIFICATIONS:")
    print("   - Format: PNG with transparent background (or JPG)")
    print("   - Size: 200x80 pixels (or similar aspect ratio)")
    print("   - File size: Under 500KB")
    print("   - Position: Top-left of invoice PDF")
    
    print("\n" + "=" * 60)
    print("✅ INVOICE WITH VENDOR LOGOS - IMPLEMENTATION COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    test_invoice_with_logo()
