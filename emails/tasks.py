from celery import shared_task
from django.conf import settings
import logging
import resend

logger = logging.getLogger('nr1')

# Configurar API key do Resend
resend.api_key = settings.RESEND_API_KEY

# Exemplo de uso:
# from emails.tasks import send_email_task
# send_email_task.delay(to_email, subject, html_body, text_body)

@shared_task(bind=True, max_retries=5, name='emails.tasks.send_email_task')
def send_email_task(self, to_email: str, subject: str, html_body: str, text_body: str = None, from_email: str = None, **kwargs):
    """
    Envia 1 email via Resend API usando biblioteca oficial.

    Args:
        to_email (str): E-mail do destinatário
        subject (str): Assunto do e-mail
        html_body (str): Conteúdo HTML do e-mail
        text_body (str): Conteúdo texto plano (opcional, gerado automaticamente do HTML se omitido)
        from_email (str): E-mail remetente (opcional, usa DEFAULT_FROM_EMAIL se omitido)
        **kwargs: Parâmetros adicionais (reply_to, tags, etc.)

    Returns:
        dict: Informações sobre o envio (status, email_id, recipient)

    Raises:
        Retry: Em caso de erros temporários (429, 5xx, timeout)
    """
    logger.info(
        f'[CELERY TASK] send_email_task INICIADA | '
        f'task_id={self.request.id} | '
        f'to_email={to_email} | '
        f'subject={subject}'
    )

    try:
        from_email = from_email or settings.RESEND_FROM_EMAIL

        # Validar API key
        if not settings.RESEND_API_KEY:
            logger.error("[CELERY] ❌ RESEND_API_KEY não configurada. Abortando envio.")
            return {'status': 'error', 'message': 'API key não configurada'}

        # Preparar payload para Resend
        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }

        # Adicionar text_body se fornecido
        if text_body:
            params['text'] = text_body

        # Adicionar reply_to se fornecido
        if 'reply_to' in kwargs:
            params['reply_to'] = kwargs['reply_to']

        # Adicionar tags se fornecidas
        if 'tags' in kwargs:
            params['tags'] = kwargs['tags']

        logger.info(f"[CELERY] 📧 Enviando e-mail para {to_email}")
        logger.info(f"[CELERY] 📝 Assunto: {subject}")

        # Enviar via Resend
        response = resend.Emails.send(params)

        logger.info(f"[CELERY] ✅ E-mail enviado com sucesso! ID: {response['id']}")
        logger.info(f"[CELERY] 📊 Resposta Resend: {response}")

        return {
            'status': 'success',
            'email_id': response['id'],
            'recipient': to_email
        }

    except Exception as e:
        # Tratamento de erros da API Resend
        error_message = str(e)
        logger.error(f"[CELERY] ❌ Erro ao enviar e-mail para {to_email}: {error_message}")

        # Verificar se é erro de rate limit (429)
        if '429' in error_message or 'rate limit' in error_message.lower():
            retry_count = self.request.retries
            countdown = min(60 * (2 ** retry_count), 3600)  # Backoff exponencial até 1h
            logger.warning(f"[CELERY] ⏳ Rate limit atingido. Retry #{retry_count + 1} em {countdown}s")
            raise self.retry(exc=e, countdown=countdown)

        # Verificar se é erro de servidor (5xx)
        if '5' in error_message[:3] or 'server error' in error_message.lower():
            retry_count = self.request.retries
            countdown = min(30 * (2 ** retry_count), 1800)  # Backoff exponencial até 30min
            logger.warning(f"[CELERY] 🔄 Erro de servidor. Retry #{retry_count + 1} em {countdown}s")
            raise self.retry(exc=e, countdown=countdown)

        # Verificar se é erro de conexão/timeout
        if any(x in error_message.lower() for x in ['timeout', 'connection', 'network']):
            retry_count = self.request.retries
            countdown = min(10 * (2 ** retry_count), 1800)
            logger.warning(f"[CELERY] 🔌 Erro de conexão. Retry #{retry_count + 1} em {countdown}s")
            raise self.retry(exc=e, countdown=countdown)

        # Para outros erros (4xx client errors), logar e retornar erro sem retry
        logger.error(f"[CELERY] ⛔ Falha permanente ao enviar e-mail para {to_email}")
        logger.exception(f"[CELERY] Detalhes do erro:")

        return {
            'status': 'error',
            'message': error_message,
            'recipient': to_email
        }
