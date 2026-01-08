# 📧 Sistema de Envio de E-mails via Resend API

## 🎯 Visão Geral

Sistema completo de envio de e-mails usando a API oficial do Resend, integrado com Celery para processamento assíncrono.

### Principais Características

✅ **Biblioteca Oficial Resend**: Usa `resend==0.8.0` ao invés de requests manual
✅ **Processamento Assíncrono**: Celery workers processam e-mails em background
✅ **Retry Inteligente**: Backoff exponencial para rate limits e erros temporários
✅ **Logs Detalhados**: Rastreamento completo de envio e falhas
✅ **Rate Limiting**: Respeita limites da API (configurável)
✅ **Templates HTML**: Sistema de templates Django para e-mails

---

## 📋 Pré-requisitos

### 1. Conta Resend

1. Crie uma conta em [https://resend.com](https://resend.com)
2. Obtenha sua API Key em [https://resend.com/api-keys](https://resend.com/api-keys)
3. Configure seu domínio verificado (ou use o domínio de testes)

### 2. Redis Rodando

```bash
# Verificar se Redis está ativo
redis-cli ping
# Deve retornar: PONG

# Se não estiver rodando, inicie:
sudo systemctl start redis
# ou
redis-server
```

### 3. Dependências Python

```bash
pip install -r requirements.txt
```

Isso instalará:
- `resend==0.8.0` - Biblioteca oficial Resend
- `celery==5.6.1` - Processamento assíncrono
- `redis==7.1.0` - Cliente Redis

---

## ⚙️ Configuração

### 1. Variáveis de Ambiente (.env)

Copie o arquivo de exemplo e configure suas variáveis:

```bash
cp .env.example .env
```

Edite `.env` e configure:

```env
# Email (Resend API)
RESEND_API_KEY=re_sua_api_key_aqui
RESEND_FROM_EMAIL=noreply@seudominio.com
DEFAULT_FROM_EMAIL=noreply@seudominio.com

# Rate Limiting (opcional)
SEND_RATE_LIMIT=100/h  # 100 e-mails por hora
```

### 2. Verificar Configurações

```python
# No shell do Django
python manage.py shell

from django.conf import settings
print(f"RESEND_API_KEY: {settings.RESEND_API_KEY[:10]}...")
print(f"RESEND_FROM_EMAIL: {settings.RESEND_FROM_EMAIL}")
```

---

## 🚀 Iniciando o Sistema

### 1. Iniciar Django

```bash
python manage.py runserver
```

### 2. Iniciar Celery Worker

**Opção A: Worker com todas as filas (RECOMENDADO para desenvolvimento)**

```bash
celery -A nr1_platform worker --loglevel=info -Q emails,celery,default,maintenance
```

**Opção B: Worker apenas para e-mails**

```bash
celery -A nr1_platform worker --loglevel=info -Q emails
```

**Opção C: Múltiplos workers (PRODUÇÃO)**

```bash
# Terminal 1: Worker para emails (alta prioridade)
celery -A nr1_platform worker --loglevel=info -Q emails -n worker_emails@%h --concurrency=4

# Terminal 2: Worker para tasks padrão
celery -A nr1_platform worker --loglevel=info -Q celery,default -n worker_default@%h --concurrency=2

# Terminal 3: Worker para manutenção
celery -A nr1_platform worker --loglevel=info -Q maintenance -n worker_maintenance@%h --concurrency=1
```

---

## 📝 Como Usar

### 1. Enviar E-mail Simples

```python
from emails.tasks import send_email_task

# Disparar envio assíncrono
task_result = send_email_task.delay(
    to_email='usuario@example.com',
    subject='Bem-vindo ao Sistema NR-1',
    html_body='<h1>Olá!</h1><p>Bem-vindo ao nosso sistema.</p>',
    text_body='Olá! Bem-vindo ao nosso sistema.'
)

print(f"Task enfileirada: {task_result.id}")
```

### 2. Enviar Magic Links (Quiz)

O sistema já está integrado! Basta usar a interface:

1. Acesse `/quiz/gerenciar/`
2. Selecione colaboradores
3. Clique em "Enviar Links"
4. Os e-mails serão enviados em background

**Por trás dos panos:**

```python
from quiz.tasks import send_magic_links_async

# A view dispara automaticamente
task_result = send_magic_links_async.delay(
    colaboradores_ids=[uuid1, uuid2, uuid3],
    base_url='https://seudominio.com'
)
```

### 3. Personalizar E-mails

Edite os templates em `templates/emails/`:

- `base_email.html` - Layout base de todos os e-mails
- `magic_link_questionario.html` - E-mail de convite para quiz
- `reset_password.html` - E-mail de recuperação de senha

**Exemplo de customização:**

```html
{% extends "emails/base_email.html" %}

{% block title %}Seu Título{% endblock %}

{% block header_title %}Cabeçalho{% endblock %}

{% block content %}
<h2>Conteúdo do E-mail</h2>
<p>Seu texto aqui...</p>

<div class="btn-container">
    <a href="{{ action_url }}" class="btn-primary">
        Clique Aqui
    </a>
</div>
{% endblock %}
```

---

## 📊 Monitoramento e Logs

### Logs Esperados

**No Django (quando dispara task):**

```
INFO [VIEW] Disparando task para enviar 5 magic links
INFO [CELERY DEBUG] Task enfileirada com sucesso | task_id=abc-123-def
```

**No Celery Worker (quando processa):**

```
[INFO] Task quiz.tasks.send_magic_links_async[abc-123] received
[INFO] [CELERY] Processando 5 magic links
[INFO] [CELERY] 📧 Enviando e-mail para user@example.com
[INFO] [CELERY] ✅ E-mail enviado com sucesso! ID: re_xyz789
[INFO] Task emails.tasks.send_email_task[def-456] succeeded in 0.8s
```

### Monitorar Filas Redis

```bash
# Ver quantidade de tasks pendentes
redis-cli LLEN celery

# Monitorar em tempo real
redis-cli MONITOR
```

### Verificar Tasks Celery

```bash
# Ver tasks registradas
celery -A nr1_platform inspect registered

# Ver filas ativas
celery -A nr1_platform inspect active_queues

# Ver tasks ativas (em processamento)
celery -A nr1_platform inspect active

# Ver tasks agendadas
celery -A nr1_platform inspect scheduled
```

---

## 🔧 Troubleshooting

### Problema: Tasks não são processadas

**Causa:** Worker não está escutando a fila `emails`

**Solução:**

```bash
# Certifique-se de incluir -Q emails
celery -A nr1_platform worker --loglevel=info -Q emails,celery,default,maintenance
```

### Problema: Erro "RESEND_API_KEY não configurada"

**Causa:** Variável de ambiente não foi carregada

**Solução:**

1. Verifique se o arquivo `.env` existe
2. Verifique se `RESEND_API_KEY=re_...` está configurado
3. Reinicie Django e Celery

```bash
# Verificar no Django shell
python manage.py shell
>>> from django.conf import settings
>>> settings.RESEND_API_KEY
```

### Problema: E-mails não chegam

**Possíveis causas e soluções:**

1. **API Key inválida**
   - Verifique em https://resend.com/api-keys
   - Gere uma nova key se necessário

2. **Domínio não verificado**
   - Verifique em https://resend.com/domains
   - Use o domínio de testes: `onboarding@resend.dev`

3. **Rate limit atingido**
   - Free tier: 100 e-mails/dia
   - Verifique logs: `[CELERY] ⏳ Rate limit atingido`
   - Atualize plano ou aguarde reset

4. **E-mail bloqueado/spam**
   - Verifique pasta de spam
   - Configure SPF/DKIM no domínio

### Problema: Redis connection refused

**Causa:** Redis não está rodando

**Solução:**

```bash
# Verificar status
sudo systemctl status redis

# Iniciar Redis
sudo systemctl start redis

# Habilitar auto-start
sudo systemctl enable redis
```

### Problema: Erro "Task of kind 'emails.tasks.send_email_task' is not registered"

**Causa:** Celery não encontrou a task

**Solução:**

1. Verifique se `emails` está em `INSTALLED_APPS` (settings.py linha 36)
2. Reinicie o Celery worker
3. Verifique tasks registradas:

```bash
celery -A nr1_platform inspect registered
```

---

## 🧪 Testando a Implementação

### Teste 1: Envio Manual via Shell

```python
python manage.py shell

from emails.tasks import send_email_task

# Enviar e-mail de teste
result = send_email_task.delay(
    to_email='seu-email@example.com',
    subject='Teste Resend API',
    html_body='<h1>Teste</h1><p>Se você recebeu isso, está funcionando!</p>'
)

print(f"Task ID: {result.id}")
print(f"Status: {result.status}")
```

### Teste 2: Envio de Magic Links

1. Acesse: http://localhost:8000/quiz/gerenciar/
2. Adicione colaboradores com e-mails válidos
3. Clique em "Enviar Links"
4. Verifique logs do Celery worker
5. Verifique se e-mails chegaram

### Teste 3: Verificar Retry em Caso de Erro

```python
# Simular erro (API key inválida temporariamente)
from emails.tasks import send_email_task
from django.conf import settings

# Salvar API key atual
original_key = settings.RESEND_API_KEY

# Definir key inválida
settings.RESEND_API_KEY = 'invalid_key'

# Tentar enviar (deve falhar e fazer retry)
result = send_email_task.delay(
    to_email='teste@example.com',
    subject='Teste Retry',
    html_body='<p>Teste</p>'
)

# Restaurar key original
settings.RESEND_API_KEY = original_key

# Verificar retries nos logs do Celery
```

---

## 📈 Boas Práticas

### 1. Rate Limiting

Configure limites adequados ao seu plano:

```env
# Free Tier: 100 emails/dia = ~4 emails/hora
SEND_RATE_LIMIT=4/h

# Paid Tier: 1000 emails/dia = ~40 emails/hora
SEND_RATE_LIMIT=40/h
```

### 2. Templates de E-mail

- Sempre use templates HTML + texto plano
- Teste em múltiplos clientes de e-mail
- Use inline CSS (melhor compatibilidade)
- Evite imagens externas grandes

### 3. Monitoramento

Configure alertas para:
- Taxa de falha > 5%
- Fila de e-mails > 100 pendentes
- Worker offline

### 4. Produção

- Use supervisor/systemd para manter workers rodando
- Configure múltiplos workers especializados
- Implemente dead letter queue para falhas permanentes
- Configure logs externos (Sentry, Datadog, etc.)

---

## 📚 Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        Django App                           │
│                                                             │
│  ┌──────────────┐         ┌─────────────────┐             │
│  │ quiz/views.py│────────▶│ quiz/tasks.py   │             │
│  └──────────────┘         └─────────────────┘             │
│                                   │                         │
│                                   │ .delay()                │
│                                   ▼                         │
│                          ┌─────────────────┐               │
│                          │ emails/tasks.py │               │
│                          └─────────────────┘               │
│                                   │                         │
└───────────────────────────────────┼─────────────────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │  Redis Queue    │
                           │   (emails)      │
                           └─────────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │ Celery Worker   │
                           │ (processa queue)│
                           └─────────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │  Resend API     │
                           │ (envia e-mail)  │
                           └─────────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │  Destinatário   │
                           └─────────────────┘
```

---

## 📂 Estrutura de Arquivos

```
nr1/
├── emails/
│   ├── __init__.py
│   └── tasks.py                    # ✅ Task de envio via Resend
│
├── quiz/
│   ├── tasks.py                    # ✅ Task de envio de magic links
│   └── views.py                    # ✅ Dispara tasks com .delay()
│
├── templates/
│   └── emails/
│       ├── base_email.html         # Template base
│       ├── magic_link_questionario.html  # E-mail de convite
│       └── reset_password.html     # E-mail de reset de senha
│
├── nr1_platform/
│   ├── settings.py                 # ✅ Configurações Resend + Celery
│   └── celery.py                   # ✅ Configuração Celery
│
├── .env                            # Variáveis de ambiente (não versionado)
├── .env.example                    # ✅ Template de variáveis
├── requirements.txt                # ✅ Dependências (inclui resend==0.8.0)
├── RESEND_SETUP.md                 # ✅ Esta documentação
└── CELERY_FIX.md                   # Documentação anterior (complementar)
```

---

## 🔗 Recursos Adicionais

### Documentação Oficial

- [Resend API Docs](https://resend.com/docs)
- [Resend Python SDK](https://github.com/resendlabs/resend-python)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Django + Celery Guide](https://docs.celeryproject.org/en/stable/django/)

### Rate Limits Resend

| Plano     | E-mails/dia | Rate Limit     |
|-----------|-------------|----------------|
| Free      | 100         | ~4/hora        |
| Pro       | 50,000      | ~2,000/hora    |
| Enterprise| Ilimitado   | Customizado    |

### Comandos Úteis

```bash
# Ver versão do Celery
celery --version

# Limpar fila de tasks
celery -A nr1_platform purge

# Recarregar workers (após mudanças no código)
celery -A nr1_platform control pool_restart

# Ver configurações do Celery
celery -A nr1_platform report
```

---

## ✅ Checklist de Validação

Após implementar, verifique:

- [ ] Variável `RESEND_API_KEY` configurada no `.env`
- [ ] Variável `RESEND_FROM_EMAIL` configurada no `.env`
- [ ] Pacote `resend==0.8.0` instalado: `pip list | grep resend`
- [ ] Redis rodando: `redis-cli PING` retorna `PONG`
- [ ] Celery worker iniciado com fila `emails`
- [ ] Tasks registradas: `celery -A nr1_platform inspect registered`
- [ ] Logs no Django: `[VIEW] Disparando task...`
- [ ] Logs no Celery: `Task received` e `✅ E-mail enviado com sucesso`
- [ ] E-mail recebido no destinatário

---

## 🆘 Suporte

Se encontrar problemas:

1. Verifique os logs do Django: `logs/nr1.log`
2. Verifique os logs do Celery worker (terminal)
3. Consulte seção [Troubleshooting](#-troubleshooting)
4. Revise `CELERY_FIX.md` para problemas de fila
5. Verifique status da API Resend: https://resend.com/status

---

**Última atualização:** 2026-01-08
**Versão do sistema:** NR-1 Platform v1.0
**Biblioteca Resend:** 0.8.0
