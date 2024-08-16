import email
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
import logging
from django.shortcuts import render
from django.contrib.auth.models import User 
from accounts.models import Account
from category.models import Category
from store.models import Product, ProductGallery
from store.forms import ProductForm
from django.views.decorators.cache import cache_control
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from orders.models import Order, OrderProduct

from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import openpyxl
from xhtml2pdf import pisa
from django.template.loader import get_template
import pandas as pd
from django.core.paginator import Paginator
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import utils
from django.http import HttpResponse
from datetime import datetime
from decimal import Decimal

from django.utils import timezone
from orders.models import OrderProduct
from category.models import Category
import calendar
from django.db.models import Count, Q
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
from carts.models import Coupon
from .forms import CouponForm
from django.db import models 
from django.db.models import Sum, F
from accounts.models import UserAddress


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



def ahome(request):

    filter_type = request.GET.get('filter', 'daily')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    orders = Order.objects.filter(is_ordered=True)

    if filter_type == 'daily':
        orders = orders.filter(created_at__date=datetime.today())
    elif filter_type == 'weekly':
        start_of_week = datetime.today() - timedelta(days=datetime.today().weekday())
        orders = orders.filter(created_at__date__gte=start_of_week)
    elif filter_type == 'monthly':
        orders = orders.filter(created_at__month=datetime.today().month)
    elif filter_type == 'yearly':
        orders = orders.filter(created_at__year=datetime.today().year)
    elif filter_type == 'custom':
        if start_date and end_date:
            start_date = parse_date(start_date)
            end_date = parse_date(end_date)
            orders = orders.filter(created_at__date__range=[start_date, end_date])

    orders_by_date = orders.values('created_at__date').annotate(order_count=Count('id')).order_by('created_at__date')

    # Prepare data for chart
    chart_data = {
        'dates': [order['created_at__date'].strftime('%Y-%m-%d') for order in orders_by_date],
        'order_counts': [order['order_count'] for order in orders_by_date]
    }

    orders = Order.objects.filter(status__in=['Completed', 'Shipped', 'Delivered'],)

    total_orders = orders.count()
    total_order_amount = orders.aggregate(Sum('order_total'))['order_total__sum'] or 0


    # Define the current time
    now = timezone.now()

    # Top selling products
    top_products = (
        OrderProduct.objects.values('product__product_name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:5]
    )
    top_products_names = [item['product__product_name'] for item in top_products]
    top_products_quantities = [item['total_quantity'] for item in top_products]

    # Monthly sales data
    months = [calendar.month_name[i] for i in range(1, 13)]
    monthly_sales = (
        OrderProduct.objects.filter(order__created_at__year=now.year)
        .values('order__created_at__month')
        .annotate(total_sales=Sum('quantity'))
    )
    sales_data = {i: 0 for i in range(1, 13)}
    for item in monthly_sales:
        sales_data[item['order__created_at__month']] = item['total_sales']
    monthly_sales_values = [sales_data[i] for i in range(1, 13)]

    # Sales by category
    sales_by_category = (
        OrderProduct.objects.values('product__category__category_name')
        .annotate(total_sales=Sum('quantity'))
    )
    categories = [item['product__category__category_name'] for item in sales_by_category]
    category_sales = [item['total_sales'] for item in sales_by_category]




    context = {
        'chart_data': chart_data,
        'total_orders' : total_orders,
        'total_order_amount' : total_order_amount,

        'top_products_names': top_products_names,
        'top_products_quantities': top_products_quantities,
        'monthly_sales_values': monthly_sales_values,
        'months': months,
        'categories': categories,
        'category_sales': category_sales,

    }
    return render(request, 'ahome.html', context)
                 


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def user_list(request):
    search_query = request.GET.get('q', '')
    users = Account.objects.filter(is_superadmin=False).order_by('-id')

    if search_query:
        users = users.filter(Q(username__icontains=search_query) | Q(email__icontains=search_query))

    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_status = request.POST.get('new_status')
        user = User.objects.get(id=user_id)  # Assuming your user model is 'User'
        user.is_active = True if new_status == 'active' else False
        user.save()
        return redirect('user_list')  # Redirect to the user list page

    context = {
        'users': page_obj,
        'search_query': search_query,
    }
    return render(request, 'userlist.html', context)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def categorylist(request):
    query = request.GET.get('q', '')
    if query:
        categories = Category.objects.filter(Q(category_name__icontains=query) | Q(description__icontains=query))
    else:
        categories = Category.objects.all()
    
    paginator = Paginator(categories, 3)  # Show 10 categories per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'categories': page_obj,
        'query': query
    }
    return render(request, 'categorylist.html', context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def addcategory(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        cat_image = request.FILES.get('cat_image')
        
     
        if Category.objects.filter(category_name=category_name).exists():
            messages.error(request, f'A category with the name "{category_name}" already exists.')
           
        
        Category.objects.create(
            category_name=category_name,
            slug=slug,
            description=description,
            cat_image=cat_image
        )
        messages.success(request, 'Category added successfully.')
        return redirect('categorylist')
    
    



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
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



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
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



def addproduct(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()  # Save the main product details
            
            # Handle gallery images
            gallery_images = request.FILES.getlist('gallery_images')
            for image in gallery_images:
                ProductGallery.objects.create(product=product, image=image)
                
            return redirect('productlist')
    else:
        form = ProductForm()
        
    return render(request, 'addproduct.html', {'form': form})


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
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


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def deleteproduct(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if 'hard_delete' in request.path:
        # Perform hard delete
        product.delete()
        return redirect('productlist')
    elif request.GET.get('soft_delete') == 'True':
        # Perform soft delete
        product.is_deleted = True
        product.save()
        return redirect('productlist')
    
    return redirect('productlist')

def delete_gallery_image(request, product_id, image_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=product_id)
        image = get_object_or_404(ProductGallery, pk=image_id, product=product)
        image.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def adminlogout(request):
    logout(request)
    return redirect('alogin')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def manage_orders(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        action = request.POST.get('action')
        order = get_object_or_404(Order, id=order_id)
        
        status_order = ['Pending', 'Completed', 'Shipped', 'Delivered', 'Cancelled', 'Return']
        
        if action == 'update_status':
            new_status = request.POST.get('status')
            current_status_index = status_order.index(order.status)
            new_status_index = status_order.index(new_status)
            
            if new_status_index >= current_status_index:
                order.status = new_status
                order.save()
                messages.success(request, 'Order status updated successfully.')
            else:
                messages.error(request, 'Invalid status update. You can only move to a forward status.')
        elif action == 'cancel':
            order.status = 'Cancelled'
            order.save()
            messages.success(request, 'Order cancelled successfully.')

    query = request.GET.get('q')
    orders = Order.objects.all().order_by('-created_at')

    if query:
        orders = orders.filter(Q(order_number__icontains=query)|Q(status__icontains=query))

    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page = request.GET.get('page')
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)

    return render(request, 'order_management.html', {'orders': orders})




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def sales_report(request):
    # Default values for start_date and end_date
    time_range = request.GET.get('time_range', 'daily')
    start_date = timezone.now()
    end_date = timezone.now()

    if time_range == 'daily':
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)
    elif time_range == 'weekly':
        start_date = start_date - timedelta(days=start_date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)
    elif time_range == 'monthly':
        start_date = start_date.replace(day=1, hour=0, minute=0, second=0)
        end_date = (end_date.replace(day=1) + timedelta(days=32)).replace(day=1, hour=23, minute=59, second=59) - timedelta(days=1)
    elif time_range == 'yearly':
        start_date = start_date.replace(month=1, day=1, hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)
    elif time_range == 'custom':
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        try:
            if start_date_str:
                start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d')
                start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
            if end_date_str:
                end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
                # Set end date to the end of the day
                end_date = end_date.replace(hour=23, minute=59, second=59)
        except (ValueError, TypeError):
            # Handle parsing errors or missing dates
            start_date = timezone.now().replace(hour=0, minute=0, second=0)
            end_date = timezone.now().replace(hour=23, minute=59, second=59)

    # Fetch orders based on filtered date range
    orders = Order.objects.filter(
        status__in=['Completed', 'Shipped', 'Delivered'],
        created_at__range=(start_date, end_date)
    ).order_by('-created_at')

    # Pagination
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page = request.GET.get('page')
    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:
        orders_page = paginator.page(1)
    except EmptyPage:
        orders_page = paginator.page(paginator.num_pages)

    total_sales_count = orders.count()
    total_order_amount = orders.aggregate(Sum('order_total'))['order_total__sum'] or 0

    #total_discount_amount = orders.aggregate(Sum('discount_amount'))['discount_amount__sum'] or 0

    # Calculate total discount amount
    total_discount_amount = 0
    for order in orders:
        for order_product in order.orderproduct_set.all():
            discount = (order_product.product.original_price - order_product.product.price) * order_product.quantity
            total_discount_amount += max(discount, 0)  # Ensure discount is not negative

    total_coupon_amount = orders.aggregate(Sum('coupon_amount'))['coupon_amount__sum'] or 0

    context = {
        'orders': orders,
        'total_sales_count': total_sales_count,
        'total_order_amount': total_order_amount,
        'total_discount_amount': total_discount_amount,
        'total_coupon_amount': total_coupon_amount,
        'time_range': time_range,
        'start_date': start_date.date(),
        'end_date': end_date.date(),
        'orders': orders_page,
    }
    return render(request, 'sales_report.html', context)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def download_pdf(request):
    # Set default start and end date range
    time_range = request.GET.get('time_range', 'weekly')
    start_date = timezone.now()
    end_date = timezone.now()

    if time_range == 'daily':
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)
    elif time_range == 'weekly':
        start_date = start_date - timedelta(days=start_date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)
    elif time_range == 'monthly':
        start_date = start_date.replace(day=1, hour=0, minute=0, second=0)
        end_date = (end_date.replace(day=1) + timedelta(days=32)).replace(day=1, hour=23, minute=59, second=59) - timedelta(days=1)
    elif time_range == 'yearly':
        start_date = start_date.replace(month=1, day=1, hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)
    elif time_range == 'custom':
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        try:
            if start_date_str:
                start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d')
                start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
            if end_date_str:
                end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
                end_date = end_date.replace(hour=23, minute=59, second=59)
        except (ValueError, TypeError):
            start_date = timezone.now().replace(hour=0, minute=0, second=0)
            end_date = timezone.now().replace(hour=23, minute=59, second=59)

    # Fetch orders based on filtered date range
    orders = Order.objects.filter(
        status__in=['Completed', 'Shipped', 'Delivered'],
        created_at__range=(start_date, end_date)
    ).order_by('-created_at')

    total_sales_count = orders.count()
    total_order_amount = orders.aggregate(Sum('order_total'))['order_total__sum'] or 0
    total_coupon_amount = orders.aggregate(Sum('coupon_amount'))['coupon_amount__sum'] or 0

    # Calculate total discount amount
    total_discount_amount = 0
    for order in orders:
        for order_product in order.orderproduct_set.all():
            discount = (order_product.product.original_price - order_product.product.price) * order_product.quantity
            total_discount_amount += max(discount, 0)  # Ensure discount is not negative

    # Prepare PDF content
    template_path = 'pdf_template.html'
    context = {
        'orders': orders,
        'total_sales_count': total_sales_count,
        'total_order_amount': total_order_amount,
        'total_discount_amount': total_discount_amount,
        'total_coupon_amount': total_coupon_amount,
        'time_range': time_range,
        'start_date': start_date.date(),
        'end_date': end_date.date(),
    }
    
    # Render the template with the context
    template = get_template(template_path)
    html = template.render(context)

    # Create a HttpResponse object with the appropriate PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    # Convert HTML to PDF
    pisa_status = pisa.CreatePDF(
        html, dest=response
    )

    # If an error occurs
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')

    return response



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def download_excel(request):
    # Set default start and end date range
    time_range = request.GET.get('time_range', 'weekly')
    start_date = timezone.now()
    end_date = timezone.now()

    if time_range == 'daily':
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)
    elif time_range == 'weekly':
        start_date = start_date - timedelta(days=start_date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)
    elif time_range == 'monthly':
        start_date = start_date.replace(day=1, hour=0, minute=0, second=0)
        end_date = (end_date.replace(day=1) + timedelta(days=32)).replace(day=1, hour=23, minute=59, second=59) - timedelta(days=1)
    elif time_range == 'yearly':
        start_date = start_date.replace(month=1, day=1, hour=0, minute=0, second=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)
    elif time_range == 'custom':
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        try:
            if start_date_str:
                start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d')
                start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
            if end_date_str:
                end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
                end_date = end_date.replace(hour=23, minute=59, second=59)
        except (ValueError, TypeError):
            start_date = timezone.now().replace(hour=0, minute=0, second=0)
            end_date = timezone.now().replace(hour=23, minute=59, second=59)

    # Fetch orders based on filtered date range
    orders = Order.objects.filter(
        status__in=['Completed', 'Shipped', 'Delivered'],
        created_at__range=(start_date, end_date)
    ).order_by('-created_at')

    #total_coupon_amount = orders.aggregate(Sum('coupon_amount'))['coupon_amount__sum'] or 0

    total_sales_count = orders.count()
    total_order_amount = orders.aggregate(Sum('order_total'))['order_total__sum'] or 0
    total_coupon_amount = orders.aggregate(Sum('coupon_amount'))['coupon_amount__sum'] or 0

    # Calculate total discount amount
    total_discount_amount = 0
    for order in orders:
        for order_product in order.orderproduct_set.all():
            discount = (order_product.product.original_price - order_product.product.price) * order_product.quantity
            total_discount_amount += max(discount, 0)  # Ensure discount is not negative
    
    # Create a DataFrame
    data = {
        'Order ID': [order.order_number for order in orders],
        'Customer': [order.user.username for order in orders],
        'Amount': [order.order_total for order in orders],
        'Coupon Amount': [order.coupon_amount for order in orders],
        'Discount Amount': [sum((order_product.product.original_price - order_product.product.price) * order_product.quantity for order_product in order.orderproduct_set.all()) for order in orders],
        #'Date': [order.created_at.replace(tzinfo=None) if order.created_at.tzinfo else order.created_at for order in orders]  # Make datetime naive
    }
    df = pd.DataFrame(data)

    # Add a row for the total coupon amount
    total_row = pd.DataFrame({
        'Order ID': [''], 
        'Customer': [''], 
        'Amount': [''], 
        'Coupon Amount': [total_coupon_amount],
        'Discount Amount': [total_discount_amount], 
        'Date': ['']})
    df = pd.concat([df, total_row])

    # Create an HttpResponse object with the content_type for Excel files
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=sales_report.xlsx'

    # Write the DataFrame to an Excel file
    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales Report')

    return response



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def coupon_management(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Coupon created successfully!')
            return redirect('coupon_management')
    else:
        form = CouponForm()

    coupons = Coupon.objects.all()

    return render(request, 'coupon_management.html', {
        'form': form,
        'coupons': coupons
    })


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, 'Coupon deleted successfully!')
    return redirect('coupon_management')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def top_selling(request):
    # Top 10 selling products
    products = OrderProduct.objects.values('product__product_name').annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum(F('quantity') * F('product_price'), output_field=models.FloatField())
    ).order_by('-total_quantity')[:10]

    ranked_products = [(rank + 1, product) for rank, product in enumerate(products)]

    # Top 10 selling categories
    categories = OrderProduct.objects.values('product__category__category_name').annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum(F('quantity') * F('product_price'), output_field=models.FloatField())
    ).order_by('-total_quantity')[:10]

    ranked_categories = [(rank + 1, category) for rank, category in enumerate(categories)]

    return render(request, 'top_selling.html', {
        'products': ranked_products,
        'categories': ranked_categories
    })



@admin_required
def download_ledger_pdf(request):
    # Create a file-like buffer to receive PDF data.
    buffer = HttpResponse(content_type='application/pdf')
    buffer['Content-Disposition'] = f'attachment; filename=ledger_book_{datetime.now().strftime("%Y-%m-%d")}.pdf'

    # Create the PDF object using the buffer as its "file."
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Styles
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph('Ledger Book', styles['Title']))
    elements.append(Spacer(1, 0.2 * inch))

    # Header row
    header_data = [
        'Order Number', 'Date', 'Status', 'Products', 'Quantity',
        'Unit Price', 'Total Discount', 'Total Amount'
    ]
    table_data = [header_data]

    # Column widths
    col_widths = [
        1.0 * inch,  # Order Number
        1.0 * inch,  # Date
        1.0 * inch,  # Status
        1.5 * inch,  # Products
        0.5 * inch, # Quantity
        1.0 * inch,  # Unit Price
        1.0 * inch,  # Total Discount
        1.0 * inch   # Total Amount
    ]

    # Fetch orders except Pending
    orders = Order.objects.exclude(status='Pending').order_by('-created_at')

    for order in orders:
        product_details = []
        for order_product in order.orderproduct_set.all():
            product_name = order_product.product.product_name
            quantity = order_product.quantity
            product_price = order_product.product_price
            discount = (order_product.product.original_price - order_product.product.price) * quantity
            product_details.append(f"{product_name}")

        product_details_str = "\n".join(product_details)
        row = [
            order.order_number,
            order.created_at.strftime('%Y-%m-%d'),
            order.status,
            Paragraph(product_details_str, styles['Normal']),
            order.orderproduct_set.count(),
            f"{order.order_total:.2f}",
            f"{order.coupon_amount:.2f}",
            f"{Decimal(order.order_total) - order.coupon_amount:.2f}"
        ]
        table_data.append(row)

    # Create table with styles and pagination
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Adjust font size to fit content
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)

    # Add a page break
    elements.append(PageBreak())

    # Order summary section
    total_orders = orders.count()
    total_order_amount = sum(Decimal(order.order_total) for order in orders)
    total_discount_amount = sum(
        (order_product.product.original_price - order_product.product.price) * order_product.quantity
        for order in orders for order_product in order.orderproduct_set.all()
    )
    total_coupon_amount = sum(order.coupon_amount for order in orders)

    elements.append(Paragraph('Order Summary', styles['Heading2']))
    elements.append(Spacer(1, 0.1 * inch))
    summary_data = [
        ['Total Orders', total_orders],
        ['Total Order Amount', f"{total_order_amount:.2f}"],
        ['Total Discount Amount', f"{total_discount_amount:.2f}"],
        ['Total Coupon Amount', f"{total_coupon_amount:.2f}"],
        ['Net Sales Amount', f"{total_order_amount - total_coupon_amount:.2f}"],
    ]
    summary_table = Table(summary_data, colWidths=[2 * inch, 3 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(summary_table)

    # Build the PDF
    doc.build(elements)

    return buffer



# views.py
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    user_address = order.address   # Assuming UserAddress is linked by user


    context = {
        'order': order,
        'user_address': user_address,
    }

    return render(request, 'order_details.html', context)
