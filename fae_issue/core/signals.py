from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Issue, IssueEvent
from .tasks import send_issue_update_to_teams

@receiver(post_save, sender=Issue)
def on_issue_save(sender, instance: Issue, created, **kwargs):
    action = 'created' if created else 'updated'
    IssueEvent.objects.create(
        issue=instance, actor=(instance.reporter if created else (instance.assignee or instance.reporter)),
        action='created' if created else 'status_changed', to_value=instance.status
    )
    send_issue_update_to_teams.delay(instance.id, action)
