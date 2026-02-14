from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse  # <--- EKLENDİ: AJAX yanıtı için

from .models import Task, RoadmapItem, CustomUser
from .forms import TaskForm
from .utils import calculate_workload_distribution

@login_required
def home(request):
    """
    Ana yönlendirici: Kullanıcıyı rolüne göre ilgili panele gönderir.
    """
    if request.user.role == 'manager':
        return redirect('manager_dashboard')
    else:
        return redirect('employee_dashboard')

@login_required
def employee_dashboard(request):
    """
    Çalışan Paneli: 
    AJAX desteği ile grafik verilerini dinamik döndürür.
    """
    today = timezone.now().date()
    
    # 1. URL Parametrelerini Yakala
    strategy = request.GET.get('strategy', 'balanced')
    date_range = request.GET.get('range', 'month')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    # 2. Tarih Aralığını Hesapla
    view_start = today
    view_end = today + timedelta(days=29)

    if date_range == 'custom' and start_str and end_str:
        try:
            view_start = datetime.strptime(start_str, '%Y-%m-%d').date()
            view_end = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    elif date_range == 'week':
        view_end = view_start + timedelta(days=6)
    elif date_range == 'month':
        view_end = view_start + timedelta(days=29)
    elif date_range == 'year':
        view_end = view_start + timedelta(days=364)

    # --- AJAX İSTEĞİ İSE SADECE JSON DÖN ---
    if request.GET.get('ajax') == 'true':
        chart_data = calculate_workload_distribution(
            request.user, 
            strategy=strategy,
            view_start=view_start,
            view_end=view_end
        )
        return JsonResponse({
            'labels': chart_data['labels'],
            'data': chart_data['data'],
            'strategy': strategy
        })
    # ---------------------------------------

    # Normal Sayfa Yüklemesi (AJAX değilse burası çalışır)
    tasks = Task.objects.filter(
        Q(assigned_to=request.user) | Q(partners=request.user)
    ).distinct().order_by('due_date')
    
    alerts = []
    for task in tasks:
        if task.status not in ['tamamlandi', 'iptal']:
            if task.due_date < today:
                alerts.append({'task': task, 'type': 'danger', 'msg': 'Gecikti!'})
            elif (task.due_date - today).days <= 2:
                alerts.append({'task': task, 'type': 'warning', 'msg': 'Yaklaşıyor!'})

    today_tasks = tasks.filter(
        start_date__lte=today,
        due_date__gte=today
    ).exclude(status__in=['tamamlandi', 'iptal'])

    teammate_tasks = Task.objects.filter(
        assigned_to__team=request.user.team
    ).exclude(
        Q(assigned_to=request.user) | Q(partners=request.user)
    ).distinct().order_by('due_date')
    
    # İlk yükleme için grafik verisi
    chart_data = calculate_workload_distribution(
        request.user, 
        strategy=strategy,
        view_start=view_start,
        view_end=view_end
    )
    
    context = {
        'tasks': tasks,
        'teammate_tasks': teammate_tasks,
        'today_tasks': today_tasks,
        'alerts': alerts,
        'page_title': 'Görevlerim ve Ekip Takibi',
        'chart_labels': chart_data['labels'],
        'chart_data': chart_data['data'],
        'current_strategy': strategy,
        'current_range': date_range,
        'start_date_val': view_start.strftime('%Y-%m-%d'),
        'end_date_val': view_end.strftime('%Y-%m-%d'),
        'today': today,
    }
    return render(request, 'dashboard_employee.html', context)

@login_required
def manager_dashboard(request):
    """
    Yönetici Paneli: AJAX desteği ile dinamik grafik.
    """
    today = timezone.now().date()
    
    # Parametreleri Al
    selected_user_id = request.GET.get('user_id')
    strategy = request.GET.get('strategy', 'balanced')
    date_range = request.GET.get('range', 'month')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    
    # Tarih Aralığı
    view_start = today
    view_end = today + timedelta(days=29)

    if date_range == 'custom' and start_str and end_str:
        try:
            view_start = datetime.strptime(start_str, '%Y-%m-%d').date()
            view_end = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError: pass
    elif date_range == 'week':
        view_end = view_start + timedelta(days=6)
    elif date_range == 'month':
        view_end = view_start + timedelta(days=29)
    elif date_range == 'year':
        view_end = view_start + timedelta(days=364)
    
    # --- AJAX İSTEĞİ (Manager) ---
    if request.GET.get('ajax') == 'true' and selected_user_id and selected_user_id != 'all':
        target_user = get_object_or_404(CustomUser, id=selected_user_id)
        workload = calculate_workload_distribution(
            target_user, 
            strategy=strategy, 
            view_start=view_start, 
            view_end=view_end
        )
        return JsonResponse({
            'type': 'individual',
            'labels': workload['labels'],
            'data': workload['data'],
            'strategy': strategy
        })
    # -----------------------------

    tasks = Task.objects.all().order_by('due_date')
    employees = CustomUser.objects.filter(role='employee')

    delayed_tasks = []
    for task in tasks:
        is_overdue = task.due_date < today and task.status != 'tamamlandi'
        is_urgent_start = (task.due_date - today).days <= 3 and task.status == 'baslanmadi' and task.due_date >= today
        if is_overdue or is_urgent_start:
            delayed_tasks.append(task)

    # Grafik Mantığı (Normal Yükleme)
    chart_context = {}
    if selected_user_id and selected_user_id != 'all':
        target_user = get_object_or_404(CustomUser, id=selected_user_id)
        workload = calculate_workload_distribution(
            target_user, 
            strategy=strategy,
            view_start=view_start,
            view_end=view_end
        )
        chart_context = {'type': 'individual', 'labels': workload['labels'], 'data': workload['data'], 'user': target_user}
    else:
        employee_names = []
        planned_data = []
        spent_data = []
        for user in employees:
            stats = Task.objects.filter(Q(assigned_to=user) | Q(partners=user)).distinct().aggregate(total_planned=Sum('planned_hours'), total_spent=Sum('spent_hours'))
            p = float(stats['total_planned'] or 0)
            s = float(stats['total_spent'] or 0)
            if p > 0 or s > 0:
                employee_names.append(user.get_full_name() or user.username)
                planned_data.append(p)
                spent_data.append(s)
        chart_context = {'type': 'aggregate', 'labels': employee_names, 'planned': planned_data, 'spent': spent_data}

    context = {
        'tasks': tasks,
        'delayed_tasks': delayed_tasks,
        'page_title': 'Ekip Yönetim Paneli',
        'today': today,
        'employees': employees,
        'selected_user_id': int(selected_user_id) if selected_user_id and selected_user_id != 'all' else None,
        'current_strategy': strategy,
        'current_range': date_range,
        'start_date_val': view_start.strftime('%Y-%m-%d'),
        'end_date_val': view_end.strftime('%Y-%m-%d'),
        'chart_context': chart_context,
    }
    return render(request, 'dashboard_manager.html', context)

@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            if request.user.role == 'employee':
                task.assigned_to = request.user
            task.save()
            form.save_m2m() 
            
            roadmap_text = form.cleaned_data.get('roadmap_summary')
            if roadmap_text:
                steps = roadmap_text.split('\n')
                for i, step in enumerate(steps, 1):
                    if step.strip():
                        RoadmapItem.objects.create(task=task, order=i, description=step.strip())

            emails = []
            if task.assigned_to.email: emails.append(task.assigned_to.email)
            emails.extend([p.email for p in task.partners.all() if p.email])
            emails.extend([p.email for p in task.informees.all() if p.email])
            
            all_recipients = list(set(emails))
            if all_recipients:
                send_mail(
                    f'Yeni Görev Atandı: {task.title}',
                    f"Merhaba, '{task.title}' başlıklı görevde isminiz geçmektedir.",
                    settings.DEFAULT_FROM_EMAIL,
                    all_recipients,
                    fail_silently=True
                )

            messages.success(request, 'Görev başarıyla oluşturuldu!')
            return redirect('home')
    else:
        form = TaskForm(user=request.user)

    return render(request, 'task_form.html', {'form': form, 'page_title': 'Yeni Görev Oluştur'})

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    today = timezone.now().date()
    return render(request, 'task_detail.html', {'task': task, 'page_title': f'Görev Detayı: {task.title}', 'today': today})

@login_required
def update_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    is_partner = task.partners.filter(id=request.user.id).exists()
    
    if request.user.role == 'employee' and task.assigned_to != request.user and not is_partner:
         messages.error(request, "Bu görevi düzenleme yetkiniz yok!")
         return redirect('home')

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            task = form.save()
            
            roadmap_text = form.cleaned_data.get('roadmap_summary')
            if roadmap_text:
                task.roadmap.all().delete()
                steps = roadmap_text.split('\n')
                for i, step in enumerate(steps, 1):
                    if step.strip():
                        RoadmapItem.objects.create(task=task, order=i, description=step.strip())
            
            recipients = [task.created_by.email]
            if task.assigned_to != request.user: recipients.append(task.assigned_to.email)
            recipients.extend([p.email for p in task.partners.all() if p.email])
            recipients.extend([p.email for p in task.informees.all() if p.email])

            if recipients:
                send_mail(
                    f'Görev Güncellendi: {task.title}',
                    f"'{task.title}' görevinde güncelleme yapıldı.",
                    settings.DEFAULT_FROM_EMAIL,
                    list(set(recipients)),
                    fail_silently=True
                )
            
            messages.success(request, 'Görev başarıyla güncellendi.')
            return redirect('task_detail', pk=task.pk)
    else:
        initial_roadmap = "".join([f"{item.description}\n" for item in task.roadmap.all()])
        form = TaskForm(instance=task, user=request.user, initial={'roadmap_summary': initial_roadmap})
    
    return render(request, 'task_form.html', {'form': form, 'page_title': 'Görevi Düzenle'})

@login_required
def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.user.role == 'manager' or task.created_by == request.user:
        task.delete()
        messages.success(request, 'Görev başarıyla silindi.')
    else:
        messages.error(request, 'Bu görevi silme yetkiniz bulunmamaktadır.')
    return redirect('home')