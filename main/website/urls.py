from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.my_orders, name='my_orders'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('invoice/<int:pk>/', views.invoice_view, name='invoice'),
    path('invoice/<int:pk>/download/', views.invoice_pdf_download, name='invoice_download'),
    path('payment/<int:invoice_id>/', views.payment_view, name='payment'),
    path('payment/<int:invoice_id>/success/', views.payment_success, name='payment_success'),
]
