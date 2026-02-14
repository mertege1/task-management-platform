from django import forms
from .models import Task, CustomUser, WorkLog

# ---------------------------------------------------------
# 1. GÖREV FORMU (TaskForm)
# ---------------------------------------------------------
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'priority', 'status', 'size', 
            'assigned_to', 'partners', 'informees',
            'start_date', 'due_date', 'planned_hours', 'spent_hours', 'roadmap_summary'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Görevin kısa başlığı'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detaylı açıklama...'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'partners': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'informees': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '3'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'planned_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'spent_hours': forms.NumberInput(attrs={
                'class': 'form-control bg-light', 
                'step': '0.1', 
                'readonly': 'readonly'
            }), 
        }
        labels = {
            'roadmap_summary': 'Yol Haritası Özeti',
            'spent_hours': 'Toplam Harcanan Süre (Otomatik)'
        }
    
    roadmap_summary = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Adım 1: Analiz...\nAdım 2: Geliştirme...'}),
        required=False,
        label="Hızlı Yol Haritası (Taslak)"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(TaskForm, self).__init__(*args, **kwargs)

        if self.user and self.user.role == 'employee':
            if not self.instance.pk:
                self.fields['assigned_to'].queryset = CustomUser.objects.filter(id=self.user.id)
                self.fields['assigned_to'].initial = self.user
            else:
                self.fields['assigned_to'].queryset = CustomUser.objects.filter(id=self.instance.assigned_to.id)
                self.fields['assigned_to'].initial = self.instance.assigned_to
            
            self.fields['assigned_to'].disabled = True

# ---------------------------------------------------------
# 2. EFOR KAYIT FORMU (WorkLogForm)
# ---------------------------------------------------------
class WorkLogForm(forms.ModelForm):
    class Meta:
        model = WorkLog
        fields = ['hours', 'date', 'description']
        widgets = {
            'hours': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.1', 
                'placeholder': 'Örn: 2.5',
                'min': '0.1',
                'required': 'true'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'required': 'true'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Bugün bu iş için neler yaptınız?',
                'required': 'true'
            }),
        }
        labels = {
            'hours': 'Çalışılan Süre (Saat)',
            'date': 'Çalışma Tarihi',
            'description': 'İş Açıklaması'
        }