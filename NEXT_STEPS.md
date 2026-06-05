# A2Z CRM - Next Steps & Integration Roadmap

## Current Project Status

The A2Z CRM foundation has been successfully built with all core models implemented. The existing views and templates can continue to work with the new database structure through backward compatibility. This document outlines the next steps for completing the integration features.

---

## Part 1: Immediate Next Steps (Integration Phase)

### 1. Create Integration Management Views

**File**: `crm/views/integrations.py` (NEW)

```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from crm.models import ConnectedAccount
import requests
from django.conf import settings
import json
import urllib.parse

# Meta OAuth Flow
@login_required
def connect_meta_account(request):
    """Initiate Meta OAuth flow"""
    config = settings.META_OAUTH_CONFIG
    
    auth_url = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={config['client_id']}&redirect_uri={config['redirect_uri']}&scope={','.join(config['scopes'])}"
    
    return redirect(auth_url)

@login_required
def meta_callback(request):
    """Handle Meta OAuth callback"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        # Handle error
        pass
    
    if code:
        # Exchange code for token
        config = settings.META_OAUTH_CONFIG
        response = requests.get('https://graph.instagram.com/v18.0/oauth/access_token', params={
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'redirect_uri': config['redirect_uri'],
            'code': code
        })
        
        data = response.json()
        
        if 'access_token' in data:
            # Store connected account
            ConnectedAccount.objects.create(
                user=request.user,
                account_type='instagram',
                external_id=data.get('user_id'),
                account_name=data.get('account_name', 'Instagram Account'),
                access_token=data['access_token'],
                status='active'
            )
            
            return redirect('dashboard')
    
    return render(request, 'crm/integration_error.html')


# Connected Accounts List
@login_required
def connected_accounts(request):
    """List user's connected accounts"""
    accounts = request.user.connected_accounts.all()
    return render(request, 'crm/connected_accounts.html', {'accounts': accounts})


# Disconnect Account
@login_required
@require_POST
def disconnect_account(request, account_id):
    """Disconnect a platform account"""
    account = ConnectedAccount.objects.get(id=account_id, user=request.user)
    account.status = 'disconnected'
    account.sync_enabled = False
    account.save()
    
    return redirect('connected_accounts')


# Webhook Receiver
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib

@csrf_exempt
def meta_webhook(request):
    """Receive and process leads from Meta"""
    
    if request.method == 'GET':
        # Webhook verification
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if verify_token == settings.WEBHOOK_VERIFY_TOKEN:
            return HttpResponse(challenge)
        return HttpResponse('Unauthorized', status=403)
    
    elif request.method == 'POST':
        # Verify signature
        signature = request.META.get('HTTP_X_HUB_SIGNATURE', '').replace('sha256=', '')
        expected_signature = hmac.new(
            settings.META_OAUTH_CONFIG['client_secret'].encode(),
            request.body,
            hashlib.sha256
        ).hexdigest()
        
        if signature != expected_signature:
            return JsonResponse({'error': 'Invalid signature'}, status=403)
        
        # Process webhook data
        data = json.loads(request.body)
        
        try:
            for entry in data.get('entry', []):
                for message in entry.get('messaging', []):
                    # Extract lead info
                    sender_id = message['sender']['id']
                    
                    # Create lead
                    from crm.models import Lead, LeadSource, LeadActivity
                    
                    lead = Lead.objects.create(
                        name=message.get('message', {}).get('text', 'Facebook Lead'),
                        phone='',  # Would extract from message
                        email='',  # Would extract from message
                        service='Inquiry via Facebook',
                        source=LeadSource.objects.get(source_type='facebook_ads'),
                        external_id=sender_id,
                        raw_data=message
                    )
                    
                    # Log activity
                    LeadActivity.objects.create(
                        lead=lead,
                        activity_type='synced',
                        description='Lead synced from Meta/Facebook'
                    )
            
            return JsonResponse({'status': 'ok'})
        
        except Exception as e:
            import logging
            logger = logging.getLogger('crm')
            logger.error(f'Webhook processing error: {str(e)}', exc_info=True)
            return JsonResponse({'error': 'Processing failed'}, status=500)
```

### 2. Create Integration Templates

**File**: `crm/templates/crm/connected_accounts.html`

```html
{% extends 'crm/base.html' %}

{% block title %}Connected Accounts - A2Z CRM{% endblock %}

{% block content %}

<div class="container mt-4">
    <h2>Connected Accounts</h2>
    
    <div class="row mb-4">
        <div class="col-md-12">
            <a href="{% url 'connect_meta_account' %}" class="btn btn-primary">
                Connect Facebook/Instagram
            </a>
            <a href="{% url 'connect_google_account' %}" class="btn btn-primary">
                Connect Google Account
            </a>
        </div>
    </div>
    
    <div class="accounts-list">
        {% for account in accounts %}
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">
                        {{ account.get_account_type_display }}: {{ account.account_name }}
                    </h5>
                    <p class="card-text">
                        Email: {{ account.account_email|default:"N/A" }}<br>
                        Status: 
                        <span class="badge {% if account.status == 'active' %}badge-success{% else %}badge-danger{% endif %}">
                            {{ account.get_status_display }}
                        </span><br>
                        Last Synced: {{ account.last_synced|default:"Never" }}<br>
                        Sync Enabled: <input type="checkbox" {% if account.sync_enabled %}checked{% endif %} disabled>
                    </p>
                    <form method="POST" action="{% url 'disconnect_account' account.id %}" style="display: inline;">
                        {% csrf_token %}
                        <button type="submit" class="btn btn-sm btn-danger">Disconnect</button>
                    </form>
                </div>
            </div>
        {% empty %}
            <p>No connected accounts yet. Connect a platform to start syncing leads!</p>
        {% endfor %}
    </div>
</div>

{% endblock %}
```

### 3. Update URLs

**File**: `crm/urls.py` (ADD TO EXISTING)

```python
from django.urls import path
from . import views

urlpatterns = [
    # ... existing URLs ...
    
    # Integration URLs
    path('integrations/meta/connect/', views.connect_meta_account, name='connect_meta_account'),
    path('integrations/meta/callback/', views.meta_callback, name='meta_callback'),
    path('integrations/connected-accounts/', views.connected_accounts, name='connected_accounts'),
    path('integrations/disconnect/<int:account_id>/', views.disconnect_account, name='disconnect_account'),
    path('webhook/meta/', views.meta_webhook, name='meta_webhook'),
]
```

---

## Part 2: Views to Update

### 1. Update `dashboard` View

```python
# In views.py - Add this to the dashboard function

# NEW: Add connected accounts to context
connected_accounts = request.user.connected_accounts.filter(status='active')

# NEW: Add lead sources to context
from crm.models import LeadSource
lead_sources = LeadSource.objects.filter(is_active=True)

# NEW: Get recent activities
from crm.models import LeadActivity
recent_activities = LeadActivity.objects.filter(
    lead__assigned_to=request.user
).order_by('-created_at')[:10]

return render(request, 'crm/dashboard.html', {
    'leads': leads,
    'total_leads': total_leads,
    # ... existing context ...
    'connected_accounts': connected_accounts,
    'lead_sources': lead_sources,
    'recent_activities': recent_activities,
})
```

### 2. Update `lead_detail` View

```python
# Add support for viewing lead source and connected account

@login_required
def lead_detail(request, id):
    lead = get_object_or_404(Lead, id=id)
    
    # Check permissions
    if lead.assigned_to != request.user and request.user.profile.role != 'admin':
        return redirect('dashboard')
    
    # ... existing code ...
    
    # NEW: Get integration source info
    source_name = lead.get_source_display_name()
    
    return render(request, 'crm/lead_detail.html', {
        'lead': lead,
        'notes': notes,
        'source_name': source_name,
        'connected_account': lead.connected_account,
    })
```

### 3. Create Duplicate Detection View

```python
@login_required
def find_duplicate_leads(request, lead_id):
    """Find potential duplicate leads"""
    from django.db.models import Q
    
    lead = get_object_or_404(Lead, id=lead_id)
    
    # Find similar leads
    duplicates = Lead.objects.filter(
        Q(phone=lead.phone) |
        Q(email=lead.email) |
        Q(name__icontains=lead.name.split()[0])  # Match first name
    ).exclude(id=lead_id)[:10]
    
    return render(request, 'crm/find_duplicates.html', {
        'lead': lead,
        'duplicates': duplicates,
    })

@login_required
@require_POST
def mark_duplicate(request, lead_id, master_id):
    """Mark a lead as duplicate of another"""
    lead = get_object_or_404(Lead, id=lead_id)
    master = get_object_or_404(Lead, id=master_id)
    
    lead.mark_as_duplicate_of(master)
    
    # Log activity
    LeadActivity.objects.create(
        lead=lead,
        activity_type='merged',
        performed_by=request.user,
        description=f'Marked as duplicate of {master.name}'
    )
    
    return redirect('lead_detail', id=master_id)
```

---

## Part 3: API Endpoints to Create

### 1. Connected Accounts API

```python
# In views.py or create views/api.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import ConnectedAccountSerializer

class ConnectedAccountViewSet(viewsets.ModelViewSet):
    serializer_class = ConnectedAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.request.user.connected_accounts.all()
    
    @action(detail=True, methods=['post'])
    def sync_leads(self, request, pk=None):
        """Manually trigger lead sync"""
        account = self.get_object()
        # Implementation depends on platform
        return Response({'status': 'Sync initiated'})
    
    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """Disconnect account"""
        account = self.get_object()
        account.status = 'disconnected'
        account.sync_enabled = False
        account.save()
        return Response({'status': 'Disconnected'})
```

### 2. Lead Activity API

```python
from .serializers import LeadActivitySerializer

class LeadActivityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeadActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        lead_id = self.request.query_params.get('lead_id')
        if lead_id:
            return LeadActivity.objects.filter(lead_id=lead_id)
        return LeadActivity.objects.all()
```

---

## Part 4: Testing the Integration

### 1. Test Meta Webhook

```bash
# Test webhook verification
curl -X GET "http://localhost:8000/webhook/meta/?hub.mode=subscribe&hub.verify_token=a2zcrm123&hub.challenge=test123"

# Test webhook data
curl -X POST "http://localhost:8000/webhook/meta/" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature: sha256=..." \
  -d '{
    "entry": [{
      "messaging": [{
        "sender": {"id": "123456"},
        "message": {"text": "I need a website"}
      }]
    }]
  }'
```

### 2. Test Connected Accounts Endpoint

```bash
# List connected accounts
curl -X GET "http://localhost:8000/api/connected-accounts/" \
  -H "Authorization: Bearer <token>"

# Disconnect account
curl -X POST "http://localhost:8000/api/connected-accounts/1/disconnect/" \
  -H "Authorization: Bearer <token>"
```

---

## Part 5: Implementation Timeline

### Phase 1: OAuth Flow (1-2 weeks)
- [ ] Implement Meta OAuth
- [ ] Implement Google OAuth
- [ ] Test token refresh logic
- [ ] Create connected accounts UI

### Phase 2: Webhook Processing (1 week)
- [ ] Implement Meta webhook handler
- [ ] Implement Google Forms webhook
- [ ] Test lead creation from webhooks
- [ ] Implement duplicate detection

### Phase 3: Sync Mechanism (1-2 weeks)
- [ ] Create sync scheduler (Celery)
- [ ] Implement Meta API lead fetching
- [ ] Implement Google Forms API sync
- [ ] Add sync status tracking

### Phase 4: Dashboard Enhancement (1 week)
- [ ] Update dashboard with sources
- [ ] Add integration status
- [ ] Add sync statistics
- [ ] Add quick-connect buttons

### Phase 5: Testing & Polish (1 week)
- [ ] Unit tests for models
- [ ] Integration tests for webhooks
- [ ] API endpoint tests
- [ ] Performance optimization

**Total Timeline**: 5-7 weeks to full integration

---

## Part 6: Environment Setup for Integration

Add to `.env`:

```env
# Meta/Facebook
META_CLIENT_ID=your-app-id
META_CLIENT_SECRET=your-app-secret
META_REDIRECT_URI=http://localhost:8000/integrations/meta/callback/
META_APP_ACCESS_TOKEN=your-app-token

# Google
GOOGLE_CLIENT_ID=your-google-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/integrations/google/callback/

# Webhook
WEBHOOK_VERIFY_TOKEN=secure-random-token

# Celery (for background tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## Part 7: Key Classes to Review

Before implementing, review these in the codebase:

1. **ConnectedAccount** (`models.py`)
   - OAuth token storage
   - Status management
   - Sync tracking

2. **LeadActivity** (`models.py`)
   - Audit logging
   - Change tracking

3. **LeadSource** (`models.py`)
   - Source management
   - Classification

4. **Lead** (updated in `models.py`)
   - Integration fields
   - Duplicate handling
   - Company information

---

## Recommended Reading Order

1. **PROJECT_SUMMARY.md** - Overview
2. **IMPLEMENTATION_GUIDE.md** - Architecture details
3. **README.md** - Features and usage
4. **SETUP_GUIDE.md** - Installation
5. **This document** - Integration roadmap

---

## Checkpoints Before Each Phase

- [ ] All code reviewed and approved
- [ ] Models verified in database
- [ ] API endpoints tested with Postman
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Tests written and passing

---

## Success Metrics

- ✅ Leads created from Meta within 5 minutes
- ✅ Leads created from Google Forms within 10 minutes
- ✅ No duplicate leads (>95% accuracy)
- ✅ Dashboard shows all sources
- ✅ Team can manage integrations from UI
- ✅ Audit trail complete for all changes
- ✅ Zero downtime during integration sync
- ✅ <100ms API response time

---

## Support & Documentation

All code changes should include:
- Docstrings explaining functionality
- Comments for complex logic
- Type hints for parameters
- Error handling with logging
- Unit tests with >80% coverage
- Integration tests for workflows

---

**Status**: Ready for Integration Development
**Next Review**: After OAuth implementation
**Points of Contact**: Development team
