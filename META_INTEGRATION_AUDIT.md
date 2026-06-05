# Meta/Facebook/Instagram Integration Audit

Audit date: June 6, 2026

## Executive Summary

The project is not ready for a real Meta/Facebook/Instagram production integration immediately after deployment.

The Django foundation contains Meta-related models, source labels, settings, and one webhook endpoint at `/webhook/`, but the actual production flows are incomplete:

- No implemented Meta OAuth connect or callback URLs.
- No exchange of authorization codes for user/page tokens.
- No Page subscription flow for `leadgen` or messaging events.
- No retrieval of lead form answers from Graph API using `leadgen_id`.
- No Meta webhook signature validation.
- No Instagram DM event parsing or reply/send logic.
- No production app/domain/redirect configuration beyond a hardcoded Render host in `ALLOWED_HOSTS`.

The current webhook can verify a static token and create a placeholder lead from any POST body. That can be useful for a smoke test, but it will not correctly ingest real Meta Lead Ads or Instagram DM data in production.

## Local Code Findings

| Area | Current state | Deployment readiness |
|---|---|---|
| Meta settings | `META_CLIENT_ID`, `META_CLIENT_SECRET`, `META_REDIRECT_URI`, and scopes are declared in `myproject/settings.py`. | Not enough by itself; no live OAuth views use this config. |
| Webhook verification | `/webhook/` accepts `hub.mode=subscribe`, `hub.verify_token`, and `hub.challenge`. | Can verify only if Meta is configured with the same token, but code currently compares against hardcoded `a2zcrm123`, not `settings.WEBHOOK_VERIFY_TOKEN`. |
| Webhook POST | Parses JSON and creates a dummy lead named `Facebook Lead`. | Not production-ready; does not verify `X-Hub-Signature-256`, parse `entry[].changes[]`, fetch lead details, deduplicate, or map fields. |
| OAuth | Roadmap snippets exist in `NEXT_STEPS.md`. | Not implemented in `crm/urls.py` or live views. |
| Connected account storage | `ConnectedAccount` model has token and permissions fields. | Storage exists, but no code populates it from Meta. Tokens are not encrypted. |
| Instagram DM | Source choices exist for `instagram_dms`; settings request `instagram_manage_messages`. | No DM webhook parser, no Page/IG account resolution, no message send/reply code. |
| Route mismatch | Docs mention `/webhook/meta/`; live route is `/webhook/`. | Meta callback must use the deployed live route unless code is changed later. |

Important code references:

- `myproject/settings.py:193` defines `META_OAUTH_CONFIG`.
- `myproject/settings.py:194-196` read `META_CLIENT_ID`, `META_CLIENT_SECRET`, and `META_REDIRECT_URI`.
- `myproject/settings.py:209` defines `WEBHOOK_VERIFY_TOKEN` with default `a2zcrm123`.
- `crm/urls.py:42` exposes the live Meta webhook at `/webhook/`.
- `crm/models.py:98` defines `ConnectedAccount`.
- `crm/models.py:126` stores `access_token` in plain text.
- `crm/models.py:134` stores granted permissions.

## Integration-by-Integration Answers

### 1. Facebook Lead Ads

#### Will it work immediately after deployment?

No. Meta may be able to verify the callback if the public URL is configured correctly and the verify token is `a2zcrm123`, but real lead ingestion will not work correctly.

Current POST behavior creates a placeholder lead and stores the raw request as a string in `message`. Real Lead Ads webhooks send a `leadgen_id`; the CRM must then call Graph API to retrieve form field data and map it to `name`, `phone`, `email`, `service`, etc.

#### Missing environment variables

Required or strongly recommended:

- `META_CLIENT_ID`: Meta App ID.
- `META_CLIENT_SECRET`: Meta App Secret.
- `META_REDIRECT_URI`: production OAuth callback URL. The currently documented default is local-only.
- `META_APP_ACCESS_TOKEN`: present in `.env.example`, but not used by current code.
- `WEBHOOK_VERIFY_TOKEN`: must be changed from the default and the code must use it.
- `ALLOWED_HOST`: production hostname if it differs from `a2z-crm-1.onrender.com`.
- `DEBUG=False`.
- `SECURE_SSL_REDIRECT=True`.
- `SESSION_COOKIE_SECURE=True`.
- `CSRF_COOKIE_SECURE=True`.

Missing from settings/code but needed for a robust production integration:

- `META_GRAPH_API_VERSION`, for example `v24.0`.
- `META_PAGE_ID`, if a single Page is managed by the deployment.
- Secure storage/encryption key for OAuth tokens if tokens remain in the database.
- Background worker/scheduler settings if polling is added as a fallback to webhooks.

#### Meta App settings required

Configure in Meta for Developers:

- App type/use case that supports Lead Ads and/or business integrations.
- Basic settings:
  - App Domains: `a2z-crm-1.onrender.com` or the final custom domain.
  - Privacy Policy URL.
  - Terms of Service URL, recommended and often required for review.
  - User Data Deletion URL or data deletion instructions.
  - Business verification for production review where required.
- Products/use cases:
  - Facebook Login for Business or Facebook Login.
  - Webhooks.
  - Marketing API / Lead Ads capability as needed.
- Login settings:
  - Client OAuth Login enabled.
  - Web OAuth Login enabled.
  - Strict Mode for redirect URIs enabled.
  - Valid OAuth Redirect URI exactly matching the production callback.
- Webhooks:
  - Page object subscription.
  - Callback URL.
  - Verify token.
  - Subscribe to `leadgen`.

#### Facebook Page permissions required

For Lead Ads retrieval and Page subscription, the connecting user/Page generally needs:

- Admin or equivalent Facebook access to the Page.
- Permission to advertise/manage leads for the Page and related ad account.
- Lead Access Manager access if enabled in Business Suite.
- Page access token or user token flow with the required scopes.

Typical Meta permissions/features to request for this project:

- `leads_retrieval`: retrieve submitted Lead Ads data.
- `pages_show_list`: list Pages the user can manage.
- `pages_read_engagement`: read Page metadata/engagement needed by Page flows.
- `pages_manage_metadata`: subscribe/unsubscribe Page webhooks.
- `pages_manage_ads` or `ads_management`: often required when managing/retrieving lead/ad objects depending on the exact API flow.
- `ads_read`: required if the CRM later reads campaign/ad/adset metadata.
- `business_management`: only if managing business assets across Business Manager; avoid requesting unless the app truly uses it.

#### Instagram Business Account requirements

Instagram Lead Ads are still associated with a Facebook Page/Meta ad account setup. For Instagram placement lead forms:

- The Instagram professional account should be connected to a Facebook Page.
- The ad/instant form must be attached to the Page/IG account managed by the business.
- The user authorizing the app must have sufficient business/Page access.
- Lead Access Manager must grant the app/user access where enabled.

#### Webhook configuration required

Production callback:

```text
https://a2z-crm-1.onrender.com/webhook/
```

Configure:

- Object: Page.
- Field: `leadgen`.
- Verify token: the production `WEBHOOK_VERIFY_TOKEN`.
- Callback must return `hub.challenge` on GET verification.
- POST handler must validate `X-Hub-Signature-256` using the Meta App Secret.
- The app must be subscribed to each Page using `/{page-id}/subscribed_apps` with `subscribed_fields=leadgen`.

The current code is missing the POST signature check and Page subscription workflow.

#### Domains, redirect URIs, callback URLs

If keeping current routes:

- App Domain: `a2z-crm-1.onrender.com`.
- Webhook callback URL: `https://a2z-crm-1.onrender.com/webhook/`.
- OAuth redirect URI currently intended by settings/docs: `https://a2z-crm-1.onrender.com/integrations/meta/callback/`.

But `/integrations/meta/callback/` is not implemented, so this redirect URI will fail until code is added.

#### Features requiring App Review

For use by real users/pages outside app roles, expect App Review and Advanced Access for:

- `leads_retrieval`.
- `pages_show_list`.
- `pages_read_engagement`.
- `pages_manage_metadata`.
- `pages_manage_ads` / `ads_management` if used.
- `ads_read` if used.
- Business verification and data handling evidence may be required depending on access level and use case.

#### Features only working in Development Mode

In Development Mode:

- Only app admins, developers, testers, and assets they can access are usable.
- Test Page/test user flows can verify basic OAuth/webhook behavior.
- Real customer Pages and non-role users cannot use the integration.
- Lead Ads Testing Tool can test delivery, but it may not represent all real ad metadata.

#### Production configuration still missing

- Real OAuth connect/callback implementation.
- Token exchange and long-lived token handling.
- Page token retrieval.
- Page subscription endpoint/call.
- Signature verification.
- Lead details retrieval from Graph API.
- Field mapping and validation.
- Duplicate detection by `leadgen_id`/external ID.
- Error logging and retry strategy.
- App Review submission materials.
- Token encryption.

### 2. Instagram Lead Ads

#### Will it work immediately after deployment?

No. Instagram Lead Ads use the same Lead Ads retrieval and `leadgen` webhook model, but the current system does not complete the required Facebook Page, ad account, or token setup.

#### Missing environment variables

Same as Facebook Lead Ads:

- `META_CLIENT_ID`.
- `META_CLIENT_SECRET`.
- `META_REDIRECT_URI`.
- `WEBHOOK_VERIFY_TOKEN`.
- Production security variables.

Potentially needed later:

- `META_GRAPH_API_VERSION`.
- `META_PAGE_ID` or connected Page identifiers stored via OAuth.

#### Meta App settings required

Same Lead Ads setup as Facebook Lead Ads:

- App domain.
- Facebook Login/Login for Business.
- Webhooks Page object with `leadgen`.
- Valid OAuth redirect URI.
- App Review for requested permissions.

#### Facebook Page permissions required

Same as Facebook Lead Ads, because Instagram Lead Ads are managed through the linked Page/business assets.

#### Instagram Business Account requirements

- Instagram account must be Professional: Business or Creator, depending on the API feature.
- Must be connected to a Facebook Page controlled by the business.
- The Page and ad account must be accessible to the authorizing user.
- Lead Access Manager must permit access to leads.

#### Webhook configuration required

Use the Page `leadgen` subscription:

```text
https://a2z-crm-1.onrender.com/webhook/
```

The webhook payload alone will not include full submitted form answers; the app must fetch lead details using the `leadgen_id`.

#### Domains, redirect URIs, callback URLs

Same as Facebook Lead Ads:

- App Domain: `a2z-crm-1.onrender.com`.
- Webhook: `https://a2z-crm-1.onrender.com/webhook/`.
- OAuth callback after implementation: `https://a2z-crm-1.onrender.com/integrations/meta/callback/`.

#### Features requiring App Review

Same Lead Ads permissions as Facebook Lead Ads, especially `leads_retrieval`.

#### Features only working in Development Mode

Only app-role users/assets are available without review/live production access.

#### Production configuration still missing

Same as Facebook Lead Ads, plus:

- Store and distinguish source as `instagram_ads` when the lead comes from Instagram placements.
- Preserve ad/form/page metadata in `raw_data`.

### 3. Instagram Direct Messages

#### Will it work immediately after deployment?

No. The project has source labels and requests `instagram_manage_messages` in settings, but there is no implemented Instagram Messaging API flow.

#### Missing environment variables

Required:

- `META_CLIENT_ID`.
- `META_CLIENT_SECRET`.
- `META_REDIRECT_URI`.
- `WEBHOOK_VERIFY_TOKEN`.

Likely needed for production:

- `META_GRAPH_API_VERSION`.
- Storage for Page IDs and Instagram Business Account IDs, preferably in `ConnectedAccount.account_metadata`.

#### Meta App settings required

Configure:

- Facebook Login/Login for Business.
- Instagram/Messenger API capability for Instagram messaging.
- Webhooks for Instagram messaging events.
- App domain, privacy policy, terms, data deletion URL.
- App Review submission with a working reviewer account and screencast.

#### Facebook Page permissions required

Common permissions for Instagram DM integrations include:

- `pages_show_list`: list Pages.
- `pages_manage_metadata`: manage Page webhook subscriptions.
- `pages_messaging`: receive/respond to Page/Instagram messaging events where required by the flow.
- `instagram_basic`: read the IG business account/profile connected to the Page.
- `instagram_manage_messages`: manage/read Instagram messages for the connected IG account.

Newer Meta flows may use business-scoped Instagram permissions such as `instagram_business_basic` and `instagram_business_manage_messages`; confirm the exact permission set in the chosen Meta product flow before implementation.

#### Instagram Business Account requirements

- Instagram account must be Professional.
- The Instagram account must be connected to a Facebook Page.
- The authorizing user must have access to that Page and IG account.
- Messaging access must be enabled for the account.
- The app must respect Instagram messaging rules, including allowed response windows and human escalation requirements.

#### Webhook configuration required

Depending on the selected Meta product flow, subscribe to Instagram messaging-related webhook fields such as:

- `messages`.
- `messaging_postbacks`.
- `message_reactions`.
- `messaging_seen`.
- `message_echoes`, if needed.

The current `/webhook/` handler does not parse these events.

#### Domains, redirect URIs, callback URLs

- App Domain: `a2z-crm-1.onrender.com`.
- Webhook callback URL: `https://a2z-crm-1.onrender.com/webhook/`, unless a separate `/webhook/instagram/` route is later added.
- OAuth redirect URI after implementation: `https://a2z-crm-1.onrender.com/integrations/meta/callback/`.

#### Features requiring App Review

Expected review items:

- `instagram_manage_messages` or newer business equivalent.
- `instagram_basic` or newer business equivalent.
- `pages_messaging`.
- `pages_manage_metadata`.
- `pages_show_list`.

Meta will typically require:

- A working end-to-end demo.
- Test credentials.
- A screencast showing exactly how each permission is used.
- Business verification for production-grade messaging access.

#### Features only working in Development Mode

Before approval/live access:

- Messaging works only for app-role accounts and connected test assets.
- Real customers cannot connect arbitrary IG accounts.
- Real inbound messages from non-role users may not be available depending on app mode and access level.

#### Production configuration still missing

- IG account discovery from connected Page.
- Webhook parsing for messaging event shapes.
- Lead creation/mapping from a DM conversation.
- Message send/reply endpoints.
- Conversation storage and compliance logic.
- App Review and Business Verification.

## Immediate Deployment Verdict

| Feature | Immediate production status |
|---|---|
| Webhook URL reachable | Possibly, if deployed at `https://a2z-crm-1.onrender.com/webhook/`. |
| Meta webhook verification | Possibly, only with hardcoded `a2zcrm123`; should be changed. |
| Facebook Lead Ads import | No. |
| Instagram Lead Ads import | No. |
| Instagram DM import | No. |
| OAuth account connection | No. |
| Page subscription | No. |
| App Review ready | No. |

## Required Meta Configuration Summary

Use the final production domain consistently:

```text
Production domain: a2z-crm-1.onrender.com
Webhook callback URL: https://a2z-crm-1.onrender.com/webhook/
OAuth redirect URI: https://a2z-crm-1.onrender.com/integrations/meta/callback/
```

Do not configure `/webhook/meta/` unless code is later changed to expose that route.

## External References

- Meta Lead Ads retrieval: https://developers.facebook.com/docs/marketing-api/guides/lead-ads/retrieving/
- Meta Graph API Webhooks: https://developers.facebook.com/docs/graph-api/webhooks/getting-started/
- Facebook Login manual OAuth flow: https://developers.facebook.com/docs/facebook-login/guides/advanced/manual-flow/
- Instagram Messaging API: https://developers.facebook.com/docs/messenger-platform/instagram/
- Meta permissions reference: https://developers.facebook.com/docs/permissions/
- Meta App Review: https://developers.facebook.com/docs/app-review/
