from django.contrib import admin
from .models import Product,ReviewRating,ProductGallery,Wishlist
import admin_thumbnails


# Register your models here.
@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'stock', 'category', 'modified_date', 'is_available')
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductGalleryInline]

    def save_model(self, request, obj, form, change):
        # Ensure original_price is set before saving the product
        if not obj.original_price:
            obj.original_price = obj.price
        # Save the product to update the price based on the highest offer percentage
        super().save_model(request, obj, form, change)
        # Update the price based on the highest offer percentage after initial save
        obj.save()



class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product']
    search_fields = ['user__username', 'product__product_name']

admin.site.register(Wishlist, WishlistAdmin)

admin.site.register(Product,ProductAdmin)
admin.site.register(ReviewRating)
admin.site.register(ProductGallery)
