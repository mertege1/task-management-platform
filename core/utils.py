from datetime import date, timedelta
from django.db.models import Q
from .models import Task
from collections import defaultdict

def calculate_workload_distribution(user, strategy='balanced', view_start=None, view_end=None):
    """
    İş yükü dağıtımını optimize eden ana fonksiyon.
    
    Parametreler:
    - user: Analiz edilecek kullanıcı
    - strategy: 'balanced', 'priority_weighted', 'size_weighted', 'deadline_weighted'
    - view_start: Grafiğin başlangıç tarihi (datetime.date objesi)
    - view_end: Grafiğin bitiş tarihi (datetime.date objesi)
    """
    
    # 1. Görevleri Çek (Atananlar veya Ortak Olunanlar)
    tasks = Task.objects.filter(
        Q(assigned_to=user) | Q(partners=user),
        status__in=['baslanmadi', 'calisiliyor', 'duraklatildi']
    ).distinct()
    
    today = date.today()
    
    # Tarih aralığı verilmediyse varsayılan olarak bugünden itibaren 15 gün
    if not view_start:
        view_start = today
    if not view_end:
        view_end = view_start + timedelta(days=14)

    daily_workload = defaultdict(float)

    # 2. Her Görevin Yükünü Hesapla ve Günlere Dağıt
    for task in tasks:
        remaining_hours = float(task.planned_hours) - float(task.spent_hours)
        if remaining_hours <= 0:
            continue
            
        # Görevin planlanan başlangıç ve bitiş tarihleri
        task_start = max(task.start_date, today) # Geçmişe iş yazılmaz, bugünden başlar
        task_end = task.due_date
        days_total = (task_end - task_start).days + 1
        
        if days_total <= 0:
            # Gecikmiş işleri doğrudan bugüne yığ
            daily_workload[today] += remaining_hours
            continue

        # Vaka Gereksinimi: Ayrı Ayrı Algoritmalar
        if strategy == 'priority_weighted':
            distribution = _algo_priority(remaining_hours, days_total, task.priority)
        elif strategy == 'size_weighted':
            distribution = _algo_size(remaining_hours, days_total, task.size)
        elif strategy == 'deadline_weighted':
            distribution = _algo_deadline(remaining_hours, days_total)
        else:
            # Standart Dengeli Dağıtım (Balanced)
            distribution = [remaining_hours / days_total] * days_total

        # Hesaplanan saatleri takvime işle
        for i, hours in enumerate(distribution):
            current_day = task_start + timedelta(days=i)
            daily_workload[current_day] += hours

    # 3. Grafiği İstenen Tarih Aralığına Göre Hazırla
    labels = []
    data = []
    
    # Görüntülenecek gün sayısı (View Start -> View End)
    delta = (view_end - view_start).days + 1
    
    # Güvenlik: Çok aşırı büyük aralıkları sınırlar (Opsiyonel, performans için)
    if delta > 366: delta = 366 
    if delta < 1: delta = 1 # Negatif tarih koruması

    for i in range(delta):
        day = view_start + timedelta(days=i)
        
        # Grafik eksen etiketi (Örn: 14 Feb)
        labels.append(day.strftime("%d %b"))
        
        # O güne ait iş yükü varsa al, yoksa 0
        val = daily_workload.get(day, 0)
        data.append(round(val, 2))
        
    return {'labels': labels, 'data': data}

# ---------------------------------------------------------
# YARDIMCI ALGORİTMALAR (AYRI AYRI)
# ---------------------------------------------------------

def _algo_priority(hours, days, priority):
    """ALGORİTMA 1: Öncelik Bazlı (Yüksek öncelik ilk günlere yığılır)"""
    weight_map = {'yuksek': 2.0, 'orta': 1.0, 'dusuk': 0.5}
    w = weight_map.get(priority, 1.0)
    # Harmonik seri ile azalan yükleme
    factors = [ (1 / (i + 1)) * w for i in range(days)]
    total_f = sum(factors)
    return [(f / total_f) * hours for f in factors]

def _algo_size(hours, days, size):
    """ALGORİTMA 2: İş Büyüklüğü Bazlı (Büyük işlere başta daha fazla pay ayrılır)"""
    # İş büyüklüğü 5 ise başta yoğun başlanır
    boost = 1 + (size / 5.0)
    factors = [ (boost if i < days/2 else 1) for i in range(days)]
    total_f = sum(factors)
    return [(f / total_f) * hours for f in factors]

def _algo_deadline(hours, days):
    """ALGORİTMA 3: Tamamlanma Tarihi Bazlı (Teslimat yaklaştıkça tempo artar)"""
    # Son günlere doğru üstel artış (Exponential)
    factors = [ (i + 1)**1.5 for i in range(days)]
    total_f = sum(factors)
    return [(f / total_f) * hours for f in factors]