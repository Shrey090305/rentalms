from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, ProductAttribute, AttributeValue, Product, ProductVariant,
    Quotation, QuotationLine, RentalOrder, OrderLine,
    Pickup, Return, Invoice, Payment, SystemSettings
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'product_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ['attribute', 'value']
    list_filter = ['attribute']
    search_fields = ['value']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'vendor', 'quantity_on_hand', 'price_per_day', 'is_rentable', 'publish_on_website']
    list_filter = ['category', 'is_rentable', 'publish_on_website', 'vendor']
    search_fields = ['name', 'description']
    filter_horizontal = ['attributes']
    inlines = [ProductVariantInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('vendor', 'category', 'name', 'description', 'image')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'sales_price', 'price_per_hour', 'price_per_day', 'price_per_week')
        }),
        ('Inventory', {
            'fields': ('quantity_on_hand',)
        }),
        ('Settings', {
            'fields': ('is_rentable', 'publish_on_website', 'attributes')
        }),
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'sku', 'quantity_on_hand']
    list_filter = ['product']
    search_fields = ['name', 'sku']


class QuotationLineInline(admin.TabularInline):
    model = QuotationLine
    extra = 0
    readonly_fields = ['get_total']
    
    def get_total(self, obj):
        return f"₹{obj.get_total()}"
    get_total.short_description = 'Total'


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'get_total_display', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer__username', 'customer__email']
    inlines = [QuotationLineInline]
    readonly_fields = ['created_at', 'updated_at']
    
    def get_total_display(self, obj):
        return f"₹{obj.get_total()}"
    get_total_display.short_description = 'Total'


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    readonly_fields = ['get_total']
    
    def get_total(self, obj):
        return f"₹{obj.get_total()}"
    get_total.short_description = 'Total'


@admin.register(RentalOrder)
class RentalOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'status', 'get_total_display', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'customer__username', 'customer__email']
    inlines = [OrderLineInline]
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'confirmed_at']
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'customer', 'quotation', 'status')
        }),
        ('Delivery Info', {
            'fields': ('delivery_address', 'delivery_city', 'delivery_state', 'delivery_pincode')
        }),
        ('Additional', {
            'fields': ('notes', 'created_at', 'updated_at', 'confirmed_at')
        }),
    )
    
    def get_total_display(self, obj):
        return f"₹{obj.get_total()}"
    get_total_display.short_description = 'Total'


@admin.register(Pickup)
class PickupAdmin(admin.ModelAdmin):
    list_display = ['order', 'pickup_date', 'picked_by', 'created_at']
    list_filter = ['pickup_date']
    search_fields = ['order__order_number', 'picked_by']


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['order', 'return_date', 'returned_by', 'late_fee', 'damage_fee']
    list_filter = ['return_date']
    search_fields = ['order__order_number', 'returned_by']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'order', 'status', 'total_amount', 'amount_paid', 'get_balance', 'created_at']
    list_filter = ['status', 'payment_term', 'created_at']
    search_fields = ['invoice_number', 'order__order_number']
    inlines = [PaymentInline]
    readonly_fields = ['invoice_number', 'subtotal', 'tax_amount', 'total_amount', 'get_balance', 'created_at']
    
    fieldsets = (
        ('Invoice Info', {
            'fields': ('invoice_number', 'order', 'status', 'payment_term')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'tax_rate', 'tax_amount', 'security_deposit', 'late_fee', 'total_amount', 'amount_paid', 'get_balance')
        }),
        ('Dates', {
            'fields': ('created_at', 'due_date', 'paid_at')
        }),
        ('Additional', {
            'fields': ('notes',)
        }),
    )
    
    def get_balance(self, obj):
        return f"₹{obj.get_balance()}"
    get_balance.short_description = 'Balance'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_method', 'reference_number', 'created_at']
    list_filter = ['payment_method', 'created_at']
    search_fields = ['invoice__invoice_number', 'reference_number']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'description']
    search_fields = ['key', 'description']

