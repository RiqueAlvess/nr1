# 🔧 Correção da Integração Celery - Envio de E-mails

## 🎯 Problema Identificado

O Celery worker **não estava processando as tasks de e-mail** porque estava escutando apenas a fila padrão (`celery`), mas as tasks de e-mail estão roteadas para a fila `emails`.

### Causa Raiz

Em `nr1_platform/settings.py` (linhas 253-258), as tasks estão configuradas para rotas específicas:

```python
CELERY_TASK_ROUTES = {
    'quiz.tasks.send_magic_links_async': {'queue': 'emails'},      # ← Fila 'emails'
    'emails.tasks.send_email_task': {'queue': 'emails'},            # ← Fila 'emails'
    'usercompany.tasks.atualizar_contador_notificacoes_empresa_task': {'queue': 'default'},
    'core.tasks.purge_expired_data': {'queue': 'maintenance'},
}
```

**Comando anterior (INCORRETO):**
```bash
celery -A nr1_platform worker --loglevel=info
```
☝️ Este comando escuta apenas a fila padrão `celery`, ignorando as filas `emails`, `default` e `maintenance`.

## ✅ Solução

### Opção 1: Worker com todas as filas (RECOMENDADO)

```bash
celery -A nr1_platform worker --loglevel=info -Q emails,celery,default,maintenance
```

### Opção 2: Worker especializado apenas para e-mails

```bash
celery -A nr1_platform worker --loglevel=info -Q emails
```

### Opção 3: Múltiplos workers especializados (PRODUÇÃO)

```bash
# Terminal 1: Worker para emails (prioridade alta)
celery -A nr1_platform worker --loglevel=info -Q emails -n worker_emails@%h --concurrency=4

# Terminal 2: Worker para tasks padrão
celery -A nr1_platform worker --loglevel=info -Q celery,default -n worker_default@%h --concurrency=2

# Terminal 3: Worker para manutenção (baixa prioridade)
celery -A nr1_platform worker --loglevel=info -Q maintenance -n worker_maintenance@%h --concurrency=1
```

## 🔍 Diagnóstico Implementado

Foram adicionados logs detalhados em:

### 1. Views (`quiz/views.py:139-152`)
```python
logger.info(
    f'[CELERY DEBUG] Disparando task send_magic_links_async | '
    f'colaboradores_ids={colaboradores_ids} | base_url={base_url}'
)
task_result = send_magic_links_async.delay(colaboradores_ids, base_url)
logger.info(f'[CELERY DEBUG] Task enfileirada | task_id={task_result.id}')
```

### 2. Service (`account/services/password_reset_service.py:78-95`)
```python
logger.info(f"[CELERY DEBUG] Disparando task send_email_task | to_email={user.email}")
task_result = send_email_task.delay(...)
logger.info(f"[CELERY DEBUG] Task enfileirada | task_id={task_result.id}")
```

### 3. Tasks (`emails/tasks.py:19-24`, `quiz/tasks.py:32-37`)
```python
logger.info(
    f'[CELERY TASK] send_email_task INICIADA | '
    f'task_id={self.request.id} | to_email={to_email}'
)
```

## 📊 Logs Esperados Após Correção

### No Django (quando dispara a task)
```
INFO [CELERY DEBUG] Disparando task send_magic_links_async | colaboradores_ids=['...'] | base_url=http://...
INFO [CELERY DEBUG] Task enfileirada com sucesso | task_id=abc-123-def-456 | colaboradores_count=5
```

### No Celery Worker (quando processa a task)
```
[2026-01-06 XX:XX:XX,XXX: INFO/MainProcess] Task quiz.tasks.send_magic_links_async[abc-123-def-456] received
[2026-01-06 XX:XX:XX,XXX: INFO/ForkPoolWorker-1] [CELERY TASK] send_magic_links_async INICIADA | task_id=abc-123-def-456
[2026-01-06 XX:XX:XX,XXX: INFO/ForkPoolWorker-1] Iniciando envio assíncrono de 5 magic links
[2026-01-06 XX:XX:XX,XXX: INFO/ForkPoolWorker-1] [CELERY DEBUG] Enfileirando send_email_task [1/5] | to_email=user@example.com
[2026-01-06 XX:XX:XX,XXX: INFO/ForkPoolWorker-1] Task quiz.tasks.send_magic_links_async[abc-123-def-456] succeeded
[2026-01-06 XX:XX:XX,XXX: INFO/MainProcess] Task emails.tasks.send_email_task[xyz-789] received
[2026-01-06 XX:XX:XX,XXX: INFO/ForkPoolWorker-2] [CELERY TASK] send_email_task INICIADA | task_id=xyz-789 | to_email=user@example.com
[2026-01-06 XX:XX:XX,XXX: INFO/ForkPoolWorker-2] Email enviado com sucesso para user@example.com | status=200
[2026-01-06 XX:XX:XX,XXX: INFO/ForkPoolWorker-2] Task emails.tasks.send_email_task[xyz-789] succeeded
```

## 🧪 Validação

### 1. Verificar se Redis está rodando
```bash
redis-cli ping
# Deve retornar: PONG
```

### 2. Verificar tasks registradas
```bash
celery -A nr1_platform inspect registered
```

### 3. Verificar filas ativas
```bash
celery -A nr1_platform inspect active_queues
```

### 4. Monitorar filas no Redis
```bash
redis-cli MONITOR
# Em outro terminal, dispare uma task e observe as mensagens no Redis
```

### 5. Testar envio de magic link
1. Acesse `/quiz/gerenciar/` no Django
2. Selecione colaboradores
3. Clique em "Enviar Links"
4. Verifique os logs do Django (deve mostrar `[CELERY DEBUG] Task enfileirada`)
5. Verifique os logs do Celery worker (deve mostrar `Task received` e `Task succeeded`)

## 🚀 Scripts Auxiliares

### `start_celery_worker.sh`
Script para iniciar o worker com todas as filas.

### `test_celery_connection.py`
Script para validar a configuração do Celery e testar enfileiramento de tasks.

## 📝 Configurações Relevantes

### Filas Configuradas
- `emails`: Tasks de envio de e-mail (send_email_task, send_magic_links_async)
- `celery`: Fila padrão para tasks genéricas
- `default`: Tasks padrão da aplicação
- `maintenance`: Tasks de manutenção (purge_expired_data)

### Rate Limiting
- `send_magic_links_async`: 100 emails/hora
- `send_email_task`: Configurável via `SEND_RATE_LIMIT` (.env)

### Retry Policy
- Ambas as tasks têm retry configurado
- Backoff exponencial para erros 429 e 5xx
- Máximo de 3-5 retries dependendo da task

## ⚠️ Troubleshooting

### Worker não processa tasks
✅ **Solução**: Certifique-se de que o worker está escutando a fila `emails`:
```bash
celery -A nr1_platform worker --loglevel=info -Q emails,celery,default,maintenance
```

### Tasks ficam pendentes no Redis
✅ **Solução**: Reinicie o worker com as filas corretas.

### Erro "Connection refused" ao Redis
✅ **Solução**: Verifique se o Redis está rodando:
```bash
sudo systemctl status redis
# ou
redis-cli ping
```

### Tasks não aparecem nos logs
✅ **Solução**: Aumente o nível de log:
```bash
celery -A nr1_platform worker --loglevel=debug -Q emails
```

## 📚 Referências

- [Celery Documentation - Routing Tasks](https://docs.celeryproject.org/en/stable/userguide/routing.html)
- [Django + Celery Best Practices](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html)
- Configurações do projeto: `nr1_platform/settings.py` (linhas 238-279)
