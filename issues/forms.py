from django import forms
from django.utils import timezone
from .models import Issue, Comment

class IssueForm(forms.ModelForm):
    # 覆寫 sla_due_at，提供 datetime-local 輸入與相容的 input_formats
    title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900'})
    )
    
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Define the common Tailwind classes for all text/select inputs
        BASE_CLASS = 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 text-gray-900 focus:ring-blue-500 focus:border-blue-500'
        
        # Apply the classes to all fields
        for field_name, field in self.fields.items():
            
            # Apply base classes to most fields (TextInput, Select, DateInput, etc.)
            field.widget.attrs.update({
                'class': BASE_CLASS
            })

            # For the Description (Textarea), add specific height and resize
            if field_name == 'description':
                 field.widget.attrs['class'] += ' h-32 resize-y'

class CommentForm(forms.ModelForm):
    # 這是為了讓使用者專注於輸入內容，不顯示 label
    body = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': '留下您的評論或更新狀態...'}),
        label='' 
    )

    class Meta:
        model = Comment
        fields = ('body',)

    # 為了套用 Tailwind CSS 樣式，我們在這裡加上 class
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 應用 Tailwind 樣式到 Textarea
        self.fields['body'].widget.attrs.update({
            'class': 'mt-1 block w-full border border-gray-300 rounded-lg shadow-sm p-3 focus:ring-blue-500 focus:border-blue-500 text-gray-900 resize-y',
        })
