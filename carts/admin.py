from django.contrib import admin
from .models import Cart, CartItem, Coupon


# Register your models here.
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Coupon)


