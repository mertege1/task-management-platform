from django import forms
from .models import Task, CustomUser

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'priority', 'status', 'size', 
            'assigned_to', 'partners', 'informees',
            'start_date', 'due_date', 'planned_hours', 'spent_hours', 'roadmap_summary'
        ]
        # Form elemanlarına Bootstrap sınıfları ve özellikleri ekleyelim
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Görevin kısa başlığı'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detaylı açıklama...'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'partners': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}), # Ctrl ile çoklu seçim
            'informees': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '3'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'planned_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'spent_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
        }
        labels = {
            'roadmap_summary': 'Yol Haritası Özeti'
        }
    
    # Yol haritası için basit bir alan ekleyelim (Şimdilik textarea, ileride detaylandırırız)
    roadmap_summary = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Adım 1: Analiz (2 saat)\nAdım 2: Geliştirme (4 saat)...'}),
        required=False,
        label="Hızlı Yol Haritası (Taslak)"
    )

    def __init__(self, *args, **kwargs):
        # Form başlatılırken kullanıcı bilgisini (user) alalım
        self.user = kwargs.pop('user', None)
        super(TaskForm, self).__init__(*args, **kwargs)

        # Eğer giriş yapan kişi 'Çalışan' ise:
        # 1. Başkasına görev atayamaz, 'assigned_to' alanı sadece kendisi olmalı veya gizlenmeli.
        # 2. Biz şimdilik otomatik olarak kendisini seçeceğiz ve alanı okunabilir yapacağız.
        if self.user and self.user.role == 'employee':
             self.fields['assigned_to'].queryset = CustomUser.objects.filter(id=self.user.id)
             self.fields['assigned_to'].initial = self.user
             self.fields['assigned_to'].widget.attrs['readonly'] = True