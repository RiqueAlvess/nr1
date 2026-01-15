# Melhorias de Segurança, LGPD e Performance - NR1 Platform

Este documento detalha todas as melhorias implementadas no projeto Django NR1 Platform para conformidade com LGPD, segurança e performance.

## 📋 Índice

- [1. Segurança](#1-segurança)
- [2. LGPD](#2-lgpd)
- [3. Performance](#3-performance)
- [4. Instalação e Configuração](#4-instalação-e-configuração)
- [5. Execução](#5-execução)

---

## 1. Segurança

### 1.1 Headers de Segurança HTTP

**Implementado em:** `nr1_platform/settings.py`

#### Content Security Policy (CSP)
```python
# django-csp configurado com:
- CSP_DEFAULT_SRC: 'self'
- CSP_SCRIPT_SRC: 'self', 'unsafe-inline', CDN permitidos
- CSP_STYLE_SRC: 'self', 'unsafe-inline', CDN permitidos
- CSP_FRAME_ANCESTORS: 'none' (proteção contra clickjacking)
```

#### HSTS (HTTP Strict Transport Security)
```python
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

#### Outros Headers
```python
SECURE_CONTENT_TYPE_NOSNIFF = True  # X-Content-Type-Options
SECURE_BROWSER_XSS_FILTER = True     # X-XSS-Protection
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
PERMISSIONS_POLICY = {...}           # Feature-Policy
```

---

### 1.2 Rate Limiting e Proteção Brute Force

**Implementado com:** `django-ratelimit` e `django-axes`

#### django-axes (Brute Force Protection)
```python
AXES_FAILURE_LIMIT = 5                # Bloquear após 5 tentativas falhas
AXES_COOLOFF_TIME = 1                 # Cooldown de 1 hora
AXES_LOCKOUT_TEMPLATE = 'account/locked_out.html'
```

**Template:** `templates/account/locked_out.html` ✅

#### Rate Limiting por View

| Endpoint | Limite | Método |
|----------|--------|--------|
| `/account/login/` | 10/hora por IP | POST |
| `/account/password-reset/` | 3/hora por IP | POST |
| `/account/password-reset/confirm/<token>/` | 10/hora por IP | POST |
| `/quiz/enviar/` | 5/hora por usuário | POST |
| `/quiz/r/<token>/` | 30/min por IP | GET |
| `/quiz/r/<token>/submit/` | 10/hora por IP | POST |
| `/importacao/upload/` | 5/hora por usuário | POST |

**Arquivos modificados:**
- `account/views.py`
- `quiz/views.py`
- `importacao/views.py`

---

### 1.3 Páginas de Erro Customizadas

**Implementado:**
- `templates/errors/404.html` - Página não encontrada
- `templates/errors/500.html` - Erro interno do servidor
- `nr1_platform/views.py` - Handlers customizados

**Configuração em:** `nr1_platform/urls.py`
```python
handler404 = 'nr1_platform.views.handler404'
handler500 = 'nr1_platform.views.handler500'
```

---

### 1.4 Validação de Input

#### Upload de CSV
**Arquivo:** `importacao/views.py`

Validações implementadas:
- ✅ Tipo de arquivo: apenas `.csv`
- ✅ Tamanho máximo: 10MB
- ✅ Validação de email via `validate_email()`
- ✅ Rate limiting: 5 uploads/hora por usuário

---

## 2. LGPD

### 2.1 Consentimento Explícito

**Model:** `quiz/models.py` → `ConsentimentoLGPD`

```python
class ConsentimentoLGPD(TimeStampedModel):
    resposta = OneToOneField(Resposta)
    aceito = BooleanField(default=False)
    data_consentimento = DateTimeField(auto_now_add=True)
    versao_termo = CharField(max_length=10, default='1.0')
    texto_termo = TextField(blank=True)
    ip_address = GenericIPAddressField()
    user_agent = CharField(max_length=500)
```

**Migração necessária:** Sim ✅

---

### 2.2 Direitos do Titular (Art. 18)

**Model:** `core/models.py` → `SolicitacaoLGPD`

```python
class SolicitacaoLGPD(TimeStampedModel):
    TIPO_CHOICES = [
        ('ACESSO', 'Solicitação de Acesso aos Dados'),
        ('CORRECAO', 'Solicitação de Correção de Dados'),
        ('EXCLUSAO', 'Solicitação de Exclusão de Dados'),
        ('PORTABILIDADE', 'Solicitação de Portabilidade de Dados'),
        ('REVOGACAO', 'Revogação de Consentimento'),
        ('OPOSICAO', 'Oposição ao Tratamento'),
    ]

    email = EmailField()
    tipo = CharField(max_length=20, choices=TIPO_CHOICES)
    status = CharField(max_length=20, choices=STATUS_CHOICES)
    protocolo = CharField(max_length=20, unique=True)  # Auto-gerado
```

**Features:**
- ✅ Protocolo único auto-gerado (formato: `LGPDxxxxxxxxxxxx`)
- ✅ Rastreamento de status (ABERTA, EM_ANALISE, CONCLUIDA, CANCELADA)
- ✅ Resposta registrada
- ✅ Auditoria completa (IP, User Agent, timestamps)

**Migração necessária:** Sim ✅

---

### 2.3 Criptografia At-Rest (PII)

**Biblioteca:** `django-encrypted-model-fields`

**Model:** `importacao/models.py` → `Colaborador`

```python
from encrypted_model_fields.fields import EncryptedEmailField

class Colaborador(TimeStampedModel):
    # Antes:
    # email = EmailField(unique=True, db_index=True)

    # Depois:
    email = EncryptedEmailField()  # Campo criptografado com Fernet
```

**Configuração em:** `nr1_platform/settings.py`
```python
FIELD_ENCRYPTION_KEY = config('FIELD_ENCRYPTION_KEY', default=SECRET_KEY)
```

**⚠️ IMPORTANTE:**
- Gerar chave separada do `SECRET_KEY`
- Comando: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- Adicionar ao `.env` como `FIELD_ENCRYPTION_KEY`

**Migração necessária:** Sim ✅
**Nota:** Dados existentes precisarão ser migrados manualmente ou via data migration.

---

### 2.4 Retenção e Purge de Dados

#### Management Command
**Arquivo:** `core/management/commands/purge_expired_data.py`

**Execução manual:**
```bash
python manage.py purge_expired_data               # Executar purge
python manage.py purge_expired_data --dry-run    # Simular sem deletar
```

**Dados removidos:**
1. **Colaboradores** com `data_expiracao < hoje` e `ativo=False`
2. **PasswordResetToken** expirados há mais de 90 dias
3. **MagicLink** expirados há mais de 1 ano
4. **AuditLog** mais antigos que `DATA_RETENTION_YEARS` (padrão: 5 anos)

#### Celery Task Automática
**Arquivo:** `core/tasks.py` → `purge_expired_data()`

**Schedule:** Diário (configurado no `CELERY_BEAT_SCHEDULE`)

```python
CELERY_BEAT_SCHEDULE = {
    'purge-expired-data-daily': {
        'task': 'core.tasks.purge_expired_data',
        'schedule': 86400.0,  # 24 horas
    },
}
```

#### Campo de Expiração
**Model:** `importacao/models.py` → `Colaborador`

```python
data_expiracao = DateField(
    null=True,
    blank=True,
    help_text='Data de expiração dos dados (política de retenção LGPD)'
)
```

**Migração necessária:** Sim ✅

---

### 2.5 Política de Senhas Reforçada

**Arquivo:** `nr1_platform/settings.py`

```python
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}  # Mínimo 12 caracteres
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

**Nota:** Compatível com usuários existentes (não força reset).

---

## 3. Performance

### 3.1 Processamento Assíncrono (Celery)

#### Configuração
**Arquivo:** `nr1_platform/celery.py` (novo)
**Inicialização:** `nr1_platform/__init__.py`

```python
# Broker e Backend
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

# Task Routing
CELERY_TASK_ROUTES = {
    'quiz.tasks.send_magic_links_async': {'queue': 'emails'},
    'core.tasks.purge_expired_data': {'queue': 'maintenance'},
}

# Rate Limiting
CELERY_TASK_ANNOTATIONS = {
    'quiz.tasks.send_magic_links_async': {'rate_limit': '100/h'},
}
```

#### Task: Envio de Magic Links
**Arquivo:** `quiz/tasks.py` → `send_magic_links_async()`

**Features:**
- ✅ Envio assíncrono em background
- ✅ Rate limiting: 100 emails/hora (respeita free tier Resend API)
- ✅ Delay de 36 segundos entre cada email
- ✅ Retry automático (max 3 tentativas)
- ✅ Logging completo

**View atualizada:** `quiz/views.py` → `enviar_links_view()`

```python
# Antes:
enviados, erros = MagicLinkService.enviar_magic_links_bulk(...)

# Depois:
from quiz.tasks import send_magic_links_async
send_magic_links_async.delay(colaboradores_ids, base_url)
```

**Impacto:** Resposta HTTP imediata + envio em background.

---

### 3.2 Cache Redis

#### Configuração
**Arquivo:** `nr1_platform/settings.py`

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'nr1',
        'TIMEOUT': 300,  # 5 minutos (padrão)
    }
}

# Timeouts específicos
CACHE_TTL = {
    'dashboard_stats': 3600,  # 1 hora
    'dashboard_kpis': 1800,   # 30 minutos
    'user_permissions': 600,  # 10 minutos
}
```

#### Uso Recomendado

**Exemplo:** Cache de estatísticas do dashboard

```python
from django.core.cache import cache
from django.conf import settings

def get_dashboard_stats(empresa_id):
    cache_key = f'dashboard_stats_{empresa_id}'
    stats = cache.get(cache_key)

    if stats is None:
        stats = calculate_complex_stats(empresa_id)
        timeout = settings.CACHE_TTL['dashboard_stats']
        cache.set(cache_key, stats, timeout)

    return stats
```

**Invalidação:** Usar signals para invalidar cache após nova resposta

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from quiz.models import Resposta

@receiver(post_save, sender=Resposta)
def invalidate_dashboard_cache(sender, instance, **kwargs):
    empresa_id = instance.magic_link.colaborador.empresa.id
    cache.delete(f'dashboard_stats_{empresa_id}')
```

---

## 4. Instalação e Configuração

### 4.1 Instalar Dependências

```bash
pip install -r requirements.txt
```

**Novas dependências:**
- `django-csp==3.8`
- `django-ratelimit==4.1.0`
- `django-axes==6.9.0`
- `bleach==6.2.0`
- `django-encrypted-model-fields==0.6.5`
- `cryptography==44.0.0`
- `celery==5.4.0`
- `redis==5.2.1`
- `django-redis==5.4.0`

---

### 4.2 Configurar Variáveis de Ambiente

**Arquivo:** `.env` (usar `.env.example` como referência)

```bash
# Novas variáveis obrigatórias:
REDIS_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
DATA_RETENTION_YEARS=5

# IMPORTANTE: Gerar chave de criptografia separada
FIELD_ENCRYPTION_KEY=<gerar com Fernet>

# Opcionais (produção):
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

### 4.3 Executar Migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

**Novas migrações:**
1. `quiz` - `ConsentimentoLGPD`
2. `core` - `SolicitacaoLGPD`
3. `importacao` - Campo `email` criptografado + `data_expiracao`

---

### 4.4 Instalar Redis

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**MacOS:**
```bash
brew install redis
brew services start redis
```

**Verificar:**
```bash
redis-cli ping  # Deve retornar "PONG"
```

---

## 5. Execução

### 5.1 Executar o Servidor Django

```bash
python manage.py runserver
```

---

### 5.2 Executar o Celery Worker

```bash
celery -A nr1_platform worker --loglevel=info
```

**Com queues específicas:**
```bash
celery -A nr1_platform worker -Q emails,maintenance --loglevel=info
```

---

### 5.3 Executar o Celery Beat (Scheduler)

```bash
celery -A nr1_platform beat --loglevel=info
```

**Nota:** Necessário para executar o purge automático diário.

---

### 5.4 Executar Tudo em Produção (Supervisor/Systemd)

**Exemplo com Supervisor:**

```ini
[program:nr1_web]
command=/path/to/venv/bin/gunicorn nr1_platform.wsgi:application
directory=/path/to/nr1
user=www-data
autostart=true
autorestart=true

[program:nr1_celery]
command=/path/to/venv/bin/celery -A nr1_platform worker --loglevel=info
directory=/path/to/nr1
user=www-data
autostart=true
autorestart=true

[program:nr1_celery_beat]
command=/path/to/venv/bin/celery -A nr1_platform beat --loglevel=info
directory=/path/to/nr1
user=www-data
autostart=true
autorestart=true
```

---

## 📊 Resumo das Melhorias

### ✅ Segurança
- [x] Headers de segurança HTTP (CSP, HSTS, etc.)
- [x] Rate limiting em endpoints críticos
- [x] Proteção brute force (django-axes)
- [x] Páginas de erro customizadas
- [x] Validação rigorosa de uploads
- [x] Política de senhas reforçada (12 caracteres)

### ✅ LGPD
- [x] Model de consentimento explícito
- [x] Model de solicitações LGPD (Art. 18)
- [x] Criptografia at-rest para PII
- [x] Management command para purge de dados
- [x] Política de retenção configurável
- [x] Auditoria completa de consentimentos

### ✅ Performance
- [x] Celery configurado para tarefas assíncronas
- [x] Envio de magic links em background
- [x] Redis configurado para cache
- [x] Purge automático diário
- [x] Rate limiting de tasks (respeita API limits)

---

## 🚀 Próximos Passos (Opcional)

### Performance Adicional
- [ ] Implementar cache nas views de dashboard
- [ ] Criar signals para invalidação de cache
- [ ] Pré-cálculo de estatísticas (triggered by signals)

### LGPD Adicional
- [ ] Views e templates para solicitações LGPD
- [ ] Checkbox de consentimento no questionário
- [ ] Integração de consentimento na view de submissão
- [ ] Exportação de dados (portabilidade)

---

## 📝 Notas Importantes

1. **Migrações de Dados:** O campo `email` criptografado requer migração manual dos dados existentes.
2. **Chave de Criptografia:** NUNCA committar `FIELD_ENCRYPTION_KEY` no repositório.
3. **Redis:** Necessário em produção para Celery e cache funcionarem.
4. **Celery Beat:** Executar em produção para purge automático diário.
5. **SSL em Produção:** Habilitar `SECURE_SSL_REDIRECT=True` apenas em HTTPS.

---

## 🔐 Checklist de Deploy

- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Redis instalado e rodando
- [ ] `.env` configurado com todas as variáveis
- [ ] `FIELD_ENCRYPTION_KEY` gerada e configurada
- [ ] Migrações executadas (`python manage.py migrate`)
- [ ] Django rodando
- [ ] Celery Worker rodando
- [ ] Celery Beat rodando
- [ ] SSL/HTTPS habilitado em produção
- [ ] Headers de segurança verificados
- [ ] Teste de envio de email assíncrono
- [ ] Teste de purge de dados (`--dry-run`)

---

**Autor:** Sistema de melhorias Django NR1 Platform
**Data:** 2026-01-01
**Versão:** 1.0
