import requests
from bs4 import BeautifulSoup

from crm.integrations.utils import extract_contacts_from_text, normalize_url, get_or_create_source
from crm.models import Lead


def build_lead_summary(title, url, emails, phones):
    summary = {
        'url': url,
        'title': title,
        'emails': emails,
        'phones': phones,
    }
    return summary


def scrape_contacts_from_url(url):
    normalized = normalize_url(url)
    response = requests.get(normalized, timeout=15, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; A2ZCRM/1.0; +https://example.com)'
    })
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.string.strip() if soup.title and soup.title.string else 'Web Scraped Lead'
    text = soup.get_text(separator=' ', strip=True)
    emails, phones = extract_contacts_from_text(text)
    return normalized, title, emails, phones


def create_scraped_leads(url, user=None, max_leads=10):
    normalized_url, title, emails, phones = scrape_contacts_from_url(url)
    source = get_or_create_source('other', 'Web Scraper', description='Leads discovered from web scraping')

    created = []
    contact_pairs = []

    for email in emails:
        contact_pairs.append({'email': email, 'phone': phones.pop(0) if phones else 'unknown'})

    for phone in phones:
        contact_pairs.append({'email': '', 'phone': phone})

    if not contact_pairs:
        contact_pairs.append({'email': '', 'phone': phones[0] if phones else 'unknown'})

    for index, contact in enumerate(contact_pairs[:max_leads]):
        external_id = f'web-scrape:{normalized_url}:{contact.get("email") or contact.get("phone") or index}'
        if Lead.objects.filter(external_id=external_id).exists():
            continue

        lead = Lead.objects.create(
            name=title if contact.get('email') else f'Scraped Lead {index + 1}',
            phone=contact.get('phone') or 'unknown',
            email=contact.get('email') or None,
            company=None,
            company_size='',
            industry='',
            service='Web Scraped Lead',
            budget=0,
            message=f'Lead extracted from {normalized_url}',
            source=source,
            source_legacy='other',
            connected_account=None,
            external_id=external_id,
            raw_data=build_lead_summary(title, normalized_url, emails, phones),
        )
        created.append(lead)

    return created
