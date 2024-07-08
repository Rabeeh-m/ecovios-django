from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from .models import Account, OTP
from .forms import RegistrationForm
from django.utils import timezone
from datetime import timedelta
import random
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(email, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It is valid for 3 minutes.'
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

            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.is_active = False  # User is inactive until OTP is verified
            user.save()

            otp_code = generate_otp()
            expires_at = timezone.now() + timedelta(minutes=10)
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
        expires_at = timezone.now() + timedelta(minutes=3)
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

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')

    return render(request, 'accounts/login.html')



