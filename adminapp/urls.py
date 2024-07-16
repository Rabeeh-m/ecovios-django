
from django.urls import path
from . import views

urlpatterns = [
    path('', views.adminlogin, name='alogin'),
    path('ahome/', views.ahome, name='ahome'),
    path('userlist/',views.user_list,name='userlist'),
    path('categories/',views.categorylist,name='categorylist'),
    path('category/add/', views.addcategory, name='addcategory'),
    path('category/edit/<int:category_id>/', views.editcategory, name='editcategory'),
    path('category/delete/<int:category_id>/', views.deletecategory, {'soft_delete': True}, name='deletecategory'),
    path('category/hard_delete/<int:category_id>/', views.deletecategory, {'soft_delete': False}, name='hard_deletecategory'),
    path('productlist/',views.productlist,name='productlist'),
    path('update-status/<int:user_id>/', views.update_status, name='update_status'),    
    path('product/add/', views.addproduct, name='addproduct'),
    path('product/edit/<int:product_id>/', views.editproduct, name='editproduct'),
    path('product/delete/<int:product_id>/', views.deleteproduct, name='deleteproduct'),
    path('alogout/', views.adminlogout, name='alogout'),
    

] 
