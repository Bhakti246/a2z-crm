# A2Z CRM - SETUP GUIDE

## Quick Start (5 minutes)

### 1. Clone & Enter Project
```bash
cd /path/to/a2z-crm
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations
```bash
python manage.py migrate
```

### 5. Create Admin User
```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

### 6. Start Development Server
```bash
python manage.py runserver
```

### 7. Access Application
- **Admin Panel**: http://localhost:8000/admin/
- **Dashboard**: http://localhost:8000/dashboard/
- **Home**: http://localhost:8000/

---

## Complete Installation Guide

### Prerequisites Check
```bash
# Check Python version (need 3.8+)
python --version

# Check pip
pip --version
```

### Step-by-Step Setup

#### 1. Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

#### 2. Install Requirements
```bash
pip install -r requirements.txt
```

**Key Dependencies**:
- Django 6.0.5
- Django REST Framework 3.14+
- Python 3.8+
- SQLite (default) or PostgreSQL/MySQL

#### 3. Environment Setup
```bash
# Copy example to .env
cp .env.example .env

# Edit .env with your settings
# nano .env  (or use your editor)
```

#### 4. Database Setup
```bash
# Create database tables
python manage.py migrate

# Expected output:
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ...
#   Applying crm.0001_initial... OK
```

#### 5. Create Admin User
```bash
python manage.py createsuperuser

# Enter:
# Username: admin
# Email: admin@example.com
# Password: (secure password)
# Superuser created successfully
```

#### 6. Verify Setup
```bash
# Check for any issues
python manage.py check

# Expected: System check identified no issues (0 silenced).
```

#### 7. Load Initial Data (Optional)
```bash
# Create sample lead sources (already done during migration)
python manage.py shell
```

#### 8. Run Development Server
```bash
python manage.py runserver

# Access:
# http://localhost:8000/ - Home
# http://localhost:8000/admin/ - Admin
# http://localhost:8000/dashboard/ - Dashboard (requires login)
```

---

## Database Models - Quick Reference

### Initialize Models Documentation
```python
# List all models
python manage.py inspectdb

# Check model structure
python manage.py dbshell
sqlite> .tables
sqlite> .schema crm_lead
```

### Database Indexes
The system uses optimized indexes on:
- `lead.phone`, `lead.email` - Contact lookup
- `lead.status`, `lead.priority` - Dashboard filtering
- `lead.created_at` - Recent lead lookup
- `connectedaccount.user`, `connectedaccount.status` - Account queries
- `task.assigned_to`, `task.status` - Task queries

---

## User Roles Setup

### Creating Users with Different Roles

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User, Group
from crm.models import UserProfile

# Create admin user
admin = User.objects.create_user('admin', 'admin@company.com', 'admin123')
profile = UserProfile.objects.create(user=admin, role='admin')

# Create manager
manager = User.objects.create_user('manager', 'manager@company.com', 'manager123')
profile = UserProfile.objects.create(user=manager, role='manager')

# Create sales rep
salesperson = User.objects.create_user('sales', 'sales@company.com', 'sales123')
profile = UserProfile.objects.create(user=salesperson, role='user', department='Sales')

print("Users created successfully!")
```

---

## Lead Source Configuration

### Verify Lead Sources Were Created
```bash
python manage.py shell
```

```python
from crm.models import LeadSource

# List all sources
for source in LeadSource.objects.all():
    print(f"{source.name} ({source.source_type}): {source.get_status_display()}")

# Expected output:
# Facebook Ads (facebook): Active
# Instagram Ads (instagram): Active
# ...
```

### Add Custom Source
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

---

## Creating Sample Data

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from crm.models import Lead, LeadSource, Task, LeadNote
from datetime import timedelta
from django.utils import timezone

# Get user
user = User.objects.first()
source = LeadSource.objects.get(source_type='facebook')

# Create sample leads
leads_data = [
    {'name': 'John Smith', 'phone': '+1234567890', 'email': 'john@example.com', 'service': 'Web Development', 'budget': 50000},
    {'name': 'Jane Doe', 'phone': '+1987654321', 'email': 'jane@example.com', 'service': 'Mobile App', 'budget': 75000},
    {'name': 'Bob Wilson', 'phone': '+1112223333', 'email': 'bob@example.com', 'service': 'Consulting', 'budget': 30000},
]

for data in leads_data:
    lead = Lead.objects.create(
        name=data['name'],
        phone=data['phone'],
        email=data['email'],
        service=data['service'],
        budget=data['budget'],
        source=source,
        assigned_to=user,
        priority='high' if data['budget'] > 50000 else 'medium'
    )
    print(f"Created lead: {lead.name}")

# Create sample tasks
for lead in Lead.objects.all()[:2]:
    Task.objects.create(
        lead=lead,
        assigned_to=user,
        created_by=user,
        task_type='call',
        title='Follow-up call',
        due_date=timezone.now().date() + timedelta(days=3),
        priority='high'
    )

print("Sample data created!")
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'django'"
```bash
# Solution: Install requirements
pip install -r requirements.txt
```

### Issue: "django.db.utils.OperationalError: no such table"
```bash
# Solution: Run migrations
python manage.py migrate
```

### Issue: "Database is locked (SQLite)"
```bash
# Solution: Close all Django processes and restart
# Windows: 
taskkill /F /IM python.exe
# macOS/Linux:
pkill -f python

# Then restart server:
python manage.py runserver
```

### Issue: "CSRF token missing"
```bash
# Ensure CSRF middleware is enabled in settings.py
# And template includes: {% csrf_token %}
```

### Issue: "Static files not loading"
```bash
# Solution: Collect static files
python manage.py collectstatic --noinput
```

### Issue: "Login redirects to blank page"
```bash
# Solution: Check LOGIN_REDIRECT_URL in settings.py
# Make sure dashboard view exists and is accessible
```

---

## Testing

### Run All Tests
```bash
python manage.py test
```

### Run Specific Test
```bash
python manage.py test crm.tests.LeadModelTests
```

### Run with Verbose Output
```bash
python manage.py test -v 2
```

### Test Coverage
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

---

## Production Deployment

### Before Going Live

#### 1. Security Checklist
```python
# In settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECRET_KEY = 'generate-new-secret-key'
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

#### 2. Database Migration
```bash
# Use PostgreSQL/MySQL instead of SQLite
# Update DATABASE_URL in .env
python manage.py migrate --database=production
```

#### 3. Static Files
```bash
python manage.py collectstatic --noinput
```

#### 4. Backup
```bash
# Backup database before deployment
# Set up automated backups
```

### Deployment Commands

#### Using Gunicorn
```bash
pip install gunicorn
gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
```

#### Using Docker
```bash
# Build image
docker build -t a2z-crm .

# Run container
docker run -p 8000:8000 a2z-crm
```

#### Using Heroku
```bash
heroku login
heroku create a2z-crm
git push heroku main
```

---

## Regular Maintenance

### Daily
- Monitor error logs: `tail -f crm.log`
- Check webhook deliveries
- Verify lead sync from integrations

### Weekly
- Review analytics
- Clean up old logs
- Check database size

### Monthly
- Run database backups
- Review security logs
- Update dependencies
- Check performance metrics

---

## Support & Resources

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)

### Get Help
1. Check IMPLEMENTATION_GUIDE.md for detailed architecture
2. Check troubleshooting section above
3. Review error logs in crm.log
4. Contact development team

---

## Next Steps After Setup

1. **Create Users**: Set up team members with appropriate roles
2. **Configure Integrations**: Set up Meta/Google OAuth (see IMPLEMENTATION_GUIDE.md)
3. **Customize Dashboard**: Adjust to your business needs
4. **Add Custom Fields**: Extend Lead model as needed
5. **Set Up Webhooks**: Configure integrations to send leads
6. **Train Team**: Onboard users on system usage
7. **Monitor**: Set up alerts and performance monitoring

---

Congratulations! Your A2Z CRM is now set up and ready to use! 🎉
