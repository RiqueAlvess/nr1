from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger('nr1')


class AnonymityChecker:
    """Verificador de k-anonymity para proteger identificação"""
    
    @staticmethod
    def check_group_size(count: int) -> bool:
        """
        Verifica se o grupo atende ao tamanho mínimo para k-anonymity
        
        Args:
            count: Número de respondentes no grupo
        
        Returns:
            bool: True se o grupo pode ser exibido
        """
        return count >= settings.MIN_GROUP_SIZE
    
    @staticmethod
    def can_display_data(filters: Dict[str, Any], queryset) -> tuple[bool, Optional[str]]:
        """
        Verifica se os dados podem ser exibidos com os filtros aplicados
        
        Args:
            filters: Dicionários com filtros aplicados
            queryset: QuerySet para contar registros
        
        Returns:
            tuple: (pode_exibir, mensagem_erro)
        """
        count = queryset.count()
        
        if not AnonymityChecker.check_group_size(count):
            message = (
                f"Dados não podem ser exibidos. "
                f"O grupo possui apenas {count} respondente(s). "
                f"Mínimo necessário: {settings.MIN_GROUP_SIZE} para garantir anonimato."
            )
            logger.warning(f"Bloqueio por k-anonymity: {filters} | Count: {count}")
            return False, message
        
        return True, None
    
    @staticmethod
    def get_available_filters(base_queryset, current_filters: Dict[str, Any]) -> Dict[str, list]:
        """
        Retorna apenas os valores de filtro que mantêm k-anonymity
        
        Args:
            base_queryset: QuerySet base
            current_filters: Filtros já aplicados
        
        Returns:
            Dict com valores permitidos para cada dimensão
        """
        available = {}
        
        # Verificar unidades disponíveis
        unidades = base_queryset.values('colaborador__setor__unidade').distinct()
        available['unidades'] = [
            u['colaborador__setor__unidade'] 
            for u in unidades 
            if base_queryset.filter(
                colaborador__setor__unidade=u['colaborador__setor__unidade']
            ).count() >= settings.MIN_GROUP_SIZE
        ]
        
        # Verificar setores disponíveis
        if 'unidade' in current_filters:
            setores = base_queryset.filter(
                colaborador__setor__unidade=current_filters['unidade']
            ).values('colaborador__setor').distinct()
            
            available['setores'] = [
                s['colaborador__setor']
                for s in setores
                if base_queryset.filter(
                    colaborador__setor=s['colaborador__setor']
                ).count() >= settings.MIN_GROUP_SIZE
            ]
        
        return available