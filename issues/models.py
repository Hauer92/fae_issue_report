from django.db import models
from django.contrib.auth import get_user_model

# Get the custom user model (or default User)
User = get_user_model()

class Issue(models.Model):
    """Represents a tracked issue or bug report."""
    class Priority(models.IntegerChoices):
        P0 = 0, "P0 - Critical"
        P1 = 1, "P1 - High"
        P2 = 2, "P2 - Medium"
        P3 = 3, "P3 - Low"

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        TRIAGED = "TRIAGED", "Triaged"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        PENDING = "PENDING", "Pending"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"
        REOPENED = "REOPENED", "Reopened"
        ON_HOLD = "ON_HOLD", "On Hold"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.IntegerField(choices=Priority.choices, default=Priority.P2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    created_by = models.ForeignKey(User, related_name="issues_created", on_delete=models.PROTECT)
    assigned_to = models.ForeignKey(User, related_name="issues_assigned", on_delete=models.SET_NULL, null=True, blank=True)
    sla_due_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.author} 於 {self.created_at.strftime("%Y-%m-%d %H:%M")} 留言'

# --- New Model Added to fix admin.py import error and SystemCheckError (E108) ---
class Comment(models.Model):
    issue = models.ForeignKey(
        Issue, 
        related_name="comments", 
        on_delete=models.CASCADE, 
        verbose_name='問題'
    )
    author = models.ForeignKey(
        User, 
        related_name="issue_comments", 
        on_delete=models.PROTECT
    )
    text = models.TextField(
        verbose_name='留言內容'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='建立時間'
    )
    class Meta:
        verbose_name = '留言'
        verbose_name_plural = '留言'
        ordering = ['created_at']
    def __str__(self):
        return f'{self.author} 於 {self.created_at.strftime("%Y-%m-%d %H:%M")} 留言'
