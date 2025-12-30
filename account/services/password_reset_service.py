"""
Serviço para gerenciamento de redefinição de senha via magic link
Utiliza Resend API para envio de emails
"""
import logging
import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from account.models import PasswordResetToken

logger = logging.getLogger('nr1')


class PasswordResetService:
    """
    Serviço para redefinição de senha via magic link
    """

    @staticmethod
    def create_reset_token(user, ip_address=None, user_agent=None):
        """
        Cria um novo token de redefinição de senha para o usuário
        Invalida tokens anteriores do mesmo usuário
        """
        try:
            # Criar novo token
            reset_token = PasswordResetToken.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Invalidar tokens anteriores
            reset_token.invalidate_previous_tokens()

            logger.info(
                f"Token de redefinição criado para usuário: {user.username} | "
                f"IP: {ip_address} | Expira em: {reset_token.expires_at}"
            )

            return reset_token

        except Exception as e:
            logger.error(
                f"Erro ao criar token de redefinição para {user.username}: {str(e)}",
                exc_info=True
            )
            raise

    @staticmethod
    def send_reset_email(user, reset_token, request):
        """
        Envia email com magic link de redefinição de senha
        """
        try:
            # Construir URL do magic link
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            reset_url = f"{protocol}://{domain}/account/password-reset/confirm/{reset_token.token}/"

            # Contexto para o template do email
            context = {
                'user': user,
                'reset_url': reset_url,
                'expires_hours': settings.MAGIC_LINK_EXPIRATION_HOURS,
                'system_name': getattr(settings, 'SYSTEM_NAME', 'Plataforma NR-1'),
                'company_name': getattr(settings, 'COMPANY_NAME', '3S Dev'),
            }

            # Renderizar HTML do email
            html_message = render_to_string('account/emails/password_reset.html', context)
            text_message = strip_tags(html_message)

            # Enviar email via Resend API
            response = requests.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {settings.API_RESEND}',
                    'Content-Type': 'application/json'
                },
                json={
                    'from': settings.DEFAULT_FROM_EMAIL,
                    'to': [user.email],
                    'subject': 'Redefinição de Senha - Plataforma NR-1',
                    'html': html_message,
                    'text': text_message
                }
            )

            if response.status_code == 200:
                logger.info(
                    f"Email de redefinição enviado com sucesso para: {user.email} | "
                    f"Token: {reset_token.token[:10]}..."
                )
                return True
            else:
                logger.error(
                    f"Erro ao enviar email de redefinição para {user.email}: "
                    f"Status {response.status_code} | {response.text}"
                )
                return False

        except Exception as e:
            logger.error(
                f"Erro ao enviar email de redefinição para {user.email}: {str(e)}",
                exc_info=True
            )
            return False

    @staticmethod
    def validate_token(token_string):
        """
        Valida um token de redefinição de senha
        Retorna o token se válido, None caso contrário
        """
        try:
            reset_token = PasswordResetToken.objects.get(token=token_string)

            if reset_token.is_valid():
                logger.info(
                    f"Token válido acessado: {token_string[:10]}... | "
                    f"Usuário: {reset_token.user.username}"
                )
                return reset_token
            else:
                reason = "usado" if reset_token.is_used else "expirado"
                logger.warning(
                    f"Token inválido ({reason}) acessado: {token_string[:10]}... | "
                    f"Usuário: {reset_token.user.username}"
                )
                return None

        except PasswordResetToken.DoesNotExist:
            logger.warning(f"Token não encontrado: {token_string[:10]}...")
            return None

    @staticmethod
    def reset_password(reset_token, new_password, ip_address=None, user_agent=None):
        """
        Redefine a senha do usuário usando um token válido
        """
        try:
            if not reset_token.is_valid():
                logger.warning(
                    f"Tentativa de usar token inválido: {reset_token.token[:10]}... | "
                    f"Usuário: {reset_token.user.username}"
                )
                return False

            # Atualizar senha
            user = reset_token.user
            user.set_password(new_password)
            user.save()

            # Marcar token como usado
            reset_token.mark_as_used(ip_address=ip_address, user_agent=user_agent)

            logger.info(
                f"Senha redefinida com sucesso para usuário: {user.username} | "
                f"IP: {ip_address}"
            )

            return True

        except Exception as e:
            logger.error(
                f"Erro ao redefinir senha: {str(e)}",
                exc_info=True
            )
            return False

    @staticmethod
    def request_password_reset(email, request):
        """
        Processa solicitação de redefinição de senha
        Retorna True se o email foi enviado com sucesso
        """
        try:
            # Buscar usuário por email
            user = User.objects.get(email__iexact=email, is_active=True)

            # Obter informações da requisição
            ip_address = PasswordResetService._get_client_ip(request)
            user_agent = PasswordResetService._get_user_agent(request)

            # Criar token
            reset_token = PasswordResetService.create_reset_token(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Enviar email
            success = PasswordResetService.send_reset_email(user, reset_token, request)

            return success

        except User.DoesNotExist:
            # Por segurança, não revelar se o email existe ou não
            logger.warning(f"Tentativa de redefinição para email inexistente: {email}")
            return True  # Retorna True para não revelar que o email não existe

        except Exception as e:
            logger.error(
                f"Erro ao processar solicitação de redefinição para {email}: {str(e)}",
                exc_info=True
            )
            return False

    @staticmethod
    def _get_client_ip(request):
        """Obtém o IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def _get_user_agent(request):
        """Obtém o User Agent"""
        return request.META.get('HTTP_USER_AGENT', '')

    @staticmethod
    def cleanup_expired_tokens():
        """
        Remove tokens expirados do banco de dados
        Deve ser executado periodicamente (cron job)
        """
        from django.utils import timezone
        from datetime import timedelta

        # Remove tokens expirados há mais de 7 dias
        cutoff_date = timezone.now() - timedelta(days=7)
        deleted_count = PasswordResetToken.objects.filter(
            expires_at__lt=cutoff_date
        ).delete()[0]

        if deleted_count > 0:
            logger.info(f"Limpeza de tokens: {deleted_count} tokens expirados removidos")

        return deleted_count
