from pathlib import Path
from decouple import config
import os
from dotenv import load_dotenv
import dj_database_url

# ============================================================================
# BASE
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# ============================================================================
# INSTALLED APPS
# ============================================================================
INSTALLED_APPS = [
    'unfold',  # Django Unfold Admin - DEVE vir antes do django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Segurança
    'axes',

    # Terceiros
    'django_htmx',

    # Apps do projeto
    'core',
    'account',
    'importacao',
    'quiz',
    'dashboard',
    'usercompany',
    'emails',
]

# ============================================================================
# MIDDLEWARE
# ============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Servir static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'nr1_platform.middleware.SecurityHeadersMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

# ============================================================================
# URLS & WSGI
# ============================================================================
ROOT_URLCONF = 'nr1_platform.urls'
WSGI_APPLICATION = 'nr1_platform.wsgi.application'

# ============================================================================
# TEMPLATES
# ============================================================================
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
                'nr1_platform.context_processors.csp_nonce',
                'core.context_processors.branding_context',
            ],
        },
    },
]

# ============================================================================
# DATABASE
# ============================================================================
DATABASES = {
    'default': dj_database_url.parse(
        os.getenv('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=False
    )
}

# ============================================================================
# PASSWORD VALIDATION
# ============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================================
# INTERNATIONALIZATION
# ============================================================================
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ============================================================================
# STATIC FILES
# ============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise (produção)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================================================
# AUTHENTICAÇÃO
# ============================================================================
LOGIN_URL = 'account:login'
LOGIN_REDIRECT_URL = 'account:dashboard'
LOGOUT_REDIRECT_URL = 'account:login'

# ============================================================================
# EMAIL (Resend)
# ============================================================================
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
RESEND_API_KEY = config('RESEND_API_KEY', default=config('API_RESEND', default=''))
RESEND_FROM_EMAIL = config('RESEND_FROM_EMAIL', default=DEFAULT_FROM_EMAIL)
API_RESEND = RESEND_API_KEY
MAGIC_LINK_EXPIRATION_HOURS = config('MAGIC_LINK_EXPIRATION_HOURS', default=48, cast=int)

# ============================================================================
# SISTEMA
# ============================================================================
SYSTEM_NAME = config('SYSTEM_NAME', default='Vivamente360')
COMPANY_NAME = config('COMPANY_NAME', default='3S Dev')

# ============================================================================
# LOGGING
# ============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
    },
    'handlers': {
        'file': {'level': 'INFO', 'class': 'logging.FileHandler', 'filename': BASE_DIR / 'logs/nr1.log', 'formatter': 'verbose'},
        'console': {'level': 'INFO', 'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'loggers': {
        'nr1': {'handlers': ['file', 'console'], 'level': 'INFO', 'propagate': False},
    },
}

# ============================================================================
# SECURITY HEADERS
# ============================================================================
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)

# ============================================================================
# DJANGO-AXES (Brute force protection)
# ============================================================================
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_ENABLE_ACCESS_FAILURE_LOG = True
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = 'account/locked_out.html'
AXES_USERNAME_FORM_FIELD = 'username'

# ============================================================================
# CACHE - MEMÓRIA LOCAL (SEM REDIS)
# ============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'nr1-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Máximo de 1000 entradas
        }
    }
}

# Cache TTL (timeouts em segundos)
CACHE_TTL = {
    'dashboard_stats': 3600,   # 1 hora
    'dashboard_kpis': 1800,    # 30 minutos
    'user_permissions': 600,   # 10 minutos
}

# ============================================================================
# LGPD - RETENÇÃO DE DADOS
# ============================================================================
DATA_RETENTION_YEARS = config('DATA_RETENTION_YEARS', default=5, cast=int)

# ============================================================================
# CRIPTOGRAFIA
# ============================================================================
FIELD_ENCRYPTION_KEY = config('FIELD_ENCRYPTION_KEY', default=SECRET_KEY)

# ============================================================================
# DEFAULT AUTO FIELD
# ============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# MEDIA FILES (Uploads)
# ============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================================
# DJANGO UNFOLD - ADMIN CUSTOMIZADO
# ============================================================================
from django.templatetags.static import static
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "Admin - Vivamente360",
    "SITE_HEADER": "Vivamente360",
    "SITE_URL": "/",
    "SITE_ICON": {
        "light": lambda request: static("public/icone.png"),
        "dark": lambda request: static("public/icone.png"),
    },
    "SITE_LOGO": {
        "light": lambda request: static("public/icone.png"),
        "dark": lambda request: static("public/icone.png"),
    },
    "SITE_SYMBOL": "settings",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "nr1_platform.utils.environment_callback",
    "DASHBOARD_CALLBACK": "nr1_platform.utils.dashboard_callback",
    "LOGIN": {
        "image": lambda request: static("public/icone.png"),
        "redirect_after": lambda request: reverse_lazy("admin:index"),
    },
    "STYLES": [
        lambda request: static("css/admin-custom.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/admin-custom.js"),
    ],
    "COLORS": {
        "primary": {
            "50": "240 253 244",
            "100": "220 252 231",
            "200": "187 247 208",
            "300": "134 239 172",
            "400": "74 222 128",
            "500": "34 197 94",
            "600": "22 163 74",
            "700": "21 128 61",
            "800": "22 101 52",
            "900": "20 83 45",
            "950": "5 46 22",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Dashboard",
                "separator": True,
                "items": [
                    {
                        "title": "Visão Geral",
                        "icon": "dashboard",
                        "link": lambda request: reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Configurações White Label",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Branding",
                        "icon": "palette",
                        "link": lambda request: reverse_lazy("admin:core_branding_changelist"),
                    },
                ],
            },
            {
                "title": "Gerenciamento",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Empresas",
                        "icon": "business",
                        "link": lambda request: reverse_lazy("admin:core_empresa_changelist"),
                    },
                    {
                        "title": "Usuários",
                        "icon": "person",
                        "link": lambda request: reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": "Perfis de Acesso",
                        "icon": "admin_panel_settings",
                        "link": lambda request: reverse_lazy("admin:account_perfilacesso_changelist"),
                    },
                ],
            },
            {
                "title": "Estrutura Organizacional",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Unidades",
                        "icon": "apartment",
                        "link": lambda request: reverse_lazy("admin:core_unidade_changelist"),
                    },
                    {
                        "title": "Setores",
                        "icon": "workspaces",
                        "link": lambda request: reverse_lazy("admin:core_setor_changelist"),
                    },
                    {
                        "title": "Cargos",
                        "icon": "badge",
                        "link": lambda request: reverse_lazy("admin:core_cargo_changelist"),
                    },
                ],
            },
            {
                "title": "Importação & Dados",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Colaboradores",
                        "icon": "groups",
                        "link": lambda request: reverse_lazy("admin:importacao_colaborador_changelist"),
                    },
                    {
                        "title": "Processos de Importação",
                        "icon": "upload_file",
                        "link": lambda request: reverse_lazy("admin:importacao_processoimportacao_changelist"),
                    },
                ],
            },
            {
                "title": "Questionários NR-1",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Dimensões",
                        "icon": "category",
                        "link": lambda request: reverse_lazy("admin:quiz_dimensao_changelist"),
                    },
                    {
                        "title": "Perguntas",
                        "icon": "quiz",
                        "link": lambda request: reverse_lazy("admin:quiz_pergunta_changelist"),
                    },
                    {
                        "title": "Magic Links",
                        "icon": "link",
                        "link": lambda request: reverse_lazy("admin:quiz_magiclink_changelist"),
                    },
                    {
                        "title": "Respostas",
                        "icon": "rate_review",
                        "link": lambda request: reverse_lazy("admin:quiz_resposta_changelist"),
                    },
                ],
            },
            {
                "title": "Auditoria & LGPD",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Logs de Auditoria",
                        "icon": "history",
                        "link": lambda request: reverse_lazy("admin:core_auditlog_changelist"),
                    },
                    {
                        "title": "Solicitações LGPD",
                        "icon": "security",
                        "link": lambda request: reverse_lazy("admin:core_solicitacaolgpd_changelist"),
                    },
                    {
                        "title": "Tokens de Senha",
                        "icon": "key",
                        "link": lambda request: reverse_lazy("admin:account_passwordresettoken_changelist"),
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": [
                "core.empresa",
            ],
            "items": [
                {
                    "title": "Informações Básicas",
                    "link": lambda context: reverse_lazy(
                        "admin:core_empresa_change",
                        args=[context["object_id"]],
                    ),
                },
                {
                    "title": "Unidades",
                    "link": lambda context: reverse_lazy(
                        "admin:core_unidade_changelist",
                    ) + f"?empresa__id__exact={context['object_id']}",
                },
            ],
        },
    ],
}
