from django.urls import include, path
from . import views

urlpatterns = [
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('verify_otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    path('resend_otp/<int:user_id>/', views.resend_otp, name='resend_otp'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='dashboard'),
    path('edit_profile', views.edit_profile, name='edit_profile'),
    path('forgot_password', views.forgot_password, name='forgot_password'),
    path('reset_password_validate/<uidb64>/<token>', views.reset_password_validate, name='reset_password_validate'),
    path('reset_password', views.reset_password, name='reset_password'),
    path('addres_management/', views.address_management, name='address_management'),
    path('address_management/<int:address_id>/', views.address_management, name='address_management_with_id'),
    path('change-password', views.change_password, name='change_password'),
]
