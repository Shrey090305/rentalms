from django.contrib import admin
from .models import Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percentage', 'is_active', 'times_used', 'max_uses', 'valid_from', 'valid_until']
    list_filter = ['is_active', 'valid_from', 'valid_until']
    search_fields = ['code']
    readonly_fields = ['times_used', 'created_at', 'updated_at']
    fieldsets = (
        ('Coupon Details', {
            'fields': ('code', 'discount_percentage', 'is_active')
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'times_used')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'discount_amount', 'used_at', 'order']
    list_filter = ['used_at', 'coupon']
    search_fields = ['coupon__code', 'user__username', 'user__email']
    readonly_fields = ['used_at']
    raw_id_fields = ['user', 'order']
