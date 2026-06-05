# IMPLEMENTATION GUIDE: A2Z CRM Architecture & Features

## Executive Summary

This document explains the complete architecture of the A2Z CRM system, including:
- Data model structure and relationships
- Integration patterns for multiple lead sources
- User roles and permissions
- API design and endpoints
- Best practices for extending the system

## Data Model Architecture

### Core Model Relationships

```
UserProfile (1) ──┐
                  │
                  ├─── ConnectedAccount (many) ──┐
                  │                               │
                  │                               ├─── Lead (many)
User (1) ─────────┤                               │
                  │                               │
                  ├─── Task (many) ──────────────┤
                  │
                  └─── LeadNote (many)
                  └─── LeadActivity (many)

Lead (1) ────────┐
                 ├─── LeadNote (many)
                 ├─── Task (many)
                 ├─── LeadActivity (many)
                 └─── LeadSource (many)

IntegrationConfig (1) ──── Configured Integrations
```

### Model Descriptions

#### UserProfile
**Purpose**: Extend Django's User model with role-based access control

**Fields**:
- `user` (OneToOneField): Link to Django User
- `role` (CharField): admin, manager, user, client
- `department` (CharField): Organization department
- `phone` (CharField): Contact phone
- `is_active` (BooleanField): Account status

**Usage**:
```python
# Get user profile
profile = request.user.profile

# Check role
if profile.role == 'admin':
    # Admin-only operations
    pass

# Update department
profile.department = 'Sales'
profile.save()
```

#### LeadSource
**Purpose**: Define and manage available lead sources

**Fields**:
- `name` (CharField): Display name
- `source_type` (CharField): Identifier (facebook, instagram, etc.)
- `description` (TextField): Detailed description
- `is_active` (BooleanField): Whether source is active
- `icon` (CharField): Icon emoji for UI

**Predefined Sources**:
- facebook: Facebook Lead Ads
- instagram: Instagram Lead Ads
- instagram_dms: Instagram Direct Messages
- google_forms: Google Forms responses
- google_maps: Google Maps inquiries
- website_form: Website contact forms
- manual: Manual entry

**Usage**:
```python
from crm.models import LeadSource

# Get all active sources
sources = LeadSource.objects.filter(is_active=True)

# Find specific source
facebook_ads = LeadSource.objects.get(source_type='facebook')

# Get leads from specific source
facebook_leads = facebook_ads.leads.all()
```

#### ConnectedAccount
**Purpose**: Store OAuth tokens and manage integrated platform accounts

**Fields**:
- `user` (ForeignKey): Owner of the account
- `account_type` (CharField): Platform (facebook, instagram, google, etc.)
- `external_id` (CharField): Platform-specific ID
- `account_name` (CharField): Account display name
- `account_email` (EmailField): Associated email
- `access_token` (TextField): OAuth access token (encrypted in prod)
- `refresh_token` (TextField): OAuth refresh token
- `token_expires_at` (DateTimeField): Token expiration
- `status` (CharField): active, expired, revoked, disconnected, pending
- `account_metadata` (JSONField): Platform-specific data
- `permissions` (JSONField): Granted permissions list
- `is_primary` (BooleanField): Primary account flag
- `last_synced` (DateTimeField): Last sync timestamp
- `sync_enabled` (BooleanField): Enable/disable sync

**Usage**:
```python
from crm.models import ConnectedAccount

# Get user's connected accounts
accounts = request.user.connected_accounts.filter(status='active')

# Check if token is expired
if account.is_token_expired():
    # Refresh token or mark as expired
    account.status = 'expired'
    account.save()

# Get leads from connected account
leads = account.leads.all()

# Create connected account (typically during OAuth callback)
ConnectedAccount.objects.create(
    user=user,
    account_type='facebook',
    external_id='123456789',
    account_name='Business Page',
    access_token='token_xyz...',
    token_expires_at=datetime.now() + timedelta(days=60),
    status='active'
)
```

#### Lead
**Purpose**: Core lead/prospect model with integration tracking

**Fields - Contact**:
- `name` (CharField): Lead name
- `phone` (CharField): Phone number (indexed for quick lookup)
- `email` (EmailField): Email address
- `company` (CharField): Company name
- `company_size` (CharField): Company size category
- `industry` (CharField): Industry/vertical

**Fields - Lead Details**:
- `service` (CharField): Service/product interested in
- `budget` (IntegerField): Budget amount
- `message` (TextField): Additional message/inquiry

**Fields - Source & Integration**:
- `source` (ForeignKey): LeadSource reference (recommended)
- `source_legacy` (CharField): Legacy source field (for backward compatibility)
- `connected_account` (ForeignKey): ConnectedAccount this lead came from
- `external_id` (CharField): Original ID from external platform
- `raw_data` (JSONField): Raw data from platform

**Fields - CRM**:
- `status` (CharField): new, contacted, interested, converted, lost, archived
- `priority` (CharField): high, medium, low
- `score` (IntegerField): Qualification score 0-100
- `ai_remark` (CharField): AI-generated remarks
- `assigned_to` (ForeignKey): Assigned to User

**Fields - Communication**:
- `whatsapp_sent` (BooleanField): WhatsApp message sent
- `email_sent` (BooleanField): Email sent
- `last_contacted_at` (DateTimeField): Last contact time

**Fields - Duplicate Management**:
- `is_duplicate` (BooleanField): Marked as duplicate
- `duplicate_of` (ForeignKey): Link to master lead

**Usage**:
```python
from crm.models import Lead, LeadSource

# Create lead from form
lead = Lead.objects.create(
    name='John Doe',
    phone='+1234567890',
    email='john@example.com',
    service='Web Development',
    budget=50000,
    source=LeadSource.objects.get(source_type='website_form'),
    status='new',
    priority='high'
)

# Search leads
leads = Lead.objects.filter(
    Q(name__icontains='john') | Q(email__icontains='john')
)

# Filter by status
converted_leads = Lead.objects.filter(status='converted')

# Get leads by source
facebook_leads = Lead.objects.filter(source__source_type='facebook')

# Mark as duplicate
duplicate_lead = Lead.objects.get(id=2)
original_lead = Lead.objects.get(id=1)
duplicate_lead.mark_as_duplicate_of(original_lead)

# Update status
lead.status = 'interested'
lead.save()
```

#### LeadNote
**Purpose**: Store notes and comments on leads

**Fields**:
- `lead` (ForeignKey): Associated lead
- `created_by` (ForeignKey): User who created note
- `note` (TextField): Note content
- `created_at` (DateTimeField): Creation timestamp

**Usage**:
```python
from crm.models import LeadNote

# Add note
LeadNote.objects.create(
    lead=lead,
    created_by=request.user,
    note='Called customer, interested but budget limited'
)

# Get all notes for lead
notes = lead.notes.all().order_by('-created_at')

# Get notes by user
user_notes = LeadNote.objects.filter(created_by=request.user)
```

#### LeadActivity
**Purpose**: Audit log for all lead modifications

**Fields**:
- `lead` (ForeignKey): Associated lead
- `activity_type` (CharField): Type of activity
- `performed_by` (ForeignKey): User who performed action
- `description` (TextField): Detailed description
- `changes` (JSONField): Field changes {field: {old: value, new: value}}
- `created_at` (DateTimeField): Activity timestamp

**Activity Types**:
- created: Lead created
- updated: Lead updated
- status_changed: Status changed
- assigned: Lead assigned
- contacted: Lead contacted
- note_added: Note added
- synced: Synced from integration
- merged: Lead merged
- archived: Lead archived

**Usage**:
```python
from crm.models import LeadActivity

# Log activity (usually done automatically via signals)
LeadActivity.objects.create(
    lead=lead,
    activity_type='status_changed',
    performed_by=request.user,
    description='Status changed from new to interested',
    changes={'status': {'old': 'new', 'new': 'interested'}}
)

# Get lead history
history = lead.activities.all().order_by('-created_at')

# Get activities by type
status_changes = LeadActivity.objects.filter(activity_type='status_changed')
```

#### Task
**Purpose**: Manage tasks and follow-ups associated with leads

**Fields**:
- `lead` (ForeignKey): Associated lead
- `assigned_to` (ForeignKey): Assigned to User
- `created_by` (ForeignKey): Task creator
- `task_type` (CharField): call, email, meeting, followup, proposal, other
- `title` (CharField): Task title
- `description` (TextField): Task description
- `due_date` (DateField): Due date
- `due_time` (TimeField): Due time
- `status` (CharField): pending, in_progress, completed, cancelled
- `priority` (CharField): high, medium, low
- `completed_at` (DateTimeField): Completion time
- `notes` (TextField): Task notes

**Usage**:
```python
from crm.models import Task
from django.utils import timezone

# Create task
task = Task.objects.create(
    lead=lead,
    assigned_to=sales_person,
    created_by=request.user,
    task_type='call',
    title='Follow up call',
    due_date='2025-01-15',
    priority='high'
)

# Get overdue tasks
overdue_tasks = [t for t in Task.objects.filter(status='pending') if t.is_overdue()]

# Complete task
task.status = 'completed'
task.completed_at = timezone.now()
task.save()
```

#### IntegrationConfig
**Purpose**: Store global configuration for integrations

**Fields**:
- `integration_type` (CharField): Integration name (facebook, google, etc.)
- `config_type` (CharField): oauth, api_key, webhook, custom
- `config_data` (JSONField): Configuration data (API keys, secrets)
- `is_active` (BooleanField): Whether config is active
- `created_by` (ForeignKey): Who created the config
- `created_at`, `updated_at` (DateTimeField): Timestamps

**Usage**:
```python
from crm.models import IntegrationConfig

# Store API key
IntegrationConfig.objects.create(
    integration_type='facebook',
    config_type='api_key',
    config_data={'api_key': 'xxx...', 'api_version': 'v18.0'},
    created_by=admin_user
)

# Get configuration
config = IntegrationConfig.objects.get(integration_type='facebook')
```

## Integration Architecture

### Adding a New Lead Source

#### Step 1: Create LeadSource
```python
from crm.models import LeadSource

LeadSource.objects.create(
    name='LinkedIn Leads',
    source_type='linkedin',
    description='Leads from LinkedIn Lead Forms',
    is_active=True,
    icon='💼'
)
```

#### Step 2: Create ConnectedAccount (if requires authentication)
```python
from crm.models import ConnectedAccount

account = ConnectedAccount.objects.create(
    user=user,
    account_type='linkedin',
    external_id='user_123',
    account_name='Company Account',
    access_token='token_xyz...',
    status='active',
    sync_enabled=True
)
```

#### Step 3: Create Webhook Handler
```python
# In views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def linkedin_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Create lead
        lead = Lead.objects.create(
            name=data['firstName'] + ' ' + data['lastName'],
            email=data['email'],
            phone=data.get('phone', ''),
            service=data.get('jobTitle', ''),
            source=LeadSource.objects.get(source_type='linkedin'),
            raw_data=data
        )
        
        # Log activity
        LeadActivity.objects.create(
            lead=lead,
            activity_type='synced',
            description='Lead synced from LinkedIn'
        )
        
        return JsonResponse({'status': 'success'})
```

#### Step 4: Add to URL routing
```python
# In urls.py
urlpatterns = [
    path('webhook/linkedin/', linkedin_webhook, name='linkedin_webhook'),
]
```

### Webhook Verification Pattern

```python
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib

@csrf_exempt
def platform_webhook_verification(request):
    if request.method == 'GET':
        # Webhook verification challenge
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        from django.conf import settings
        if verify_token == settings.WEBHOOK_VERIFY_TOKEN:
            return HttpResponse(challenge)
        return HttpResponse('Unauthorized', status=403)
    
    elif request.method == 'POST':
        # Process webhook
        signature = request.META.get('HTTP_X_HUB_SIGNATURE', '')
        
        # Validate signature
        from django.conf import settings
        expected_signature = 'sha1=' + hmac.new(
            settings.WEBHOOK_VERIFY_TOKEN.encode(),
            request.body,
            hashlib.sha1
        ).hexdigest()
        
        if signature != expected_signature:
            return JsonResponse({'error': 'Invalid signature'}, status=403)
        
        # Process event
        return JsonResponse({'status': 'success'})
```

## API Design Patterns

### REST API Endpoints Structure

```python
# In urls.py
from rest_framework.routers import DefaultRouter
from .views import LeadViewSet, TaskViewSet, ConnectedAccountViewSet

router = DefaultRouter()
router.register(r'leads', LeadViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'connected-accounts', ConnectedAccountViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
```

### Custom Serialization

```python
from rest_framework import serializers
from .models import Lead

class LeadDetailSerializer(serializers.ModelSerializer):
    """Extended serializer with related data"""
    
    source_display = serializers.CharField(source='get_source_display_name')
    notes_count = serializers.SerializerMethodField()
    tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = '__all__'
    
    def get_notes_count(self, obj):
        return obj.notes.count()
    
    def get_tasks_count(self, obj):
        return obj.tasks.filter(status='pending').count()
```

## User Roles & Permissions

### Role Hierarchy
```
Admin
├─ Full system access
├─ Create/edit users
├─ Configure integrations
└─ View all data

Manager
├─ Manage own team
├─ Assign leads
├─ View team analytics
└─ Cannot configure system

User
├─ View assigned leads
├─ Update lead status
├─ Create tasks
└─ Cannot view others' data

Client
├─ View dashboard
├─ See own leads
└─ Limited functionality
```

### Permission Checks
```python
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'admin'

@user_passes_test(is_admin)
def admin_only_view(request):
    # Admin-only operations
    pass
```

## Best Practices

### 1. Atomic Operations
```python
from django.db import transaction

@transaction.atomic
def create_lead_from_webhook(data):
    lead = Lead.objects.create(...)
    LeadActivity.objects.create(...)  # Both succeed or both fail
```

### 2. Bulk Operations
```python
# Good - single query
leads = Lead.objects.select_related('source', 'assigned_to').filter(status='new')

# Avoid - N+1 queries
for lead in leads:
    print(lead.source.name)  # Extra query per iteration
```

### 3. Logging
```python
import logging
logger = logging.getLogger('crm')

logger.info(f'Lead created: {lead.id} from source: {lead.source}')
logger.error(f'Webhook processing failed: {str(error)}', exc_info=True)
```

### 4. Error Handling
```python
from django.http import JsonResponse

def webhook_handler(request):
    try:
        data = json.loads(request.body)
        lead = create_lead_from_data(data)
        return JsonResponse({'status': 'success', 'lead_id': lead.id})
    except ValidationError as e:
        logger.error(f'Validation error: {e}')
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f'Unexpected error: {e}', exc_info=True)
        return JsonResponse({'error': 'Internal error'}, status=500)
```

## Extending the System

### Adding Custom Fields to Lead
```python
# models.py
class Lead(models.Model):
    # ... existing fields ...
    custom_field = models.CharField(max_length=255, blank=True)
    
# Create migration
# python manage.py makemigrations
# python manage.py migrate

# Update serializer
class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [..., 'custom_field']
```

### Creating Custom Managers
```python
class LeadManager(models.Manager):
    def hot_leads(self):
        return self.filter(priority='high', status='new')
    
    def converted_this_month(self):
        from django.utils import timezone
        from datetime import timedelta
        month_ago = timezone.now() - timedelta(days=30)
        return self.filter(status='converted', updated_at__gte=month_ago)

class Lead(models.Model):
    # ...
    objects = LeadManager()

# Usage
hot_leads = Lead.objects.hot_leads()
```

## Testing

### Model Tests
```python
from django.test import TestCase
from .models import Lead, LeadSource

class LeadModelTests(TestCase):
    def setUp(self):
        self.source = LeadSource.objects.create(
            name='Test Source',
            source_type='test'
        )
    
    def test_lead_creation(self):
        lead = Lead.objects.create(
            name='Test Lead',
            phone='+1234567890',
            source=self.source
        )
        self.assertEqual(lead.name, 'Test Lead')
        self.assertEqual(lead.status, 'new')
```

### API Tests
```python
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

class LeadAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='123')
        self.client.login(username='testuser', password='123')
    
    def test_list_leads(self):
        response = self.client.get('/api/leads/')
        self.assertEqual(response.status_code, 200)
```

## Monitoring & Analytics

### Key Metrics
- Lead source distribution
- Conversion rate by source
- Average lead score
- Lead status distribution
- Response time metrics
- Sync success rate

### Queries for Analytics
```python
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

# Leads by source
leads_by_source = Lead.objects.values('source__name').annotate(count=Count('id'))

# Conversion rate
total_leads = Lead.objects.count()
converted = Lead.objects.filter(status='converted').count()
conversion_rate = (converted / total_leads * 100) if total_leads else 0

# New leads this month
month_ago = timezone.now() - timedelta(days=30)
new_leads = Lead.objects.filter(created_at__gte=month_ago).count()

# Average lead score
avg_score = Lead.objects.aggregate(avg=models.Avg('score'))['avg']
```

---

This comprehensive guide covers the entire architecture. Refer back to specific sections as needed when implementing features or extending the system.
