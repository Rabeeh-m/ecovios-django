from django.urls import include, path
from . import views

urlpatterns = [
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('verify_otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    path('resend_otp/<int:user_id>/', views.resend_otp, name='resend_otp'),

    path('accounts/', include('allauth.urls')),
    
]
