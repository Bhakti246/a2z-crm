from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator
import json


class UserProfile(models.Model):
    """Extended user profile for role-based access control"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('user', 'User'),
        ('client', 'Client'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    department = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class LeadSource(models.Model):
    """Defines available lead sources in the system"""
    
    SOURCE_TYPES = [
        ('facebook', 'Facebook Ads'),
        ('instagram', 'Instagram Ads'),
        ('instagram_dms', 'Instagram Direct Messages'),
        ('google_forms', 'Google Forms'),
        ('google_maps', 'Google Maps Business'),
        ('website_form', 'Website Form'),
        ('landing_page', 'Landing Page'),
        ('whatsapp', 'WhatsApp Inquiry'),
        ('email', 'Email Inquiry'),
        ('manual', 'Manual Entry'),
        ('api', 'API Integration'),
        ('other', 'Other Source'),
    ]
    
    name = models.CharField(max_length=100)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # For UI
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Lead Source"
        verbose_name_plural = "Lead Sources"
        unique_together = ('name', 'source_type')
    
    def __str__(self):
        return self.name


class IntegrationConfig(models.Model):
    """Stores configuration for external integrations"""
    
    CONFIG_TYPES = [
        ('oauth', 'OAuth Connection'),
        ('api_key', 'API Key'),
        ('webhook', 'Webhook'),
        ('custom', 'Custom Config'),
    ]
    
    integration_type = models.CharField(max_length=50)  # 'facebook', 'google', 'instagram', etc.
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPES, default='oauth')
    
    # Sensitive data (should be encrypted in production)
    config_data = models.JSONField(default=dict)  # Stores API key, secret, etc.
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Integration Config"
        verbose_name_plural = "Integration Configs"
        unique_together = ('integration_type', 'config_type')
    
    def __str__(self):
        return f"{self.integration_type} - {self.get_config_type_display()}"


class ConnectedAccount(models.Model):
    """Represents a user's connected social/platform account"""
    
    ACCOUNT_TYPES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('google', 'Google'),
        ('google_forms', 'Google Forms'),
        ('other', 'Other Platform'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Token Expired'),
        ('revoked', 'Revoked'),
        ('disconnected', 'Disconnected'),
        ('pending', 'Pending Verification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connected_accounts')
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    
    # Account identifiers
    external_id = models.CharField(max_length=255, unique=True, db_index=True)
    account_name = models.CharField(max_length=255)
    account_email = models.EmailField(blank=True, null=True)
    
    # OAuth tokens (should be encrypted in production)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    encrypted_access_token = models.TextField(blank=True, null=True)
    encrypted_refresh_token = models.TextField(blank=True, null=True)
    token_expires_at = models.DateTimeField(blank=True, null=True)
    token_last_checked_at = models.DateTimeField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Metadata
    account_metadata = models.JSONField(default=dict)  # Store platform-specific data
    permissions = models.JSONField(default=list)  # List of permissions granted
    
    is_primary = models.BooleanField(default=False)  # Primary account for user
    last_synced = models.DateTimeField(blank=True, null=True)
    sync_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Connected Account"
        verbose_name_plural = "Connected Accounts"
        unique_together = ('user', 'account_type', 'external_id')
        indexes = [
            models.Index(fields=['user', 'account_type']),
            models.Index(fields=['status', 'sync_enabled']),
        ]
    
    def __str__(self):
        return f"{self.account_name} ({self.get_account_type_display()})"
    
    def is_token_expired(self):
        """Check if OAuth token has expired"""
        from django.utils import timezone
        if self.token_expires_at:
            return timezone.now() >= self.token_expires_at
        return False

    def set_access_token(self, value):
        from crm.integrations.meta.crypto import encrypt_value

        self.encrypted_access_token = encrypt_value(value) if value else ''
        self.access_token = ''

    def get_access_token(self):
        from crm.integrations.meta.crypto import decrypt_value

        if self.encrypted_access_token:
            return decrypt_value(self.encrypted_access_token)
        return self.access_token or ''

    def set_refresh_token(self, value):
        from crm.integrations.meta.crypto import encrypt_value

        self.encrypted_refresh_token = encrypt_value(value) if value else ''
        self.refresh_token = ''

    def get_refresh_token(self):
        from crm.integrations.meta.crypto import decrypt_value

        if self.encrypted_refresh_token:
            return decrypt_value(self.encrypted_refresh_token)
        return self.refresh_token or ''


class WebhookEvent(models.Model):
    """Durable webhook event log for idempotent async processing."""

    STATUS_CHOICES = [
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('dead_letter', 'Dead Letter'),
    ]

    provider = models.CharField(max_length=50, default='meta', db_index=True)
    event_type = models.CharField(max_length=100, db_index=True)
    external_id = models.CharField(max_length=255, db_index=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received', db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, null=True)
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Webhook Event"
        verbose_name_plural = "Webhook Events"
        unique_together = ('provider', 'event_type', 'external_id')
        indexes = [
            models.Index(fields=['provider', 'status'], name='crm_wh_provider_status'),
            models.Index(fields=['event_type', 'external_id'], name='crm_wh_event_external'),
        ]
        ordering = ['-received_at']

    def __str__(self):
        return f"{self.provider}:{self.event_type}:{self.external_id}"


class MetaConversation(models.Model):
    """Instagram/Facebook messaging conversation tracked by Meta IDs."""

    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
    ]

    connected_account = models.ForeignKey(
        ConnectedAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='meta_conversations'
    )
    lead = models.ForeignKey(
        'Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='meta_conversations'
    )
    platform = models.CharField(max_length=30, choices=PLATFORM_CHOICES, default='instagram')
    conversation_id = models.CharField(max_length=255, unique=True, db_index=True)
    sender_id = models.CharField(max_length=255, db_index=True)
    recipient_id = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=20, default='open', db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    last_message_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Meta Conversation"
        verbose_name_plural = "Meta Conversations"
        ordering = ['-last_message_at', '-created_at']

    def __str__(self):
        return f"{self.platform} conversation {self.conversation_id}"


class MetaMessage(models.Model):
    """Message event from Instagram/Facebook messaging webhooks."""

    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]

    conversation = models.ForeignKey(
        MetaConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    message_id = models.CharField(max_length=255, unique=True, db_index=True)
    sender_id = models.CharField(max_length=255, db_index=True)
    recipient_id = models.CharField(max_length=255, db_index=True)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='inbound')
    text = models.TextField(blank=True, null=True)
    event_type = models.CharField(max_length=100, default='message')
    raw_data = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Meta Message"
        verbose_name_plural = "Meta Messages"
        ordering = ['-sent_at', '-created_at']

    def __str__(self):
        return f"{self.direction} {self.message_id}"


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
        ('archived', 'Archived'),
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
        ('google_maps', 'Google Maps'),
        ('other', 'Other'),
    ]

    # Basic contact information
    name = models.CharField(max_length=100, db_index=True)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)
    
    # Company information
    company = models.CharField(max_length=255, blank=True, null=True)
    company_size = models.CharField(max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)

    # Lead information
    service = models.CharField(max_length=100)
    budget = models.IntegerField(default=0)
    message = models.TextField(blank=True, null=True)

    # Lead source and tracking
    source = models.ForeignKey(
        LeadSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )
    source_legacy = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        default='manual',
        help_text="Legacy source field. Use 'source' ForeignKey instead."
    )
    
    # Integration tracking
    connected_account = models.ForeignKey(
        ConnectedAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )
    external_id = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        db_index=True,
        help_text="ID from external platform (Facebook, Instagram, etc.)"
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw data received from external platform"
    )

    # CRM fields
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        db_index=True
    )
    
    # Scoring
    score = models.IntegerField(default=0, help_text="Lead qualification score (0-100)")
    ai_remark = models.CharField(max_length=200, blank=True, null=True)

    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads'
    )

    # Communication tracking
    whatsapp_sent = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    last_contacted_at = models.DateTimeField(blank=True, null=True)

    # Duplicate tracking
    is_duplicate = models.BooleanField(default=False, db_index=True)
    duplicate_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='duplicates'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        indexes = [
            models.Index(fields=['phone', 'email']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def mark_as_duplicate_of(self, other_lead):
        """Mark this lead as duplicate of another lead"""
        self.is_duplicate = True
        self.duplicate_of = other_lead
        self.save()
    
    def get_source_display_name(self):
        """Get display name of lead source"""
        if self.source:
            return self.source.name
        return self.get_source_legacy_display()


class LeadActivity(models.Model):
    """Audit log for tracking all lead activity"""
    
    ACTIVITY_TYPES = [
        ('created', 'Lead Created'),
        ('updated', 'Lead Updated'),
        ('status_changed', 'Status Changed'),
        ('assigned', 'Assigned to User'),
        ('contacted', 'Contacted'),
        ('note_added', 'Note Added'),
        ('synced', 'Synced from Integration'),
        ('merged', 'Merged with Another Lead'),
        ('archived', 'Archived'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    
    # Who performed the action
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lead_activities'
    )
    
    # What changed
    description = models.TextField(blank=True, null=True)
    changes = models.JSONField(default=dict)  # {field: {old: value, new: value}}
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = "Lead Activity"
        verbose_name_plural = "Lead Activities"
        indexes = [
            models.Index(fields=['lead', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.lead.name}"



class LeadNote(models.Model):

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='notes'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lead_notes'
    )

    note = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = "Lead Note"
        verbose_name_plural = "Lead Notes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Note on {self.lead.name} ({self.created_at.date()})"


class Task(models.Model):

    TASK_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    TASK_TYPES = [
        ('call', 'Call Lead'),
        ('email', 'Send Email'),
        ('meeting', 'Schedule Meeting'),
        ('followup', 'Follow Up'),
        ('proposal', 'Send Proposal'),
        ('other', 'Other Task'),
    ]

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )

    task_type = models.CharField(
        max_length=50,
        choices=TASK_TYPES,
        default='call'
    )

    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    due_date = models.DateField(db_index=True)
    due_time = models.DateTimeField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=TASK_STATUS,
        default='pending',
        db_index=True
    )
    
    priority = models.CharField(
        max_length=10,
        choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
        default='medium'
    )

    completed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tasks'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        indexes = [
            models.Index(fields=['lead', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]
        ordering = ['due_date', '-created_at']

    def __str__(self):
        return f"{self.get_task_type_display()} - {self.lead.name}"
    
    def is_overdue(self):
        """Check if task is overdue"""
        from django.utils import timezone
        if self.status != 'completed' and self.due_date:
            return timezone.now().date() > self.due_date
        return False

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.lead.name} - {self.task_type}"
