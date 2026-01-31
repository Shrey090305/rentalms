from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Product, ProductImage, ProductVariant, Quotation, QuotationLine,
    RentalOrder, OrderLine, Invoice, Payment, Return
)


class ProductForm(forms.ModelForm):
    """Form for creating/editing products"""
    
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'image', 'cost_price', 'sales_price',
            'price_per_hour', 'price_per_day', 'price_per_week',
            'quantity_on_hand', 'is_rentable', 'publish_on_website', 'attributes'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'attributes':
                field.widget.attrs['class'] = 'form-control'


class ProductImageForm(forms.ModelForm):
    """Form for adding individual product images"""
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'order']
        widgets = {
            'alt_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional description'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'value': 0}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class AddToCartForm(forms.Form):
    """Form for adding product to cart with rental dates"""
    quantity = forms.IntegerField(min_value=1, initial=1)
    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text='Rental start date and time'
    )
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text='Rental end date and time'
    )
    variant = forms.ModelChoiceField(
        queryset=ProductVariant.objects.none(),
        required=False,
        help_text='Select variant if available'
    )
    
    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        
        if product:
            # Set variant choices
            self.fields['variant'].queryset = product.variants.all()
            
            # Set max quantity based on available stock
            if product.quantity_on_hand > 0:
                self.fields['quantity'].widget.attrs['max'] = product.quantity_on_hand
        
        # Add Bootstrap classes
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        quantity = cleaned_data.get('quantity')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date")
            
            # Check availability
            if self.product:
                available = self.product.get_available_quantity(start_date, end_date)
                if quantity and quantity > available:
                    raise ValidationError(f"Only {available} units available for selected dates")
        
        return cleaned_data


class CheckoutForm(forms.ModelForm):
    """Checkout form for creating rental order"""
    
    class Meta:
        model = RentalOrder
        fields = ['delivery_method', 'delivery_address', 'delivery_city', 'delivery_state', 'delivery_pincode', 'notes']
        widgets = {
            'delivery_method': forms.RadioSelect,
            'delivery_address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pre-fill with user's info if available
        if user and not self.instance.pk:
            self.fields['delivery_address'].initial = user.address
            self.fields['delivery_city'].initial = user.city
            self.fields['delivery_state'].initial = user.state
            self.fields['delivery_pincode'].initial = user.pincode
        
        # Add Bootstrap classes
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class OrderStatusUpdateForm(forms.ModelForm):
    """Form for updating order status"""
    
    class Meta:
        model = RentalOrder
        fields = ['status']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].widget.attrs['class'] = 'form-select'


class PickupForm(forms.Form):
    """Form for recording pickup"""
    pickup_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text='Pickup date and time'
    )
    picked_by = forms.CharField(
        max_length=200,
        help_text='Name of person picking up'
    )
    id_proof = forms.CharField(
        max_length=100,
        required=False,
        help_text='ID proof number'
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ReturnForm(forms.ModelForm):
    """Form for recording return"""
    
    class Meta:
        model = Return
        fields = ['return_date', 'returned_by', 'condition_notes', 'damage_fee']
        widgets = {
            'return_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'condition_notes': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class PaymentForm(forms.ModelForm):
    """Form for recording payment"""
    
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, invoice=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.invoice = invoice
        
        # Set max amount to invoice balance
        if invoice:
            balance = invoice.get_balance()
            self.fields['amount'].widget.attrs['max'] = float(balance)
            self.fields['amount'].initial = balance
            self.fields['amount'].help_text = f'Maximum: ₹{balance}'
        
        # Add Bootstrap classes
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if self.invoice and amount > self.invoice.get_balance():
            raise ValidationError(f"Amount cannot exceed balance of ₹{self.invoice.get_balance()}")
        return amount


class ProductSearchForm(forms.Form):
    """Form for searching products"""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search products...',
            'class': 'form-control'
        })
    )
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'All Categories')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min Price',
            'class': 'form-control'
        })
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max Price',
            'class': 'form-control'
        })
    )
    available_only = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
