from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class SignUpForm(UserCreationForm):
    """Customer signup form"""
    email = forms.EmailField(required=True)
    company_name = forms.CharField(max_length=200, required=True)
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
        fields = ['username', 'email', 'password1', 'password2', 'company_name', 'gstin', 
                  'phone', 'address', 'city', 'state', 'pincode']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'coupon_code':
                field.widget.attrs['placeholder'] = 'Enter coupon code (optional)'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'customer'
        user.email = self.cleaned_data['email']
        user.company_name = self.cleaned_data['company_name']
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
        fields = ['email', 'company_name', 'gstin', 'phone', 'address', 'city', 'state', 'pincode']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
