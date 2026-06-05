from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserProfile, LeadSource, IntegrationConfig, ConnectedAccount,
    Lead, LeadNote, LeadActivity, Task, WebhookEvent,
    MetaConversation, MetaMessage
)


# ================================
# USER PROFILE ADMIN
# ================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'department')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'role')
        }),
        ('Profile Details', {
            'fields': ('department', 'phone', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ================================
# LEAD SOURCE ADMIN
# ================================

@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'is_active', 'created_at')
    list_filter = ('source_type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'source_type', 'is_active')
        }),
        ('Details', {
            'fields': ('description', 'icon')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ================================
# INTEGRATION CONFIG ADMIN
# ================================

@admin.register(IntegrationConfig)
class IntegrationConfigAdmin(admin.ModelAdmin):
    list_display = ('integration_type', 'config_type', 'is_active', 'created_by', 'created_at')
    list_filter = ('integration_type', 'config_type', 'is_active')
    search_fields = ('integration_type',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Integration', {
            'fields': ('integration_type', 'config_type', 'is_active')
        }),
        ('Configuration', {
            'fields': ('config_data',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ================================
# CONNECTED ACCOUNT ADMIN
# ================================

@admin.register(ConnectedAccount)
class ConnectedAccountAdmin(admin.ModelAdmin):
    list_display = (
        'account_name',
        'user',
        'account_type',
        'status_badge',
        'last_synced',
        'is_primary',
        'created_at'
    )
    list_filter = ('account_type', 'status', 'is_primary', 'sync_enabled', 'created_at')
    search_fields = ('account_name', 'account_email', 'external_id', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'external_id')
    fieldsets = (
        ('User & Account', {
            'fields': ('user', 'account_type', 'account_name', 'account_email')
        }),
        ('External Integration', {
            'fields': ('external_id', 'account_metadata')
        }),
        ('OAuth', {
            'fields': ('token_expires_at', 'token_last_checked_at'),
            'classes': ('collapse',),
            'description': 'OAuth tokens are encrypted at rest and intentionally hidden.'
        }),
        ('Sync & Permissions', {
            'fields': ('sync_enabled', 'last_synced', 'permissions')
        }),
        ('Settings', {
            'fields': ('status', 'is_primary')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'expired': 'orange',
            'revoked': 'red',
            'disconnected': 'gray',
            'pending': 'blue',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('provider', 'event_type', 'external_id', 'status', 'attempts', 'received_at', 'processed_at')
    list_filter = ('provider', 'event_type', 'status', 'received_at')
    search_fields = ('external_id', 'last_error')
    readonly_fields = ('provider', 'event_type', 'external_id', 'payload', 'attempts', 'last_error', 'received_at', 'processed_at')


class MetaMessageInline(admin.TabularInline):
    model = MetaMessage
    extra = 0
    readonly_fields = ('message_id', 'sender_id', 'recipient_id', 'direction', 'text', 'event_type', 'sent_at', 'created_at')
    can_delete = False


@admin.register(MetaConversation)
class MetaConversationAdmin(admin.ModelAdmin):
    list_display = ('conversation_id', 'platform', 'sender_id', 'recipient_id', 'lead', 'status', 'last_message_at')
    list_filter = ('platform', 'status', 'created_at')
    search_fields = ('conversation_id', 'sender_id', 'recipient_id', 'lead__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MetaMessageInline]


@admin.register(MetaMessage)
class MetaMessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'conversation', 'direction', 'event_type', 'sent_at', 'created_at')
    list_filter = ('direction', 'event_type', 'created_at')
    search_fields = ('message_id', 'sender_id', 'recipient_id', 'text')
    readonly_fields = ('created_at',)


# ================================
# LEAD ADMIN
# ================================

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'phone',
        'email',
        'service',
        'status_badge',
        'priority_badge',
        'source',
        'assigned_to',
        'score',
        'is_duplicate',
        'created_at',
    )

    search_fields = (
        'name',
        'phone',
        'email',
        'service',
        'company',
    )

    list_filter = (
        'source',
        'status',
        'priority',
        'is_duplicate',
        'created_at',
        'connected_account',
    )

    readonly_fields = (
        'score',
        'created_at',
        'updated_at',
        'external_id',
    )

    fieldsets = (
        ('Contact Information', {
            'fields': (
                'name',
                'phone',
                'email',
                'company',
                'company_size',
                'industry',
            )
        }),

        ('Lead Details', {
            'fields': (
                'service',
                'budget',
                'message',
                'source',
            )
        }),

        ('CRM Status', {
            'fields': (
                'status',
                'priority',
                'score',
                'assigned_to',
                'ai_remark',
            )
        }),

        ('Communication', {
            'fields': (
                'whatsapp_sent',
                'email_sent',
                'last_contacted_at',
            )
        }),

        ('Integration Tracking', {
            'fields': (
                'connected_account',
                'external_id',
                'raw_data',
            ),
            'classes': ('collapse',)
        }),

        ('Duplicate Management', {
            'fields': (
                'is_duplicate',
                'duplicate_of',
            ),
            'classes': ('collapse',)
        }),

        ('Dates', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'new': '#0066ff',
            'contacted': '#0099ff',
            'interested': '#00cc00',
            'converted': '#006600',
            'lost': '#ff0000',
            'closed': '#999999',
        }
        color = colors.get(obj.status, '#666666')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def priority_badge(self, obj):
        colors = {
            'high': '#ff0000',
            'medium': '#ff9900',
            'low': '#00cc00',
        }
        color = colors.get(obj.priority, '#666666')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'


# ================================
# LEAD NOTE ADMIN
# ================================

@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'lead',
        'created_by',
        'created_at',
    )

    search_fields = (
        'lead__name',
        'note',
    )

    list_filter = (
        'created_at',
        'created_by',
    )

    readonly_fields = (
        'created_at',
    )

    ordering = (
        '-created_at',
    )


# ================================
# LEAD ACTIVITY ADMIN
# ================================

@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'lead',
        'activity_type',
        'performed_by',
        'created_at',
    )

    list_filter = (
        'activity_type',
        'created_at',
        'performed_by',
    )

    search_fields = (
        'lead__name',
        'description',
    )

    readonly_fields = (
        'created_at',
    )

    ordering = (
        '-created_at',
    )


# ================================
# TASK ADMIN
# ================================

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'lead',
        'task_type',
        'assigned_to',
        'status_badge',
        'priority_badge',
        'due_date',
        'created_at',
    )

    search_fields = (
        'lead__name',
        'assigned_to__username',
        'title',
    )

    list_filter = (
        'status',
        'priority',
        'task_type',
        'due_date',
        'created_at',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'completed_at',
    )

    fieldsets = (
        ('Lead & Assignment', {
            'fields': (
                'lead',
                'assigned_to',
                'created_by',
            )
        }),

        ('Task Details', {
            'fields': (
                'task_type',
                'title',
                'description',
            )
        }),

        ('Schedule', {
            'fields': (
                'due_date',
                'due_time',
            )
        }),

        ('Status', {
            'fields': (
                'status',
                'priority',
                'completed_at',
                'notes',
            )
        }),

        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#ff9900',
            'in_progress': '#0099ff',
            'completed': '#00cc00',
            'cancelled': '#999999',
        }
        color = colors.get(obj.status, '#666666')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def priority_badge(self, obj):
        colors = {
            'high': '#ff0000',
            'medium': '#ff9900',
            'low': '#00cc00',
        }
        color = colors.get(obj.priority, '#666666')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
