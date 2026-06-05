from django import forms
from .models import Lead, LeadNote, Task


class LeadForm(forms.ModelForm):
    """Form for creating and editing leads"""

    class Meta:
        model = Lead

        fields = [
            'name',
            'phone',
            'email',
            'company',
            'company_size',
            'industry',
            'service',
            'budget',
            'message',
            'source',
            'source_legacy',
            'status',
            'priority',
            'assigned_to',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Full Name',
                'required': True
            }),

            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Phone Number',
                'required': True
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Email Address'
            }),

            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Company Name'
            }),

            'company_size': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('', '-- Select Company Size --'),
                ('startup', 'Startup (1-10)'),
                ('small', 'Small (11-50)'),
                ('medium', 'Medium (51-200)'),
                ('large', 'Large (201-1000)'),
                ('enterprise', 'Enterprise (1000+)'),
            ]),

            'industry': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Industry'
            }),

            'service': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What service are they interested in?',
                'required': True
            }),

            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Budget (in USD)',
                'type': 'number',
                'min': '0'
            }),

            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Additional Message/Notes',
                'rows': 4
            }),

            'source': forms.Select(attrs={
                'class': 'form-control'
            }),

            'source_legacy': forms.Select(attrs={
                'class': 'form-control'
            }),

            'status': forms.Select(attrs={
                'class': 'form-control'
            }),

            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),

            'assigned_to': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

        labels = {
            'name': 'Full Name *',
            'phone': 'Phone Number *',
            'email': 'Email Address',
            'company': 'Company',
            'company_size': 'Company Size',
            'industry': 'Industry',
            'service': 'Service Interest *',
            'budget': 'Budget',
            'message': 'Additional Notes',
            'source': 'Lead Source',
            'source_legacy': 'Source (Legacy)',
            'status': 'Status',
            'priority': 'Priority',
            'assigned_to': 'Assigned To',
        }


class LeadNoteForm(forms.ModelForm):
    """Form for adding notes to leads"""

    class Meta:
        model = LeadNote
        fields = ['note']

        widgets = {
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Add a note...',
                'rows': 3,
                'required': True
            })
        }

        labels = {
            'note': 'Add Note'
        }


class TaskForm(forms.ModelForm):
    """Form for creating and editing tasks"""

    class Meta:
        model = Task
        fields = [
            'task_type',
            'title',
            'description',
            'due_date',
            'due_time',
            'priority',
            'assigned_to',
            'status',
        ]

        widgets = {
            'task_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),

            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Task Title',
                'required': True
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Task Description',
                'rows': 3
            }),

            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),

            'due_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),

            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),

            'assigned_to': forms.Select(attrs={
                'class': 'form-control'
            }),

            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

        labels = {
            'task_type': 'Task Type *',
            'title': 'Title *',
            'description': 'Description',
            'due_date': 'Due Date *',
            'due_time': 'Due Time',
            'priority': 'Priority',
            'assigned_to': 'Assign To',
            'status': 'Status',
        }


class LeadFilterForm(forms.Form):
    """Form for filtering leads in dashboard"""

    STATUS_CHOICES = [('', '-- All Statuses --')] + list(Lead.STATUS_CHOICES)
    PRIORITY_CHOICES = [('', '-- All Priorities --')] + list(Lead.PRIORITY_CHOICES)

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, phone, email, service...'
        })
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    source = forms.CharField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
