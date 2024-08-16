from django.contrib import admin
from .models import Category

# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('category_name',)}
    list_display = ('category_name', 'slug', 'offer_percentage')
    fields = ('category_name', 'slug', 'description', 'cat_image', 'offer_percentage')


admin.site.register(Category, CategoryAdmin)

