from django.urls import path
from .views import home, delete_lead, edit_lead, LeadCreateAPIView

urlpatterns = [
    path('', home),
    path('delete/<int:id>/', delete_lead),
    path('edit/<int:id>/', edit_lead),
    path('api/leads/create/', LeadCreateAPIView.as_view()),
]
