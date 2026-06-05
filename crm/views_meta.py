import base64
import hashlib
import hmac
import json
import secrets
import urllib.parse
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from crm.integrations.meta.client import MetaAPIError, MetaGraphClient
from crm.integrations.meta.processors import record_webhook_events
from crm.integrations.meta.security import verify_meta_signature
from crm.models import ConnectedAccount, MetaConversation, MetaMessage
from crm.tasks import process_meta_webhook_event


@login_required
@require_GET
def meta_connect(request):
    state = secrets.token_urlsafe(32)
    request.session['meta_oauth_state'] = state

    params = {
        'client_id': settings.META_OAUTH_CONFIG['client_id'],
        'redirect_uri': settings.META_OAUTH_CONFIG['redirect_uri'],
        'state': state,
        'scope': ','.join(settings.META_OAUTH_CONFIG['scopes']),
        'response_type': 'code',
    }
    url = f"https://www.facebook.com/{settings.META_GRAPH_API_VERSION}/dialog/oauth?{urllib.parse.urlencode(params)}"
    return redirect(url)


@login_required
@require_GET
def meta_callback(request):
    expected_state = request.session.pop('meta_oauth_state', None)
    received_state = request.GET.get('state')
    if not expected_state or not hmac.compare_digest(expected_state, received_state or ''):
        return JsonResponse({'error': 'Invalid OAuth state'}, status=400)

    if request.GET.get('error'):
        return JsonResponse({
            'error': request.GET.get('error'),
            'error_description': request.GET.get('error_description', ''),
        }, status=400)

    code = request.GET.get('code')
    if not code:
        return JsonResponse({'error': 'Missing authorization code'}, status=400)

    try:
        client = MetaGraphClient()
        token_payload = client.exchange_code(code)
        access_token = token_payload['access_token']

        try:
            long_lived = client.exchange_long_lived_token(access_token)
            access_token = long_lived.get('access_token', access_token)
            expires_in = long_lived.get('expires_in')
        except MetaAPIError:
            expires_in = token_payload.get('expires_in')

        authed_client = MetaGraphClient(access_token=access_token)
        profile = authed_client.user_profile()
        debug = client.debug_token(access_token).get('data', {})
        permissions = [
            item['permission'] for item in debug.get('granular_scopes', [])
            if item.get('permission')
        ] or debug.get('scopes', [])

        token_expires_at = None
        if expires_in:
            token_expires_at = timezone.now() + timedelta(seconds=int(expires_in))
        elif debug.get('expires_at'):
            token_expires_at = timezone.datetime.fromtimestamp(debug['expires_at'], tz=timezone.get_current_timezone())

        account, _ = ConnectedAccount.objects.update_or_create(
            user=request.user,
            account_type='facebook',
            external_id=str(profile['id']),
            defaults={
                'account_name': profile.get('name') or 'Meta User',
                'account_email': profile.get('email') or '',
                'token_expires_at': token_expires_at,
                'status': 'active',
                'permissions': permissions,
                'account_metadata': {'meta_user': profile, 'token_debug': debug},
            },
        )
        account.set_access_token(access_token)
        account.save()

        pages = discover_and_store_pages(request.user, access_token)
        return JsonResponse({'status': 'connected', 'account_id': account.id, 'pages': pages})
    except (KeyError, MetaAPIError, ValueError) as exc:
        return JsonResponse({'error': str(exc)}, status=400)


def discover_and_store_pages(user, user_access_token):
    pages = []
    client = MetaGraphClient(access_token=user_access_token)
    for page in client.pages():
        page_token = page.get('access_token')
        instagram_account = page.get('instagram_business_account') or {}
        metadata = {
            'page_id': page.get('id'),
            'page_category': page.get('category'),
            'instagram_business_account': instagram_account,
        }
        account, _ = ConnectedAccount.objects.update_or_create(
            user=user,
            account_type='facebook',
            external_id=str(page['id']),
            defaults={
                'account_name': page.get('name') or 'Facebook Page',
                'status': 'active',
                'account_metadata': metadata,
                'permissions': settings.META_OAUTH_CONFIG['scopes'],
            },
        )
        account.set_access_token(page_token)
        account.save()

        if page_token:
            client.subscribe_page_to_leadgen(page['id'], page_token)

        pages.append({
            'id': page.get('id'),
            'name': page.get('name'),
            'category': page.get('category'),
            'instagram_business_account': instagram_account,
        })
    return pages


@csrf_exempt
def meta_webhook(request):
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        if mode == 'subscribe' and hmac.compare_digest(token or '', settings.WEBHOOK_VERIFY_TOKEN):
            return HttpResponse(challenge)
        return HttpResponse('Verification failed', status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not verify_meta_signature(request.body, request.headers.get('X-Hub-Signature-256', '')):
        return JsonResponse({'error': 'Invalid signature'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    events = record_webhook_events(payload)
    for event in events:
        process_meta_webhook_event.delay(event.id)

    return JsonResponse({'status': 'accepted', 'events': len(events)})


@csrf_exempt
@require_POST
def meta_data_deletion(request):
    signed_request = request.POST.get('signed_request')
    if not signed_request:
        return JsonResponse({'error': 'Missing signed_request'}, status=400)

    try:
        signature, payload = signed_request.split('.', 1)
        expected = base64.urlsafe_b64encode(
            hmac.new(
                settings.META_OAUTH_CONFIG['client_secret'].encode(),
                payload.encode(),
                hashlib.sha256,
            ).digest()
        ).decode().rstrip('=')
        if not hmac.compare_digest(signature, expected):
            return JsonResponse({'error': 'Invalid signed_request'}, status=403)

        padded = payload + '=' * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
        user_id = str(data.get('user_id') or '')
        ConnectedAccount.objects.filter(external_id=user_id).update(
            status='revoked',
            encrypted_access_token='',
            encrypted_refresh_token='',
            access_token='',
            refresh_token='',
        )
        return JsonResponse({
            'url': request.build_absolute_uri('/privacy/data-deletion/status/'),
            'confirmation_code': hashlib.sha256(user_id.encode()).hexdigest()[:16],
        })
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid signed_request'}, status=400)


@login_required
@require_POST
def send_meta_message(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
        conversation = MetaConversation.objects.get(id=body['conversation_id'])
        text = body['text'].strip()
        account = conversation.connected_account
        if not account or not account.get_access_token():
            return JsonResponse({'error': 'Conversation has no active Page token'}, status=400)

        response = MetaGraphClient().send_message(conversation.sender_id, text, account.get_access_token())
        message_id = response.get('message_id') or response.get('recipient_id') or secrets.token_urlsafe(12)
        MetaMessage.objects.create(
            conversation=conversation,
            message_id=message_id,
            sender_id=conversation.recipient_id,
            recipient_id=conversation.sender_id,
            direction='outbound',
            text=text,
            event_type='manual_reply',
            raw_data=response,
            sent_at=timezone.now(),
        )
        return JsonResponse({'status': 'sent', 'response': response})
    except (KeyError, json.JSONDecodeError, MetaConversation.DoesNotExist, MetaAPIError) as exc:
        return JsonResponse({'error': str(exc)}, status=400)
