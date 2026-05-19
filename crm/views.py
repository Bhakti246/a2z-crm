from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import LeadForm
from .models import Lead
from .serializers import LeadSerializer


def home(request):

    success = False

    if request.method == 'POST':

        form = LeadForm(request.POST)

        if form.is_valid():

            form.save()

            success = True

    form = LeadForm()

    leads = Lead.objects.all()

    return render(request, 'crm/home.html', {
        'success': success,
        'leads': leads,
        'form': form
    })


def delete_lead(request, id):

    lead = Lead.objects.get(id=id)

    lead.delete()

    return redirect('/')


def edit_lead(request, id):

    lead = Lead.objects.get(id=id)

    if request.method == 'POST':

        lead.name = request.POST['name']
        lead.phone = request.POST['phone']
        lead.service = request.POST['service']
        lead.budget = request.POST['budget']
        lead.message = request.POST['message']

        lead.save()

        return redirect('/')

        return render(request, 'crm/edit.html', {
        'lead': lead
    })


class LeadCreateAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        serializer = LeadSerializer(data=request.data)

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    'success': True,
                    'lead_id': serializer.data['id']
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                'success': False,
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST,
        )