from django.contrib import admin
from .models import Payment, Order, OrderProduct, Wallet

# Register your models here.
class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'ordered')
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'get_full_name', 'get_phone_number', 'get_email', 'get_city', 'order_total', 'status', 'is_ordered', 'created_at']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'address__first_name', 'address__last_name', 'address__phone_number', 'address__email']
    list_per_page = 20
    inlines = [OrderProductInline]


    def get_full_name(self, obj):
        return obj.address.full_name if obj.address else "No Address"
    
    get_full_name.short_description = 'Full Name'

    def get_phone_number(self, obj):
        return obj.address.phone_number if obj.address else "No Phone"

    get_phone_number.short_description = 'Phone'

    def get_email(self, obj):
        return obj.address.email if obj.address else "No Email"

    get_email.short_description = 'Email'

    def get_city(self, obj):
        return obj.address.city if obj.address else "No City"

    get_city.short_description = 'City'


class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_amount')


admin.site.register(Payment)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)
admin.site.register(Wallet)


