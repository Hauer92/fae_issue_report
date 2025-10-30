from django import forms
from django.utils import timezone
from .models import Issue

class IssueForm(forms.ModelForm):
    # 覆寫 sla_due_at，提供 datetime-local 輸入與相容的 input_formats
    sla_due_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'vDateTimeInput'}
        ),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model = Issue
        fields = ['title', 'description', 'priority', 'status', 'assigned_to', 'sla_due_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'vTextField', 'placeholder': 'Short summary'}),
            'description': forms.Textarea(attrs={'rows': 6, 'class': 'vLargeTextField', 'placeholder': 'Details, steps, expected/actual...'}),
            'priority': forms.Select(attrs={'class': 'vSelect'}),
            'status': forms.Select(attrs={'class': 'vSelect'}),
            'assigned_to': forms.Select(attrs={'class': 'vSelect'}),
        }
