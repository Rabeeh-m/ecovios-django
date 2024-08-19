from django.shortcuts import get_object_or_404, render,redirect, HttpResponse
from carts.views import _cart_id
from .forms import OrderForm
from . models import Order, OrderProduct,Payment, Wallet
import datetime
from datetime import timedelta
from django.contrib import messages
from carts.models import Cart, CartItem
from accounts.models import Account, UserAddress
from django.http import JsonResponse
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import datetime
from carts.models import CartItem
from orders.models import Order
from accounts.models import UserAddress
from store.models import Product

@login_required(login_url='login')
def place_order(request):
    current_user = request.user
    total = 0
    quantity = 0

    # Check if the 'buy_now' product is in the session
    buy_now_product_id = request.session.get('buy_now_product_id')
    if buy_now_product_id:
        try:
            product = Product.objects.get(id=buy_now_product_id)
            cart_item, created = CartItem.objects.get_or_create(
                user=current_user,
                product=product,
                is_active=True,
                defaults={'quantity': 1}
            )
            if not created:
                cart_item.quantity += 1
                cart_item.save()
            # Clear the 'buy_now' product ID from the session
            request.session.pop('buy_now_product_id', None)
        except Product.DoesNotExist:
            messages.error(request, 'Product not found.')
            return redirect('store')

    # Get all cart items for the current user
    cart_items = CartItem.objects.filter(user=current_user, is_active=True)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        if address_id:
            address = get_object_or_404(UserAddress, id=address_id, user=current_user)
            data = Order()
            data.user = current_user
            data.first_name = address.first_name
            data.last_name = address.last_name
            data.phone = address.phone_number
            data.email = address.email
            data.address_line_1 = address.address_line_1
            data.address_line_2 = address.address_line_2
            data.city = address.city
            data.state = address.state
            data.country = address.country
            data.order_total = total
            data.ip = request.META.get('REMOTE_ADDR')
            data.address = address
            data.save()

            # Generate order number
            yr = int(datetime.date.today().strftime('%y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            request.session['order_number'] = order_number

            return redirect('cod')  # Replace with your order confirmation page URL
        else:
            messages.error(request, 'Please select an address.')
            return redirect('checkout')
    else:
        return redirect('checkout')




def cod(request):

    current_user = request.user
    order_number = request.session.get('order_number')
    
    order = Order.objects.filter(order_number=order_number, user=current_user, is_ordered=False).last()
    if not order: 
        return redirect('place_order')
    
    cart_items = CartItem.objects.filter(user=current_user)
    total=0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        
    try:
        cart = Cart.objects.filter(cartitem__user=current_user).first()
    except Cart.DoesNotExist:
        cart = None

    discount = 0
    
    grand_total = total
    if cart and cart.coupon:
        discount = cart.coupon.discount
        grand_total = total - discount

    delivery_charge = 50
    grand_total = grand_total + delivery_charge
    # Create Payment instance with Cash on Delivery
    payment = Payment(
        user=current_user,
        payment_id=f'COD-{order_number}',  # You can customize the payment_id format if needed
        payment_method='Cash on Delivery',
        amount_paid=grand_total,  # Assuming amount_paid is the total after discount
        status='Pending',  # Or any status that reflects the payment's current state
        created_at=timezone.now()
    )
    payment.save()

    # Link Payment to Order
    order.payment = payment
    #order.is_ordered = True  # Assuming the order should be marked as ordered now
    order.coupon_amount = discount
    order.order_total = total
    order.save()


    address = order.address
    order_total = order.order_total
    cart_items = CartItem.objects.filter(user=current_user)

    context = {
        'order': order,
        'address': address,
        'cart_items': cart_items,
        'total': total, 
        'order_total' : order_total,
        'discount' : discount,
        'grand_total': grand_total
        
    }

    return render(request, 'orders/cod.html', context)

    
def confirm_order(request):
    current_user = request.user
    order_number = request.session.get('order_number')
    order = Order.objects.filter(order_number=order_number, user=current_user, is_ordered=False).last()
    
    if not order:
        return redirect('place_order')
    
    cart_items = CartItem.objects.filter(user=current_user)
    total = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
    
    try:
        carts = Cart.objects.filter(cartitem__user=current_user) #.first()
        discount = 0
        grand_total = total
        for cart in carts:
            if cart.coupon:
                discount = cart.coupon.discount
        grand_total = total - discount
        # if cart and cart.coupon:
        #     discount = cart.coupon.discount
        #     grand_total = total - discount

        # Update the order total with the discounted price
        order.order_total = total
        
    except Cart.DoesNotExist:
        cart = None

    
    delivery_charge = 50
    grand_total = grand_total + delivery_charge
    
    # Mark the order as ordered and set status to completed
    order.is_ordered = True
    order.status = 'Completed'
    order.order_total = grand_total
    order.save()
    
    cart_items = CartItem.objects.filter(user=current_user)
    expected_delivery_date = order.created_at + timedelta(days=7)


    for cart_item in cart_items:
        order_product = OrderProduct.objects.create(
            order=order,
            user=current_user,
            product=cart_item.product,
            quantity=cart_item.quantity,
            product_price=cart_item.product.price,
            ordered=True
        )
        order_product.save()

    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()
    
    # Clear the cart after order is confirmed
    cart_items.delete()
    
    # Get all products in the order
    ordered_products = OrderProduct.objects.filter(order=order)

    for ordered_product in ordered_products:
        ordered_product.sub_total = ordered_product.product_price * ordered_product.quantity
   
    # Get the shipping address associated with the order
    
    address = order.address
    cart_items = CartItem.objects.filter(user=current_user)
    
    context = {
        'order': order,
        'address': address,
        'cart_items': cart_items,
        'expected_delivery_date': expected_delivery_date,
        'ordered_products': ordered_products,
        'total' : total,
        'grand_total' : grand_total
    }
    
    return render(request, 'orders/confirm_order.html', context)



def order_management(request):
    current_user = request.user
    orders = Order.objects.filter(user=current_user, is_ordered=True).order_by('-created_at')
    order_count = orders.count()  # Get the count of orders
    paginator = Paginator(orders, 10)  # Show 10 orders per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': orders,
        'page_obj': page_obj,
        'order_count': order_count,
    }
    return render(request, 'orders/order_management.html', context)



def view_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    ordered_products = OrderProduct.objects.filter(order=order)

    for ordered_product in ordered_products:
        ordered_product.sub_total = ordered_product.product_price * ordered_product.quantity
        
    address = order.address
    
    # total -= float(order.coupon_amount)


    context = {
        'order': order,
        'ordered_products': ordered_products,
        'address' : address,
    }
    return render(request, 'orders/view_order.html', context)


def order_history(request):
    current_user = request.user
    orders = Order.objects.filter(user=current_user, is_ordered=True).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'orders/order_history.html', context)



def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])
    
    # Calculate the total and apply coupon discount
    cart_items = CartItem.objects.filter(user=request.user)
    total = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)

    # Fetch the cart to check for an applied coupon
    try:
        cart = Cart.objects.filter(cartitem__user=request.user).first()
    except Cart.DoesNotExist:
        cart = None

    discount = 0
    grand_total = total
    if cart and cart.coupon:
        discount = cart.coupon.discount
        grand_total = total - discount

    # Add delivery charges
    delivery_charge = 50
    grand_total = grand_total + delivery_charge

    # Create Payment instance with Paytm or other payment methods
    payment = Payment(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_paid=grand_total,  # Reflects total after discount and delivery charges
        status=body['status'],
    )
    payment.save()

    # Update the order with payment and mark as ordered
    order.payment = payment
    order.is_ordered = True
    order.coupon_amount = discount
    order.order_total = grand_total  # This is the total before applying discount
    order.status = 'Completed'
    order.save()

    # Save the order number to the session before redirecting to payment
    

    # Process the order products
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        # Update the stock
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear the cart
    CartItem.objects.filter(user=request.user).delete()

    # Send confirmation email
    # mail_subject = 'Thank you for your order'
    # message = render_to_string('orders/order_received_email.html', {
    #     'user': request.user,
    #     'order': order,
    # })
    # to_email = request.user.email
    # send_email = EmailMessage(mail_subject, message, to=[to_email])
    # send_email.send()

    # Return a JsonResponse with order and transaction details
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id
    }
    return JsonResponse(data)




def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        subtotal = 0
        address = order.address
        
        
        for i in ordered_products:
            subtotal = i.product_price * i.quantity

        try:
            cart = Cart.objects.filter(cartitem__user=request.user).first()
        except Cart.DoesNotExist:
            cart = None

        discount = 0
        total = 0
        if cart and cart.coupon:
            discount = cart.coupon.discount
            total = subtotal - discount

        grand_total =order.order_total

            
        payment = Payment.objects.get(payment_id=transID)
        context = {
            'order': order,
            'address' : address,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
            'total' : total,
            'grand_total': grand_total,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
    
 
from decimal import Decimal

def cancel_order(request, order_number):
    try:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        if order.status != 'Cancelled':
            order.status = 'Cancelled'
            order.save()

            # Check if payment method is not 'Cash on Delivery'
            if order.payment and order.payment.payment_method != 'Cash on Delivery':
            # Update the wallet
                wallet, created = Wallet.objects.get_or_create(user=order.user)
                wallet.total_amount += Decimal(order.order_total)
                wallet.save()

            messages.success(request, 'Order cancelled and wallet updated successfully.')
        return redirect('order_management')
    except Order.DoesNotExist:
        return render(request, 'orders/order_not_found.html', {'order_number': order_number})
        

def return_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.status == 'Delivered':
        order.status = 'Return'
        order.save()

        # Check if payment method is not 'Cash on Delivery'
        #if order.payment and order.payment.payment_method != 'Cash on Delivery':
        # Update the wallet
        wallet, created = Wallet.objects.get_or_create(user=order.user)
        wallet.total_amount += Decimal(order.order_total)
        wallet.save()

        messages.success(request, 'Order Returned and wallet updated successfully.')

    else:
        messages.error(request, 'Order cannot be returned.')

    return redirect('order_management')
    

@login_required(login_url='login')
def wallet_view(request):
    # Get or create the wallet for the current user
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Get all cancelled orders for the current user
    cancelled_orders = Order.objects.filter(
        user=request.user,
        status='Cancelled'
    ).exclude(
        payment__payment_method='Cash on Delivery'
    ).order_by('-created_at' )
    
    # Get the referral code from the user's account
    referral_code = request.user.referral_code

    context = {
        'wallet': wallet,
        'cancelled_orders': cancelled_orders,
        'referral_code' : referral_code
    }
    return render(request, 'orders/wallet.html', context)



# def cancel_order(request, order_number):
#     try:
#         order = Order.objects.get(order_number=order_number, user=request.user)
#         order.status = 'Canceled'
#         order.delete()
#         # order.save()
#         return redirect('order_management')
#     except Order.DoesNotExist:
#         return render(request, 'orders/order_not_found.html', {'order_number': order_number})



from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from io import BytesIO

def download_invoice(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    ordered_products = OrderProduct.objects.filter(order=order)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        'header',
        parent=styles['Title'],
        fontSize=18,
        alignment=1,  # Center alignment
    )
    
    content_style = ParagraphStyle(
        'content',
        parent=styles['Normal'],
        fontSize=12,
    )
    
    # Create the PDF content
    elements = []

    # Title
    title = Paragraph("Invoice", header_style)
    elements.append(title)
    elements.append(Paragraph("<br/>", content_style))  # Add some space

    # Order Details
    order_details = [
        ['Order Number:', order.order_number],
        ['Payment Id:', f' {order.payment.payment_id}'],
        ['Order Status:', order.status],
        ['Order Date:', order.created_at.strftime('%Y-%m-%d %H:%M:%S')],
        ['Payment Method:', f' {order.payment.payment_method}'],
        ['Total Amount:', f' {order.order_total}'],
    ]
    order_table = Table(order_details, colWidths=[120, 400])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#f0f0f0'),
        ('TEXTCOLOR', (0, 0), (0, 0), '#000000'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, '#000000'),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ]))
    elements.append(order_table)
    
    elements.append(Paragraph("<br/><br/>", content_style))  # Add some space
    
    # Billing Address
    address_data = [
        ['Billing Address', ''],
        ['Name:', f' {order.address.first_name}{order.address.last_name}'],
        ['Address:', f' {order.address.address_line_1}'],
        ['City:', order.address.city],
        ['State:', order.address.state],
        ['Country:', order.address.country],
        ['Phone:', order.address.phone_number],
    ]
    address_table = Table(address_data, colWidths=[120, 400])
    address_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#f0f0f0'),
        ('TEXTCOLOR', (0, 0), (0, 0), '#000000'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, '#000000'),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ]))
    elements.append(address_table)

    elements.append(Paragraph("<br/><br/>", content_style))  # Add some space
    
    # Ordered Products
    product_data = [['Product', 'Quantity', 'Price', 'Subtotal']]
    for ordered_product in ordered_products:
        subtotal = ordered_product.product_price * ordered_product.quantity
        product_data.append([
            ordered_product.product.product_name,
            ordered_product.quantity,
            f' {ordered_product.product_price}',
            f' {subtotal}'
        ])
    
    product_table = Table(product_data, colWidths=[200, 100, 100, 100])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#f0f0f0'),
        ('TEXTCOLOR', (0, 0), (0, 0), '#000000'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, '#000000'),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ]))
    elements.append(product_table)

    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'
    return response



def payment_failed(request):    
    return render(request, 'orders/payment_failed.html')


# orders/views.py
from django.shortcuts import redirect, get_object_or_404
from store.models import Product
from carts.models import Cart, CartItem

def buy_now(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        if not product_id:
            return redirect('store')  # Redirect if no product ID is provided

        product = get_object_or_404(Product, id=product_id)
        cart_id = request.session.get('cart_id')

        if not cart_id:
            cart_id = _cart_id(request)
            request.session['cart_id'] = cart_id

        try:
            cart = Cart.objects.get(cart_id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=cart_id)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        return redirect('checkout')
    else:
        return redirect('store')





from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Order, Wallet, OrderProduct
from carts.models import CartItem
from accounts.models import UserAddress

@login_required
def wallet_payment(request):
    user = request.user
    addresses = UserAddress.objects.filter(user=user)
    cart_items = CartItem.objects.filter(user=user)
    total = sum(item.sub_total() for item in cart_items)  # Call sub_total as a method
    
    # Assuming you have logic to calculate discount; if not, set it to 0
    discount = 0  # Replace with your discount calculation logic

    grand_total = (total - discount) + 50  # Assuming 50 is the delivery charge
    wallet_balance = Wallet.objects.get(user=user).total_amount

    context = {
        'address': addresses[0],  # Assuming only one address for simplicity
        'cart_items': cart_items,
        'total': total,
        'discount': discount,
        'grand_total': grand_total,
        'wallet_balance': wallet_balance,
    }
    return render(request, 'orders/wallet_payment.html', context)



@login_required
def wallet_order(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)
    addresses = UserAddress.objects.filter(user=user)
    
    if not addresses.exists():
        return redirect('orders:wallet_payment')  # Redirect to the payment page if no address found
    
    address = addresses.first()  # Assuming the first address if multiple addresses exist

    # Calculate total
    total = sum(item.sub_total() for item in cart_items)
    
    # Assuming you have logic to calculate discount; if not, set it to 0
    discount = 0  # Replace with your discount calculation logic
    
    grand_total = (total - discount) + 50  # Assuming 50 is the delivery charge
    wallet = Wallet.objects.get(user=user)

    if wallet.total_amount >= grand_total:
        # Deduct the total from wallet balance
        wallet.total_amount -= grand_total
        wallet.save()

        order_number = request.session.get('order_number')

        # Create a payment instance
        payment = Payment.objects.create(
            user=user,
            payment_id=f'WALLET-{order_number}',  # Custom payment_id format for wallet payments
            payment_method='Wallet',
            amount_paid=grand_total,  # Total after any discounts
            status='Completed',  # Assuming the payment is completed
            created_at=timezone.now(),
        )

        # Create an order instance
        order = Order.objects.create(
            user=user,
            order_total=grand_total,
            payment=payment,  # Associate payment with order
            address=address,  # Save billing address with the order
            status='Completed',  # Set the appropriate status
            order_number=order_number,
            is_ordered=True
        )

        # Save cart items as order products
        for cart_item in cart_items:
            order_product = OrderProduct.objects.create(
                order=order,
                user=user,
                product=cart_item.product,
                quantity=cart_item.quantity,
                product_price=cart_item.product.price,
                ordered=True
            )
            order_product.save()

        # Clear the cart after ordering
        cart_items.delete()

        address = order.address
        order_total = order.order_total
        cart_items = CartItem.objects.filter(user=user)
        ordered_products = OrderProduct.objects.filter(order=order)

        for ordered_product in ordered_products:
            ordered_product.sub_total = ordered_product.product_price * ordered_product.quantity

        # Prepare context for confirm_order.html
        context = {
            'order': order,
            'address': address,
            'cart_items': cart_items,
            'total': total, 
            'order_total' : order_total,
            'discount' : discount,
            'grand_total': grand_total,
            'ordered_products': ordered_products,
        }

        return render(request, 'orders/confirm_order.html', context)
    else:
        # If the wallet balance is insufficient
        return render(request, 'orders/wallet_payment.html', {
            'error': 'Insufficient wallet balance to complete the order.',
            'total': total,
            'discount': discount,
            'grand_total': grand_total,
            'wallet_balance': wallet.total_amount,
        })
    
