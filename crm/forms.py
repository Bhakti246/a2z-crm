from django import forms

from .models import Lead


class LeadForm(forms.ModelForm):

    class Meta:

        model = Lead

        fields = [

            'name',
            'phone',
            'email',
            'service',
            'budget',
            'message',
            'source',

        ]

        widgets = {

            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Name'
            }),

            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Phone Number'
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Email'
            }),

            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Company Name'
            }),

            'service': forms.Select(attrs={
                'class': 'form-control'
            }),

            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Budget'
            }),

            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Message',
                'rows': 5
            }),

            'source': forms.Select(attrs={
                'class': 'form-control'
            }),

        }