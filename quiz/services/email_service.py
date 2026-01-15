"""
Serviço de envio de e-mails - Processamento síncrono
"""
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
import logging
import resend

from quiz.models import MagicLink

logger = logging.getLogger('nr1')

# Configurar API key do Resend
resend.api_key = settings.RESEND_API_KEY


class EmailService:
    """Serviço para envio de e-mails de forma síncrona"""

    @staticmethod
    def send_email(to_email: str, subject: str, html_body: str, text_body: str = None, from_email: str = None, **kwargs):
        """
        Envia 1 email via Resend API usando biblioteca oficial.

        Args:
            to_email (str): E-mail do destinatário
            subject (str): Assunto do e-mail
            html_body (str): Conteúdo HTML do e-mail
            text_body (str): Conteúdo texto plano (opcional)
            from_email (str): E-mail remetente (opcional, usa DEFAULT_FROM_EMAIL se omitido)
            **kwargs: Parâmetros adicionais (reply_to, tags, etc.)

        Returns:
            dict: Informações sobre o envio (status, email_id, recipient)
        """
        try:
            from_email = from_email or settings.RESEND_FROM_EMAIL

            # Validar API key
            if not settings.RESEND_API_KEY:
                logger.error("❌ RESEND_API_KEY não configurada. Abortando envio.")
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

            logger.info(f"📧 Enviando e-mail para {to_email}")
            logger.info(f"📝 Assunto: {subject}")

            # Enviar via Resend
            response = resend.Emails.send(params)

            logger.info(f"✅ E-mail enviado com sucesso! ID: {response['id']}")
            logger.info(f"📊 Resposta Resend: {response}")

            return {
                'status': 'success',
                'email_id': response['id'],
                'recipient': to_email
            }

        except Exception as e:
            error_message = str(e)
            logger.error(f"❌ Erro ao enviar e-mail para {to_email}: {error_message}")
            logger.exception("Detalhes do erro:")

            return {
                'status': 'error',
                'message': error_message,
                'recipient': to_email
            }

    @staticmethod
    def send_magic_links(colaboradores_ids, base_url):
        """
        Envia magic links em lote de forma síncrona

        Args:
            colaboradores_ids: Lista de UUIDs dos colaboradores
            base_url: URL base para construir o link

        Returns:
            dict: Status do envio com contadores
        """
        logger.info(
            f'Iniciando envio síncrono de magic links | '
            f'colaboradores_count={len(colaboradores_ids)} | '
            f'base_url={base_url}'
        )

        from quiz.services.magic_link_service import MagicLinkService

        # Primeiro, gerar os magic links se necessário
        gerados, ja_existentes = MagicLinkService.gerar_magic_links_bulk(colaboradores_ids)
        logger.info(f'Magic links gerados: {gerados}, já existentes: {ja_existentes}')

        # Buscar magic links para envio
        magic_links = MagicLink.objects.filter(
            colaborador_id__in=colaboradores_ids,
            status__in=['PENDING', 'ACCESSED']
        ).select_related('colaborador')

        total = magic_links.count()
        enviados = 0
        erros = 0

        logger.info(f'Iniciando envio de {total} emails')

        for idx, magic_link in enumerate(magic_links, 1):
            try:
                # Gerar novo token
                token = MagicLink.gerar_token()
                token_hash = MagicLink.hash_token(token)

                # Atualizar hash (para próximo uso)
                magic_link.token_hash = token_hash
                magic_link.save()

                # Construir URL completa do magic link
                quiz_path = reverse('quiz:responder', kwargs={'token': token})
                magic_link_url = f"{base_url}{quiz_path}"

                # Preparar contexto para renderizar o email
                context = {
                    'magic_link': magic_link_url,
                    'expiration_hours': settings.MAGIC_LINK_EXPIRATION_HOURS,
                    'system_name': settings.SYSTEM_NAME,
                    'company_name': settings.COMPANY_NAME,
                }

                # Renderizar template do email
                html_message = render_to_string('emails/magic_link_questionario.html', context)
                text_message = strip_tags(html_message)
                subject = "Convite para Avaliação de Riscos Psicossociais - NR-1"

                # Enviar email de forma síncrona
                logger.info(
                    f'Enviando email [{idx}/{total}] | '
                    f'to_email={magic_link.colaborador.email}'
                )

                resultado = EmailService.send_email(
                    to_email=magic_link.colaborador.email,
                    subject=subject,
                    html_body=html_message,
                    text_body=text_message
                )

                if resultado['status'] == 'success':
                    enviados += 1
                    logger.info(
                        f'Email enviado com sucesso [{idx}/{total}] | '
                        f'email_id={resultado.get("email_id")} | '
                        f'to_email={magic_link.colaborador.email}'
                    )
                else:
                    erros += 1
                    logger.error(
                        f'Erro ao enviar email [{idx}/{total}] | '
                        f'to_email={magic_link.colaborador.email} | '
                        f'error={resultado.get("message")}'
                    )

            except Exception as e:
                erros += 1
                logger.exception(f'Erro ao processar envio para [{idx}/{total}]: {magic_link.colaborador.email}')

        resultado_final = {
            'status': 'completed',
            'total': total,
            'enviados': enviados,
            'erros': erros,
            'gerados': gerados,
            'ja_existentes': ja_existentes
        }

        logger.info(f'Envio síncrono concluído: {resultado_final}')

        return resultado_final
