from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from auth_app.views import login_view

urlpatterns = [
    path('', login_view),  # 👈 Now home page shows login form
    path('admin/', admin.site.urls),
    path('auth/', include('auth_app.urls')),
]



#Date: 2025-05-19