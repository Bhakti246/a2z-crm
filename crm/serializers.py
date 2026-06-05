from rest_framework import serializers
from .models import (
    UserProfile, LeadSource, IntegrationConfig, ConnectedAccount,
    Lead, LeadNote, LeadActivity, Task, MetaConversation, MetaMessage,
    WebhookEvent
)


# =========================
# USER PROFILE SERIALIZER
# =========================

class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'user',
            'role',
            'department',
            'phone',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# =========================
# LEAD SOURCE SERIALIZER
# =========================

class LeadSourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeadSource
        fields = [
            'id',
            'name',
            'source_type',
            'description',
            'is_active',
            'icon',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# =========================
# CONNECTED ACCOUNT SERIALIZER
# =========================

class ConnectedAccountSerializer(serializers.ModelSerializer):

    user_email = serializers.CharField(source='user.email', read_only=True)
    is_token_expired = serializers.SerializerMethodField()

    class Meta:
        model = ConnectedAccount
        fields = [
            'id',
            'user',
            'user_email',
            'account_type',
            'external_id',
            'account_name',
            'account_email',
            'status',
            'is_primary',
            'sync_enabled',
            'last_synced',
            'permissions',
            'is_token_expired',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'external_id',
            'access_token',
            'refresh_token',
            'created_at',
            'updated_at',
            'is_token_expired',
        ]
        extra_kwargs = {
            'user': {'write_only': True},
        }

    def get_is_token_expired(self, obj):
        return obj.is_token_expired()


class WebhookEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEvent
        fields = [
            'id',
            'provider',
            'event_type',
            'external_id',
            'status',
            'attempts',
            'last_error',
            'received_at',
            'processed_at',
        ]
        read_only_fields = fields


class MetaMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaMessage
        fields = [
            'id',
            'conversation',
            'message_id',
            'sender_id',
            'recipient_id',
            'direction',
            'text',
            'event_type',
            'sent_at',
            'created_at',
        ]
        read_only_fields = fields


class MetaConversationSerializer(serializers.ModelSerializer):
    messages = MetaMessageSerializer(many=True, read_only=True)

    class Meta:
        model = MetaConversation
        fields = [
            'id',
            'connected_account',
            'lead',
            'platform',
            'conversation_id',
            'sender_id',
            'recipient_id',
            'status',
            'metadata',
            'last_message_at',
            'created_at',
            'updated_at',
            'messages',
        ]
        read_only_fields = fields


# =========================
# LEAD NOTE SERIALIZER
# =========================

class LeadNoteSerializer(serializers.ModelSerializer):

    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:

        model = LeadNote

        fields = [
            'id',
            'lead',
            'created_by',
            'created_by_name',
            'note',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'created_by_name',
        ]


# =========================
# LEAD ACTIVITY SERIALIZER
# =========================

class LeadActivitySerializer(serializers.ModelSerializer):

    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)

    class Meta:
        model = LeadActivity
        fields = [
            'id',
            'lead',
            'activity_type',
            'activity_type_display',
            'performed_by',
            'performed_by_name',
            'description',
            'changes',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'activity_type_display',
            'performed_by_name',
        ]


# =========================
# LEAD SERIALIZER
# =========================

class LeadSerializer(serializers.ModelSerializer):

    notes = LeadNoteSerializer(many=True, read_only=True)
    activities = LeadActivitySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    source_name = serializers.CharField(source='source.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)

    class Meta:

        model = Lead

        fields = [
            'id',

            # BASIC INFO
            'name',
            'phone',
            'email',
            'company',
            'company_size',
            'industry',

            # LEAD DETAILS
            'service',
            'budget',
            'message',
            'status',
            'status_display',
            'priority',
            'priority_display',

            # SOURCE INFORMATION
            'source',
            'source_name',
            'source_legacy',

            # INTEGRATION TRACKING
            'connected_account',
            'external_id',
            'raw_data',

            # SCORING & RANKING
            'score',
            'ai_remark',

            # ASSIGNMENT
            'assigned_to',
            'assigned_to_name',

            # COMMUNICATION
            'whatsapp_sent',
            'email_sent',
            'last_contacted_at',

            # DUPLICATE TRACKING
            'is_duplicate',
            'duplicate_of',

            # RELATIONSHIPS
            'notes',
            'activities',

            # TIMESTAMPS
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'notes',
            'activities',
            'status_display',
            'priority_display',
            'source_name',
            'assigned_to_name',
        ]

    # =========================
    # NAME VALIDATION
    # =========================

    def validate_name(self, value):

        if len(value.strip()) < 2:

            raise serializers.ValidationError(
                "Name must be at least 2 characters."
            )

        return value

    # =========================
    # PHONE VALIDATION
    # =========================

    def validate_phone(self, value):

        if len(value.strip()) < 7:

            raise serializers.ValidationError(
                "Phone must be at least 7 characters."
            )

        return value

    # =========================
    # BUDGET VALIDATION
    # =========================

    def validate_budget(self, value):

        if value < 0:

            raise serializers.ValidationError(
                "Budget cannot be negative."
            )

        return value

    # =========================
    # SCORE VALIDATION
    # =========================

    def validate_score(self, value):

        if value < 0 or value > 100:

            raise serializers.ValidationError(
                "Score must be between 0 and 100."
            )

        return value


# =========================
# TASK SERIALIZER
# =========================

class TaskSerializer(serializers.ModelSerializer):

    lead_name = serializers.CharField(source='lead.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'lead',
            'lead_name',
            'assigned_to',
            'assigned_to_name',
            'task_type',
            'task_type_display',
            'title',
            'description',
            'due_date',
            'due_time',
            'status',
            'status_display',
            'priority',
            'completed_at',
            'notes',
            'created_by',
            'created_at',
            'updated_at',
            'is_overdue',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'lead_name',
            'assigned_to_name',
            'status_display',
            'task_type_display',
            'is_overdue',
        ]

    def get_is_overdue(self, obj):
        return obj.is_overdue()

    # PHONE VALIDATION
    # =========================

    def validate_phone(self, value):

        cleaned_phone = value.replace(" ", "").replace("-", "")

        if len(cleaned_phone) < 10:

            raise serializers.ValidationError(
                "Phone number is too short."
            )

        return cleaned_phone

    # =========================
    # BUDGET VALIDATION
    # =========================

    def validate_budget(self, value):

        if value is not None and value < 0:

            raise serializers.ValidationError(
                "Budget cannot be negative."
            )

        return value

    # =========================
    # MESSAGE VALIDATION
    # =========================

    def validate_message(self, value):

        if len(value.strip()) < 5:

            raise serializers.ValidationError(
                "Message is too short."
            )

        return value

    # =========================
    # CREATE LEAD
    # =========================

    def create(self, validated_data):

        lead = Lead.objects.create(
            **validated_data
        )

        return lead

    # =========================
    # UPDATE LEAD
    # =========================

    def update(self, instance, validated_data):

        instance.name = validated_data.get(
            'name',
            instance.name
        )

        instance.phone = validated_data.get(
            'phone',
            instance.phone
        )

        instance.email = validated_data.get(
            'email',
            instance.email
        )

        instance.company = validated_data.get(
            'company',
            instance.company
        )

        instance.service = validated_data.get(
            'service',
            instance.service
        )

        instance.budget = validated_data.get(
            'budget',
            instance.budget
        )

        instance.message = validated_data.get(
            'message',
            instance.message
        )

        instance.status = validated_data.get(
            'status',
            instance.status
        )

        instance.source = validated_data.get(
            'source',
            instance.source
        )

        instance.external_id = validated_data.get(
            'external_id',
            instance.external_id
        )

        instance.raw_data = validated_data.get(
            'raw_data',
            instance.raw_data
        )

        instance.save()

        return instance
