from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Task, RoadmapItem
from .forms import TaskForm

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

@login_required
def create_task(request):
    """
    Yeni görev oluşturma sayfası.
    """
    if request.method == 'POST':
        # Formu doldurulmuş verilerle başlat (user bilgisini de gönderiyoruz)
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user # Görevi oluşturan kişiyi (request.user) kaydet
            
            # Eğer çalışan oluşturuyorsa, atanan kişi kendisidir (Formda readonly olsa bile garantileyelim)
            if request.user.role == 'employee':
                task.assigned_to = request.user
            
            task.save() # Önce görevi kaydet (ID oluşsun)
            form.save_m2m() # Sonra Partners gibi çoklu ilişkileri (Many-to-Many) kaydet
            
            # YOL HARİTASI KAYIT MANTIĞI
            # Formdan gelen metni satır satır bölüp RoadmapItem olarak kaydediyoruz
            roadmap_text = form.cleaned_data.get('roadmap_summary')
            if roadmap_text:
                steps = roadmap_text.split('\n')
                for i, step in enumerate(steps, 1):
                    if step.strip(): # Boş satır değilse
                        RoadmapItem.objects.create(
                            task=task,
                            order=i,
                            description=step.strip()
                        )
            
            messages.success(request, 'Görev başarıyla oluşturuldu!')
            return redirect('home')
    else:
        # Boş form göster
        form = TaskForm(user=request.user)

    context = {
        'form': form,
        'page_title': 'Yeni Görev Oluştur'
    }
    return render(request, 'task_form.html', context)


@login_required
def task_detail(request, pk):
    """
    Görevin tüm detaylarını ve yol haritasını gösterir.
    pk: Primary Key (Görevin ID'si)
    """
    task = get_object_or_404(Task, pk=pk)
    
    context = {
        'task': task,
        'page_title': f'Görev Detayı: {task.title}'
    }
    return render(request, 'task_detail.html', context)

@login_required
def update_task(request, pk):
    """
    Mevcut bir görevi düzenler.
    create_task ile aynı formu (task_form.html) kullanır ama içi dolu gelir.
    """
    task = get_object_or_404(Task, pk=pk)
    
    # GÜVENLİK KONTROLÜ:
    # Çalışanlar sadece kendilerine atanan görevleri düzenleyebilir.
    # Yönetici ise her şeyi düzenleyebilir.
    if request.user.role == 'employee' and task.assigned_to != request.user:
         messages.error(request, "Bu görevi düzenleme yetkiniz yok! Sadece kendi görevlerinizi güncelleyebilirsiniz.")
         return redirect('home')

    if request.method == 'POST':
        # instance=task diyerek "bu formu şu görev verileriyle güncelle" diyoruz
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            task = form.save() # Güncellemeyi kaydet
            
            # YOL HARİTASI GÜNCELLEME MANTIĞI
            roadmap_text = form.cleaned_data.get('roadmap_summary')
            if roadmap_text:
                # Mevcut adımları silip yenilerini ekliyoruz (sıralama bozulmaması için en temiz yöntem)
                task.roadmap.all().delete()
                steps = roadmap_text.split('\n')
                for i, step in enumerate(steps, 1):
                    if step.strip():
                        RoadmapItem.objects.create(
                            task=task,
                            order=i,
                            description=step.strip()
                        )
            
            messages.success(request, 'Görev başarıyla güncellendi.')
            return redirect('task_detail', pk=task.pk)
    else:
        # Formu mevcut bilgilerle doldurup göster
        # Yol haritasını metin alanına geri yüklüyoruz ki kullanıcı görebilsin
        initial_roadmap = ""
        for item in task.roadmap.all():
            initial_roadmap += f"{item.description}\n"
            
        form = TaskForm(instance=task, user=request.user, initial={'roadmap_summary': initial_roadmap})
    
    return render(request, 'task_form.html', {'form': form, 'page_title': 'Görevi Düzenle'})