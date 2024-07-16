import email
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import logging
from django.shortcuts import render
from django.contrib.auth.models import User 
from accounts.models import Account
from category.models import Category
from store.models import Product
from store.forms import ProductForm
from django.views.decorators.cache import cache_control
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


User = get_user_model()

logger = logging.getLogger(__name__)
# Create your views here.

def admin_required(view_func):
    @login_required(login_url='alogin')
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superadmin:
            return redirect('alogin')  
        return view_func(request, *args, **kwargs)
    return wrapper

def adminlogin(request):
    error_message = None 
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        logger.debug(f"Email: {email}, Password: {password}")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            logger.debug(f"Authenticated user: {user.email}, is_superadmin: {user.is_superadmin}")
        else:
            logger.debug("Authentication failed")

        if user is not None and user.is_superadmin:
            login(request, user)
            return redirect('ahome')
        else:
            error_message = "Invalid credentials or not a superuser"
    
    return render(request, 'adminlogin.html', {'error_message': error_message})


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def ahome(request):
    return render(request, 'ahome.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def user_list(request):
    users = User.objects.filter(is_superadmin=False).order_by('-id')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_status = request.POST.get('new_status')
        user = Account.objects.get(id=user_id)
        user.status = new_status
        user.save()
        return redirect('userlist')  # Redirect to the user list page
    return render(request, 'userlist.html', {'users': users})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def categorylist(request):
    categories = Category.objects.all()
    return render(request, 'categorylist.html', {'categories': categories})



def addcategory(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        cat_image = request.FILES.get('cat_image')
        
     
        if Category.objects.filter(category_name=category_name).exists():
            messages.error(request, f'A category with the name "{category_name}" already exists.')
            return render(request, 'categoryform.html')
        
        Category.objects.create(
            category_name=category_name,
            slug=slug,
            description=description,
            cat_image=cat_image
        )
        messages.success(request, 'Category added successfully.')
        return redirect('categorylist')
    
    return render(request, 'categoryform.html')

def editcategory(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        cat_image = request.FILES.get('cat_image')
        
        # Check if the updated category name already exists (excluding current category)
        if category_name != category.category_name and Category.objects.filter(category_name=category_name).exists():
            messages.error(request, f'A category with the name "{category_name}" already exists.')
            return render(request, 'categoryform.html', {'category': category})
        
        category.category_name = category_name
        category.slug = slug
        category.description = description
        if cat_image:
            category.cat_image = cat_image
        category.save()
        
        messages.success(request, 'Category updated successfully.')
        return redirect('categorylist')
    
    return render(request, 'categoryform.html', {'category': category})

def deletecategory(request, category_id, soft_delete=True):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        if soft_delete:
            category.is_deleted = True
            category.save()
            messages.success(request, f'Category "{category.category_name}" has been marked as deleted.')
        else:
            category.delete()
            messages.success(request, f'Category "{category.category_name}" has been deleted successfully.')
        
        return redirect('categorylist')
    
    return render(request, 'deletecategory.html', {'category': category})


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def productlist(request):
    products = Product.objects.all()
    return render(request, 'productlist.html', {'products': products})

@cache_control(no_cache=True,must_revalidate=True,no_store=True)
@admin_required
def update_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status == 'blocked':
            user.is_active = False
        elif new_status == 'active':
            user.is_active = True
        user.save()
        return redirect('userlist')  # Redirect to the user list page 
    return render(request, 'userlist.html', {'users': User.objects.all()})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def productlist(request):
    products = Product.objects.all().order_by('id')
    paginator = Paginator(products, 10)  # Show 10 products per page
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
    }
    return render(request, 'productlist.html', context)

@login_required
def addproduct(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully.')
            return redirect('productlist')
        else:
            messages.error(request, 'Error adding product. Please correct the form errors.')
    else:
        form = ProductForm()

    return render(request, 'addproduct.html', {'form': form})

def editproduct(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('productlist')
        else:
            messages.error(request, 'Error updating product. Please correct the form errors.')
    else:
        form = ProductForm(instance=product)

    return render(request, 'editproduct.html', {'form': form, 'product': product})

def deleteproduct(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.is_deleted = True
        product.save()
        messages.success(request, f'Product "{product.product_name}" has been marked as deleted.')
        return redirect('productlist')
    
    return render(request, 'deleteproduct.html', {'product': product})


@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def adminlogout(request):
    logout(request)
    return redirect('alogin')

