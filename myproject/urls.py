from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [

    # ADMIN PANEL
    path('admin/', admin.site.urls),

    # CRM APP URLS
    path('', include('crm.urls')),

    # LOGIN
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html'
        ),
        name='login'
    ),

    # LOGOUT
    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),

]