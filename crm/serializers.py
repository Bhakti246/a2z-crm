from rest_framework import serializers

from .models import Lead, LeadNote


# =========================
# LEAD NOTE SERIALIZER
# =========================

class LeadNoteSerializer(serializers.ModelSerializer):

    class Meta:

        model = LeadNote

        fields = [

            'id',
            'note',
            'created_at',

        ]

        read_only_fields = [

            'id',
            'created_at',

        ]


# =========================
# LEAD SERIALIZER
# =========================

class LeadSerializer(serializers.ModelSerializer):

    notes = LeadNoteSerializer(
        many=True,
        read_only=True
    )

    class Meta:

        model = Lead

        fields = [

            'id',

            # BASIC INFO
            'name',
            'phone',
            'email',
            'company',

            # LEAD DETAILS
            'service',
            'budget',
            'message',
            'status',
            'source',

            # TRACKING
            'external_id',
            'raw_data',

            # TIMESTAMPS
            'created_at',
            'updated_at',

            # NOTES
            'notes',

        ]

        read_only_fields = [

            'id',
            'created_at',
            'updated_at',
            'notes',

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