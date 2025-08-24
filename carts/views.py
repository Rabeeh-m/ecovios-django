
# carts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product
from .models import Cart, CartItem, Coupon  # Import Coupon here
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from store.models import Wishlist
from accounts.models import UserAddress
import math
from django.views.decorators.cache import cache_control
from django.http import JsonResponse
from django.utils import timezone


def _cart_id(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
    
    # Remove the product from the wishlist
    Wishlist.objects.filter(user=request.user, product=product).delete()
    cart.save()
    
    # try:
    #     cart_item = CartItem.objects.get(product=product, cart=cart)
    #     cart_item.quantity += 1
    #     cart_item.save()
    # except CartItem.DoesNotExist:
    #     cart_item = CartItem.objects.create(
    #         product=product,
    #         quantity=1,
    #         cart=cart,
    #         user=current_user
    #     )
    #     cart_item.save()
    
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart, user=current_user)
        # Check if increasing quantity would exceed stock
        if cart_item.quantity + 1 > product.stock:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': f'Insufficient stock for {product.product_name}. Available: {product.stock}',
                    'quantity': cart_item.quantity,
                    'sub_total': cart_item.sub_total(),
                    'total': cart.total_amount(),
                    'grand_total': cart.total_amount() - (cart.coupon.discount if cart.coupon else 0),
                    'discount': cart.coupon.discount if cart.coupon else 0,
                }, status=400)
            return redirect('cart')  # Redirect to cart if non-AJAX request
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        # Check if stock is sufficient for new item
        if product.stock < 1:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': f'Insufficient stock for {product.product_name}. Available: {product.stock}',
                    'quantity': 0,
                    'sub_total': 0,
                    'total': cart.total_amount(),
                    'grand_total': cart.total_amount() - (cart.coupon.discount if cart.coupon else 0),
                    'discount': cart.coupon.discount if cart.coupon else 0,
                }, status=400)
            return redirect('cart')
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart,
            user=current_user
        )
        cart_item.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        total = 0
        quantity = 0
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            total += (item.product.price * item.quantity)
            quantity += item.quantity

        discount = cart.coupon.discount if cart.coupon else 0
        grand_total = total - discount

        return JsonResponse({
            'quantity': cart_item.quantity,
            'sub_total': cart_item.sub_total(),
            'total': total,
            'grand_total': grand_total,
            'discount': discount,
        })

    # Redirect to checkout page
    return redirect('checkout')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        total = 0
        quantity = 0
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            total += (item.product.price * item.quantity)
            quantity += item.quantity

        discount = cart.coupon.discount if cart.coupon else 0
        grand_total = total - discount

        return JsonResponse({
            'quantity': cart_item.quantity if cart_item.quantity > 0 else 0,
            'sub_total': cart_item.sub_total() if cart_item.quantity > 0 else 0,
            'total': total,
            'grand_total': grand_total,
            'discount': discount,
        })

    return redirect('cart')

def remove_cart_item(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_item.delete()
    return redirect('cart')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code')

        # Always calculate total before trying coupon (so it's available in both success/fail cases)
        if request.user.is_authenticated:
            cart = Cart.objects.filter(cartitem__user=request.user).first()
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))

        total = 0
        quantity = 0
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            total += (item.product.price * item.quantity)
            quantity += item.quantity

        try:
            coupon = Coupon.objects.get(
                code=code,
                active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now()
            )

            cart.coupon = coupon
            cart.save()

            discount = coupon.discount
            grand_total = total - discount

            return JsonResponse({
                'total': total,
                'grand_total': grand_total,
                'discount': discount,
                'coupon_applied': True,
                'message': 'Coupon applied successfully!'
            })

        except Coupon.DoesNotExist:
            # No coupon or invalid/expired — just return the regular totals
            grand_total = total
            return JsonResponse({
                'total': total,
                'grand_total': grand_total,
                'discount': 0,
                'coupon_applied': False,
                'message': 'Invalid coupon code or the coupon has expired.'
            })


def remove_coupon(request):
    if request.user.is_authenticated:
        carts = Cart.objects.filter(cartitem__user=request.user)
    else:
        carts = Cart.objects.filter(cart_id=_cart_id(request))

    if carts.exists():
        for cart in carts:
            cart.coupon = None
            cart.save()
        
        total = 0
        quantity = 0
        for cart in carts:
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            for item in cart_items:
                total += (item.product.price * item.quantity)
                quantity += item.quantity
        grand_total = total

        return JsonResponse({
            'total': total,
            'grand_total': grand_total,
            'discount': 0,
            'message': 'Coupon removed successfully!'
        })
    else:
        return JsonResponse({
            'total': 0,
            'grand_total': 0,
            'discount': 0,
            'message': 'No cart found to remove the coupon.'
        })


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def cart(request, total=0, quantity=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        has_insufficient_stock = False
        is_available = True
        
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
            # Check if any cart item exceeds product stock
            if cart_item.quantity > cart_item.product.stock:
                has_insufficient_stock = True
            # If any product is unavailable, set is_available to False
            if not cart_item.product.is_available:
                is_available = False
        
        discount = 0
        grand_total = total
        coupon = None
        
        if cart.coupon:
            coupon = cart.coupon
            discount = cart.coupon.discount
            grand_total = total - discount
        
    except Cart.DoesNotExist:
        cart_items = []
        coupon = None
        discount = 0
        grand_total = total
        has_insufficient_stock = False
        is_available = True

    context = {
        'total': total,
        'grand_total': grand_total,
        'quantity': quantity,
        'cart_items': cart_items,
        'coupon': coupon,
        'discount': discount,
        'has_insufficient_stock': has_insufficient_stock,
        'is_available' : is_available,
    }

    return render(request, 'store/cart.html', context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def checkout(request):
    # Initialize variables
    cart_items = []
    sub_total = 0
    total = 0
    quantity = 0
    discount = 0
    has_insufficient_stock = False
    is_available = True
    
    # Get cart_id from session or create a new cart if none exists
    cart_id = _cart_id(request)  # Assuming _cart_id function is used to get the cart ID
    try:
        cart = Cart.objects.get(cart_id=cart_id)
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        # Remove unavailable products from cart
        for cart_item in cart_items:
            if not cart_item.product.is_available:
                cart_item.delete()  # Remove the cart item if product is unavailable
                is_available = False
        
        # Refresh cart_items after deletions
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        # Calculate sub_total, total, quantity and check stock
        for cart_item in cart_items:
            sub_total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
            total += cart_item.sub_total()
            if cart_item.quantity > cart_item.product.stock:
                has_insufficient_stock = True
            
    except Cart.DoesNotExist:
        cart = None

    # Handle coupons and discounts
    grand_total = total
    if cart and cart.coupon:
        discount = cart.coupon.discount
        grand_total = total - discount

    # Fetch user addresses
    addresses = UserAddress.objects.filter(user=request.user)

    # Handle POST request for address selection
    if request.method == "POST":
        address_id = request.POST.get('address_id')
        if address_id:
            selected_address = UserAddress.objects.get(id=address_id, user=request.user)
        else:
            selected_address = None
    else:
        selected_address = None

    # Pass context to template
    context = {
        'cart_items': cart_items,
        'sub_total': sub_total,
        'total': total,
        'grand_total': grand_total,
        'quantity': quantity,
        'discount': discount,
        'addresses': addresses,
        'selected_address': selected_address,
        'has_insufficient_stock': has_insufficient_stock,
        'is_available': is_available,
    }
    
    return render(request, 'store/checkout.html', context)


def update_cart_quantity(request, product_id):
    cart_item = get_object_or_404(CartItem, product__id=product_id)
    
    if request.GET.get('action') == 'increase':
        cart_item.quantity += 1
    elif request.GET.get('action') == 'decrease':
        cart_item.quantity -= 1

    # Ensure quantity is within bounds
    cart_item.quantity = max(1, min(cart_item.quantity, 5))
    cart_item.save()

    return JsonResponse({
        'success': True,
        'new_quantity': cart_item.quantity
    })


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def cart_add(request,product_id):
    current_user = request.user 
    product = Product.objects.get(id=product_id) 
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )

    # Remove the product from the wishlist
    Wishlist.objects.filter(user=request.user, product=product).delete()
    cart.save()

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,
            cart = cart,
            user=current_user
        )
        cart_item.save()
    return redirect('cart')
