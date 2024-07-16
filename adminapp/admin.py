from django.contrib import admin
from .models import Category, Product, ProductImage, UserAction, UserBlock

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3  # Minimum 3 images

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage)
admin.site.register(UserAction)
admin.site.register(UserBlock)
