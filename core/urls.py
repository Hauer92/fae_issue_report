from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IssueViewSet, AttachmentViewSet

router = DefaultRouter()
router.register(r'issues', IssueViewSet, basename='issue')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
urlpatterns = [ path('', include(router.urls)) ]
