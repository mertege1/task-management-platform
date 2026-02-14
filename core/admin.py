from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Task, RoadmapItem, WorkLog

# 1. Kullanıcı Modelini Admin Paneline Tanıt
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Listeleme ekranında görünecek alanlar
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'team', 'title']
    # Kullanıcı detayına girince görünecek ekstra alanlar
    fieldsets = UserAdmin.fieldsets + (
        ('Şirket Bilgileri', {'fields': ('role', 'team', 'title')}),
    )

# 2. Yol Haritası Adımlarını Görev İçinde Göster (Inline)
class RoadmapInline(admin.TabularInline):
    model = RoadmapItem
    extra = 1 # Varsayılan olarak 1 boş satır göster

# 3. Efor Kayıtlarını Görev İçinde Göster (Inline)
class WorkLogInline(admin.TabularInline):
    model = WorkLog
    extra = 0 # Otomatik boş satır çıkarma, sadece mevcutları göster
    readonly_fields = ['created_at']
    fields = ['user', 'hours', 'date', 'description']

# 4. Görev Yönetimi Admin Ayarları
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assigned_to', 'priority', 'status', 'due_date', 'planned_hours', 'spent_hours']
    # Görevin atandığı kişinin ekibine göre filtreleme yapabilme
    list_filter = ['status', 'priority', 'assigned_to', 'assigned_to__team'] 
    search_fields = ['title', 'description']
    # Görev sayfasının altında hem yol haritasını hem de efor kayıtlarını göster
    inlines = [RoadmapInline, WorkLogInline]

# 5. Efor Kayıtları İçin Ayrı Bir Yönetim Sayfası
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'hours', 'date']
    list_filter = ['date', 'user', 'task']
    search_fields = ['description', 'task__title', 'user__username']

# Modelleri kaydet
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(WorkLog, WorkLogAdmin)

# 6. Admin Paneli Görsel Özelleştirmeleri
admin.site.site_header = "İş Yönetim Platformu"      # Sol üstteki mavi başlık
admin.site.site_title = "İş Takip Admin Paneli"      # Tarayıcı sekmesinde görünen başlık
admin.site.index_title = "Yönetim Merkezi"           # Sayfanın ortasındaki başlık