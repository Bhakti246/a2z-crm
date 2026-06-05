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
    update_status,
)
from .views_meta import (
    meta_callback,
    meta_connect,
    meta_data_deletion,
    meta_webhook,
    send_meta_message,
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

    path(
    'update-status/<int:lead_id>/',
    update_status,
    name='update_status'),

    path('webhook/', meta_webhook, name='meta_webhook'),
    path('webhook/meta/', meta_webhook, name='meta_webhook_named'),
    path('integrations/meta/connect/', meta_connect, name='connect_meta_account'),
    path('integrations/meta/callback/', meta_callback, name='meta_callback'),
    path('integrations/meta/messages/send/', send_meta_message, name='send_meta_message'),
    path('privacy/meta/data-deletion/', meta_data_deletion, name='meta_data_deletion'),
]
