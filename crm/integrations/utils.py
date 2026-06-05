import re
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from crm.models import LeadSource


SOURCE_MAPPINGS = {
    'website': ('website', 'Website Form'),
    'website_form': ('website', 'Website Form'),
    'landing_page': ('landing_page', 'Landing Page'),
    'google_forms': ('google_forms', 'Google Forms'),
    'facebook_ads': ('facebook', 'Facebook Lead Ads'),
    'instagram_ads': ('instagram', 'Instagram Ads'),
    'instagram_dms': ('instagram', 'Instagram Direct Messages'),
    'whatsapp': ('whatsapp', 'WhatsApp Inquiry'),
    'google_maps': ('google_maps', 'Google Maps Business'),
    'manual': ('manual', 'Manual Entry'),
    'other': ('other', 'Other Source'),
}


def normalize_source_input(source_value, source_legacy=None):
    if source_value is None or source_value == '':
        source_value = source_legacy or 'manual'

    if isinstance(source_value, int):
        try:
            return LeadSource.objects.get(pk=source_value)
        except LeadSource.DoesNotExist:
            source_value = str(source_value)

    source_value = str(source_value).strip().lower()

    if source_value.isdigit():
        try:
            return LeadSource.objects.get(pk=int(source_value))
        except LeadSource.DoesNotExist:
            pass

    if source_value in SOURCE_MAPPINGS:
        source_type, name = SOURCE_MAPPINGS[source_value]
        return get_or_create_source(source_type, name)

    for key, (source_type, name) in SOURCE_MAPPINGS.items():
        if key in source_value:
            return get_or_create_source(source_type, name)

    if source_value:
        return get_or_create_source('other', source_value.title())

    return get_or_create_source('manual', 'Manual Entry')


def get_or_create_source(source_type, name, description=None):
    defaults = {'description': description or f'Leads from {name}', 'is_active': True}
    if source_type not in [item[0] for item in LeadSource.SOURCE_TYPES]:
        source_type = 'other'
    source, _ = LeadSource.objects.get_or_create(
        source_type=source_type,
        name=name,
        defaults=defaults,
    )
    return source


EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(?:\+\d{1,3}[\s-]?)?(?:\(\d{2,4}\)|\d{2,4})[\s-]?\d{3,4}[\s-]?\d{3,4}')


def is_valid_url(url):
    validator = URLValidator()
    try:
        validator(url)
        return True
    except ValidationError:
        return False


def normalize_phone(phone):
    cleaned = re.sub(r'[^\d+]', '', phone)
    return cleaned if len(cleaned) >= 7 else ''


def extract_contacts_from_text(text):
    emails = set(EMAIL_REGEX.findall(text or ''))
    phones = set(normalize_phone(match) for match in PHONE_REGEX.findall(text or ''))
    phones = {phone for phone in phones if phone}
    return list(emails), list(phones)


def normalize_url(raw_url):
    if not raw_url:
        return ''
    raw_url = raw_url.strip()
    if raw_url.startswith('//'):
        raw_url = 'https:' + raw_url
    if not raw_url.startswith(('http://', 'https://')):
        raw_url = 'https://' + raw_url
    return raw_url
