from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.adminlogin, name='alogin'),
    path('ahome/', views.ahome, name='ahome'),
    path('userlist/',views.user_list,name='userlist'),
    path('categories/',views.categorylist,name='categorylist'),
    path('category/add/', views.addcategory, name='addcategory'),
    path('category/edit/<int:category_id>/', views.editcategory, name='editcategory'),
    path('category/delete/<int:category_id>/', views.deletecategory, {'soft_delete': True}, name='deletecategory'),
    path('category/hard_delete/<int:category_id>/', views.deletecategory, {'soft_delete': False}, name='hard_deletecategory'),
    path('product/hard_delete/<int:product_id>/', views.deleteproduct, name='hard_delete_product'),
    path('productlist/',views.productlist,name='productlist'),
    path('update-status/<int:user_id>/', views.update_status, name='update_status'),    
    path('product/add/', views.addproduct, name='addproduct'),
    path('product/edit/<int:product_id>/', views.editproduct, name='editproduct'),
    path('product/delete/<int:product_id>/', views.deleteproduct, name='deleteproduct'),
    path('delete-gallery-image/', views.delete_gallery_image, name='delete_gallery_image'),
    path('alogout/', views.adminlogout, name='alogout'),
    path('manage_orders/', views.manage_orders, name='manage_orders'),
    path('sales-report/', views.sales_report, name='sales_report'),
    path('sales-report/download-pdf/', views.download_pdf, name='download_pdf'),
    path('sales-report/download-excel/', views.download_excel, name='download_excel'),
    path('coupon-management/', views.coupon_management, name='coupon_management'),
    path('delete-coupon/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),
    path('top_selling/', views.top_selling, name='top_selling'),
    path('download_ledger/', views.download_ledger_pdf, name='download_ledger_pdf'),
    path('order/<int:order_id>/details/', views.order_details, name='order_details'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
