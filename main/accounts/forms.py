from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class SignUpForm(UserCreationForm):
    """Signup form for customers and vendors"""
    ROLE_CHOICES = [
        ('customer', 'Customer - Rent Products'),
        ('vendor', 'Vendor - List Products for Rent'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        initial='customer',
        required=True,
        help_text='Select your account type'
    )
    email = forms.EmailField(required=True)
    profile_pic = forms.ImageField(required=False, help_text='Profile picture')
    company_name = forms.CharField(max_length=200, required=True)
    company_logo = forms.ImageField(required=False, help_text='Company logo for invoices (recommended: 200x80px)')
    gstin = forms.CharField(
        max_length=15, 
        required=True,
        help_text='GST Identification Number (15 characters)'
    )
    phone = forms.CharField(max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    city = forms.CharField(max_length=100, required=False)
    state = forms.CharField(max_length=100, required=False)
    pincode = forms.CharField(max_length=10, required=False)
    coupon_code = forms.CharField(max_length=50, required=False, help_text='Optional coupon code')
    
    class Meta:
        model = User
        fields = ['role', 'username', 'email', 'password1', 'password2', 'profile_pic', 'company_name', 'company_logo', 'gstin', 
                  'phone', 'address', 'city', 'state', 'pincode']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if field_name != 'role':  # Radio buttons don't need form-control class
                field.widget.attrs['class'] = 'form-control'
            if field_name == 'coupon_code':
                field.widget.attrs['placeholder'] = 'Enter coupon code (optional)'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']  # Use selected role
        user.email = self.cleaned_data['email']
        if self.cleaned_data.get('profile_pic'):
            user.profile_pic = self.cleaned_data['profile_pic']
        user.company_name = self.cleaned_data['company_name']
        if self.cleaned_data.get('company_logo'):
            user.company_logo = self.cleaned_data['company_logo']
        user.gstin = self.cleaned_data['gstin']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data.get('address', '')
        user.city = self.cleaned_data.get('city', '')
        user.state = self.cleaned_data.get('state', '')
        user.pincode = self.cleaned_data.get('pincode', '')
        
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """User profile edit form"""
    
    class Meta:
        model = User
        fields = ['email', 'profile_pic', 'company_name', 'company_logo', 'gstin', 'phone', 'address', 'city', 'state', 'pincode']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = kwargs.get('instance')
        
        # Remove fields based on user role
        if user:
            if user.role == 'customer':
                # Customers don't need company logo
                if 'company_logo' in self.fields:
                    del self.fields['company_logo']
            else:
                # Vendors/admins don't need profile pic in this form (they can use company logo)
                if 'profile_pic' in self.fields:
                    del self.fields['profile_pic']
        
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
