from django.urls import path
from . import views

app_name = 'issues'

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create, name='create'),
    path('<int:pk>/', views.detail, name='detail'),
]
