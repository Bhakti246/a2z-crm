# A2Z CRM - Multi-Source Lead Management System

A scalable Django-based CRM system for collecting, managing, and organizing leads from multiple platforms including Facebook, Instagram, Google Forms, Google Maps, and more.

## Project Overview

**A2Z CRM** is designed to:
- Connect and manage leads from multiple lead sources (Meta, Google, etc.)
- Provide a unified dashboard for lead management
- Track lead status, priority, and qualification scores
- Support role-based access control
- Offer extensible architecture for adding new lead sources
- Maintain proper audit trails and activity logs

## Table of Contents

1. [Project Structure](#project-structure)
2. [Setup & Installation](#setup--installation)
3. [Environment Configuration](#environment-configuration)
4. [Database Models](#database-models)
5. [API Endpoints](#api-endpoints)
6. [Integration Architecture](#integration-architecture)
7. [Dashboard Features](#dashboard-features)
8. [Development](#development)
9. [Deployment](#deployment)

## Project Structure

```
a2z-crm/
├── crm/                           # Main CRM application
│   ├── migrations/                # Database migrations
│   ├── templates/
│   │   ├── crm/
│   │   │   ├── base.html          # Base template with navigation
│   │   │   ├── dashboard.html     # Main lead dashboard
│   │   │   ├── lead_detail.html   # Lead detail view
│   │   │   ├── edit.html          # Edit lead form
│   │   │   ├── home.html          # Home/lead creation
│   │   │   └── tasks.html         # Tasks management
│   │   └── registration/
│   │       └── login.html         # Login template
│   ├── static/
│   │   ├── css/
│   │   │   ├── dashboard.css
│   │   │   └── style.css
│   │   └── js/
│   │       ├── app.js
│   │       └── dashboard.js
│   ├── models.py                  # Data models
│   ├── views.py                   # View functions
│   ├── serializers.py             # REST API serializers
│   ├── forms.py                   # Django forms
│   ├── urls.py                    # URL routing
│   ├── admin.py                   # Admin panel configuration
│   └── apps.py                    # App configuration
├── myproject/                     # Django project settings
│   ├── settings.py                # Settings configuration
│   ├── urls.py                    # Project-level URL routing
│   ├── asgi.py
│   └── wsgi.py
├── manage.py                      # Django management script
├── requirements.txt               # Python dependencies
├── db.sqlite3                     # SQLite database (development)
└── README.md                      # This file
```

## Setup & Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Virtual environment tool (venv recommended)

### Installation Steps

1. **Clone the repository**
   ```bash
   cd /path/to/a2z-crm
   ```

2. **Create and activate virtual environment**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser account**
   ```bash
   python manage.py createsuperuser
   # Follow the prompts to create an admin account
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Admin: http://localhost:8000/admin/
   - Dashboard: http://localhost:8000/dashboard/
   - Home: http://localhost:8000/

## Environment Configuration

Create a `.env` file in the project root for environment variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOST=localhost

# Database (optional - defaults to SQLite)
DATABASE_URL=

# Meta/Facebook Integration
META_CLIENT_ID=your-meta-app-id
META_CLIENT_SECRET=your-meta-app-secret
META_REDIRECT_URI=http://localhost:8000/integrations/meta/callback/

# Google Integration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/integrations/google/callback/

# Webhook Configuration
WEBHOOK_VERIFY_TOKEN=your-secure-webhook-token

# Security (Production)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
DJANGO_LOG_LEVEL=INFO
```

## Database Models

### Core Models

#### UserProfile
Extends Django User model with role-based access control.
- **Fields**: user, role, department, phone, is_active
- **Roles**: admin, manager, user, client

#### LeadSource
Defines available lead sources in the system.
- **Fields**: name, source_type, description, is_active, icon
- **Types**: facebook, instagram, google_forms, google_maps, website_form, manual, etc.

#### Lead
Main model representing a lead/prospect.
- **Fields**:
  - Contact: name, phone, email, company, industry
  - Details: service, budget, message, status, priority
  - Scoring: score (0-100), ai_remark
  - Integration: connected_account, external_id, raw_data
  - Tracking: assigned_to, whatsapp_sent, email_sent, last_contacted_at
  - Duplicate: is_duplicate, duplicate_of
- **Status**: new, contacted, interested, converted, lost, archived, etc.
- **Indexes**: Optimized for search by name, phone, email, and status

#### LeadNote
Comments and notes on leads.
- **Fields**: lead, created_by, note, created_at

#### LeadActivity
Audit log for all lead modifications.
- **Fields**: lead, activity_type, performed_by, description, changes, created_at
- **Types**: created, updated, status_changed, assigned, contacted, synced, etc.

#### Task
Tasks and follow-ups associated with leads.
- **Fields**: 
  - lead, assigned_to, created_by
  - task_type, title, description
  - due_date, due_time, status, priority
  - completed_at
- **Status**: pending, in_progress, completed, cancelled

#### ConnectedAccount
Manages connected social/platform accounts for users.
- **Fields**:
  - user, account_type (facebook, instagram, google, etc.)
  - external_id, account_name, account_email
  - access_token, refresh_token, token_expires_at
  - status (active, expired, revoked, disconnected, pending)
  - permissions, account_metadata
  - sync_enabled, last_synced
- **Purpose**: Stores OAuth tokens and platform-specific data

#### IntegrationConfig
Global configuration for external integrations.
- **Fields**: integration_type, config_type, config_data, is_active, created_by
- **Usage**: Stores API keys, secrets, and global settings

## API Endpoints

### Lead Endpoints
```
GET    /api/leads/              # List all leads (paginated)
POST   /api/leads/              # Create new lead
GET    /api/leads/<id>/         # Get lead details
PUT    /api/leads/<id>/         # Update lead
DELETE /api/leads/<id>/         # Delete lead
```

### Connected Account Endpoints
```
GET    /api/connected-accounts/     # List user's connected accounts
POST   /api/connected-accounts/     # Add new connected account
GET    /api/connected-accounts/<id>/ # Get account details
PUT    /api/connected-accounts/<id>/ # Update account
DELETE /api/connected-accounts/<id>/ # Disconnect account
```

### Task Endpoints
```
GET    /api/tasks/              # List tasks
POST   /api/tasks/              # Create task
PUT    /api/tasks/<id>/         # Update task
DELETE /api/tasks/<id>/         # Delete task
```

### Webhook Endpoints
```
POST   /webhook/                # Meta/Facebook webhook receiver
GET    /webhook/                # Webhook verification
```

## Integration Architecture

### Supported Lead Sources

1. **Facebook/Meta**
   - Facebook Lead Ads
   - WhatsApp Inquiries
   - Direct API integration

2. **Instagram**
   - Instagram Lead Ads
   - Instagram Direct Messages

3. **Google**
   - Google Forms responses
   - Google Maps business inquiries

4. **Website**
   - Custom forms
   - Landing pages
   - Contact forms

5. **Manual Entry**
   - Admin/user manual entry
   - CSV import (future)

### Adding New Lead Sources

To add a new lead source:

1. **Create a LeadSource** in the database
2. **Define the integration handler** (if external API)
3. **Create webhook/sync logic** for the platform
4. **Update dashboard** to show the new source

Example:
```python
from crm.models import LeadSource

# Create new source
LeadSource.objects.create(
    name='LinkedIn Leads',
    source_type='linkedin',
    description='Leads from LinkedIn Lead Forms',
    is_active=True
)
```

### OAuth Flow (Meta Example)

1. User initiates connection on dashboard
2. Redirected to Meta login
3. User grants permissions
4. Redirect back to app with access_token
5. ConnectedAccount created with token
6. Periodic sync pulls leads from Meta

## Dashboard Features

### Lead Management
- **List View**: Paginated lead listing with search and filters
- **Lead Cards**: Quick overview of lead status and priority
- **Advanced Search**: Search by name, phone, email, service, source
- **Filters**: Status, priority, source, assigned user

### Analytics
- **Lead Count**: Total leads in system
- **Priority Distribution**: High/medium/low breakdown
- **Source Distribution**: Leads by source
- **Status Distribution**: Leads by status
- **Communication Stats**: WhatsApp/email sent counts

### Connected Accounts
- **View Connections**: List all connected accounts
- **Add Connection**: OAuth flow for new platforms
- **Manage**: Enable/disable sync, view last sync time
- **Permissions**: Show granted permissions

### Tasks
- **Task Board**: View pending, in-progress, completed tasks
- **Create Task**: Assign tasks to leads
- **Due Dates**: Track overdue tasks
- **Notifications**: Alert on overdue tasks

## Development

### Adding New Fields to Lead

1. **Update model** in `crm/models.py`
2. **Create migration**: `python manage.py makemigrations`
3. **Apply migration**: `python manage.py migrate`
4. **Update serializer** in `crm/serializers.py`
5. **Update form** in `crm/forms.py`
6. **Update templates** if needed

### Creating Custom Views

```python
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Lead

@login_required
def custom_lead_view(request):
    leads = Lead.objects.filter(assigned_to=request.user)
    return render(request, 'crm/custom.html', {'leads': leads})
```

### Testing

```bash
# Run all tests
python manage.py test

# Run specific test
python manage.py test crm.tests.LeadModelTests

# Run with verbose output
python manage.py test -v 2
```

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Comment complex logic

## Deployment

### Production Checklist

1. **Security**
   - [ ] Set `DEBUG = False`
   - [ ] Use environment variables for secrets
   - [ ] Update `ALLOWED_HOSTS`
   - [ ] Set strong `SECRET_KEY`
   - [ ] Enable HTTPS (`SECURE_SSL_REDIRECT = True`)
   - [ ] Enable security cookies

2. **Database**
   - [ ] Migrate to PostgreSQL or MySQL
   - [ ] Set up database backups
   - [ ] Run `python manage.py migrate`

3. **Static Files**
   - [ ] Run `python manage.py collectstatic`
   - [ ] Configure static file serving (S3/CDN)

4. **Environment**
   - [ ] Install production dependencies
   - [ ] Configure `.env` file
   - [ ] Set up logging

5. **Performance**
   - [ ] Enable caching
   - [ ] Optimize database queries
   - [ ] Use gunicorn/uwsgi WSGI server
   - [ ] Set up reverse proxy (nginx)

### Deployment Platforms

**Heroku**:
```bash
git push heroku main
```

**AWS/DigitalOcean**:
- Use gunicorn + nginx
- Configure environment variables
- Set up SSL certificates

**Docker**:
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Troubleshooting

### Migration Issues
```bash
# Reset database (development only)
python manage.py migrate crm zero
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

### Static Files Not Loading
```bash
python manage.py collectstatic --noinput
```

### Database Locked (SQLite)
- Close all Django processes
- Delete `db.sqlite3`
- Run `python manage.py migrate`

## Support & Contributing

For issues, feature requests, or contributions, please:
1. Document the issue clearly
2. Include steps to reproduce
3. Submit with test cases if possible
4. Follow the existing code style

## Future Enhancements

- [ ] SMS/WhatsApp lead sync
- [ ] AI-powered lead scoring
- [ ] Advanced reporting and analytics
- [ ] Email campaign integration
- [ ] Bulk lead import/export
- [ ] Mobile app
- [ ] GraphQL API
- [ ] WebSocket real-time updates

## License

Internal Use - A2Z CRM

## Support

For technical support, contact the development team.
