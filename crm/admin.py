from django.contrib import admin
from .models import Lead, LeadNote, Task


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'phone',
        'email',
        'service',
        'budget',
        'source',
        'status',
        'priority',
        'score',
        'assigned_to',
        'whatsapp_sent',
        'email_sent',
        'is_duplicate',
        'created_at',
    )

    search_fields = (
        'name',
        'phone',
        'email',
        'service',
    )

    list_filter = (
        'source',
        'status',
        'priority',
        'created_at',
    )

    ordering = (
        '-created_at',
    )

    readonly_fields = (
        'score',
        'created_at',
        'updated_at',
    )

    fieldsets = (

        ('Customer Information', {
            'fields': (
                'name',
                'phone',
                'email',
            )
        }),

        ('Lead Information', {
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
            )
        }),

        ('Automation Status', {
            'fields': (
                'whatsapp_sent',
                'email_sent',
                'is_duplicate',
            )
        }),

        ('Dates', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )


@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'lead',
        'created_at',
    )

    search_fields = (
        'lead__name',
    )

    ordering = (
        '-created_at',
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'lead',
        'assigned_to',
        'task_type',
        'status',
        'due_time',
        'created_at',
    )

    search_fields = (
        'lead__name',
        'assigned_to',
    )

    list_filter = (
        'status',
        'due_time',
    )

    ordering = (
        '-created_at',
    )