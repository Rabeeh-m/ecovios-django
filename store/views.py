
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from .models import Product, ReviewRating,ProductGallery,Wishlist
from category.models import Category
from django.core.paginator import EmptyPage,PageNotAnInteger,Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from carts.views import _cart_id
from carts.models import CartItem
from django.db.models import Q,Avg
from django.utils import timezone
from .forms import ReviewForm
from django.contrib import messages
# Create your views here.

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)

        paginator = Paginator(products,6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)

        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available = True).order_by('id')

        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)

        product_count = products.count()

    # Calculate average rating for each product
    for product in products:
        product.avg_rating = product.averageReview()

    sort_option = request.GET.get('sort')
    if sort_option == 'price_low':
        paged_products = products.order_by('price')
    elif sort_option == 'price_high':
        paged_products = products.order_by('-price')
    elif sort_option == 'name_a_z':
        paged_products = products.order_by('product_name')
    elif sort_option == 'name_z_a':
        paged_products = products.order_by('-product_name')
    

     # Filter by featured products
    featured_products = request.GET.get('featured')
    if featured_products:
        products = products.filter(is_featured=True)

    # Filter by rating
    filter_by_rating = request.GET.get('rating')
    if filter_by_rating:
        if filter_by_rating == '4plus':
            paged_products = products.annotate(avg_rating=Avg('reviewrating__rating')).filter(avg_rating__gte=4)
        elif filter_by_rating == '3plus':
            paged_products = products.annotate(avg_rating=Avg('reviewrating__rating')).filter(avg_rating__gte=3)
        elif filter_by_rating == '2plus':
            paged_products = products.annotate(avg_rating=Avg('reviewrating__rating')).filter(avg_rating__gte=2)
        elif filter_by_rating == '1plus':
            paged_products = products.annotate(avg_rating=Avg('reviewrating__rating')).filter(avg_rating__gte=1)

    
    # Filter by new arrivals
    filter_new_arrivals = request.GET.get('new_arrivals')
    if filter_new_arrivals:

     # Assuming "new arrivals" means products added within the last 30 days

        thirty_days_ago = timezone.now() - timezone.timedelta(days=10)
        paged_products = products.filter(created_date__gte=thirty_days_ago)



    context = {
        'products' : paged_products,
        'product_count' : product_count,
        'sort_option': sort_option,
    }

    return render(request, 'store/store.html', context)



from django.shortcuts import render, redirect, get_object_or_404, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from store.models import Product, ProductGallery, ReviewRating
from carts.models import CartItem, Cart


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Product.DoesNotExist:
        raise Http404("Product does not exist")

    if request.method == 'POST' and 'buy_now' in request.POST:
        cart_id = _cart_id(request)
        cart, created = Cart.objects.get_or_create(cart_id=cart_id)

        cart_item, created = CartItem.objects.get_or_create(
            product=single_product,
            cart=cart,
            defaults={'quantity': 1, 'user': request.user}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()

        return redirect('checkout')

    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)
    related_products = Product.objects.filter(category=single_product.category).exclude(id=single_product.id)[:4]
    in_wishlist = Wishlist.objects.filter(user=request.user, product=single_product).exists()

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'reviews': reviews,
        'related_products': related_products,
        'product_gallery': product_gallery,
        'in_wishlist': in_wishlist,
    }

    return render(request, 'store/product_detail.html', context)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')

    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        products = 0
        product_count = 0
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()

    context = {
        'products' : products,
        'product_count' : product_count,
    }
    return render(request, 'store/store.html', context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('product_detail', product.category.slug, product.slug)

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    return redirect('product_detail', product.category.slug, product.slug)


# @cache_control(no_cache=True, must_revalidate=True, no_store=True)
# @login_required(login_url='login')
# def wishlist(request):
#     wishlists = Wishlist.objects.filter(user=request.user)
#     context = {
#         'wishlists': wishlists,
#     }
#     return render(request, 'store/wishlist.html', context)



from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from .models import Wishlist, Product

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def toggle_wishlist(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        user = request.user

        wishlist, created = Wishlist.objects.get_or_create(user=user, product=product)

        if created:
            return JsonResponse({'added': True})
        else:
            wishlist.delete()
            return JsonResponse({'removed': True})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login')
def wishlist(request):
    wishlists = Wishlist.objects.filter(user=request.user)
    context = {
        'wishlists': wishlists,
    }
    return render(request, 'store/wishlist.html', context)

