from django.contrib import admin
from .models import Project, Asset, Issue, Attachment, IssueEvent

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display=("id","name","customer")

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display=("id","serial_no","project","location")
    search_fields=("serial_no","location")

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display=("id","title","project","priority","status","assignee","created_at")
    list_filter=("status","priority","project")
    search_fields=("title","description")

admin.site.register(Attachment)
admin.site.register(IssueEvent)
