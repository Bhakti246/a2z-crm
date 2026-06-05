# Meta Integration Production Implementation Report

Date: June 6, 2026

## Implemented Code Paths

Core integration files:

- `crm/views_meta.py`: Meta OAuth connect/callback, webhook verification and ingestion, data deletion callback, authenticated send-message endpoint.
- `crm/integrations/meta/client.py`: Meta Graph API client for OAuth token exchange, token debug, profile fetch, Page discovery, Page subscription, lead retrieval, and message send.
- `crm/integrations/meta/processors.py`: Lead Ads and messaging processors, idempotent webhook event creation, lead mapping, duplicate prevention, conversation-to-lead conversion.
- `crm/integrations/meta/security.py`: `X-Hub-Signature-256` validation and secret masking helper.
- `crm/integrations/meta/crypto.py`: Fernet encryption/decryption for tokens at rest.
- `crm/tasks.py`: Celery tasks for async webhook processing and token health checks.
- `crm/urls.py`: Production routes for `/integrations/meta/connect/`, `/integrations/meta/callback/`, `/webhook/`, `/webhook/meta/`, message sending, and Meta data deletion.

Database and admin:

- `crm/models.py`: Added encrypted token fields, token health timestamp, `WebhookEvent`, `MetaConversation`, and `MetaMessage`.
- `crm/migrations/0002_meta_integration_production.py`: Migration for encrypted token fields and Meta integration tables.
- `crm/admin.py`: Added admin screens for webhook events, conversations, and messages; hid raw OAuth token fields.
- `crm/serializers.py`: Added serializers for webhook events, conversations, and messages.

Production platform:

- `myproject/settings.py`: Env helpers, PostgreSQL via `DATABASE_URL`, secure cookie/HTTPS controls, masked logging, Meta config, Celery config, Sentry hook, default big auto fields.
- `myproject/settings_production.py`: Strict production settings module with required env validation.
- `myproject/celery.py` and `myproject/__init__.py`: Celery app bootstrap.
- `Dockerfile`, `.dockerignore`, `render.yaml`: Docker and Render web/worker/beat/PostgreSQL/Redis deployment configuration.
- `.env.example`: Expanded production Meta, Redis, Celery, encryption, and host variables.
- `requirements.txt`: Pinned Django 5.2.8 and added Celery, cryptography, PostgreSQL, Redis, Sentry, and database URL support.

Tests:

- `crm/tests.py`: Added tests for signature validation, webhook verification, webhook event recording/idempotency, token encryption, Lead Ads processing, and messaging event capture.

## Security Controls

- Meta webhook POSTs now require valid `X-Hub-Signature-256` computed with the Meta App Secret.
- OAuth state is generated per session and validated in the callback.
- Meta access tokens are encrypted before storage via `ConnectedAccount.set_access_token()`.
- Raw OAuth tokens are cleared from legacy plaintext fields when set through new code.
- Admin no longer displays token fields.
- Logging masks sensitive key names and legacy raw payload `print()` calls were removed.
- Production settings enforce HTTPS, secure cookies, HSTS, `DEBUG=False`, PostgreSQL, and required Meta env vars.
- Meta data deletion callback is implemented for App Review readiness.

## Runtime Flow

1. User opens `/integrations/meta/connect/`.
2. App redirects to Meta Login with configured scopes and a signed session state.
3. Meta returns to `/integrations/meta/callback/`.
4. App exchanges the code, obtains a long-lived token when available, fetches the user profile, stores encrypted token data, fetches `/me/accounts`, stores Page records, stores Instagram Business metadata, and subscribes Pages to `leadgen`.
5. Meta sends webhooks to `/webhook/` or `/webhook/meta/`.
6. Webhook verification responds synchronously.
7. Webhook POST validates signature, records idempotent `WebhookEvent` rows, queues Celery processing, and returns 200 quickly.
8. Celery fetches lead details by `leadgen_id`, maps field data into `Lead`, stores `raw_data`, prevents duplicates by `external_id`, and creates `LeadActivity`.
9. Messaging webhooks create `MetaConversation` and `MetaMessage` records and create a lead for new inbound conversations.

## Required Meta Dashboard Configuration

- App Domain: production domain, for example `a2z-crm-1.onrender.com`.
- Valid OAuth Redirect URI: `https://a2z-crm-1.onrender.com/integrations/meta/callback/`.
- Webhook callback URL: `https://a2z-crm-1.onrender.com/webhook/` or `/webhook/meta/`.
- Webhook object: Page.
- Lead Ads field: `leadgen`.
- Messaging fields if enabled: `messages`, `message_reactions`, `messaging_seen`.
- Verify token: production `WEBHOOK_VERIFY_TOKEN`.
- Required App Review permissions depend on enabled features, typically `leads_retrieval`, `pages_show_list`, `pages_read_engagement`, `pages_manage_metadata`, `instagram_basic`, `instagram_manage_messages`, and `pages_messaging`.

## Deployment Steps

1. Install dependencies from `requirements.txt`.
2. Set `DJANGO_SETTINGS_MODULE=myproject.settings_production`.
3. Set all required env vars from `.env.example`, including `DATABASE_URL`, Redis/Celery URLs, Meta credentials, `WEBHOOK_VERIFY_TOKEN`, and `META_TOKEN_ENCRYPTION_KEY`.
4. Run `python manage.py migrate`.
5. Run `python manage.py collectstatic --noinput`.
6. Start web: `gunicorn myproject.wsgi:application --bind 0.0.0.0:8000`.
7. Start worker: `celery -A myproject worker --loglevel=INFO`.
8. Start beat: `celery -A myproject beat --loglevel=INFO`.
9. Configure Meta App dashboard URLs and submit App Review materials.

## Verification

Commands run successfully:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test crm -v 1
```

Current test result: 8 tests passing.

## Remaining External Work

The code is implemented, but production use still requires external Meta-side completion:

- Meta App Review and Advanced Access approval.
- Business verification where Meta requires it.
- Real Page/Instagram Business assets connected by an authorized user.
- Production privacy policy, terms, and data deletion URL published.
- Real webhook delivery tests through Meta tools and at least one live Lead Ads flow before customer launch.
