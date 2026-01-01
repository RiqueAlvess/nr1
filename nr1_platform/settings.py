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
    'csp',  # django-csp
    'axes',  # django-axes (brute force protection)

    # Apps do projeto
    'core',
    'account',
    'importacao',
    'quiz',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'csp.middleware.CSPMiddleware',  # Content Security Policy
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
API_RESEND = config('API_RESEND')

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

# Content Security Policy (CSP)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Necessário para Django Admin
    "https://cdn.jsdelivr.net",  # Chart.js e bibliotecas
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Necessário para Django Admin e Bootstrap
    "https://cdn.jsdelivr.net",
)
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://cdn.jsdelivr.net")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)  # Equivalente a X-Frame-Options: DENY
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)

# Referrer Policy
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Permissions Policy (Feature-Policy)
PERMISSIONS_POLICY = {
    "geolocation": [],
    "microphone": [],
    "camera": [],
    "payment": [],
    "usb": [],
}

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
AXES_LOCKOUT_CALLABLE = 'axes.lockout.reset_on_success'  # Reset após login bem-sucedido
AXES_ONLY_USER_FAILURES = False  # Rastrear por IP também
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
# CELERY - ASYNC TASKS
# ============================================================================

# Broker e Backend
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')

# Configurações
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Task routing
CELERY_TASK_ROUTES = {
    'quiz.tasks.send_magic_links_async': {'queue': 'emails'},
    'core.tasks.purge_expired_data': {'queue': 'maintenance'},
}

# Rate limiting para tarefas de email (respeitar free tier da API)
CELERY_TASK_ANNOTATIONS = {
    'quiz.tasks.send_magic_links_async': {'rate_limit': '100/h'},  # 100 emails por hora
}

# Retry policy
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Beat schedule (tarefas periódicas)
CELERY_BEAT_SCHEDULE = {
    'purge-expired-data-daily': {
        'task': 'core.tasks.purge_expired_data',
        'schedule': 86400.0,  # 24 horas
    },
}

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