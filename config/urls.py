from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Django'nun hazır auth URL'lerini (login/logout) dahil ediyoruz
    path('accounts/', include('django.contrib.auth.urls')),
    # Kendi uygulamamızın URL'lerini ana dizine bağlıyoruz
    path('', include('core.urls')),
]