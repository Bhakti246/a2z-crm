from django.shortcuts import render, redirect, get_object_or_404

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import json

from .forms import LeadForm
from .models import Lead, LeadNote, Task
from .serializers import LeadSerializer


# ==============================
# HOME PAGE + CREATE LEAD
# ==============================

def home(request):

    success = False

    if request.method == "POST":

        score = 0

        budget = int(request.POST.get('budget', 0))

        if budget >= 50000:
            score += 50

        if request.POST.get('source') == 'website':
            score += 20

        if request.POST.get('service'):
            score += 10

        lead = Lead.objects.create(
        name=request.POST.get('name'),
        phone=request.POST.get('phone'),
        email=request.POST.get('email'),
        service=request.POST.get('service'),
        budget=request.POST.get('budget'),
        source=request.POST.get('source'),
        message=request.POST.get('message'),
        ai_score=score
    )

        if int(lead.budget) >= 50000:
            lead.priority = 'high'

        elif int(lead.budget) >= 20000:
            lead.priority = 'medium'

        else:
            lead.priority = 'low'


        lead.whatsapp_sent = True
        lead.email_sent = True

        lead.save()

        Task.objects.create(
            lead=lead,
            assigned_to="Sales Team",
            task_type="Call Lead",
            due_time=timezone.now(),
            status="pending" 
        )

        success = True

    return render(request, 'crm/home.html', {
        'success': success
    })


# ==============================
# DASHBOARD
# ==============================

@login_required
def dashboard(request):

    search = request.GET.get('search')

    status_filter = request.GET.get('status')

    all_leads = Lead.objects.all().order_by('-id')

    # SEARCH
    if search:

        all_leads = all_leads.filter(

            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(service__icontains=search) |
            Q(source__icontains=search) |
            Q(status__icontains=search)

        )

    # STATUS FILTER
    if status_filter:

        all_leads = all_leads.filter(
            status=status_filter
        )

    # PAGINATION
    paginator = Paginator(all_leads, 5)

    page = request.GET.get('page')

    leads = paginator.get_page(page)

    # ANALYTICS
    total_leads = Lead.objects.count()

    high_priority_count = Lead.objects.filter(
        priority='high'
    ).count()

    whatsapp_sent_count = Lead.objects.filter(
        whatsapp_sent=True
    ).count()

    email_sent_count = Lead.objects.filter(
        email_sent=True
    ).count()

    converted_count = Lead.objects.filter(
        status='converted'
    ).count()

    medium_priority_count = Lead.objects.filter(
        priority='medium'
    ).count()

    low_priority_count = Lead.objects.filter(
    priority='low'
    ).count()

    website_count = Lead.objects.filter(
    source='website'
    ).count()

    google_forms_count = Lead.objects.filter(
    source='google_forms'
    ).count()

    instagram_count = Lead.objects.filter(
    source='instagram_dms'
    ).count()

    manual_count = Lead.objects.filter(
    source='manual'
    ).count()


    return render(request, 'crm/dashboard.html', {

        'leads': leads,
        'total_leads': total_leads,
        'high_priority_count': high_priority_count,
        'medium_priority_count': medium_priority_count,
        'low_priority_count': low_priority_count,
        'whatsapp_sent_count': whatsapp_sent_count,
        'email_sent_count': email_sent_count,
        'converted_count': converted_count,
        'website_count': website_count,
        'google_forms_count': google_forms_count,
        'instagram_count': instagram_count,
        'manual_count': manual_count,

    })


# ===========================
# TASKS
# ===========================

@login_required
def tasks(request):

    tasks = Task.objects.all().order_by('-id')

    pending_tasks = Task.objects.filter(
        status='pending'
    ).count()

    completed_tasks = Task.objects.filter(
        status='completed'
    ).count()

    today_tasks = Task.objects.filter(
        created_at__date=timezone.now().date()
    ).count()

    return render(request, 'crm/tasks.html', {

        'tasks': tasks,

        'pending_tasks': pending_tasks,

        'completed_tasks': completed_tasks,

        'today_tasks': today_tasks,

    })


# ==============================
# EDIT LEAD
# ==============================

@login_required
def edit_lead(request, id):

    lead = get_object_or_404(Lead, id=id)

    if request.method == "POST":

        lead.name = request.POST.get('name')
        lead.phone = request.POST.get('phone')
        lead.email = request.POST.get('email')
        lead.company = request.POST.get('company')
        lead.service = request.POST.get('service')
        lead.budget = request.POST.get('budget')
        lead.source = request.POST.get('source')
        lead.status = request.POST.get('status')
        lead.priority = request.POST.get('priority')
        lead.message = request.POST.get('message')

        lead.save()

        return redirect('dashboard')

    return render(request, 'crm/edit.html', {
        'lead': lead
    })


# ==============================
# DELETE LEAD
# ==============================

@login_required
def delete_lead(request, id):

    lead = get_object_or_404(Lead, id=id)

    lead.delete()

    return redirect('dashboard')


# ==============================
# LEAD DETAIL + NOTES
# ==============================

@login_required
def lead_detail(request, id):

    lead = get_object_or_404(Lead, id=id)

    if request.method == "POST":

        # Update Status
        if 'update_status' in request.POST:

            new_status = request.POST.get('status')

            if new_status:
                lead.status = new_status
                lead.save()

            return redirect('lead_detail', id=lead.id)

        # Add Note
        note_text = request.POST.get('note')

        if note_text:

            LeadNote.objects.create(
                lead=lead,
                note=note_text
            )

            return redirect('lead_detail', id=lead.id)

    notes = lead.notes.all().order_by('-id')

    return render(request, 'crm/lead_detail.html', {
        'lead': lead,
        'notes': notes
    })


# ==============================
# TASKS PAGE
# ==============================

@login_required
def tasks(request):

    tasks = Task.objects.all().order_by('-id')

    return render(request, 'crm/tasks.html', {
        'tasks': tasks
    })

# ==============================
# COMPLETE TASK
# ==============================

@login_required
def complete_task(request, id):

    task = get_object_or_404(Task, id=id)

    task.status = "completed"

    task.save()

    return redirect('tasks')


# ==============================
# DELETE TASK
# ==============================

@login_required
def delete_task(request, id):

    task = get_object_or_404(Task, id=id)

    task.delete()

    return redirect('tasks')


# ==============================
# API CREATE LEAD
# ==============================

class LeadCreateAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        print("========== API HIT ==========")
        print(request.data)

        serializer = LeadSerializer(data=request.data)

        if serializer.is_valid():

            lead = serializer.save()

            # AUTO CREATE TASK
            Task.objects.create(
                lead=lead,
                task_type="Call Lead",
                assigned_to="Sales Team",
                priority="high"
            )

            return Response({

                "message": "Lead Created Successfully",
                "data": serializer.data

            }, status=status.HTTP_201_CREATED)

        return Response({

            "errors": serializer.errors

        }, status=status.HTTP_400_BAD_REQUEST)


# ==============================
# META / FACEBOOK WEBHOOK
# ==============================

@csrf_exempt
def meta_webhook(request):

    if request.method == "POST":

        data = json.loads(request.body)

        print("========== META WEBHOOK ==========")
        print(data)

        try:

            Lead.objects.create(

                name="Facebook Lead",
                phone="0000000000",
                email="facebook@gmail.com",
                company="Meta",
                service="Meta Ads",
                budget="10000",
                source="facebook_ads",
                message=str(data),
                location="Unknown",

            )

            return JsonResponse({
                "status": "success"
            })

        except Exception as e:

            return JsonResponse({
                "error": str(e)
            })

    return JsonResponse({
        "message": "Webhook Working"
    })