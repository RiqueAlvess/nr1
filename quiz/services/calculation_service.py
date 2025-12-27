import logging
from typing import Dict, Any
from quiz.models import Pergunta, Dimensao

logger = logging.getLogger('nr1')


class CalculationService:
    """Serviço de cálculo de scores e riscos psicossociais"""
    
    def calcular_score_global(self, respostas: Dict[str, int]) -> float:
        """
        Calcula score global (soma das 35 respostas)
        
        Args:
            respostas: Dict com formato {"1": 3, "2": 4, ...}
        
        Returns:
            float: Score global (0-140, mas normalizado para 0-105 na interpretação)
        """
        total = sum(respostas.values())
        return total
    
    def calcular_scores_dimensoes(self, respostas: Dict[str, int]) -> Dict[str, Any]:
        """
        Calcula score médio para cada dimensão
        
        Args:
            respostas: Dict com respostas
        
        Returns:
            Dict: Scores por dimensão com interpretação
        """
        dimensoes = Dimensao.objects.prefetch_related('perguntas').filter(ativa=True)
        scores = {}
        
        for dimensao in dimensoes:
            perguntas_dimensao = dimensao.perguntas.filter(ativa=True)
            
            # Calcular média das respostas desta dimensão
            valores = []
            for pergunta in perguntas_dimensao:
                numero_str = str(pergunta.numero)
                if numero_str in respostas:
                    valores.append(respostas[numero_str])
            
            if valores:
                score_medio = sum(valores) / len(valores)
                nivel_risco = self._interpretar_dimensao(score_medio, dimensao.polaridade)
                
                scores[dimensao.nome] = {
                    'score': round(score_medio, 2),
                    'nivel_risco': nivel_risco,
                    'polaridade': dimensao.polaridade,
                    'total_perguntas': len(valores)
                }
        
        return scores
    
    def _interpretar_dimensao(self, score: float, polaridade: str) -> str:
        """
        Interpreta score de uma dimensão
        
        Args:
            score: Score médio (0-4)
            polaridade: POSITIVA ou NEGATIVA
        
        Returns:
            str: Nível de risco
        """
        if polaridade == 'NEGATIVA':
            # Maior pontuação = maior risco
            if score >= 3:
                return 'CRÍTICO'
            elif score >= 2:
                return 'ATENÇÃO'
            else:
                return 'SATISFATÓRIO'
        else:  # POSITIVA
            # Menor pontuação = maior risco
            if score <= 1:
                return 'CRÍTICO'
            elif score <= 2:
                return 'ATENÇÃO'
            else:
                return 'SATISFATÓRIO'
    
    def calcular_matriz_risco_nr1(
        self,
        respostas_queryset,
        filtros: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Calcula matriz de risco NR-1 para um grupo
        
        Args:
            respostas_queryset: QuerySet de Respostas
            filtros: Filtros aplicados (para auditoria)
        
        Returns:
            Dict com probabilidade, severidade e nível de risco
        """
        total_respondentes = respostas_queryset.count()
        
        if total_respondentes == 0:
            return {
                'probabilidade': 0,
                'severidade': 0,
                'nivel_risco': 0,
                'classificacao': 'SEM DADOS'
            }
        
        # Contar respondentes em risco crítico
        criticos = 0
        for resposta in respostas_queryset:
            if resposta.get_nivel_risco_global() == 'CRÍTICO':
                criticos += 1
        
        # Probabilidade = proporção de críticos
        probabilidade = (criticos / total_respondentes) * 100
        
        # Severidade (definida pelo impacto à saúde)
        # Simplificado: severidade fixa para riscos psicossociais
        severidade = 4  # Alta severidade por padrão
        
        # Nível de Risco (NR) = Probabilidade x Severidade
        if probabilidade >= 50:
            prob_nivel = 4
        elif probabilidade >= 25:
            prob_nivel = 3
        elif probabilidade >= 10:
            prob_nivel = 2
        else:
            prob_nivel = 1
        
        nivel_risco = prob_nivel * severidade
        
        # Classificação
        if nivel_risco >= 12:
            classificacao = 'CRÍTICO'
        elif nivel_risco >= 6:
            classificacao = 'ALTO'
        elif nivel_risco >= 3:
            classificacao = 'MÉDIO'
        else:
            classificacao = 'BAIXO'
        
        return {
            'probabilidade': round(probabilidade, 2),
            'probabilidade_nivel': prob_nivel,
            'severidade': severidade,
            'nivel_risco': nivel_risco,
            'classificacao': classificacao,
            'total_respondentes': total_respondentes,
            'respondentes_criticos': criticos
        }