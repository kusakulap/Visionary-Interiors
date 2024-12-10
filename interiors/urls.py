from django.urls import path
from . import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path("admin/", admin.site.urls, name='admin'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('contact/', views.contact, name='contact'),
    path('generate/', views.generate_image, name='generate_image'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
