from .models import Quotation


def cart_processor(request):
    """Add cart/quotation info to all templates"""
    cart_count = 0
    cart = None
    
    if request.user.is_authenticated and hasattr(request.user, 'is_customer') and request.user.is_customer():
        # Get or create draft quotation
        cart = Quotation.objects.filter(
            customer=request.user,
            status='draft'
        ).first()
        
        if cart:
            cart_count = sum(line.quantity for line in cart.lines.all())
    
    return {
        'cart': cart,
        'cart_count': cart_count,
    }
