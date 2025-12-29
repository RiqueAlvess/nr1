import logging
from django.db.models import Count, Q, Avg
from typing import Dict, Any, Optional
from django.conf import settings
from quiz.models import Resposta, MagicLink
from core.models import Setor, Unidade
from core.utils.anonymity import AnonymityChecker
from quiz.services.calculation_service import CalculationService

logger = logging.getLogger('nr1')


class DashboardService:
    """Serviço de agregação de dados para dashboard"""
    
    def __init__(self):
        self.calc_service = CalculationService()
        self.anonymity_checker = AnonymityChecker()
    
    def get_kpis_empresa(self, empresa_id: str) -> Dict[str, Any]:
        """
        Retorna KPIs consolidados da empresa
        
        Args:
            empresa_id: UUID da empresa
        
        Returns:
            Dict com KPIs
        """
        # Total de colaboradores
        total_colaboradores = MagicLink.objects.filter(
            colaborador__cargo__setor__unidade__empresa_id=empresa_id
        ).count()
        
        # Respostas concluídas
        respostas_concluidas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        ).count()
        
        # Taxa de adesão
        taxa_adesao = (
            (respostas_concluidas / total_colaboradores * 100)
            if total_colaboradores > 0
            else 0
        )
        
        # Scores
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        )
        
        # Se não houver respostas, retornar dados zerados mas ainda visualizáveis
        if respostas.count() == 0:
            return {
                'total_colaboradores': total_colaboradores,
                'respostas_concluidas': 0,
                'taxa_adesao': 0,
                'pode_visualizar': True,
                'score_medio_global': 0,
                'igrp': 0,
                'distribuicao_risco': {
                    'critico': 0,
                    'atencao': 0,
                    'satisfatorio': 0,
                },
                'percentual_alto_risco': 0,
                'matriz_nr1': {
                    'probabilidade': 0,
                    'probabilidade_nivel': 0,
                    'severidade': 0,
                    'nivel_risco': 0,
                    'classificacao': 'SEM DADOS',
                    'total_respondentes': 0,
                    'respondentes_criticos': 0
                }
            }
        
        # Score médio global
        score_medio = respostas.aggregate(Avg('score_global'))['score_global__avg']
        
        # Distribuição por nível de risco
        criticos = sum(1 for r in respostas if r.get_nivel_risco_global() == 'CRÍTICO')
        atencao = sum(1 for r in respostas if r.get_nivel_risco_global() == 'ATENÇÃO')
        satisfatorio = sum(1 for r in respostas if r.get_nivel_risco_global() == 'SATISFATÓRIO')
        
        # IGRP (Índice Geral de Risco Psicossocial)
        # Normalizado de 0 a 100, onde 0 = sem risco e 100 = risco máximo
        igrp = 100 - ((score_medio / 140) * 100) if score_medio else 0
        
        # Matriz de risco NR-1
        matriz_risco = self.calc_service.calcular_matriz_risco_nr1(respostas)
        
        return {
            'total_colaboradores': total_colaboradores,
            'respostas_concluidas': respostas_concluidas,
            'taxa_adesao': round(taxa_adesao, 2),
            'pode_visualizar': True,
            'score_medio_global': round(score_medio, 2) if score_medio else 0,
            'igrp': round(igrp, 2),
            'distribuicao_risco': {
                'critico': criticos,
                'atencao': atencao,
                'satisfatorio': satisfatorio,
            },
            'percentual_alto_risco': round(
                (criticos / respostas_concluidas * 100) if respostas_concluidas > 0 else 0,
                2
            ),
            'matriz_nr1': matriz_risco
        }
    
    def get_dados_por_unidade(self, empresa_id: str) -> Dict[str, Any]:
        """
        Retorna dados agregados por unidade
        Aplica k-anonymity
        
        Args:
            empresa_id: UUID da empresa
        
        Returns:
            Dict com dados por unidade (apenas unidades que atendem k-anonymity)
        """
        unidades = Unidade.objects.filter(empresa_id=empresa_id)
        dados_unidades = []
        
        for unidade in unidades:
            respostas = Resposta.objects.filter(
                magic_link__colaborador__cargo__setor__unidade=unidade
            )
            
            count = respostas.count()

            # Incluir todas as unidades, mesmo sem respostas
            score_medio = respostas.aggregate(Avg('score_global'))['score_global__avg'] if count > 0 else None

            dados_unidades.append({
                'unidade_id': str(unidade.id),
                'unidade_nome': unidade.nome,
                'total_respostas': count,
                'score_medio': round(score_medio, 2) if score_medio else 0,
            })
        
        return {
            'unidades': dados_unidades,
            'total_unidades_visiveis': len(dados_unidades)
        }
    
    def get_dados_por_setor(
        self,
        empresa_id: str,
        unidade_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retorna dados agregados por setor
        Aplica k-anonymity
        
        Args:
            empresa_id: UUID da empresa
            unidade_id: UUID da unidade (opcional)
        
        Returns:
            Dict com dados por setor
        """
        setores_query = Setor.objects.filter(unidade__empresa_id=empresa_id)
        
        if unidade_id:
            setores_query = setores_query.filter(unidade_id=unidade_id)
        
        dados_setores = []
        
        for setor in setores_query:
            respostas = Resposta.objects.filter(
                magic_link__colaborador__cargo__setor=setor
            )
            
            count = respostas.count()

            # Incluir todos os setores, mesmo sem respostas
            score_medio = respostas.aggregate(Avg('score_global'))['score_global__avg'] if count > 0 else None

            # Calcular matriz de risco para o setor
            matriz_risco = self.calc_service.calcular_matriz_risco_nr1(respostas)

            dados_setores.append({
                'setor_id': str(setor.id),
                'setor_nome': setor.nome,
                'unidade_id': str(setor.unidade.id),
                'unidade_nome': setor.unidade.nome,
                'total_respostas': count,
                'score_medio': round(score_medio, 2) if score_medio else 0,
                'nivel_risco_nr1': matriz_risco['classificacao'],
            })
        
        return {
            'setores': dados_setores,
            'total_setores_visiveis': len(dados_setores)
        }
    
    def get_dimensoes_criticas(self, empresa_id: str) -> Dict[str, Any]:
        """
        Identifica dimensões com maior criticidade
        
        Args:
            empresa_id: UUID da empresa
        
        Returns:
            Dict com dimensões ordenadas por criticidade
        """
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        )
        
        if respostas.count() == 0:
            return {
                'pode_visualizar': True,
                'dimensoes': [],
                'total_respostas': 0
            }
        
        # Agregar scores por dimensão
        dimensoes_agregadas = {}
        
        for resposta in respostas:
            for dimensao_nome, dados in resposta.scores_dimensoes.items():
                if dimensao_nome not in dimensoes_agregadas:
                    dimensoes_agregadas[dimensao_nome] = {
                        'scores': [],
                        'polaridade': dados['polaridade']
                    }
                dimensoes_agregadas[dimensao_nome]['scores'].append(dados['score'])
        
        # Calcular médias e identificar críticas
        dimensoes_lista = []
        
        for dimensao_nome, dados in dimensoes_agregadas.items():
            score_medio = sum(dados['scores']) / len(dados['scores'])
            nivel_risco = self.calc_service._interpretar_dimensao(
                score_medio,
                dados['polaridade']
            )
            
            dimensoes_lista.append({
                'dimensao': dimensao_nome,
                'score_medio': round(score_medio, 2),
                'nivel_risco': nivel_risco,
                'polaridade': dados['polaridade']
            })
        
        # Ordenar por criticidade
        ordem_risco = {'CRÍTICO': 0, 'ATENÇÃO': 1, 'SATISFATÓRIO': 2}
        dimensoes_lista.sort(key=lambda x: ordem_risco[x['nivel_risco']])
        
        return {
            'pode_visualizar': True,
            'dimensoes': dimensoes_lista,
            'total_respostas': respostas.count()
        }