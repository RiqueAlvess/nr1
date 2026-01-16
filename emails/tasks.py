from django.conf import settings
import logging
import resend

logger = logging.getLogger('nr1')

# Configurar API key do Resend
resend.api_key = settings.RESEND_API_KEY

# Exemplo de uso:
# from emails.tasks import send_email_task
# send_email_task(to_email, subject, html_body, text_body)

def send_email_task(to_email: str, subject: str, html_body: str, text_body: str = None, from_email: str = None, **kwargs):
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
        Exception: Em caso de erros no envio
    """
    logger.info(
        f'[EMAIL] send_email_task INICIADA | '
        f'to_email={to_email} | '
        f'subject={subject}'
    )

    try:
        from_email = from_email or settings.RESEND_FROM_EMAIL

        # Validar API key
        if not settings.RESEND_API_KEY:
            logger.error("[EMAIL] ❌ RESEND_API_KEY não configurada. Abortando envio.")
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

        logger.info(f"[EMAIL] 📧 Enviando e-mail para {to_email}")
        logger.info(f"[EMAIL] 📝 Assunto: {subject}")

        # Enviar via Resend
        response = resend.Emails.send(params)

        logger.info(f"[EMAIL] ✅ E-mail enviado com sucesso! ID: {response['id']}")
        logger.info(f"[EMAIL] 📊 Resposta Resend: {response}")

        return {
            'status': 'success',
            'email_id': response['id'],
            'recipient': to_email
        }

    except Exception as e:
        # Tratamento de erros da API Resend
        error_message = str(e)
        logger.error(f"[EMAIL] ❌ Erro ao enviar e-mail para {to_email}: {error_message}")
        logger.exception(f"[EMAIL] Detalhes do erro:")

        return {
            'status': 'error',
            'message': error_message,
            'recipient': to_email
        }
