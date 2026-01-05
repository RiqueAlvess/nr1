from celery import shared_task
from django.conf import settings
import logging
import requests

logger = logging.getLogger('nr1')

# Exemplo de uso:
# from emails.tasks import send_email_task
# send_email_task.delay(to_email, subject, html_body, text_body)

@shared_task(bind=True, max_retries=5, name='emails.tasks.send_email_task')
def send_email_task(self, to_email: str, subject: str, html_body: str, text_body: str, from_email: str = None):
    """
    Envia 1 email via Resend (ou provider configurado).
    - Aceita qualquer 2xx como sucesso (response.ok).
    - Retries com backoff exponencial em 429/5xx.
    """
    try:
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        api_key = getattr(settings, 'API_RESEND', None)
        if not api_key:
            logger.error("API_RESEND não configurada. Abortando envio.")
            return False

        payload = {
            'from': from_email,
            'to': [to_email],
            'subject': subject,
            'html': html_body,
            'text': text_body
        }

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        response = requests.post('https://api.resend.com/emails', headers=headers, json=payload, timeout=30)

        # Aceitar qualquer 2xx
        if response.ok:
            logger.info(f"Email enviado com sucesso para {to_email} | status={response.status_code}")
            return True

        # Se 429 (rate limit), requeue com backoff exponencial
        if response.status_code == 429:
            retry_count = self.request.retries
            countdown = min(60 * (2 ** retry_count), 3600)  # expo backoff até 1h
            logger.warning(f"429 ao enviar para {to_email}. Retry em {countdown}s. Resp: {response.text}")
            raise self.retry(countdown=countdown)

        # Para 5xx, retry também
        if 500 <= response.status_code < 600:
            retry_count = self.request.retries
            countdown = min(30 * (2 ** retry_count), 1800)
            logger.warning(f"Server error {response.status_code} para {to_email}. Retry em {countdown}s.")
            raise self.retry(countdown=countdown)

        # Para 4xx (exceto 429), considerar falha permanente
        logger.error(f"Falha ao enviar email para {to_email}: status={response.status_code} | {response.text}")
        return False

    except requests.RequestException as exc:
        # Ex.: timeout, conexão — retry com backoff
        retry_count = self.request.retries
        countdown = min(10 * (2 ** retry_count), 1800)
        logger.exception(f"RequestException ao enviar email para {to_email}. Retry em {countdown}s.")
        raise self.retry(exc=exc, countdown=countdown)
    except Exception as e:
        logger.exception(f"Erro inesperado ao enviar email para {to_email}")
        raise self.retry(exc=e, countdown=60)
