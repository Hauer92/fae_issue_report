from django.contrib import admin
from .models import Issue, Comment

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "priority", "status", "assigned_to", "created_by", "created_at")
    list_filter = ("priority", "status", "assigned_to")
    search_fields = ("title", "description")
    autocomplete_fields = ("assigned_to", "created_by")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "issue", "author", "created_at")
