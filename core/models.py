# ⚠️ 以下僅為 Meta.ordering 與 indexes 片段，請合併到你現有的模型類別中。
# 請不要移除你既有的欄位定義。

from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=255)
    customer = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['updated_at']),
        ]

class Asset(models.Model):
    name = models.CharField(max_length=255)
    serial_no = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['project']),
        ]

class Issue(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]

    title = models.CharField(max_length=255)
    priority = models.CharField(max_length=50)
    assignee = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['project', 'status']),
            models.Index(fields=['asset', 'status']),
        ]

class Attachment(models.Model):
    issue = models.ForeignKey('Issue', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['issue']),
            models.Index(fields=['created_at']),
        ]

class IssueEvent(models.Model):
    issue = models.ForeignKey('Issue', on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['issue']),
            models.Index(fields=['created_at']),
            models.Index(fields=['event_type']),
        ]
