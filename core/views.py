from rest_framework import viewsets, permissions
from .models import Issue, Attachment
from .serializers import IssueSerializer, AttachmentSerializer

class IsReporterOrManager(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if isinstance(obj, Issue):
            return obj.reporter_id == request.user.id or (obj.assignee_id == request.user.id)
        return False

class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.select_related("project","asset","reporter","assignee").all().order_by("-id")
    serializer_class = IssueSerializer
    permission_classes = [permissions.IsAuthenticated, IsReporterOrManager]

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.select_related("issue","uploaded_by").all()
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsReporterOrManager]
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
