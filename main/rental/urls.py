from django.urls import path
from . import views

app_name = 'rental'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Product Management
    path('products/', views.product_manage, name='product_manage'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Order Management
    path('orders/', views.order_manage, name='order_manage'),
    path('orders/<int:pk>/', views.order_detail_manage, name='order_detail_manage'),
    path('orders/<int:pk>/update-status/', views.order_update_status, name='order_update_status'),
    
    # Pickup & Return
    path('orders/<int:order_id>/pickup/', views.record_pickup, name='record_pickup'),
    path('orders/<int:order_id>/return/', views.record_return, name='record_return'),
    
    # Invoice & Payment
    path('orders/<int:order_id>/invoice/', views.invoice_manage, name='invoice_manage'),
    path('invoice/<int:invoice_id>/payment/', views.record_payment, name='record_payment'),
]
