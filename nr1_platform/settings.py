from pathlib import Path
from decouple import config
import os
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Security
    'axes',  # django-axes (brute force protection)

    # Third-party
    'django_htmx',  # HTMX integration

    # Apps do projeto
    'core',
    'account',
    'importacao',
    'quiz',
    'dashboard',
    'usercompany',
    'emails',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'nr1_platform.middleware.SecurityHeadersMiddleware',  # Content Security Policy customizado
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_htmx.middleware.HtmxMiddleware',  # HTMX middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',  # Brute force protection (must be last)
]

ROOT_URLCONF = 'nr1_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'nr1_platform.context_processors.csp_nonce',  # Nonce CSP
            ],
        },
    },
]

WSGI_APPLICATION = 'nr1_platform.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.parse(
        os.getenv('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=False
    )
}

# Password validation (LGPD - Política de Senhas Reforçada)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}  # Mínimo 12 caracteres
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login
LOGIN_URL = 'account:login'
LOGIN_REDIRECT_URL = 'account:dashboard'
LOGOUT_REDIRECT_URL = 'account:login'

# Email (Resend API)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
# Configurações Resend - Usar biblioteca oficial resend
RESEND_API_KEY = config('RESEND_API_KEY', default=config('API_RESEND', default=''))
RESEND_FROM_EMAIL = config('RESEND_FROM_EMAIL', default=DEFAULT_FROM_EMAIL)
# Manter API_RESEND para compatibilidade com código legacy
API_RESEND = RESEND_API_KEY

# Magic Link
MAGIC_LINK_EXPIRATION_HOURS = config('MAGIC_LINK_EXPIRATION_HOURS', default=48, cast=int)

# K-Anonymity - Mínimo de respondentes para exibir dados (1 = sempre exibir)
MIN_GROUP_SIZE = config('MIN_GROUP_SIZE', default=1, cast=int)

# Sistema
SYSTEM_NAME = config('SYSTEM_NAME', default='Vivamente360')
COMPANY_NAME = config('COMPANY_NAME', default='3S Dev')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'nr1.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'nr1': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================================
# SEGURANÇA - HTTP HEADERS
# ============================================================================

# SecurityMiddleware - Headers de Segurança HTTP
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# HSTS (HTTP Strict Transport Security)
# Em produção, configurar SECURE_SSL_REDIRECT = True no .env
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configurações SSL (ativar em produção via .env)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)

# Content Security Policy (CSP) - Implementado via middleware customizado
# As configurações CSP estão em nr1_platform/middleware.py (SecurityHeadersMiddleware)
# Para usar nonce em templates: <script nonce="{{ csp_nonce }}">código</script>

# Referrer Policy e Permissions Policy - Implementados via middleware customizado
# As configurações estão em nr1_platform/middleware.py (SecurityHeadersMiddleware)

# ============================================================================
# SEGURANÇA - BRUTE FORCE PROTECTION (django-axes)
# ============================================================================

# Backend de autenticação do django-axes
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # Axes backend (primeiro)
    'django.contrib.auth.backends.ModelBackend',
]

# Configurações do django-axes
AXES_FAILURE_LIMIT = 5  # Bloquear após 5 tentativas falhas
AXES_COOLOFF_TIME = 1  # Cooldown de 1 hora
AXES_ENABLE_ACCESS_FAILURE_LOG = True  # Log de tentativas
AXES_RESET_ON_SUCCESS = True  # Reset contador após login bem-sucedido
AXES_LOCKOUT_TEMPLATE = 'account/locked_out.html'  # Template customizado
AXES_USERNAME_FORM_FIELD = 'username'  # Campo de usuário no form

# ============================================================================
# CACHE - REDIS
# ============================================================================

REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'nr1',
        'TIMEOUT': 300,  # 5 minutos (padrão)
    }
}

# Timeout específicos por tipo de cache
CACHE_TTL = {
    'dashboard_stats': 3600,  # 1 hora
    'dashboard_kpis': 1800,   # 30 minutos
    'user_permissions': 600,  # 10 minutos
}

# ============================================================================
# CELERY - ASYNC TASKS (DESABILITADO - Envio de e-mails é síncrono)
# ============================================================================
# NOTA: Celery/Redis foram removidos para simplificar o envio de e-mails.
# Os e-mails agora são enviados de forma síncrona diretamente do backend.
# Se necessário reativar o Celery no futuro, descomente as linhas abaixo.

# # Broker e Backend
# CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
# CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')

# # Configurações
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = TIME_ZONE
# CELERY_ENABLE_UTC = True

# # Task routing
# CELERY_TASK_ROUTES = {
#     'quiz.tasks.send_magic_links_async': {'queue': 'emails'},
#     'emails.tasks.send_email_task': {'queue': 'emails'},
#     'usercompany.tasks.atualizar_contador_notificacoes_empresa_task': {'queue': 'default'},
#     'core.tasks.purge_expired_data': {'queue': 'maintenance'},
# }

# # Rate limiting configurável via env (padrão: 100 emails por hora)
# SEND_RATE_LIMIT = config('SEND_RATE_LIMIT', default='100/h')

# # Rate limiting para tarefas de email (respeitar free tier da API)
# CELERY_TASK_ANNOTATIONS = {
#     'quiz.tasks.send_magic_links_async': {'rate_limit': '100/h'},  # 100 emails por hora
#     'emails.tasks.send_email_task': {'rate_limit': SEND_RATE_LIMIT},  # Rate limit configurável
# }

# # Retry policy
# CELERY_TASK_ACKS_LATE = True
# CELERY_TASK_REJECT_ON_WORKER_LOST = True

# # Beat schedule (tarefas periódicas)
# CELERY_BEAT_SCHEDULE = {
#     'purge-expired-data-daily': {
#         'task': 'core.tasks.purge_expired_data',
#         'schedule': 86400.0,  # 24 horas
#     },
# }

# ============================================================================
# LGPD - RETENÇÃO DE DADOS
# ============================================================================

# Política de retenção padrão (em anos)
DATA_RETENTION_YEARS = config('DATA_RETENTION_YEARS', default=5, cast=int)

# ============================================================================
# CRIPTOGRAFIA - DJANGO ENCRYPTED MODEL FIELDS
# ============================================================================

# Chave de criptografia para campos sensíveis (PII)
# IMPORTANTE: Usar uma chave diferente do SECRET_KEY
# Gerar com: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
FIELD_ENCRYPTION_KEY = config('FIELD_ENCRYPTION_KEY', default=SECRET_KEY)