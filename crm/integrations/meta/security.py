import hashlib
import hmac

from django.conf import settings


def verify_meta_signature(raw_body, signature_header):
    if not signature_header or not signature_header.startswith('sha256='):
        return False

    provided = signature_header.removeprefix('sha256=')
    expected = hmac.new(
        settings.META_OAUTH_CONFIG['client_secret'].encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(provided, expected)


def mask_secret(value, visible=4):
    if not value:
        return ''
    value = str(value)
    if len(value) <= visible:
        return '*' * len(value)
    return f"{value[:visible]}{'*' * 8}"
