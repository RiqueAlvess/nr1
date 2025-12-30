import httpx
import logging
from django.conf import settings
from django.template.loader import render_to_string
from typing import List, Optional, Dict, Any

logger = logging.getLogger('nr1')


class EmailService:
    """Serviço de envio de emails via Resend API com suporte a templates Django"""

    RESEND_API_URL = "https://api.resend.com/emails"

    @staticmethod
    def send_email(
        to: List[str],
        subject: str,
        html_content: str,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Envia email via Resend API

        Args:
            to: Lista de destinatários
            subject: Assunto do email
            html_content: Conteúdo HTML do email
            from_email: Email do remetente (usa DEFAULT_FROM_EMAIL se não especificado)

        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        from_email = from_email or settings.DEFAULT_FROM_EMAIL

        # Log do início do envio
        logger.info(
            f"Iniciando envio de email | Destinatários: {', '.join(to)} | "
            f"Assunto: {subject}"
        )

        headers = {
            "Authorization": f"Bearer {settings.API_RESEND}",
            "Content-Type": "application/json"
        }

        payload = {
            "from": from_email,
            "to": to,
            "subject": subject,
            "html": html_content
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    EmailService.RESEND_API_URL,
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    logger.info(
                        f"✓ Email enviado com sucesso | Destinatários: {', '.join(to)} | "
                        f"Response ID: {response.json().get('id', 'N/A')}"
                    )
                    return True
                else:
                    logger.error(
                        f"✗ Erro ao enviar email | Status: {response.status_code} | "
                        f"Destinatários: {', '.join(to)} | "
                        f"Erro: {response.text}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.error(
                f"✗ Timeout ao enviar email via Resend API | "
                f"Destinatários: {', '.join(to)}"
            )
            return False
        except Exception as e:
            logger.error(
                f"✗ Erro inesperado ao enviar email | "
                f"Destinatários: {', '.join(to)} | "
                f"Erro: {str(e)}"
            )
            return False

    @staticmethod
    def send_template_email(
        to: List[str],
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None
    ) -> bool:
        """
        Envia email usando template Django

        Args:
            to: Lista de destinatários
            subject: Assunto do email
            template_name: Nome do template (ex: 'emails/magic_link_questionario.html')
            context: Contexto para renderização do template
            from_email: Email do remetente (usa DEFAULT_FROM_EMAIL se não especificado)

        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        logger.info(
            f"Renderizando template de email | Template: {template_name} | "
            f"Destinatários: {', '.join(to)}"
        )

        try:
            # Adicionar contexto padrão
            default_context = {
                'system_name': settings.SYSTEM_NAME,
                'company_name': settings.COMPANY_NAME,
            }
            context = {**default_context, **context}

            # Renderizar template
            html_content = render_to_string(template_name, context)

            logger.info(
                f"✓ Template renderizado com sucesso | Template: {template_name}"
            )

            # Enviar email
            return EmailService.send_email(
                to=to,
                subject=subject,
                html_content=html_content,
                from_email=from_email
            )

        except Exception as e:
            logger.error(
                f"✗ Erro ao renderizar template | Template: {template_name} | "
                f"Erro: {str(e)}"
            )
            return False
    
    @staticmethod
    def send_magic_link(email: str, magic_link: str) -> bool:
        """
        Envia magic link para responder questionário usando template Django

        Args:
            email: Email do destinatário
            magic_link: URL completa do magic link

        Returns:
            bool: True se enviado com sucesso
        """
        logger.info(
            f"Preparando envio de magic link | Email: {email}"
        )

        subject = "Convite para Avaliação de Riscos Psicossociais - NR-1"

        context = {
            'magic_link': magic_link,
            'expiration_hours': settings.MAGIC_LINK_EXPIRATION_HOURS,
        }

        return EmailService.send_template_email(
            to=[email],
            subject=subject,
            template_name='emails/magic_link_questionario.html',
            context=context
        )

    @staticmethod
    def send_password_reset(email: str, reset_link: str, user_name: str) -> bool:
        """
        Envia link para redefinição de senha usando template Django

        Args:
            email: Email do destinatário
            reset_link: URL completa do link de redefinição
            user_name: Nome do usuário

        Returns:
            bool: True se enviado com sucesso
        """
        logger.info(
            f"Preparando envio de redefinição de senha | Email: {email} | "
            f"Usuário: {user_name}"
        )

        subject = f"Redefinição de Senha - {settings.SYSTEM_NAME}"

        context = {
            'reset_link': reset_link,
            'user_name': user_name,
            'expiration_hours': 24,  # Padrão para redefinição de senha
        }

        return EmailService.send_template_email(
            to=[email],
            subject=subject,
            template_name='emails/reset_password.html',
            context=context
        )