import logging
from core.models import AuditLog
from django.contrib.auth.models import User
from typing import Optional, Dict, Any

logger = logging.getLogger('nr1')


class AuditService:
    """Serviço centralizado de auditoria"""
    
    @staticmethod
    def log(
        action: str,
        description: str,
        user: Optional[User] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Registra evento de auditoria
        
        Args:
            action: Tipo de ação (deve estar em AuditLog.ACTION_CHOICES)
            description: Descrição detalhada do evento
            user: Usuário que executou a ação (se aplicável)
            ip_address: IP de origem
            user_agent: User agent do navegador
            metadata: Dados adicionais em formato JSON
        
        Returns:
            AuditLog: Registro criado
        """
        try:
            audit_entry = AuditLog.objects.create(
                action=action,
                description=description,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            logger.info(
                f"Audit: {action} | User: {user.username if user else 'Anonymous'} | {description}"
            )
            
            return audit_entry
            
        except Exception as e:
            logger.error(f"Erro ao registrar auditoria: {str(e)}")
            raise
    
    @staticmethod
    def get_client_ip(request) -> Optional[str]:
        """Extrai IP do cliente da requisição"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def get_user_agent(request) -> str:
        """Extrai user agent da requisição"""
        return request.META.get('HTTP_USER_AGENT', '')