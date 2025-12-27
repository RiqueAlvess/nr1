import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from typing import List, Tuple
from quiz.models import MagicLink
from importacao.models import Colaborador
from core.services.email_service import EmailService
from core.services.audit_service import AuditService

logger = logging.getLogger('nr1')


class MagicLinkService:
    """Serviço de geração e envio de magic links"""
    
    @staticmethod
    def gerar_magic_links_bulk(colaboradores_ids: List[str]) -> Tuple[int, int]:
        """
        Gera magic links em massa para colaboradores
        
        Args:
            colaboradores_ids: Lista de UUIDs de colaboradores
        
        Returns:
            Tuple: (total gerados, total já existentes)
        """
        gerados = 0
        ja_existentes = 0
        
        colaboradores = Colaborador.objects.filter(
            id__in=colaboradores_ids,
            ativo=True
        )
        
        for colaborador in colaboradores:
            # Verificar se já existe magic link
            if hasattr(colaborador, 'magic_link'):
                ja_existentes += 1
                continue
            
            # Gerar token
            token = MagicLink.gerar_token()
            token_hash = MagicLink.hash_token(token)
            
            # Calcular expiração
            expires_at = timezone.now() + timedelta(
                hours=settings.MAGIC_LINK_EXPIRATION_HOURS
            )
            
            # Criar magic link
            magic_link = MagicLink.objects.create(
                colaborador=colaborador,
                token_hash=token_hash,
                expires_at=expires_at
            )
            
            # Auditoria
            AuditService.log(
                action='MAGIC_LINK_GENERATED',
                description=f'Magic link gerado para colaborador {str(colaborador.id)[:8]}',
                metadata={
                    'magic_link_id': str(magic_link.id),
                    'expires_at': expires_at.isoformat()
                }
            )
            
            gerados += 1
        
        return gerados, ja_existentes
    
    @staticmethod
    def enviar_magic_links_bulk(
        colaboradores_ids: List[str],
        base_url: str
    ) -> Tuple[int, int]:
        """
        Envia magic links em massa por email
        
        Args:
            colaboradores_ids: Lista de UUIDs de colaboradores
            base_url: URL base do sistema (ex: https://nr1.example.com)
        
        Returns:
            Tuple: (total enviados, total erros)
        """
        enviados = 0
        erros = 0
        
        colaboradores = Colaborador.objects.filter(
            id__in=colaboradores_ids,
            ativo=True
        ).select_related('magic_link')
        
        for colaborador in colaboradores:
            if not hasattr(colaborador, 'magic_link'):
                logger.warning(f"Colaborador {colaborador.id} não possui magic link")
                erros += 1
                continue
            
            magic_link = colaborador.magic_link
            
            if magic_link.status == 'COMPLETED':
                logger.info(f"Magic link {magic_link.id} já foi usado")
                erros += 1
                continue
            
            # Recriar token (apenas para envio, não armazenado)
            # Na prática, precisamos armazenar o token temporariamente
            # Vamos ajustar: o token será gerado e o link completo criado
            
            # Gerar novo token
            token = MagicLink.gerar_token()
            token_hash = MagicLink.hash_token(token)
            
            # Atualizar hash (para próximo uso)
            magic_link.token_hash = token_hash
            magic_link.save()
            
            # Construir URL completa
            quiz_path = reverse('quiz:responder', kwargs={'token': token})
            magic_link_url = f"{base_url}{quiz_path}"
            
            # Enviar email
            sucesso = EmailService.send_magic_link(
                email=colaborador.email,
                magic_link=magic_link_url
            )
            
            if sucesso:
                enviados += 1
                
                # Auditoria
                AuditService.log(
                    action='MAGIC_LINK_SENT',
                    description=f'Magic link enviado para {colaborador.email}',
                    metadata={
                        'magic_link_id': str(magic_link.id),
                        'colaborador_id': str(colaborador.id)
                    }
                )
            else:
                erros += 1
        
        return enviados, erros
    
    @staticmethod
    def validar_token(token: str) -> MagicLink | None:
        """
        Valida token e retorna magic link se válido
        
        Args:
            token: Token em texto puro
        
        Returns:
            MagicLink ou None se inválido
        """
        token_hash = MagicLink.hash_token(token)
        
        try:
            magic_link = MagicLink.objects.select_related('colaborador').get(
                token_hash=token_hash
            )
            
            if magic_link.is_valid():
                return magic_link
            
            return None
            
        except MagicLink.DoesNotExist:
            return None