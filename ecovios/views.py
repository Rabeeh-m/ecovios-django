from django.shortcuts import render
from store.models import Product,ReviewRating
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def home(request):
    products = Product.objects.all().filter(is_available = True).order_by('created_date')

    reviews = {}  # Initialize reviews as an empty dictionary

    # Get the reviews
    for product in products:
        product_reviews = ReviewRating.objects.filter(product_id=product.id, status=True)
        reviews[product.id] = product_reviews

    context = {
        'products' : products,
        'reviews' : reviews,
    }

    return render(request,'home.html', context)