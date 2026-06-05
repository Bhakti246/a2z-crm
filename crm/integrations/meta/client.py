import requests
from django.conf import settings


class MetaAPIError(Exception):
    pass


class MetaGraphClient:
    def __init__(self, access_token=None, base_url=None, timeout=15):
        self.access_token = access_token
        self.base_url = base_url or settings.META_API_BASE_URL
        self.timeout = timeout

    def _request(self, method, path, **kwargs):
        params = kwargs.pop('params', {}) or {}
        data = kwargs.pop('data', None)

        if self.access_token:
            params.setdefault('access_token', self.access_token)

        url = f"{self.base_url}/{path.lstrip('/')}"
        response = requests.request(
            method,
            url,
            params=params,
            data=data,
            timeout=self.timeout,
            **kwargs,
        )

        try:
            payload = response.json()
        except ValueError:
            payload = {'raw': response.text}

        if response.status_code >= 400 or 'error' in payload:
            error = payload.get('error', payload)
            raise MetaAPIError(str(error))

        return payload

    def get(self, path, params=None):
        return self._request('GET', path, params=params)

    def post(self, path, data=None, params=None):
        return self._request('POST', path, data=data, params=params)

    def exchange_code(self, code):
        return self.get('oauth/access_token', params={
            'client_id': settings.META_OAUTH_CONFIG['client_id'],
            'client_secret': settings.META_OAUTH_CONFIG['client_secret'],
            'redirect_uri': settings.META_OAUTH_CONFIG['redirect_uri'],
            'code': code,
        })

    def exchange_long_lived_token(self, short_lived_token):
        return self.get('oauth/access_token', params={
            'grant_type': 'fb_exchange_token',
            'client_id': settings.META_OAUTH_CONFIG['client_id'],
            'client_secret': settings.META_OAUTH_CONFIG['client_secret'],
            'fb_exchange_token': short_lived_token,
        })

    def debug_token(self, token):
        app_token = f"{settings.META_OAUTH_CONFIG['client_id']}|{settings.META_OAUTH_CONFIG['client_secret']}"
        return self.get('debug_token', params={
            'input_token': token,
            'access_token': app_token,
        })

    def user_profile(self):
        return self.get('me', params={'fields': 'id,name,email'})

    def pages(self):
        return self.get('me/accounts', params={
            'fields': 'id,name,category,access_token,instagram_business_account{id,username,name}'
        }).get('data', [])

    def subscribe_page_to_leadgen(self, page_id, page_access_token):
        client = MetaGraphClient(access_token=page_access_token)
        return client.post(f'{page_id}/subscribed_apps', data={'subscribed_fields': 'leadgen'})

    def lead_details(self, leadgen_id, page_access_token):
        client = MetaGraphClient(access_token=page_access_token)
        return client.get(leadgen_id, params={
            'fields': 'id,created_time,field_data,ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,form_id,platform'
        })

    def send_message(self, recipient_id, text, page_access_token, messaging_type='RESPONSE'):
        client = MetaGraphClient(access_token=page_access_token)
        return client.post('me/messages', data={
            'recipient': {'id': recipient_id},
            'message': {'text': text},
            'messaging_type': messaging_type,
        })
