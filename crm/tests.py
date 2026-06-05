import hashlib
import hmac
import json
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from crm.integrations.meta.processors import process_leadgen_event, record_webhook_events
from crm.integrations.meta.security import verify_meta_signature
from crm.models import ConnectedAccount, Lead, MetaConversation, WebhookEvent


@override_settings(
    META_OAUTH_CONFIG={
        'client_id': 'app-id',
        'client_secret': 'app-secret',
        'redirect_uri': 'https://example.com/integrations/meta/callback/',
        'scopes': ['pages_show_list', 'leads_retrieval'],
    },
    WEBHOOK_VERIFY_TOKEN='verify-token',
    CELERY_TASK_ALWAYS_EAGER=False,
    SECURE_SSL_REDIRECT=False,
)
class MetaSecurityTests(TestCase):
    def test_signature_validation_accepts_valid_signature(self):
        body = b'{"object":"page"}'
        digest = hmac.new(b'app-secret', body, hashlib.sha256).hexdigest()

        self.assertTrue(verify_meta_signature(body, f'sha256={digest}'))

    def test_signature_validation_rejects_invalid_signature(self):
        self.assertFalse(verify_meta_signature(b'{}', 'sha256=bad'))

    def test_webhook_verification_uses_environment_token(self):
        response = self.client.get(reverse('meta_webhook'), {
            'hub.mode': 'subscribe',
            'hub.verify_token': 'verify-token',
            'hub.challenge': 'challenge-123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'challenge-123')

    @patch('crm.views_meta.process_meta_webhook_event.delay')
    def test_webhook_post_records_events_and_returns_immediately(self, delay):
        payload = {
            'entry': [{
                'id': 'page-1',
                'changes': [{
                    'field': 'leadgen',
                    'value': {'leadgen_id': 'lead-1', 'page_id': 'page-1', 'form_id': 'form-1'},
                }],
            }],
        }
        body = json.dumps(payload).encode()
        digest = hmac.new(b'app-secret', body, hashlib.sha256).hexdigest()

        response = self.client.post(
            reverse('meta_webhook'),
            data=body,
            content_type='application/json',
            HTTP_X_HUB_SIGNATURE_256=f'sha256={digest}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WebhookEvent.objects.count(), 1)
        delay.assert_called_once()


@override_settings(SECRET_KEY='test-secret-key')
class MetaTokenEncryptionTests(TestCase):
    def test_connected_account_encrypts_access_token(self):
        user = User.objects.create_user(username='owner')
        account = ConnectedAccount.objects.create(
            user=user,
            account_type='facebook',
            external_id='meta-user-1',
            account_name='Owner',
        )

        account.set_access_token('super-secret-token')
        account.save()
        account.refresh_from_db()

        self.assertEqual(account.access_token, '')
        self.assertNotIn('super-secret-token', account.encrypted_access_token)
        self.assertEqual(account.get_access_token(), 'super-secret-token')


@override_settings(
    META_OAUTH_CONFIG={
        'client_id': 'app-id',
        'client_secret': 'app-secret',
        'redirect_uri': 'https://example.com/integrations/meta/callback/',
        'scopes': ['pages_show_list', 'leads_retrieval'],
    },
)
class MetaLeadProcessingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner')
        self.page_account = ConnectedAccount.objects.create(
            user=self.user,
            account_type='facebook',
            external_id='page-1',
            account_name='Business Page',
            status='active',
        )
        self.page_account.set_access_token('page-token')
        self.page_account.save()

    def test_record_webhook_events_is_idempotent(self):
        payload = {
            'entry': [{
                'id': 'page-1',
                'changes': [{
                    'field': 'leadgen',
                    'value': {'leadgen_id': 'lead-1', 'page_id': 'page-1'},
                }],
            }],
        }

        record_webhook_events(payload)
        record_webhook_events(payload)

        self.assertEqual(WebhookEvent.objects.count(), 1)

    @patch('crm.integrations.meta.processors.MetaGraphClient.lead_details')
    def test_process_leadgen_event_creates_lead_and_activity(self, lead_details):
        lead_details.return_value = {
            'id': 'lead-1',
            'platform': 'facebook',
            'field_data': [
                {'name': 'full_name', 'values': ['Jane Buyer']},
                {'name': 'email', 'values': ['jane@example.com']},
                {'name': 'phone_number', 'values': ['1234567890']},
                {'name': 'company_name', 'values': ['Jane Co']},
            ],
        }
        event = WebhookEvent.objects.create(
            provider='meta',
            event_type='leadgen',
            external_id='lead-1',
            payload={'page_id': 'page-1', 'value': {'leadgen_id': 'lead-1', 'page_id': 'page-1'}},
        )

        lead = process_leadgen_event(event)

        self.assertEqual(lead.name, 'Jane Buyer')
        self.assertEqual(lead.external_id, 'lead-1')
        self.assertEqual(lead.source_legacy, 'facebook_ads')
        self.assertEqual(lead.activities.count(), 1)


class MetaMessagingTests(TestCase):
    def test_message_event_creates_conversation_event(self):
        payload = {
            'entry': [{
                'id': 'page-1',
                'messaging': [{
                    'sender': {'id': 'sender-1'},
                    'recipient': {'id': 'page-1'},
                    'timestamp': 1700000000000,
                    'message': {'mid': 'message-1', 'text': 'Hello'},
                }],
            }],
        }

        events = record_webhook_events(payload)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, 'messages')
        self.assertEqual(events[0].external_id, 'message-1')
