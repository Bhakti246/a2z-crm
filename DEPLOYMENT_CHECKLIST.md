# Deployment Checklist

Audit date: June 6, 2026

This checklist focuses on deploying the Django app and making Meta/Facebook/Instagram integrations production-ready. The application code for OAuth, Page discovery, encrypted tokens, webhook processing, Lead Ads ingestion, messaging storage, Celery processing, and deployment configuration has now been added; Meta dashboard setup and App Review remain external launch requirements.

## 1. Django Production Baseline

- [ ] Set `DEBUG=False`.
- [ ] Set a strong production `SECRET_KEY`.
- [ ] Confirm `ALLOWED_HOSTS` contains the final domain only, for example `a2z-crm-1.onrender.com` and any custom domain.
- [ ] Set `SECURE_SSL_REDIRECT=True`.
- [ ] Set `SESSION_COOKIE_SECURE=True`.
- [ ] Set `CSRF_COOKIE_SECURE=True`.
- [ ] Configure production database, preferably PostgreSQL instead of SQLite.
- [ ] Run migrations on the production database.
- [ ] Run `collectstatic`.
- [ ] Configure persistent logs or external logging.
- [ ] Configure backups.
- [ ] Confirm the app is reachable over HTTPS.

## 2. Required Production Environment Variables

Set these in the deployment platform:

```env
SECRET_KEY=...
DEBUG=False
ALLOWED_HOST=a2z-crm-1.onrender.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
DJANGO_LOG_LEVEL=INFO

META_CLIENT_ID=...
META_CLIENT_SECRET=...
META_REDIRECT_URI=https://a2z-crm-1.onrender.com/integrations/meta/callback/
META_APP_ACCESS_TOKEN=...
WEBHOOK_VERIFY_TOKEN=...
```

Recommended additions before implementation:

```env
META_GRAPH_API_VERSION=v24.0
```

If polling, async retries, or sync jobs are added:

```env
CELERY_BROKER_URL=...
CELERY_RESULT_BACKEND=...
REDIS_URL=...
```

## 3. Route and URL Decisions

Current deployed webhook route:

```text
https://a2z-crm-1.onrender.com/webhook/
```

Planned but not implemented routes:

```text
https://a2z-crm-1.onrender.com/integrations/meta/connect/
https://a2z-crm-1.onrender.com/integrations/meta/callback/
https://a2z-crm-1.onrender.com/webhook/meta/
```

Before configuring Meta, decide whether to:

- [ ] Keep the current `/webhook/` URL and configure Meta to use it.
- [ ] Or implement `/webhook/meta/` and configure Meta to use that route.
- [ ] Implement the OAuth connect and callback routes before setting `META_REDIRECT_URI` to production.

## 4. Meta App Setup

In Meta for Developers:

- [ ] Create or select the Meta app.
- [ ] Add the final domain in App Domains: `a2z-crm-1.onrender.com`.
- [ ] Add Privacy Policy URL.
- [ ] Add Terms of Service URL.
- [ ] Add User Data Deletion callback/instructions URL.
- [ ] Add business/contact information.
- [ ] Complete Business Verification if required.
- [ ] Add Facebook Login or Facebook Login for Business.
- [ ] Add Webhooks product.
- [ ] Add Marketing API/Lead Ads use case if required by the dashboard flow.
- [ ] Switch to Live mode only after review and production testing are ready.

## 5. OAuth Configuration

- [ ] Enable Client OAuth Login.
- [ ] Enable Web OAuth Login.
- [ ] Enable Strict Mode for Redirect URIs.
- [ ] Add exact Valid OAuth Redirect URI:

```text
https://a2z-crm-1.onrender.com/integrations/meta/callback/
```

- [ ] Confirm the same value is set in `META_REDIRECT_URI`.
- [ ] Implement the Django callback before testing this in production.
- [ ] Store granted permissions in `ConnectedAccount.permissions`.
- [ ] Store Page ID, Page token, IG business account ID, and token expiry metadata.
- [ ] Encrypt access tokens before real production use.

## 6. Facebook Lead Ads Permissions

Request only what the CRM actually uses.

Minimum likely set:

- [ ] `leads_retrieval`.
- [ ] `pages_show_list`.
- [ ] `pages_read_engagement`.
- [ ] `pages_manage_metadata`.

Additional permissions if needed:

- [ ] `pages_manage_ads` or `ads_management`, if retrieving/managing ad objects requires it.
- [ ] `ads_read`, if reading campaign/ad/adset metadata.
- [ ] `business_management`, only if managing Business Manager assets.

Operational Page access:

- [ ] Connecting user has admin/full control or sufficient task access on the Facebook Page.
- [ ] Connecting user can access the relevant ad account.
- [ ] Lead Access Manager grants access to the app/user where enabled.
- [ ] A Page access token is generated and stored.
- [ ] App is subscribed to the Page `leadgen` webhook field.

## 7. Instagram Lead Ads Requirements

- [ ] Instagram account is Professional.
- [ ] Instagram account is connected to the Facebook Page.
- [ ] Page/ad account are accessible to the connecting user.
- [ ] Lead Access Manager permits lead retrieval.
- [ ] `leadgen` Page webhook is configured.
- [ ] CRM maps Instagram placement leads to `instagram_ads` or equivalent source.

## 8. Instagram Direct Messages Requirements

Only needed if the CRM will ingest or respond to Instagram DMs.

- [ ] Instagram account is Professional.
- [ ] Instagram account is connected to a Facebook Page.
- [ ] Messaging access is enabled for the IG account.
- [ ] App has Instagram Messaging capability configured.
- [ ] App has the required permissions, likely including:
  - [ ] `pages_show_list`.
  - [ ] `pages_manage_metadata`.
  - [ ] `pages_messaging`.
  - [ ] `instagram_basic` or newer business equivalent.
  - [ ] `instagram_manage_messages` or newer business equivalent.
- [ ] Webhooks subscribe to required message fields.
- [ ] CRM implements human escalation/compliance behavior.
- [ ] CRM stores conversation/message identifiers if messages become leads.

## 9. Webhook Configuration

In Meta Webhooks:

- [ ] Object: Page.
- [ ] Callback URL: `https://a2z-crm-1.onrender.com/webhook/` unless route changes.
- [ ] Verify token: production `WEBHOOK_VERIFY_TOKEN`.
- [ ] Subscribe to `leadgen` for Lead Ads.
- [ ] Subscribe to Instagram messaging fields only after DM support is implemented.
- [ ] Verify callback over HTTPS.
- [ ] Subscribe each Page to the app via Graph API.
- [ ] Validate `X-Hub-Signature-256` on every POST.
- [ ] Return 200 quickly and process heavy work asynchronously.
- [ ] Log delivery failures.
- [ ] Add retry/idempotency handling using `leadgen_id` or message IDs.

## 10. App Review Checklist

Prepare before submission:

- [ ] Working production or staging URL over HTTPS.
- [ ] Reviewer login credentials.
- [ ] Screencast showing each permission in use.
- [ ] Clear steps to connect a Page/IG account.
- [ ] Demonstration of lead retrieval from a real or test Lead Ad.
- [ ] Demonstration of DM handling if requesting messaging permissions.
- [ ] Explanation of data storage, deletion, and user benefit.
- [ ] Privacy policy mentions lead/contact data and platform data.
- [ ] Data deletion flow is reachable and documented.
- [ ] Business verification completed if required.

Permissions/features likely requiring review:

- [ ] `leads_retrieval`.
- [ ] `pages_show_list`.
- [ ] `pages_read_engagement`.
- [ ] `pages_manage_metadata`.
- [ ] `pages_manage_ads` / `ads_management`.
- [ ] `ads_read`.
- [ ] `business_management`.
- [ ] `pages_messaging`.
- [ ] `instagram_basic` / business equivalent.
- [ ] `instagram_manage_messages` / business equivalent.

## 11. Development Mode Limits

Before Live mode and App Review:

- [ ] Only app roles can authorize the app.
- [ ] Only Pages/IG assets accessible to app roles can be used.
- [ ] Real customer Pages cannot connect.
- [ ] Real customer Instagram DMs cannot be managed.
- [ ] Lead Ads Testing Tool can test basic webhook delivery, but production behavior must still be validated with real assets.

## 12. Code Work Still Required Before Production Meta Launch

Implementation status: completed in code; still requires production credentials and live Meta verification.

- [x] Implement `/integrations/meta/connect/`.
- [x] Implement `/integrations/meta/callback/`.
- [x] Exchange auth code for access token.
- [x] Exchange short-lived token for long-lived user token where applicable.
- [x] Fetch Pages and Page access tokens.
- [x] Store connected Page/IG account in `ConnectedAccount`.
- [x] Subscribe Page to `leadgen`.
- [x] Validate webhook signatures with `META_CLIENT_SECRET`.
- [x] Parse `entry[].changes[]` leadgen events.
- [x] Fetch lead details from Graph API using `leadgen_id`.
- [x] Map lead fields to CRM fields.
- [x] Save `external_id=leadgen_id` and `raw_data`.
- [x] Prevent duplicate leads.
- [x] Create `LeadActivity` records for synced leads.
- [x] Handle token expiry/revocation.
- [x] Add retry and dead-letter handling for failed webhook processing.
- [x] Add integration tests for verification, signature validation, and lead parsing.

## 13. Go/No-Go

Current code status: Go for staging verification.

Production launch status: No-go until Meta App settings, real credentials, webhook subscriptions, App Review/Advanced Access, privacy/data deletion pages, and live asset testing are complete.
