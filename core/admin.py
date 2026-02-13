from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Task, RoadmapItem

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

# 3. Görev Yönetimi Admin Ayarları
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assigned_to', 'priority', 'status', 'due_date', 'planned_hours', 'spent_hours']
    # DÜZELTME: 'team' yerine 'assigned_to__team' kullanıldı.
    # Böylece görevin atandığı kişinin ekibine göre filtreleme yapabileceğiz.
    list_filter = ['status', 'priority', 'assigned_to', 'assigned_to__team'] 
    search_fields = ['title', 'description']
    inlines = [RoadmapInline] # Görev sayfasının altında yol haritasını göster

# Modelleri kaydet
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Task, TaskAdmin)

# 4. Admin Paneli Görsel Özelleştirmeleri (BURAYI EKLİYORUZ)
admin.site.site_header = "İş Yönetim Platformu"      # Sol üstteki mavi başlık (Django administration yerine)
admin.site.site_title = "İş Takip Admin Paneli"      # Tarayıcı sekmesinde görünen başlık
admin.site.index_title = "Yönetim Merkezi"           # Sayfanın ortasındaki başlık (Site administration yerine)