from django.conf import settings
from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=200)
    customer = models.CharField(max_length=200, blank=True)
    def __str__(self): return self.name

class Asset(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    serial_no = models.CharField(max_length=120)
    location = models.CharField(max_length=200, blank=True)
    def __str__(self): return self.serial_no

class Issue(models.Model):
    class Priority(models.IntegerChoices):
        LOW=1,'Low'; NORMAL=2,'Normal'; HIGH=3,'High'; CRITICAL=4,'Critical'
    class Status(models.TextChoices):
        NEW='NEW','New'
        IN_PROGRESS='INP','In Progress'
        ON_SITE='ONS','On-site'
        WAITING_PARTS='WTP','Waiting Parts'
        TESTING='TST','Testing'
        CUSTOMER_CONFIRM='CCF','Customer Confirm'
        RESOLVED='RES','Resolved'
        CLOSED='CLO','Closed'

    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=300)
    description = models.TextField()
    priority = models.IntegerField(choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField(max_length=3, choices=Status.choices, default=Status.NEW)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reported_issues')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_issues')
    sla_due_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return f"#{self.id} {self.title}"

class Attachment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class IssueEvent(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=50)  # created/status_changed/reassigned/sla_warn/sla_breach/closed
    from_value = models.CharField(max_length=100, blank=True)
    to_value = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
