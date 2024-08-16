
from django.contrib import admin
from django.urls import path,include
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.urls import re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('store/', include('store.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('alogin/', include('adminapp.urls')),
    path('cart/', include('carts.urls')),

    path('orders/', include('orders.urls')),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
