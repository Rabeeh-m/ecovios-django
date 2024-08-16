from django.db import models
from django.urls import reverse

# Create your models here.

class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)
    offer_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def get_url(self):
        return reverse('products_by_category', args=[self.slug])

    def __str__(self):
        return self.category_name
    

    def get_discounted_products(self):
        products = self.product_set.all()
        return [product.get_discounted_price() for product in products]
    
    def save(self, *args, **kwargs):
        is_new_instance = self.pk is None
        old_offer_percentage = None
        
        if not is_new_instance:
            # Get the old category instance to compare offer_percentage
            old_instance = Category.objects.get(pk=self.pk)
            old_offer_percentage = old_instance.offer_percentage

        # Save the category instance
        super().save(*args, **kwargs)

        # Check if offer_percentage has changed
        if not is_new_instance and old_offer_percentage != self.offer_percentage:
            self.update_product_prices()

    def update_product_prices(self):
        products = self.product_set.all()
        for product in products:
            # Update the product's price based on the category's new offer_percentage
            product.save()  # This will trigger the product's save method
    


