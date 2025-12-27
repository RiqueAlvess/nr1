import httpx
import logging
from django.conf import settings
from typing import List, Optional

logger = logging.getLogger('nr1')


class EmailService:
    """Serviço de envio de emails via Resend API"""
    
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
                    logger.info(f"Email enviado com sucesso para {', '.join(to)}")
                    return True
                else:
                    logger.error(
                        f"Erro ao enviar email: {response.status_code} - {response.text}"
                    )
                    return False
                    
        except httpx.TimeoutException:
            logger.error("Timeout ao enviar email via Resend API")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar email: {str(e)}")
            return False
    
    @staticmethod
    def send_magic_link(email: str, magic_link: str) -> bool:
        """
        Envia magic link para responder questionário
        
        Args:
            email: Email do destinatário
            magic_link: URL completa do magic link
        
        Returns:
            bool: True se enviado com sucesso
        """
        subject = "Convite para Avaliação de Riscos Psicossociais - NR-1"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Avaliação de Riscos Psicossociais</h2>
                
                <p>Você está sendo convidado(a) a participar da avaliação de riscos psicossociais de sua organização, conforme NR-1.</p>
                
                <p><strong>Informações importantes:</strong></p>
                <ul>
                    <li>Suas respostas são <strong>totalmente anônimas</strong></li>
                    <li>O questionário leva aproximadamente 10-15 minutos</li>
                    <li>Este link é válido por 48 horas</li>
                    <li>Após responder, o link expira automaticamente</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{magic_link}" 
                       style="background-color: #2563eb; color: white; padding: 15px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Responder Questionário
                    </a>
                </div>
                
                <p style="font-size: 12px; color: #666; margin-top: 30px;">
                    Se você não solicitou esta avaliação, pode ignorar este email com segurança.
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                
                <p style="font-size: 12px; color: #999;">
                    {settings.SYSTEM_NAME} | {settings.COMPANY_NAME}
                </p>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(
            to=[email],
            subject=subject,
            html_content=html_content
        )