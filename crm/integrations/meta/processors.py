import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from crm.integrations.meta.client import MetaGraphClient
from crm.models import (
    ConnectedAccount,
    Lead,
    LeadActivity,
    LeadSource,
    MetaConversation,
    MetaMessage,
    WebhookEvent,
)

logger = logging.getLogger('crm')


def normalize_field_data(field_data):
    mapped = {}
    for item in field_data or []:
        name = item.get('name')
        values = item.get('values') or []
        mapped[name] = values[0] if values else ''
    return mapped


def lead_values_from_meta(details):
    fields = normalize_field_data(details.get('field_data'))
    name = fields.get('full_name') or fields.get('name') or 'Meta Lead'
    phone = fields.get('phone_number') or fields.get('phone') or ''
    email = fields.get('email') or ''
    company = fields.get('company_name') or fields.get('company') or ''
    city = fields.get('city') or ''
    custom_questions = {
        key: value for key, value in fields.items()
        if key not in {'full_name', 'name', 'phone_number', 'phone', 'email', 'company_name', 'company', 'city'}
    }
    return {
        'name': name,
        'phone': phone or 'unknown',
        'email': email or None,
        'company': company or None,
        'service': custom_questions.get('service') or custom_questions.get('what_service_are_you_interested_in') or 'Meta Lead Ads',
        'message': city or '',
        'raw_fields': fields,
        'custom_questions': custom_questions,
    }


def get_or_create_source(source_type, name):
    source, _ = LeadSource.objects.get_or_create(
        source_type=source_type,
        name=name,
        defaults={'description': f'Leads from {name}', 'is_active': True},
    )
    return source


def connected_page_account(page_id):
    return ConnectedAccount.objects.filter(
        account_type='facebook',
        external_id=str(page_id),
        status='active',
    ).first()


@transaction.atomic
def process_leadgen_event(event):
    payload = event.payload
    value = payload.get('value', {})
    leadgen_id = str(value.get('leadgen_id') or event.external_id)
    page_id = str(value.get('page_id') or payload.get('page_id') or '')

    if Lead.objects.filter(external_id=leadgen_id).exists():
        event.status = 'processed'
        event.processed_at = timezone.now()
        event.save(update_fields=['status', 'processed_at'])
        return None

    account = connected_page_account(page_id)
    if not account:
        raise ValueError(f'No active connected Page account for page_id={page_id}')

    details = MetaGraphClient().lead_details(leadgen_id, account.get_access_token())
    values = lead_values_from_meta(details)
    platform = (details.get('platform') or value.get('platform') or '').lower()
    source_type = 'instagram_ads' if 'instagram' in platform else 'facebook_ads'
    source_name = 'Instagram Ads' if source_type == 'instagram_ads' else 'Facebook Lead Ads'

    lead = Lead.objects.create(
        name=values['name'],
        phone=values['phone'],
        email=values['email'],
        company=values['company'],
        service=values['service'],
        budget=0,
        message=values['message'],
        source=get_or_create_source('instagram' if source_type == 'instagram_ads' else 'facebook', source_name),
        source_legacy=source_type,
        connected_account=account,
        external_id=leadgen_id,
        raw_data={
            'webhook': payload,
            'lead_details': details,
            'custom_questions': values['custom_questions'],
        },
    )

    LeadActivity.objects.create(
        lead=lead,
        activity_type='synced',
        description='Lead synced from Meta Lead Ads webhook',
        changes={'external_id': {'old': None, 'new': leadgen_id}},
    )

    event.status = 'processed'
    event.processed_at = timezone.now()
    event.save(update_fields=['status', 'processed_at'])
    return lead


def event_external_id(event_type, payload):
    if event_type == 'leadgen':
        return str(payload.get('value', {}).get('leadgen_id') or payload.get('leadgen_id'))
    message = payload.get('message') or {}
    return str(message.get('mid') or payload.get('message_id') or payload.get('timestamp'))


def record_webhook_events(payload):
    events = []
    for entry in payload.get('entry', []):
        page_id = entry.get('id')

        for change in entry.get('changes', []):
            event_type = change.get('field', 'change')
            event_payload = {'page_id': page_id, **change}
            external_id = event_external_id(event_type, event_payload)
            if not external_id or external_id == 'None':
                continue
            event, _ = WebhookEvent.objects.get_or_create(
                provider='meta',
                event_type=event_type,
                external_id=external_id,
                defaults={'payload': event_payload},
            )
            events.append(event)

        for messaging in entry.get('messaging', []):
            message = messaging.get('message') or {}
            reaction = messaging.get('reaction') or {}
            event_type = 'message_reactions' if reaction else 'messages'
            event_payload = {'page_id': page_id, **messaging}
            external_id = str(message.get('mid') or reaction.get('mid') or messaging.get('timestamp'))
            if not external_id or external_id == 'None':
                continue
            event, _ = WebhookEvent.objects.get_or_create(
                provider='meta',
                event_type=event_type,
                external_id=external_id,
                defaults={'payload': event_payload},
            )
            events.append(event)
    return events


@transaction.atomic
def process_message_event(event):
    payload = event.payload
    sender_id = str((payload.get('sender') or {}).get('id') or '')
    recipient_id = str((payload.get('recipient') or {}).get('id') or payload.get('page_id') or '')
    message = payload.get('message') or {}
    message_id = str(message.get('mid') or event.external_id)
    text = message.get('text') or ''
    timestamp = payload.get('timestamp')
    sent_at = timezone.now()
    if timestamp:
        sent_at = timezone.datetime.fromtimestamp(int(timestamp) / 1000, tz=timezone.get_current_timezone())

    account = connected_page_account(recipient_id) or connected_page_account(payload.get('page_id'))
    conversation_id = f"{recipient_id}:{sender_id}"
    conversation, _ = MetaConversation.objects.get_or_create(
        conversation_id=conversation_id,
        defaults={
            'connected_account': account,
            'platform': 'instagram' if payload.get('instagram') else 'facebook',
            'sender_id': sender_id,
            'recipient_id': recipient_id,
            'last_message_at': sent_at,
            'metadata': {'first_payload': payload},
        },
    )
    conversation.last_message_at = sent_at
    conversation.save(update_fields=['last_message_at', 'updated_at'])

    meta_message, created = MetaMessage.objects.get_or_create(
        message_id=message_id,
        defaults={
            'conversation': conversation,
            'sender_id': sender_id,
            'recipient_id': recipient_id,
            'direction': 'inbound',
            'text': text,
            'event_type': event.event_type,
            'raw_data': payload,
            'sent_at': sent_at,
        },
    )

    if created and not conversation.lead:
        source = get_or_create_source('instagram_dms', 'Instagram Direct Messages')
        lead = Lead.objects.create(
            name=f'Meta DM {sender_id}',
            phone='unknown',
            service='Instagram Direct Message',
            budget=0,
            message=text,
            source=source,
            source_legacy='instagram_dms',
            connected_account=account,
            external_id=conversation_id,
            raw_data={'conversation_id': conversation_id, 'message': payload},
        )
        conversation.lead = lead
        conversation.save(update_fields=['lead'])
        LeadActivity.objects.create(
            lead=lead,
            activity_type='synced',
            description='Lead created from Meta messaging conversation',
        )

    event.status = 'processed'
    event.processed_at = timezone.now()
    event.save(update_fields=['status', 'processed_at'])
    return meta_message


def mark_event_failure(event, exc, max_attempts=5):
    event.attempts += 1
    event.last_error = str(exc)
    event.status = 'dead_letter' if event.attempts >= max_attempts else 'failed'
    event.save(update_fields=['attempts', 'last_error', 'status'])
    logger.exception('Meta webhook event processing failed: %s', event.id)
