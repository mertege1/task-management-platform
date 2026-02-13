from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Task

@login_required
def home(request):
    """
    Kullanıcı giriş yaptıktan sonra karşılaştığı ana yönlendirici.
    Kullanıcının rolüne bakar ve ilgili dashboard'a gönderir.
    """
    if request.user.role == 'manager':
        return redirect('manager_dashboard')
    else:
        # Varsayılan olarak herkesi çalışan dashboarduna gönder (yönetici değilse)
        return redirect('employee_dashboard')

@login_required
def employee_dashboard(request):
    """
    Çalışan Paneli: Sadece giriş yapan kullanıcıya atanmış görevleri listeler.
    """
    # assigned_to=request.user diyerek sadece o kişiye ait görevleri çekiyoruz.
    tasks = Task.objects.filter(assigned_to=request.user).order_by('due_date')
    
    context = {
        'tasks': tasks,
        'page_title': 'Görevlerim'
    }
    return render(request, 'dashboard_employee.html', context)

@login_required
def manager_dashboard(request):
    """
    Yönetici Paneli: Tüm sistemdeki görevleri listeler.
    """
    # Yönetici her şeyi görebilir (all())
    tasks = Task.objects.all().order_by('due_date')
    
    context = {
        'tasks': tasks,
        'page_title': 'Ekip Yönetim Paneli'
    }
    return render(request, 'dashboard_manager.html', context)