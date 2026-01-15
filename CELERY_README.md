# 📬 Celery - Processamento Assíncrono de E-mails

## 📋 Visão Geral

Este projeto usa **Celery** para processamento assíncrono de tasks, principalmente envio de e-mails. O Celery permite que operações demoradas sejam executadas em segundo plano, sem bloquear as requisições HTTP.

## 🏗️ Arquitetura

```
┌─────────────┐         ┌──────────┐         ┌────────────────┐         ┌──────────┐
│   Django    │────────>│  Redis   │────────>│ Celery Worker  │────────>│  Resend  │
│  (Web App)  │  enqueue│ (Broker) │  dequeue│  (Background)  │   API   │  (Email) │
└─────────────┘         └──────────┘         └────────────────┘         └──────────┘
     │                                               │
     │                                               │
     └─────────────── Logs e Status ─────────────────┘
```

### Componentes

1. **Django**: Enfileira tasks quando usuário solicita envio de e-mails
2. **Redis**: Broker que armazena as filas de tasks
3. **Celery Worker**: Processa as tasks em segundo plano
4. **Resend API**: Serviço externo para envio de e-mails

## 🎯 Tasks Implementadas

### 1. `send_email_task` (emails/tasks.py)
Envia um único e-mail via Resend API.

**Parâmetros:**
- `to_email`: Email do destinatário
- `subject`: Assunto do email
- `html_body`: Corpo HTML do email
- `text_body`: Corpo texto plano (fallback)
- `from_email`: Email remetente (opcional)

**Configurações:**
- **Fila**: `emails`
- **Max retries**: 5
- **Rate limit**: Configurável via `SEND_RATE_LIMIT` (.env)
- **Retry strategy**: Backoff exponencial para 429/5xx

**Uso:**
```python
from emails.tasks import send_email_task

send_email_task.delay(
    to_email='user@example.com',
    subject='Bem-vindo!',
    html_body='<p>Olá!</p>',
    text_body='Olá!'
)
```

### 2. `send_magic_links_async` (quiz/tasks.py)
Envia magic links em lote para múltiplos colaboradores.

**Parâmetros:**
- `colaboradores_ids`: Lista de UUIDs dos colaboradores
- `base_url`: URL base para construir os magic links

**Configurações:**
- **Fila**: `emails`
- **Max retries**: 3
- **Rate limit**: 100 emails/hora

**Funcionamento:**
1. Gera magic links para colaboradores (se necessário)
2. Para cada colaborador:
   - Gera novo token
   - Renderiza template de email
   - Enfileira `send_email_task` para envio
3. Retorna estatísticas do processamento

**Uso:**
```python
from quiz.tasks import send_magic_links_async

colaboradores = ['uuid-1', 'uuid-2', 'uuid-3']
base_url = 'https://example.com'

send_magic_links_async.delay(colaboradores, base_url)
```

## 🚀 Como Usar

### Desenvolvimento

```bash
# 1. Iniciar Redis (se não estiver rodando)
redis-cli ping  # Verificar se está rodando

# 2. Iniciar Celery Worker (COMANDO CORRETO!)
./start_celery_worker.sh all

# Ou manualmente:
celery -A nr1_platform worker --loglevel=info -Q emails,celery,default,maintenance
```

### Produção

#### Opção 1: Systemd (Recomendado)

```bash
# 1. Copiar service file
sudo cp celery_worker.service /etc/systemd/system/

# 2. Editar paths no service file
sudo nano /etc/systemd/system/celery_worker.service

# 3. Habilitar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable celery_worker
sudo systemctl start celery_worker

# 4. Verificar status
sudo systemctl status celery_worker

# 5. Ver logs
sudo journalctl -u celery_worker -f
```

#### Opção 2: Supervisor

```bash
# Instalar supervisor
sudo apt-get install supervisor

# Criar config em /etc/supervisor/conf.d/celery.conf
# (ver exemplo abaixo)

# Recarregar supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start celery
```

Exemplo de config para Supervisor (`/etc/supervisor/conf.d/celery.conf`):

```ini
[program:celery]
command=/var/www/nr1/venv/bin/celery -A nr1_platform worker -Q emails,celery,default,maintenance -n worker@%%h --loglevel=info
directory=/var/www/nr1
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=998
```

## 📊 Monitoramento

### Verificar Tasks Registradas

```bash
celery -A nr1_platform inspect registered
```

### Verificar Filas Ativas

```bash
celery -A nr1_platform inspect active_queues
```

### Verificar Workers Ativos

```bash
celery -A nr1_platform inspect active
```

### Verificar Tasks em Execução

```bash
celery -A nr1_platform inspect active
```

### Monitorar Redis

```bash
# Conectar ao Redis CLI
redis-cli

# Ver todas as chaves do Celery
KEYS celery*

# Ver tamanho das filas
LLEN celery.emails
LLEN celery.celery
LLEN celery.default
```

### Flower (Web UI - Opcional)

```bash
# Instalar Flower
pip install flower

# Iniciar Flower
celery -A nr1_platform flower --port=5555

# Acessar: http://localhost:5555
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```bash
# Redis - Broker e Backend
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# Rate Limiting (opcional)
SEND_RATE_LIMIT=100/h  # 100 emails por hora

# Email API
API_RESEND=re_your_api_key_here
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Settings (nr1_platform/settings.py)

```python
# Broker e Backend
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')

# Serialização
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Rotas de Tasks
CELERY_TASK_ROUTES = {
    'quiz.tasks.send_magic_links_async': {'queue': 'emails'},
    'emails.tasks.send_email_task': {'queue': 'emails'},
    'usercompany.tasks.*': {'queue': 'default'},
    'core.tasks.purge_expired_data': {'queue': 'maintenance'},
}

# Rate Limiting
CELERY_TASK_ANNOTATIONS = {
    'quiz.tasks.send_magic_links_async': {'rate_limit': '100/h'},
    'emails.tasks.send_email_task': {'rate_limit': SEND_RATE_LIMIT},
}
```

## 🐛 Troubleshooting

### ❌ Tasks não são processadas

**Sintoma:** Django enfileira tasks (retorna 200 OK) mas Celery worker não processa.

**Causa:** Worker não está escutando a fila correta.

**Solução:**
```bash
# ❌ ERRADO (escuta apenas fila 'celery')
celery -A nr1_platform worker --loglevel=info

# ✅ CORRETO (escuta todas as filas)
celery -A nr1_platform worker --loglevel=info -Q emails,celery,default,maintenance
```

### ❌ Connection refused - Redis

**Sintoma:** Erro `Connection refused` ao tentar conectar no Redis.

**Solução:**
```bash
# Verificar se Redis está rodando
redis-cli ping

# Se não estiver, iniciar:
sudo systemctl start redis

# Verificar porta e host em .env:
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
```

### ❌ Tasks ficam pendentes

**Sintoma:** Tasks aparecem no Redis mas não são processadas.

**Causa:** Worker parado ou com erro.

**Solução:**
```bash
# Verificar logs do worker
sudo journalctl -u celery_worker -n 100

# Reiniciar worker
sudo systemctl restart celery_worker
```

### ❌ Rate limit atingido

**Sintoma:** Muitos emails são rejeitados com erro 429.

**Causa:** Limite de envio da API Resend foi atingido.

**Solução:**
```bash
# Ajustar SEND_RATE_LIMIT no .env
SEND_RATE_LIMIT=50/h  # Reduzir para 50 emails/hora

# Reiniciar worker para aplicar nova configuração
sudo systemctl restart celery_worker
```

### ❌ Tasks executam mas emails não são enviados

**Sintoma:** Worker processa tasks com sucesso mas nenhum email chega.

**Causa:** API_RESEND não configurada ou inválida.

**Solução:**
```bash
# Verificar variável no .env
API_RESEND=re_your_valid_api_key

# Verificar logs do worker
sudo journalctl -u celery_worker -f

# Procurar por: "API_RESEND não configurada" ou "401 Unauthorized"
```

## 📝 Logs

### Formato dos Logs

Os logs incluem marcadores `[CELERY DEBUG]` e `[CELERY TASK]` para facilitar o rastreamento:

```
# Django (quando enfileira)
INFO [CELERY DEBUG] Disparando task send_magic_links_async | colaboradores_ids=[...] | base_url=http://...
INFO [CELERY DEBUG] Task enfileirada com sucesso | task_id=abc-123 | colaboradores_count=5

# Celery Worker (quando processa)
INFO Task quiz.tasks.send_magic_links_async[abc-123] received
INFO [CELERY TASK] send_magic_links_async INICIADA | task_id=abc-123 | colaboradores_count=5
INFO [CELERY DEBUG] Enfileirando send_email_task [1/5] | to_email=user@example.com
INFO Task emails.tasks.send_email_task[xyz-789] received
INFO [CELERY TASK] send_email_task INICIADA | task_id=xyz-789 | to_email=user@example.com
INFO Email enviado com sucesso para user@example.com | status=200
INFO Task emails.tasks.send_email_task[xyz-789] succeeded
```

### Localizações dos Logs

- **Django**: `logs/nr1.log`
- **Celery (systemd)**: `sudo journalctl -u celery_worker -f`
- **Celery (supervisor)**: `/var/log/celery/worker.log`
- **Celery (development)**: Terminal onde o worker foi iniciado

## 🧪 Testes

### Script de Teste

```bash
# Executar script de teste (se disponível)
python test_celery_connection.py
```

### Teste Manual

```python
# Abrir shell do Django
python manage.py shell

# Importar e testar task
from emails.tasks import send_email_task

# Enfileirar task de teste
result = send_email_task.delay(
    to_email='test@example.com',
    subject='Teste Celery',
    html_body='<p>Teste de envio via Celery</p>',
    text_body='Teste de envio via Celery'
)

# Verificar task_id
print(f"Task ID: {result.id}")
print(f"Status: {result.status}")

# Aguardar resultado (máximo 30 segundos)
result.get(timeout=30)
```

## 📚 Referências

- [Celery Documentation](https://docs.celeryproject.org/)
- [Django + Celery](https://docs.celeryproject.org/en/stable/django/)
- [Resend API](https://resend.com/docs)
- [Redis Documentation](https://redis.io/documentation)

## 🤝 Suporte

Para problemas ou dúvidas:

1. Verificar logs: `sudo journalctl -u celery_worker -f`
2. Consultar `CELERY_FIX.md` para diagnóstico
3. Executar `test_celery_connection.py` para validar configuração
4. Verificar issues no repositório do projeto
