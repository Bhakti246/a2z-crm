from django.db import models


class Lead(models.Model):

    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('follow_up', 'Follow Up'),
        ('interested', 'Interested'),
        ('converted', 'Converted'),
        ('not_interested', 'Not Interested'),
        ('closed', 'Closed'),
        ('qualified', 'Qualified'),
        ('meeting', 'Meeting Scheduled'),
        ('proposal', 'Proposal Sent'),
        ('lost', 'Lost'),

    ]

    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    SOURCE_CHOICES = [
        ('website', 'Website Form'),
        ('landing_page', 'Landing Page'),
        ('google_forms', 'Google Forms'),
        ('facebook_ads', 'Facebook Lead Ads'),
        ('instagram_ads', 'Instagram Ads'),
        ('instagram_dms', 'Instagram DM'),
        ('whatsapp', 'WhatsApp Inquiry'),
        ('manual', 'Manual Entry'),
    ]

    name = models.CharField(max_length=100)

    phone = models.CharField(max_length=20)

    email = models.EmailField(
        blank=True,
        null=True
    )

    service = models.CharField(max_length=100)

    budget = models.IntegerField(default=0)

    message = models.TextField(
        blank=True,
        null=True
    )

    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        default='website'
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='new'
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    score = models.IntegerField(default=0)

    ai_remark = models.CharField(
    max_length=100,
    blank=True,
    null=True
)

    assigned_to = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    whatsapp_sent = models.BooleanField(default=False)

    email_sent = models.BooleanField(default=False)

    is_duplicate = models.BooleanField(default=False)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class LeadNote(models.Model):

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='notes'
    )

    note = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.lead.name


class Task(models.Model):

    TASK_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    assigned_to = models.CharField(max_length=100)

    task_type = models.CharField(
        max_length=100,
        default='Call Lead'
    )

    due_time = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=TASK_STATUS,
        default='pending'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.lead.name} - {self.task_type}"