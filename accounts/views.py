from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from orders.models import Order
from .models import Account, OTP, UserAddress
from .forms import RegistrationForm, UserForm, UserProfileForm, UserProfile, AddressForm
from django.utils import timezone
from datetime import timedelta
import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.db.models import ProtectedError
from carts.views import _cart_id
from carts.models import Cart,CartItem
from django.db import IntegrityError
from orders.models import Wallet
from decimal import Decimal
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


#from orders.models import Order

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(email, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It is valid for 1 minutes.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            referral_code = form.cleaned_data.get('referral_code')

            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.is_active = False  # User is inactive until OTP is verified

            if referral_code:
                try:
                    referrer = Account.objects.get(referral_code=referral_code)
                    user.referred_by = referrer
                    wallet = Wallet.objects.get(user=referrer)
                    wallet.total_amount += Decimal('100.00')  # Add referral amount
                    wallet.save()
                except Account.DoesNotExist:
                    messages.error(request, 'Invalid referral code.')

            user.save()

            otp_code = generate_otp()
            expires_at = timezone.now() + timedelta(minutes=1)
            otp = OTP.objects.create(user=user, otp=otp_code, expires_at=expires_at)
            send_otp(email, otp_code)

            messages.success(request, 'Registration successful. Please check your email for the OTP.')
            return redirect('verify_otp', user_id=user.id)

    else:
        form = RegistrationForm()

    context = {
        'form': form,
    }

    return render(request, 'accounts/register.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def verify_otp(request, user_id):
    user = Account.objects.get(id=user_id)
    if request.method == 'POST':
        otp_code = request.POST['otp']
        otp = OTP.objects.get(user=user)

        if otp.is_valid() and otp.otp == otp_code:
            user.is_active = True
            user.save()
            messages.success(request, 'OTP verified successfully. You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid or expired OTP.')
            return redirect('verify_otp', user_id=user.id)

    return render(request, 'accounts/verify_otp.html', {'user_id': user.id})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def resend_otp(request, user_id):
    user = Account.objects.get(id=user_id)
    otp = OTP.objects.get(user=user)

    if not otp.is_valid():
        otp_code = generate_otp()
        expires_at = timezone.now() + timedelta(minutes=1)
        otp.otp = otp_code
        otp.expires_at = expires_at
        otp.save()
        send_otp(user.email, otp_code)
        messages.success(request, 'A new OTP has been sent to your email.')
    else:
        messages.error(request, 'Current OTP is still valid.')

    return redirect('verify_otp', user_id=user.id)

@login_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out')
    return redirect('login')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            user = None

        
        if user:
            if not user.is_active:
                messages.error(request, 'Your account is blocked. Please contact support.')
            else:
                user = auth.authenticate(email=email, password=password)
                if user is not None:

                    try:
                        cart = Cart.objects.get(cart_id=_cart_id(request))
                        is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                        if is_cart_item_exists:
                            cart_item = CartItem.objects.filter(cart=cart)

                            for item in cart_item:
                                item.user = user
                                item.save()
                    except:
                        pass
                    
                    auth.login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid login credentials')
                    return redirect('login')

    return render(request, 'accounts/login.html')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()
    context = {
        'orders_count' : orders_count,
    }
    return render(request,'accounts/dashboard.html',context)#


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def edit_profile(request):
    userprofile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updatd.')
            return redirect('edit_profile')
        else:
            messages.error(request, 'Add Valid First Name & Last Name')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    

    context = {
        'user_form' : user_form,
        'profile_form' : profile_form,
        'userprofile' : userprofile,

    }
    
    return render(request, 'accounts/edit_profile.html', context)



def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__iexact=email)

            # Reset Password Email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html',{
                'user' : user,
                'domain' : current_site,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request,'Password reset email has been sent to your email address.')
            return redirect('login')

        else:
            messages.error(request, 'Account does not exist!')
            return redirect('forgot_password')

    return render(request, 'accounts/forgot_password.html')



def reset_password_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('reset_password')
    else:
        messages.error(request, 'This link is has been expired!')
        return redirect('login')
    

def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')
        
        else:
            messages.error(request, 'Password do not match!')
            return redirect('reset_password')
        
    else:
        return render(request, 'accounts/reset_password.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def address_management(request, address_id=None):
    if address_id:
        address = get_object_or_404(UserAddress, id=address_id)
        if request.method == 'POST':
            if 'edit' in request.POST:
                form = AddressForm(request.POST, instance=address)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Address updated successfully.')
                    return redirect('address_management')
            elif 'delete' in request.POST:
                try:
                    address.delete()
                    messages.success(request, 'Address deleted successfully.')
                except IntegrityError:
                    messages.error(request, 'Cannot delete address because it is referenced by an order.')
                return redirect('address_management')
        else:
            form = AddressForm(instance=address)
    else:
        address = None
        form = AddressForm(request.POST or None)
        if request.method == 'POST' and 'add' in request.POST:
            if form.is_valid():
                new_address = form.save(commit=False)
                new_address.user = request.user
                new_address.save()
                messages.success(request, 'Address added successfully.')
                return redirect('address_management')

    addresses = UserAddress.objects.filter(user=request.user)
    return render(request, 'accounts/address_management.html', {'addresses': addresses, 'form': form, 'address': address})


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important, to keep the user logged in after password change
            messages.success(request, 'Your password was successfully updated!')
            return redirect('edit_profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'password_form': form})
