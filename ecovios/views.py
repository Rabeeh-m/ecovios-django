from django.shortcuts import render
from store.models import Product
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control


@login_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    products = Product.objects.all().filter(is_available = True)

    context = {
        'products' : products
    }

    return render(request,'home.html', context)