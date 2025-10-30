from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Issue(models.Model):
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
        return f"#{self.id} {self.title}"

class Comment(models.Model):
    issue = models.ForeignKey(Issue, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.issue}"
