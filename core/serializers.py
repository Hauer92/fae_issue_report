from rest_framework import serializers
from .models import Issue, Attachment

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id","file","uploaded_by","uploaded_at"]
        read_only_fields = ["uploaded_by","uploaded_at"]

class IssueSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    reporter_name = serializers.SerializerMethodField()
    assignee_name = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = ["id","project","asset","title","description","priority","status",
                  "reporter","assignee","reporter_name","assignee_name","sla_due_at",
                  "attachments","created_at","updated_at"]
        read_only_fields = ["reporter","created_at","updated_at"]

    def get_reporter_name(self, obj): return obj.reporter.get_full_name() or obj.reporter.username
    def get_assignee_name(self, obj): return obj.assignee.get_full_name() if obj.assignee else None

    def create(self, validated_data):
        validated_data["reporter"] = self.context["request"].user
        return super().create(validated_data)
