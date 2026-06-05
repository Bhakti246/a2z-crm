from celery import shared_task
from django.utils import timezone

from crm.integrations.meta.client import MetaGraphClient
from crm.integrations.meta.processors import (
    mark_event_failure,
    process_leadgen_event,
    process_message_event,
)
from crm.models import ConnectedAccount, WebhookEvent


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def process_meta_webhook_event(self, event_id):
    event = WebhookEvent.objects.get(id=event_id)
    event.status = 'processing'
    event.save(update_fields=['status'])
    try:
        if event.event_type == 'leadgen':
            process_leadgen_event(event)
        elif event.event_type in {'messages', 'message_reactions', 'messaging_seen'}:
            process_message_event(event)
        else:
            event.status = 'processed'
            event.processed_at = timezone.now()
            event.save(update_fields=['status', 'processed_at'])
    except Exception as exc:
        mark_event_failure(event, exc)
        raise


@shared_task
def check_meta_token_health():
    for account in ConnectedAccount.objects.filter(account_type__in=['facebook', 'instagram'], status='active'):
        token = account.get_access_token()
        if not token:
            account.status = 'revoked'
            account.token_last_checked_at = timezone.now()
            account.save(update_fields=['status', 'token_last_checked_at'])
            continue

        try:
            payload = MetaGraphClient().debug_token(token)
            data = payload.get('data', {})
            account.token_last_checked_at = timezone.now()
            if not data.get('is_valid', False):
                account.status = 'revoked'
            expires_at = data.get('expires_at')
            if expires_at:
                account.token_expires_at = timezone.datetime.fromtimestamp(expires_at, tz=timezone.get_current_timezone())
            account.save(update_fields=['status', 'token_last_checked_at', 'token_expires_at'])
        except Exception:
            account.status = 'expired'
            account.token_last_checked_at = timezone.now()
            account.save(update_fields=['status', 'token_last_checked_at'])
