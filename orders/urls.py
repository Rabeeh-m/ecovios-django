
from django.urls import path
from . import views

urlpatterns = [
    path('place_order', views.place_order, name='place_order'),
    path('cod', views.cod, name='cod'),
    path('payments', views.payments, name='payments'),
    path('confirm_order', views.confirm_order, name='confirm_order'),
    path('order_management', views.order_management, name='order_management'),
    path('view_order/<str:order_number>/', views.view_order, name='view_order'),
    path('cancel_order/<str:order_number>/', views.cancel_order, name='cancel_order'),
    path('return_order/<str:order_number>/', views.return_order, name='return_order'),
    path('order_history', views.order_history, name='order_history'),
    path('order_complete/', views.order_complete, name='order_complete'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('download_invoice/<str:order_number>/', views.download_invoice, name='download_invoice'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('buy_now/', views.buy_now, name='buy_now'),
    path('wallet_payment/', views.wallet_payment, name='wallet_payment'),
    path('wallet_order/', views.wallet_order, name='wallet_order'),
] 
