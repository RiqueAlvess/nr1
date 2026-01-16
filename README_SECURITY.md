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

#### Purge Automático via Cron Job
**Arquivo:** `core/management/commands/purge_expired_data_cron.py`

Para executar o purge automaticamente em produção, configure um cron job:

```bash
# Editar crontab
crontab -e

# Adicionar linha (executar diariamente às 3h da manhã)
0 3 * * * cd /caminho/do/projeto && /caminho/do/venv/bin/python manage.py purge_expired_data_cron >> /var/log/nr1_purge.log 2>&1
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

### 3.1 Envio de Emails Síncrono

**Arquivo:** `quiz/views.py` → `enviar_links_view()`

**Implementação:**
- ✅ Envio síncrono via `EmailService.send_magic_links()`
- ✅ Rate limiting: 5 envios/hora por usuário (via `django-ratelimit`)
- ✅ Retry automático na API Resend
- ✅ Logging completo

**Impacto:** Para volumes pequenos (<50 colaboradores), o envio síncrono é adequado e simplifica a arquitetura.

---

### 3.2 Cache em Memória

#### Configuração
**Arquivo:** `nr1_platform/settings.py`

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'nr1-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Timeouts específicos
CACHE_TTL = {
    'dashboard_stats': 3600,  # 1 hora
    'dashboard_kpis': 1800,   # 30 minutos
    'user_permissions': 600,  # 10 minutos
}
```

**Nota:** Cache em memória é resetado a cada reinício do servidor. Para cache persistente em produção, considere migrar para Redis no futuro.

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

**Principais dependências:**
- `django-csp==3.8`
- `django-ratelimit==4.1.0`
- `django-axes==8.1.0`
- `django-encrypted-model-fields==0.6.5`
- `cryptography==46.0.3`
- `resend==2.19.0`

---

### 4.2 Configurar Variáveis de Ambiente

**Arquivo:** `.env` (usar `.env.example` como referência)

```bash
# Variáveis obrigatórias:
SECRET_KEY=<sua-secret-key>
DATABASE_URL=postgresql://user:password@localhost:5432/nr1_db
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
RESEND_API_KEY=re_your_api_key
API_RESEND=re_your_api_key
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

## 5. Execução

### 5.1 Desenvolvimento Local

```bash
python manage.py runserver
```

### 5.2 Produção

**Com Gunicorn:**
```bash
gunicorn nr1_platform.wsgi:application --bind 0.0.0.0:8000
```

**Nota:** Para purge automático de dados, configure um cron job conforme descrito na seção 2.4.

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
- [x] Envio de magic links síncrono (adequado para volumes pequenos)
- [x] Cache em memória (LocMemCache)
- [x] Management command para purge de dados
- [x] Rate limiting em views críticas (respeita API limits)

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
3. **Cache em Memória:** Cache é resetado a cada reinício do servidor. Adequado para volumes pequenos.
4. **Purge Automático:** Configure cron job em produção para executar purge diário.
5. **SSL em Produção:** Habilitar `SECURE_SSL_REDIRECT=True` apenas em HTTPS.
6. **Envio de Emails:** Síncrono - adequado para <50 colaboradores por envio.

---

## 🔐 Checklist de Deploy

- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] `.env` configurado com todas as variáveis
- [ ] `FIELD_ENCRYPTION_KEY` gerada e configurada
- [ ] Migrações executadas (`python manage.py migrate`)
- [ ] Django/Gunicorn rodando
- [ ] Cron job configurado para purge de dados (opcional)
- [ ] SSL/HTTPS habilitado em produção
- [ ] Headers de segurança verificados
- [ ] Teste de envio de email síncrono
- [ ] Teste de purge de dados (`--dry-run`)

---

**Autor:** Sistema de melhorias Django NR1 Platform
**Data:** 2026-01-01
**Versão:** 1.0
