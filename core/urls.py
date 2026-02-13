from django.urls import path
from . import views

urlpatterns = [
    # Ana sayfa (Yönlendirici - Giriş sonrası buraya düşer)
    path('', views.home, name='home'),
    
    # Çalışan Paneli Adresi
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'),
    
    # Yönetici Paneli Adresi
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),
]