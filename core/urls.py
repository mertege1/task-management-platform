from django.urls import path
from . import views

urlpatterns = [
    # Ana sayfa (Yönlendirici - Giriş sonrası buraya düşer)
    path('', views.home, name='home'),
    
    # Çalışan Paneli Adresi
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'),
    
    # Yönetici Paneli Adresi
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),

    # Görev Oluşturma
    path('task/create/', views.create_task, name='create_task'),

    # Görev Detay ve Düzenleme
    # <int:pk> kısmı, URL'deki sayıyı alıp fonksiyona 'pk' (ID) olarak gönderir.
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    path('task/<int:pk>/edit/', views.update_task, name='update_task'),
    
    path('task/<int:pk>/delete/', views.delete_task, name='delete_task'),
]