from .settings import *  # noqa: F401,F403

DEBUG = False

SECRET_KEY = require_env('SECRET_KEY')
ALLOWED_HOSTS = [require_env('ALLOWED_HOST')] + env_list('ALLOWED_HOSTS')

SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', True)
SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD', False)

if not os.environ.get('DATABASE_URL'):
    raise RuntimeError('DATABASE_URL is required in production')

for name in ['META_CLIENT_ID', 'META_CLIENT_SECRET', 'META_REDIRECT_URI', 'WEBHOOK_VERIFY_TOKEN']:
    require_env(name)
