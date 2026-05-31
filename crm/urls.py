from django.urls import path

from .views import (
    home,
    dashboard,
    delete_lead,
    edit_lead,
    lead_detail,
    LeadCreateAPIView,
    tasks,
    complete_task,
    delete_task,
)

urlpatterns = [

    path('', home, name='home'),

    path('dashboard/', dashboard, name='dashboard'),

    path('edit/<int:id>/', edit_lead, name='edit_lead'),

    path('delete/<int:id>/', delete_lead, name='delete_lead'),

    path('lead/<int:id>/', lead_detail, name='lead_detail'),

    path('tasks/', tasks, name='tasks'),

    path('tasks/complete/<int:id>/', complete_task, name='complete_task'),

    path('tasks/delete/<int:id>/', delete_task, name='delete_task'),

    path('api/leads/', LeadCreateAPIView.as_view(), name='lead-create-api'),
]