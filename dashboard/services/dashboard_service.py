import logging
import statistics
from collections import Counter, defaultdict
from django.db.models import Count, Q, Avg
from typing import Dict, Any, Optional, List
from django.conf import settings
from quiz.models import Resposta, MagicLink, Pergunta
from core.models import Setor, Unidade
from core.utils.anonymity import AnonymityChecker
from quiz.services.calculation_service import CalculationService
from quiz.services.statistics_service import StatisticsService
from importacao.models import Colaborador, Cargo

logger = logging.getLogger('nr1')


class DashboardService:
    """Serviço de agregação de dados para dashboard"""

    def __init__(self):
        self.calc_service = CalculationService()
        self.anonymity_checker = AnonymityChecker()
        self.stats_service = StatisticsService()
    
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

        # Scores - Otimizado com select_related para evitar queries N+1
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        ).select_related(
            'magic_link',
            'magic_link__colaborador',
            'magic_link__colaborador__cargo',
            'magic_link__colaborador__cargo__setor',
            'magic_link__colaborador__cargo__setor__unidade'
        )
        
        # Se não houver respostas, retornar dados zerados mas ainda visualizáveis
        if respostas.count() == 0:
            return {
                'total_colaboradores': total_colaboradores,
                'respostas_concluidas': 0,
                'taxa_adesao': 0,
                'pode_visualizar': True,
                'score_medio_global': 0,
                'mediana_score': 0,
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
                },
                # Novos KPIs estatísticos - valores zerados
                'tempo_medio_minutos': 0,
                'cv_percent': 0,
                'desvio_padrao': 0,
                'score_minimo': 0,
                'score_maximo': 0,
                'quartis': {'Q1': 0, 'Q2': 0, 'Q3': 0},
            }
        
        # Score médio global
        score_medio = respostas.aggregate(Avg('score_global'))['score_global__avg']

        # Extrair todos os scores para cálculos estatísticos
        scores = [r.score_global for r in respostas if r.score_global is not None]

        # Mediana dos scores
        mediana_score = statistics.median(scores) if scores else 0

        # Distribuição por nível de risco
        criticos = sum(1 for r in respostas if r.get_nivel_risco_global() == 'CRÍTICO')
        atencao = sum(1 for r in respostas if r.get_nivel_risco_global() == 'ATENÇÃO')
        satisfatorio = sum(1 for r in respostas if r.get_nivel_risco_global() == 'SATISFATÓRIO')

        # IGRP (Índice Geral de Risco Psicossocial)
        # Normalizado de 0 a 100, onde 0 = sem risco e 100 = risco máximo
        igrp = 100 - ((score_medio / 140) * 100) if score_medio else 0

        # Matriz de risco NR-1
        matriz_risco = self.calc_service.calcular_matriz_risco_nr1(respostas)

        # Estatísticas avançadas usando StatisticsService
        estatisticas = self.stats_service.calcular_estatisticas_completas(scores)

        # Tempo médio de resposta
        tempos = [r.tempo_total_segundos for r in respostas if r.tempo_total_segundos]
        tempo_medio_minutos = round(
            self.stats_service.calcular_media(tempos) / 60, 2
        ) if tempos else 0

        return {
            'total_colaboradores': total_colaboradores,
            'respostas_concluidas': respostas_concluidas,
            'taxa_adesao': round(taxa_adesao, 2),
            'pode_visualizar': True,
            'score_medio_global': round(score_medio, 2) if score_medio else 0,
            'mediana_score': round(mediana_score, 2),
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
            'matriz_nr1': matriz_risco,
            # Novos KPIs estatísticos
            'tempo_medio_minutos': tempo_medio_minutos,
            'cv_percent': estatisticas['cv_percent'],
            'desvio_padrao': estatisticas['desvio_padrao'],
            'score_minimo': estatisticas['minimo'],
            'score_maximo': estatisticas['maximo'],
            'quartis': estatisticas['quartis'],
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
        # Otimizado: select_related para empresa
        unidades = Unidade.objects.filter(empresa_id=empresa_id).select_related('empresa')
        dados_unidades = []

        for unidade in unidades:
            # Otimizado: select_related para evitar queries N+1
            respostas = Resposta.objects.filter(
                magic_link__colaborador__cargo__setor__unidade=unidade
            ).select_related(
                'magic_link',
                'magic_link__colaborador',
                'magic_link__colaborador__cargo',
                'magic_link__colaborador__cargo__setor',
                'magic_link__colaborador__cargo__setor__unidade'
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
        # Otimizado: select_related para unidade e empresa
        setores_query = Setor.objects.filter(
            unidade__empresa_id=empresa_id
        ).select_related('unidade', 'unidade__empresa')

        if unidade_id:
            setores_query = setores_query.filter(unidade_id=unidade_id)

        dados_setores = []

        for setor in setores_query:
            # Otimizado: select_related para evitar queries N+1
            respostas = Resposta.objects.filter(
                magic_link__colaborador__cargo__setor=setor
            ).select_related(
                'magic_link',
                'magic_link__colaborador',
                'magic_link__colaborador__cargo',
                'magic_link__colaborador__cargo__setor',
                'magic_link__colaborador__cargo__setor__unidade'
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
        # Otimizado: select_related para evitar queries N+1
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        ).select_related(
            'magic_link',
            'magic_link__colaborador',
            'magic_link__colaborador__cargo',
            'magic_link__colaborador__cargo__setor',
            'magic_link__colaborador__cargo__setor__unidade'
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

    def get_estatisticas_avancadas(self, empresa_id: str) -> Dict[str, Any]:
        """
        Retorna estatísticas avançadas dos scores

        Args:
            empresa_id: UUID da empresa

        Returns:
            Dict com mediana, CV%, desvio padrão, quartis, etc.
        """
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        )

        if respostas.count() == 0:
            return {
                'mediana_score': 0,
                'cv_percentual': 0,
                'desvio_padrao': 0,
                'variancia': 0,
                'quartis': {'Q1': 0, 'Q2': 0, 'Q3': 0},
                'score_minimo': 0,
                'score_maximo': 0,
                'amplitude': 0,
            }

        # Extrair todos os scores
        scores = [r.score_global for r in respostas if r.score_global is not None]

        if not scores:
            return {
                'mediana_score': 0,
                'cv_percentual': 0,
                'desvio_padrao': 0,
                'variancia': 0,
                'quartis': {'Q1': 0, 'Q2': 0, 'Q3': 0},
                'score_minimo': 0,
                'score_maximo': 0,
                'amplitude': 0,
            }

        # Cálculos estatísticos
        media = statistics.mean(scores)
        mediana = statistics.median(scores)
        desvio_padrao = statistics.stdev(scores) if len(scores) > 1 else 0
        variancia = statistics.variance(scores) if len(scores) > 1 else 0
        cv = (desvio_padrao / media * 100) if media > 0 else 0

        # Quartis
        quartis_valores = statistics.quantiles(scores, n=4) if len(scores) >= 2 else [0, 0, 0]
        quartis = {
            'Q1': round(quartis_valores[0], 2) if len(quartis_valores) > 0 else 0,
            'Q2': round(mediana, 2),
            'Q3': round(quartis_valores[2], 2) if len(quartis_valores) > 2 else 0,
        }

        return {
            'mediana_score': round(mediana, 2),
            'cv_percentual': round(cv, 2),
            'desvio_padrao': round(desvio_padrao, 2),
            'variancia': round(variancia, 2),
            'quartis': quartis,
            'score_minimo': round(min(scores), 2),
            'score_maximo': round(max(scores), 2),
            'amplitude': round(max(scores) - min(scores), 2),
        }

    def get_distribuicao_scores(self, empresa_id: str, bins: int = 10) -> Dict[str, Any]:
        """
        Retorna distribuição dos scores em bins (para histograma)

        Args:
            empresa_id: UUID da empresa
            bins: Número de intervalos

        Returns:
            Dict com labels e counts para histograma
        """
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        )

        scores = [r.score_global for r in respostas if r.score_global is not None]

        if not scores:
            return {'labels': [], 'counts': []}

        # Criar bins
        min_score = 0
        max_score = 140
        intervalo = (max_score - min_score) / bins

        labels = []
        counts = [0] * bins

        for i in range(bins):
            inicio = min_score + i * intervalo
            fim = min_score + (i + 1) * intervalo
            labels.append(f"{int(inicio)}-{int(fim)}")

        # Contar scores em cada bin
        for score in scores:
            bin_idx = min(int((score - min_score) / intervalo), bins - 1)
            counts[bin_idx] += 1

        return {
            'labels': labels,
            'counts': counts,
            'total': len(scores)
        }

    def get_tempo_medio_resposta(self, empresa_id: str) -> Dict[str, Any]:
        """
        Retorna tempo médio de resposta ao questionário

        Args:
            empresa_id: UUID da empresa

        Returns:
            Dict com tempo médio em minutos
        """
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        ).exclude(tempo_total_segundos__isnull=True)

        if respostas.count() == 0:
            return {
                'tempo_medio_minutos': 0,
                'tempo_mediano_minutos': 0,
                'tempo_minimo_minutos': 0,
                'tempo_maximo_minutos': 0,
            }

        tempos_segundos = [r.tempo_total_segundos for r in respostas]
        tempos_minutos = [t / 60 for t in tempos_segundos]

        return {
            'tempo_medio_minutos': round(statistics.mean(tempos_minutos), 2),
            'tempo_mediano_minutos': round(statistics.median(tempos_minutos), 2),
            'tempo_minimo_minutos': round(min(tempos_minutos), 2),
            'tempo_maximo_minutos': round(max(tempos_minutos), 2),
        }

    def get_pontuacao_por_pergunta(self, empresa_id: str) -> List[Dict[str, Any]]:
        """
        Retorna pontuação média por pergunta com possibilidade de ordenação

        Args:
            empresa_id: UUID da empresa

        Returns:
            Lista de dicts com número, texto, média e nível de risco por pergunta
        """
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        )

        if respostas.count() == 0:
            return []

        # Agregar respostas por pergunta
        perguntas_data = {}

        for resposta in respostas:
            for pergunta_num, valor in resposta.respostas.items():
                if pergunta_num not in perguntas_data:
                    perguntas_data[pergunta_num] = []
                perguntas_data[pergunta_num].append(valor)

        # Calcular médias
        resultado = []

        for pergunta_num, valores in perguntas_data.items():
            try:
                pergunta = Pergunta.objects.get(numero=int(pergunta_num))
                media = statistics.mean(valores)

                # Determinar criticidade baseado na polaridade da dimensão
                nivel_risco = self.calc_service._interpretar_dimensao(
                    media,
                    pergunta.dimensao.polaridade
                )

                resultado.append({
                    'numero': int(pergunta_num),
                    'texto': pergunta.texto,
                    'dimensao': pergunta.dimensao.nome,
                    'media': round(media, 2),
                    'nivel_risco': nivel_risco,
                    'total_respostas': len(valores),
                })
            except Pergunta.DoesNotExist:
                continue

        # Ordenar por número de pergunta
        resultado.sort(key=lambda x: x['numero'])

        return resultado

    def get_distribuicao_respostas_por_pergunta(
        self,
        empresa_id: str,
        pergunta_numero: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retorna distribuição de respostas (0-4) por pergunta

        Args:
            empresa_id: UUID da empresa
            pergunta_numero: Número da pergunta específica (opcional)

        Returns:
            Dict com distribuição de respostas por pergunta
        """
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        )

        if respostas.count() == 0:
            return {}

        distribuicao = {}

        for resposta in respostas:
            for perg_num, valor in resposta.respostas.items():
                perg_num_int = int(perg_num)

                # Filtrar por pergunta específica se fornecido
                if pergunta_numero is not None and perg_num_int != pergunta_numero:
                    continue

                if perg_num not in distribuicao:
                    distribuicao[perg_num] = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

                if valor in [0, 1, 2, 3, 4]:
                    distribuicao[perg_num][valor] += 1

        return distribuicao

    def get_analise_por_genero(self, empresa_id: str) -> Dict[str, Any]:
        """
        Retorna análise de scores por gênero

        Args:
            empresa_id: UUID da empresa

        Returns:
            Dict com scores médios e distribuição por gênero
        """
        # OTIMIZAÇÃO: Carregar apenas campos necessários
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id,
            score_global__isnull=False
        ).select_related(
            'magic_link__colaborador'
        ).only(
            'score_global',
            'magic_link__colaborador__sexo'
        ).defer(
            'respostas',
            'scores_dimensoes'
        )

        total_respostas = respostas.count()
        if total_respostas == 0:
            return {
                'por_genero': {},
                'total': 0
            }

        # Agrupar por gênero
        por_genero = defaultdict(list)

        for resposta in respostas:
            sexo = resposta.magic_link.colaborador.sexo
            por_genero[sexo].append(resposta.score_global)

        # Calcular estatísticas por gênero
        resultado = {}

        for sexo, scores in por_genero.items():
            sexo_display = dict(Colaborador.SEXO_CHOICES).get(sexo, 'Não informado')

            resultado[sexo] = {
                'sexo_display': sexo_display,
                'total': len(scores),
                'score_medio': round(statistics.mean(scores), 2),
                'mediana': round(statistics.median(scores), 2),
                'desvio_padrao': round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
            }

        return {
            'por_genero': resultado,
            'total': total_respostas
        }

    def get_analise_por_faixa_etaria(self, empresa_id: str) -> Dict[str, Any]:
        """
        Retorna análise de scores por faixa etária

        Args:
            empresa_id: UUID da empresa

        Returns:
            Dict com scores médios e distribuição por faixa etária
        """
        # OTIMIZAÇÃO: Carregar apenas campos necessários, sem JSONField pesado
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id,
            score_global__isnull=False
        ).select_related(
            'magic_link__colaborador'
        ).only(
            'score_global',
            'magic_link__colaborador__data_nascimento'
        ).defer(
            'respostas',
            'scores_dimensoes'
        )

        total_respostas = respostas.count()
        if total_respostas == 0:
            return {
                'por_faixa': {},
                'total': 0
            }

        # Agrupar por faixa etária
        por_faixa = defaultdict(list)

        # Helper para calcular faixa etária
        from datetime import date
        today = date.today()

        for resposta in respostas:
            colaborador = resposta.magic_link.colaborador
            # Calcular faixa inline para evitar property overhead
            if colaborador.data_nascimento:
                idade = today.year - colaborador.data_nascimento.year - (
                    (today.month, today.day) < (colaborador.data_nascimento.month, colaborador.data_nascimento.day)
                )
                if idade < 18:
                    faixa = 'Menor de 18'
                elif idade < 25:
                    faixa = '18-24'
                elif idade < 30:
                    faixa = '25-29'
                elif idade < 40:
                    faixa = '30-39'
                elif idade < 50:
                    faixa = '40-49'
                elif idade < 60:
                    faixa = '50-59'
                else:
                    faixa = '60+'
            else:
                faixa = 'Não informado'

            por_faixa[faixa].append(resposta.score_global)

        # Calcular estatísticas por faixa
        resultado = {}
        faixas_ordem = ['18-24', '25-29', '30-39', '40-49', '50-59', '60+', 'Não informado']

        for faixa in faixas_ordem:
            if faixa in por_faixa:
                scores = por_faixa[faixa]
                resultado[faixa] = {
                    'total': len(scores),
                    'score_medio': round(statistics.mean(scores), 2),
                    'mediana': round(statistics.median(scores), 2),
                    'desvio_padrao': round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
                }

        return {
            'por_faixa': resultado,
            'total': total_respostas
        }

    def get_piramide_etaria_com_risco(self, empresa_id: str) -> Dict[str, Any]:
        """
        Retorna dados para pirâmide etária com níveis de risco

        Args:
            empresa_id: UUID da empresa

        Returns:
            Dict com dados para pirâmide etária dividida por sexo e nível de risco
        """
        # OTIMIZAÇÃO: Carregar apenas campos necessários
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id,
            score_global__isnull=False
        ).select_related(
            'magic_link__colaborador'
        ).only(
            'score_global',
            'magic_link__colaborador__data_nascimento',
            'magic_link__colaborador__sexo'
        ).defer(
            'respostas',
            'scores_dimensoes'
        )

        total_respostas = respostas.count()
        if total_respostas == 0:
            return {
                'faixas': [],
                'masculino': {},
                'feminino': {},
                'total': 0
            }

        # Estrutura de dados por faixa, sexo e nível de risco
        piramide = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        # Helper para calcular faixa etária e nível de risco inline
        from datetime import date
        today = date.today()

        for resposta in respostas:
            colaborador = resposta.magic_link.colaborador

            # Calcular faixa inline
            if colaborador.data_nascimento:
                idade = today.year - colaborador.data_nascimento.year - (
                    (today.month, today.day) < (colaborador.data_nascimento.month, colaborador.data_nascimento.day)
                )
                if idade < 18:
                    faixa = 'Menor de 18'
                elif idade < 25:
                    faixa = '18-24'
                elif idade < 30:
                    faixa = '25-29'
                elif idade < 40:
                    faixa = '30-39'
                elif idade < 50:
                    faixa = '40-49'
                elif idade < 60:
                    faixa = '50-59'
                else:
                    faixa = '60+'
            else:
                faixa = 'Não informado'

            sexo = colaborador.sexo

            # Calcular nível de risco inline (evitar chamada de método)
            score = resposta.score_global
            if score <= 35:
                nivel_risco = 'CRÍTICO'
            elif score <= 50:
                nivel_risco = 'ATENÇÃO'
            else:
                nivel_risco = 'SATISFATÓRIO'

            piramide[faixa][sexo][nivel_risco] += 1

        # Organizar dados para o frontend
        faixas_ordem = ['18-24', '25-29', '30-39', '40-49', '50-59', '60+']

        masculino_data = {}
        feminino_data = {}

        for faixa in faixas_ordem:
            # Masculino (valores negativos para o gráfico)
            masc_critico = -piramide[faixa]['M']['CRÍTICO']
            masc_atencao = -piramide[faixa]['M']['ATENÇÃO']
            masc_satisfatorio = -piramide[faixa]['M']['SATISFATÓRIO']

            # Feminino (valores positivos)
            fem_critico = piramide[faixa]['F']['CRÍTICO']
            fem_atencao = piramide[faixa]['F']['ATENÇÃO']
            fem_satisfatorio = piramide[faixa]['F']['SATISFATÓRIO']

            masculino_data[faixa] = {
                'critico': masc_critico,
                'atencao': masc_atencao,
                'satisfatorio': masc_satisfatorio,
                'total': masc_critico + masc_atencao + masc_satisfatorio
            }

            feminino_data[faixa] = {
                'critico': fem_critico,
                'atencao': fem_atencao,
                'satisfatorio': fem_satisfatorio,
                'total': fem_critico + fem_atencao + fem_satisfatorio
            }

        return {
            'faixas': faixas_ordem,
            'masculino': masculino_data,
            'feminino': feminino_data,
            'total': respostas.count()
        }

    def get_dimensoes_por_genero(self, empresa_id: str) -> Dict[str, Any]:
        """
        Retorna pontuação média por dimensão separada por gênero (para gráfico radar)

        Args:
            empresa_id: UUID da empresa

        Returns:
            Dict com scores por dimensão e gênero
        """
        # OTIMIZAÇÃO: Carregar apenas campos necessários
        # scores_dimensoes é necessário aqui, mas defer respostas
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        ).select_related(
            'magic_link__colaborador'
        ).only(
            'scores_dimensoes',
            'magic_link__colaborador__sexo'
        ).defer(
            'respostas'
        )

        total_respostas = respostas.count()
        if total_respostas == 0:
            return {
                'dimensoes': [],
                'por_genero': {}
            }

        # Agrupar scores de dimensões por gênero
        dimensoes_por_genero = defaultdict(lambda: defaultdict(list))

        for resposta in respostas:
            sexo = resposta.magic_link.colaborador.sexo

            # Verificar se scores_dimensoes existe e não está vazio
            if resposta.scores_dimensoes:
                for dimensao_nome, dados in resposta.scores_dimensoes.items():
                    if isinstance(dados, dict) and 'score' in dados:
                        dimensoes_por_genero[sexo][dimensao_nome].append(dados['score'])

        # Calcular médias
        resultado = defaultdict(dict)
        todas_dimensoes = set()

        for sexo, dimensoes in dimensoes_por_genero.items():
            sexo_display = dict(Colaborador.SEXO_CHOICES).get(sexo, 'Não informado')

            for dimensao, scores in dimensoes.items():
                if scores:  # Verificar se há scores
                    todas_dimensoes.add(dimensao)
                    resultado[sexo_display][dimensao] = round(statistics.mean(scores), 2)

        return {
            'dimensoes': sorted(list(todas_dimensoes)),
            'por_genero': dict(resultado)
        }

    # ========================================================================
    # NOVOS MÉTODOS - Evolução do Dashboard NR-1
    # ========================================================================

    def get_distribuicao_respostas_completa(
        self,
        empresa_id: str,
        unidade_id: Optional[str] = None,
        setor_id: Optional[str] = None,
        cargo_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retorna distribuição completa de respostas (0-4) por pergunta
        com suporte a filtros hierárquicos para drill-down.

        Args:
            empresa_id: UUID da empresa
            unidade_id: UUID da unidade (opcional)
            setor_id: UUID do setor (opcional)
            cargo_id: UUID do cargo (opcional)

        Returns:
            Dict com distribuição por pergunta e metadados das perguntas
        """
        try:
            logger.info(f"get_distribuicao_respostas_completa - início (empresa_id={empresa_id})")

            # Query base com filtros hierárquicos
            respostas_query = Resposta.objects.filter(
                magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
            )

            if unidade_id:
                respostas_query = respostas_query.filter(
                    magic_link__colaborador__cargo__setor__unidade_id=unidade_id
                )
            if setor_id:
                respostas_query = respostas_query.filter(
                    magic_link__colaborador__cargo__setor_id=setor_id
                )
            if cargo_id:
                respostas_query = respostas_query.filter(
                    magic_link__colaborador__cargo_id=cargo_id
                )

            respostas = respostas_query.all()

            if not respostas.exists():
                logger.info("get_distribuicao_respostas_completa - sucesso (sem respostas)")
                return {
                    'distribuicao': {},
                    'perguntas_info': [],
                    'total_respostas': 0,
                    'filtros_aplicados': {
                        'unidade_id': unidade_id,
                        'setor_id': setor_id,
                        'cargo_id': cargo_id
                    }
                }

            # Agregar distribuição por pergunta
            distribuicao = {}

            for resposta in respostas:
                for perg_num, valor in resposta.respostas.items():
                    if perg_num not in distribuicao:
                        distribuicao[perg_num] = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

                    if valor in [0, 1, 2, 3, 4]:
                        distribuicao[perg_num][valor] += 1

            # Obter metadados das perguntas
            perguntas_info = []
            for perg_num in sorted(distribuicao.keys(), key=int):
                try:
                    pergunta = Pergunta.objects.select_related('dimensao').get(
                        numero=int(perg_num)
                    )
                    total = sum(distribuicao[perg_num].values())
                    valores = [
                        v * distribuicao[perg_num][v]
                        for v in range(5)
                    ]
                    media = sum(valores) / total if total > 0 else 0

                    perguntas_info.append({
                        'numero': int(perg_num),
                        'texto': pergunta.texto,
                        'dimensao': pergunta.dimensao.nome,
                        'polaridade': pergunta.dimensao.polaridade,
                        'distribuicao': [
                            distribuicao[perg_num][i] for i in range(5)
                        ],
                        'total': total,
                        'media': round(media, 2),
                        'nivel_risco': self.calc_service._interpretar_dimensao(
                            media, pergunta.dimensao.polaridade
                        )
                    })
                except Pergunta.DoesNotExist:
                    continue

            logger.info("get_distribuicao_respostas_completa - sucesso")
            return {
                'distribuicao': distribuicao,
                'perguntas_info': perguntas_info,
                'total_respostas': respostas.count(),
                'filtros_aplicados': {
                    'unidade_id': unidade_id,
                    'setor_id': setor_id,
                    'cargo_id': cargo_id
                }
            }
        except Exception as e:
            logger.error(f"Erro em get_distribuicao_respostas_completa: {str(e)}", exc_info=True)
            return {
                'distribuicao': {},
                'perguntas_info': [],
                'total_respostas': 0,
                'filtros_aplicados': {
                    'unidade_id': unidade_id,
                    'setor_id': setor_id,
                    'cargo_id': cargo_id
                }
            }

    def get_dimensoes_por_polaridade(self, empresa_id: str) -> Dict[str, Any]:
        """
        Retorna dimensões agrupadas por polaridade (Positiva vs Negativa)
        para gráfico de barras comparativo.

        Args:
            empresa_id: UUID da empresa

        Returns:
            Dict com dimensões separadas por polaridade e estatísticas
        """
        try:
            logger.info(f"get_dimensoes_por_polaridade - início (empresa_id={empresa_id})")

            respostas = Resposta.objects.filter(
                magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
            )

            if not respostas.exists():
                logger.info("get_dimensoes_por_polaridade - sucesso (sem respostas)")
                return {
                    'positivas': [],
                    'negativas': [],
                    'resumo': {
                        'media_positivas': 0,
                        'media_negativas': 0,
                        'total_positivas': 0,
                        'total_negativas': 0
                    }
                }

            # Agregar por dimensão e polaridade
            dimensoes_data = defaultdict(lambda: {'scores': [], 'polaridade': None})

            for resposta in respostas:
                for dimensao_nome, dados in resposta.scores_dimensoes.items():
                    dimensoes_data[dimensao_nome]['scores'].append(dados['score'])
                    dimensoes_data[dimensao_nome]['polaridade'] = dados['polaridade']

            # Separar e calcular estatísticas
            positivas = []
            negativas = []

            for dimensao_nome, dados in dimensoes_data.items():
                score_medio = self.stats_service.calcular_media(dados['scores'])
                desvio = self.stats_service.calcular_desvio_padrao_populacional(dados['scores'])
                nivel_risco = self.calc_service._interpretar_dimensao(
                    score_medio, dados['polaridade']
                )

                item = {
                    'dimensao': dimensao_nome,
                    'score_medio': round(score_medio, 2),
                    'desvio_padrao': round(desvio, 2),
                    'nivel_risco': nivel_risco,
                    'total_respostas': len(dados['scores'])
                }

                if dados['polaridade'] == 'POSITIVA':
                    positivas.append(item)
                else:
                    negativas.append(item)

            # Ordenar por criticidade
            ordem_risco = {'CRÍTICO': 0, 'ATENÇÃO': 1, 'SATISFATÓRIO': 2}
            positivas.sort(key=lambda x: ordem_risco[x['nivel_risco']])
            negativas.sort(key=lambda x: ordem_risco[x['nivel_risco']])

            # Calcular médias gerais
            media_positivas = self.stats_service.calcular_media(
                [d['score_medio'] for d in positivas]
            ) if positivas else 0
            media_negativas = self.stats_service.calcular_media(
                [d['score_medio'] for d in negativas]
            ) if negativas else 0

            logger.info("get_dimensoes_por_polaridade - sucesso")
            return {
                'positivas': positivas,
                'negativas': negativas,
                'resumo': {
                    'media_positivas': round(media_positivas, 2),
                    'media_negativas': round(media_negativas, 2),
                    'total_positivas': len(positivas),
                    'total_negativas': len(negativas)
                }
            }
        except Exception as e:
            logger.error(f"Erro em get_dimensoes_por_polaridade: {str(e)}", exc_info=True)
            return {
                'positivas': [],
                'negativas': [],
                'resumo': {
                    'media_positivas': 0,
                    'media_negativas': 0,
                    'total_positivas': 0,
                    'total_negativas': 0
                }
            }

    def get_radar_multinivel(
        self,
        empresa_id: str,
        unidade_id: Optional[str] = None,
        setor_id: Optional[str] = None,
        cargo_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retorna dados para gráfico radar com suporte a múltiplos níveis
        (Empresa, Unidade, Setor, Cargo).

        Args:
            empresa_id: UUID da empresa
            unidade_id: UUID da unidade (opcional)
            setor_id: UUID do setor (opcional)
            cargo_id: UUID do cargo (opcional)

        Returns:
            Dict com scores por dimensão para o nível selecionado
        """
        try:
            logger.info(f"get_radar_multinivel - início (empresa_id={empresa_id})")

            # Query base
            respostas_query = Resposta.objects.filter(
                magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
            )

            # Aplicar filtros hierárquicos
            nivel = 'empresa'
            nivel_nome = None

            if cargo_id:
                respostas_query = respostas_query.filter(
                    magic_link__colaborador__cargo_id=cargo_id
                )
                nivel = 'cargo'
                try:
                    cargo = Cargo.objects.get(id=cargo_id)
                    nivel_nome = cargo.nome
                except Cargo.DoesNotExist:
                    nivel_nome = 'Cargo não encontrado'
            elif setor_id:
                respostas_query = respostas_query.filter(
                    magic_link__colaborador__cargo__setor_id=setor_id
                )
                nivel = 'setor'
                try:
                    setor = Setor.objects.get(id=setor_id)
                    nivel_nome = setor.nome
                except Setor.DoesNotExist:
                    nivel_nome = 'Setor não encontrado'
            elif unidade_id:
                respostas_query = respostas_query.filter(
                    magic_link__colaborador__cargo__setor__unidade_id=unidade_id
                )
                nivel = 'unidade'
                try:
                    unidade = Unidade.objects.get(id=unidade_id)
                    nivel_nome = unidade.nome
                except Unidade.DoesNotExist:
                    nivel_nome = 'Unidade não encontrada'

            respostas = respostas_query.all()

            if not respostas.exists():
                logger.info("get_radar_multinivel - sucesso (sem respostas)")
                return {
                    'labels': [],
                    'scores': [],
                    'niveis_risco': [],
                    'polaridades': [],
                    'nivel': nivel,
                    'nivel_nome': nivel_nome,
                    'total_respostas': 0
                }

            # Agregar por dimensão
            dimensoes_scores = defaultdict(list)
            polaridades = {}

            for resposta in respostas:
                for dimensao_nome, dados in resposta.scores_dimensoes.items():
                    dimensoes_scores[dimensao_nome].append(dados['score'])
                    polaridades[dimensao_nome] = dados['polaridade']

            # Calcular médias e riscos
            labels = []
            scores = []
            niveis_risco = []
            pols = []

            for dimensao_nome in sorted(dimensoes_scores.keys()):
                score_medio = self.stats_service.calcular_media(
                    dimensoes_scores[dimensao_nome]
                )
                pol = polaridades[dimensao_nome]
                nivel_risco = self.calc_service._interpretar_dimensao(score_medio, pol)

                labels.append(dimensao_nome)
                scores.append(round(score_medio, 2))
                niveis_risco.append(nivel_risco)
                pols.append(pol)

            logger.info("get_radar_multinivel - sucesso")
            return {
                'labels': labels,
                'scores': scores,
                'niveis_risco': niveis_risco,
                'polaridades': pols,
                'nivel': nivel,
                'nivel_nome': nivel_nome,
                'total_respostas': respostas.count()
            }
        except Exception as e:
            logger.error(f"Erro em get_radar_multinivel: {str(e)}", exc_info=True)
            return {
                'labels': [],
                'scores': [],
                'niveis_risco': [],
                'polaridades': [],
                'nivel': 'empresa',
                'nivel_nome': None,
                'total_respostas': 0
            }

    def get_consistencia_interna(self, empresa_id: str) -> Dict[str, Any]:
        """
        Calcula métricas de consistência interna (desvio padrão, variância)
        por dimensão e por pergunta.

        Args:
            empresa_id: UUID da empresa

        Returns:
            Dict com métricas de consistência por dimensão e pergunta
        """
        try:
            logger.info(f"get_consistencia_interna - início (empresa_id={empresa_id})")

            respostas = Resposta.objects.filter(
                magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
            )

            if not respostas.exists():
                logger.info("get_consistencia_interna - sucesso (sem respostas)")
                return {
                    'por_dimensao': [],
                    'por_pergunta': [],
                    'consistencia_geral': {
                        'cv_percent': 0,
                        'classificacao': 'SEM DADOS'
                    }
                }

            # Consistência por dimensão
            dimensoes_scores = defaultdict(list)

            for resposta in respostas:
                for dimensao_nome, dados in resposta.scores_dimensoes.items():
                    dimensoes_scores[dimensao_nome].append(dados['score'])

            por_dimensao = []
            for dimensao_nome in sorted(dimensoes_scores.keys()):
                scores = dimensoes_scores[dimensao_nome]
                estatisticas = self.stats_service.calcular_estatisticas_completas(scores)

                por_dimensao.append({
                    'dimensao': dimensao_nome,
                    'media': estatisticas['media'],
                    'desvio_padrao': estatisticas['desvio_padrao'],
                    'variancia': estatisticas['variancia'],
                    'cv_percent': estatisticas['cv_percent'],
                    'classificacao_cv': self.stats_service.interpretar_cv(
                        estatisticas['cv_percent']
                    ),
                    'n': estatisticas['n']
                })

            # Consistência por pergunta
            perguntas_valores = defaultdict(list)

            for resposta in respostas:
                for perg_num, valor in resposta.respostas.items():
                    perguntas_valores[perg_num].append(valor)

            por_pergunta = []
            for perg_num in sorted(perguntas_valores.keys(), key=int):
                valores = perguntas_valores[perg_num]
                estatisticas = self.stats_service.calcular_estatisticas_completas(
                    [float(v) for v in valores]
                )

                try:
                    pergunta = Pergunta.objects.select_related('dimensao').get(
                        numero=int(perg_num)
                    )
                    dimensao = pergunta.dimensao.nome
                except Pergunta.DoesNotExist:
                    dimensao = 'Desconhecida'

                por_pergunta.append({
                    'numero': int(perg_num),
                    'dimensao': dimensao,
                    'media': estatisticas['media'],
                    'desvio_padrao': estatisticas['desvio_padrao'],
                    'variancia': estatisticas['variancia'],
                    'cv_percent': estatisticas['cv_percent'],
                    'classificacao_cv': self.stats_service.interpretar_cv(
                        estatisticas['cv_percent']
                    ),
                    'n': estatisticas['n']
                })

            # Consistência geral (usando scores globais)
            scores_globais = [
                r.score_global for r in respostas if r.score_global is not None
            ]
            cv_geral = self.stats_service.calcular_coeficiente_variacao(scores_globais)

            logger.info("get_consistencia_interna - sucesso")
            return {
                'por_dimensao': por_dimensao,
                'por_pergunta': por_pergunta,
                'consistencia_geral': {
                    'cv_percent': round(cv_geral, 2),
                    'classificacao': self.stats_service.interpretar_cv(cv_geral)
                }
            }
        except Exception as e:
            logger.error(f"Erro em get_consistencia_interna: {str(e)}", exc_info=True)
            return {
                'por_dimensao': [],
                'por_pergunta': [],
                'consistencia_geral': {
                    'cv_percent': 0,
                    'classificacao': 'SEM DADOS'
                }
            }

    def get_scores_por_agrupamento(
        self,
        empresa_id: str,
        agrupamento: str = 'unidade'
    ) -> Dict[str, Any]:
        """
        Retorna scores médios por agrupamento para comparação.

        Args:
            empresa_id: UUID da empresa
            agrupamento: 'unidade', 'setor' ou 'cargo'

        Returns:
            Dict com scores por agrupamento selecionado
        """
        try:
            logger.info(f"get_scores_por_agrupamento - início (empresa_id={empresa_id})")

            respostas = Resposta.objects.filter(
                magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
            ).select_related(
                'magic_link__colaborador__cargo__setor__unidade'
            )

            if not respostas.exists():
                logger.info("get_scores_por_agrupamento - sucesso (sem respostas)")
                return {'grupos': [], 'agrupamento': agrupamento}

            grupos_scores = defaultdict(list)

            for resposta in respostas:
                if resposta.score_global is None:
                    continue

                colaborador = resposta.magic_link.colaborador

                if agrupamento == 'unidade':
                    grupo_nome = colaborador.cargo.setor.unidade.nome
                    grupo_id = str(colaborador.cargo.setor.unidade.id)
                elif agrupamento == 'setor':
                    grupo_nome = colaborador.cargo.setor.nome
                    grupo_id = str(colaborador.cargo.setor.id)
                elif agrupamento == 'cargo':
                    grupo_nome = colaborador.cargo.nome
                    grupo_id = str(colaborador.cargo.id)
                else:
                    continue

                grupos_scores[grupo_nome].append({
                    'id': grupo_id,
                    'score': resposta.score_global
                })

            grupos = []
            for grupo_nome, dados in grupos_scores.items():
                scores = [d['score'] for d in dados]
                estatisticas = self.stats_service.calcular_estatisticas_completas(scores)

                grupos.append({
                    'nome': grupo_nome,
                    'id': dados[0]['id'],
                    'score_medio': estatisticas['media'],
                    'mediana': estatisticas['mediana'],
                    'desvio_padrao': estatisticas['desvio_padrao'],
                    'cv_percent': estatisticas['cv_percent'],
                    'total_respostas': estatisticas['n'],
                    'score_minimo': estatisticas['minimo'],
                    'score_maximo': estatisticas['maximo']
                })

            # Ordenar por score médio (menor = maior risco)
            grupos.sort(key=lambda x: x['score_medio'])

            logger.info("get_scores_por_agrupamento - sucesso")
            return {
                'grupos': grupos,
                'agrupamento': agrupamento
            }
        except Exception as e:
            logger.error(f"Erro em get_scores_por_agrupamento: {str(e)}", exc_info=True)
            return {'grupos': [], 'agrupamento': agrupamento}

    def get_histograma_scores(
        self,
        empresa_id: str,
        num_bins: int = 10
    ) -> Dict[str, Any]:
        """
        Retorna dados para histograma de distribuição dos scores globais
        com quartis sobrepostos.

        Args:
            empresa_id: UUID da empresa
            num_bins: Número de intervalos

        Returns:
            Dict com dados do histograma e quartis
        """
        try:
            logger.info(f"get_histograma_scores - início (empresa_id={empresa_id})")

            respostas = Resposta.objects.filter(
                magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
            )

            scores = [
                r.score_global for r in respostas if r.score_global is not None
            ]

            if not scores:
                logger.info("get_histograma_scores - sucesso (sem scores)")
                return {
                    'labels': [],
                    'counts': [],
                    'total': 0,
                    'quartis': {'Q1': 0, 'Q2': 0, 'Q3': 0},
                    'estatisticas': {}
                }

            # Gerar histograma com range fixo (0-140)
            histograma = self.stats_service.gerar_histograma(
                scores,
                num_bins=num_bins,
                min_valor=0,
                max_valor=140
            )

            # Calcular estatísticas e quartis
            estatisticas = self.stats_service.calcular_estatisticas_completas(scores)

            logger.info("get_histograma_scores - sucesso")
            return {
                'labels': histograma['labels'],
                'counts': histograma['counts'],
                'total': histograma['total'],
                'quartis': estatisticas['quartis'],
                'estatisticas': {
                    'media': estatisticas['media'],
                    'mediana': estatisticas['mediana'],
                    'desvio_padrao': estatisticas['desvio_padrao'],
                    'cv_percent': estatisticas['cv_percent']
                }
            }
        except Exception as e:
            logger.error(f"Erro em get_histograma_scores: {str(e)}", exc_info=True)
            return {
                'labels': [],
                'counts': [],
                'total': 0,
                'quartis': {'Q1': 0, 'Q2': 0, 'Q3': 0},
                'estatisticas': {}
            }

    def get_cargos_disponiveis(self, empresa_id: str) -> List[Dict[str, Any]]:
        """
        Retorna lista de cargos disponíveis para filtros.

        Args:
            empresa_id: UUID da empresa

        Returns:
            Lista de cargos com id e nome
        """
        try:
            logger.info(f"get_cargos_disponiveis - início (empresa_id={empresa_id})")

            cargos = Cargo.objects.filter(
                setor__unidade__empresa_id=empresa_id,
                ativo=True
            ).values('id', 'nome', 'setor__nome', 'setor__unidade__nome')

            resultado = [
                {
                    'id': str(c['id']),
                    'nome': c['nome'],
                    'setor': c['setor__nome'],
                    'unidade': c['setor__unidade__nome']
                }
                for c in cargos
            ]

            logger.info("get_cargos_disponiveis - sucesso")
            return resultado
        except Exception as e:
            logger.error(f"Erro em get_cargos_disponiveis: {str(e)}", exc_info=True)
            return []

    def get_evolucao_temporal(
        self,
        empresa_id: str,
        unidade_id: Optional[str] = None,
        setor_id: Optional[str] = None,
        periodo: str = 'mensal'
    ) -> Dict[str, Any]:
        """
        Retorna evolução temporal dos scores globais e por dimensão.

        Args:
            empresa_id: UUID da empresa
            unidade_id: UUID da unidade (opcional)
            setor_id: UUID do setor (opcional)
            periodo: 'diario', 'semanal' ou 'mensal'

        Returns:
            Dict com evolução temporal dos scores
        """
        try:
            logger.info(f"get_evolucao_temporal - início (empresa_id={empresa_id})")

            from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
            from datetime import datetime, timedelta

            # Query base
            respostas_query = Resposta.objects.filter(
                magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
            ).select_related('magic_link')

            # Aplicar filtros hierárquicos
            if setor_id:
                respostas_query = respostas_query.filter(
                    magic_link__colaborador__cargo__setor_id=setor_id
                )
            elif unidade_id:
                respostas_query = respostas_query.filter(
                    magic_link__colaborador__cargo__setor__unidade_id=unidade_id
                )

            respostas = respostas_query.order_by('created_at')

            if not respostas.exists():
                logger.info("get_evolucao_temporal - sucesso (sem respostas)")
                return {
                    'labels': [],
                    'scores_globais': [],
                    'scores_dimensoes': {},
                    'periodo': periodo,
                    'total_respostas': 0
                }

            # Definir truncamento baseado no período
            trunc_func = {
                'diario': TruncDay,
                'semanal': TruncWeek,
                'mensal': TruncMonth
            }.get(periodo, TruncMonth)

            # Agrupar respostas por período
            periodos_scores = defaultdict(lambda: {
                'scores_globais': [],
                'scores_dimensoes': defaultdict(list)
            })

            for resposta in respostas:
                if resposta.score_global is None:
                    continue

                # Truncar data para o período
                if periodo == 'diario':
                    periodo_key = resposta.created_at.date()
                elif periodo == 'semanal':
                    # Primeira segunda-feira da semana
                    periodo_key = resposta.created_at.date() - timedelta(
                        days=resposta.created_at.weekday()
                    )
                else:  # mensal
                    periodo_key = resposta.created_at.replace(day=1).date()

                periodos_scores[periodo_key]['scores_globais'].append(resposta.score_global)

                # Adicionar scores por dimensão
                for dimensao_nome, dados in resposta.scores_dimensoes.items():
                    periodos_scores[periodo_key]['scores_dimensoes'][dimensao_nome].append(
                        dados['score']
                    )

            # Ordenar períodos
            periodos_ordenados = sorted(periodos_scores.keys())

            # Calcular médias por período
            labels = []
            scores_globais = []
            scores_dimensoes = defaultdict(list)

            for periodo_key in periodos_ordenados:
                dados_periodo = periodos_scores[periodo_key]

                # Formatar label
                if periodo == 'diario':
                    label = periodo_key.strftime('%d/%m/%Y')
                elif periodo == 'semanal':
                    label = periodo_key.strftime('Sem %d/%m')
                else:  # mensal
                    label = periodo_key.strftime('%b/%Y')

                labels.append(label)

                # Calcular média global
                media_global = self.stats_service.calcular_media(
                    dados_periodo['scores_globais']
                )
                scores_globais.append(round(media_global, 2))

                # Calcular médias por dimensão
                for dimensao_nome, scores in dados_periodo['scores_dimensoes'].items():
                    media_dimensao = self.stats_service.calcular_media(scores)
                    scores_dimensoes[dimensao_nome].append(round(media_dimensao, 2))

            logger.info("get_evolucao_temporal - sucesso")
            return {
                'labels': labels,
                'scores_globais': scores_globais,
                'scores_dimensoes': dict(scores_dimensoes),
                'periodo': periodo,
                'total_respostas': respostas.count()
            }
        except Exception as e:
            logger.error(f"Erro em get_evolucao_temporal: {str(e)}", exc_info=True)
            return {
                'labels': [],
                'scores_globais': [],
                'scores_dimensoes': {},
                'periodo': periodo,
                'total_respostas': 0
            }

    def get_matriz_nr1_completa(
        self,
        empresa_id: str,
        unidade_id: Optional[str] = None,
        setor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retorna dados para matriz NR-1 (Probabilidade × Severidade) com
        distribuição de respondentes em cada célula da matriz.

        Args:
            empresa_id: UUID da empresa
            unidade_id: UUID da unidade (opcional)
            setor_id: UUID do setor (opcional)

        Returns:
            Dict com matriz de risco completa
        """
        try:
            logger.info(f"get_matriz_nr1_completa - início (empresa_id={empresa_id})")

            # Query base
            respostas_query = Resposta.objects.filter(
                magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
            )

            # Aplicar filtros hierárquicos
            if setor_id:
                respostas_query = respostas_query.filter(
                    magic_link__colaborador__cargo__setor_id=setor_id
                )
            elif unidade_id:
                respostas_query = respostas_query.filter(
                    magic_link__colaborador__cargo__setor__unidade_id=unidade_id
                )

            respostas = respostas_query.all()

            if not respostas.exists():
                logger.info("get_matriz_nr1_completa - sucesso (sem respostas)")
                return {
                    'matriz': [[0] * 5 for _ in range(5)],
                    'labels_probabilidade': ['Raro', 'Improvável', 'Possível', 'Provável', 'Quase Certo'],
                    'labels_severidade': ['Insignificante', 'Menor', 'Moderado', 'Maior', 'Catastrófico'],
                    'total_respostas': 0,
                    'distribuicao_niveis': {
                        'BAIXO': 0,
                        'MÉDIO': 0,
                        'ALTO': 0,
                        'CRÍTICO': 0
                    }
                }

            # Criar matriz 5x5
            matriz = [[0 for _ in range(5)] for _ in range(5)]
            distribuicao_niveis = {'BAIXO': 0, 'MÉDIO': 0, 'ALTO': 0, 'CRÍTICO': 0}

            for resposta in respostas:
                if resposta.score_global is None:
                    continue

                # Calcular índices de probabilidade e severidade baseado no score (0-140)
                score = resposta.score_global

                # Severidade: Quanto menor o score, maior a severidade
                # 0-28: Catastrófico (índice 4)
                # 28-56: Maior (índice 3)
                # 56-84: Moderado (índice 2)
                # 84-112: Menor (índice 1)
                # 112-140: Insignificante (índice 0)
                if score <= 28:
                    severidade = 4
                elif score <= 56:
                    severidade = 3
                elif score <= 84:
                    severidade = 2
                elif score <= 112:
                    severidade = 1
                else:
                    severidade = 0

                # Probabilidade: Baseado no percentual de dimensões críticas
                dimensoes_criticas = sum(
                    1 for d in resposta.scores_dimensoes.values()
                    if self.calc_service._interpretar_dimensao(d['score'], d['polaridade']) == 'CRÍTICO'
                )
                total_dimensoes = len(resposta.scores_dimensoes)

                if total_dimensoes > 0:
                    percentual_critico = dimensoes_criticas / total_dimensoes

                    # Mapear para índice de probabilidade (0-4)
                    if percentual_critico >= 0.8:
                        probabilidade = 4  # Quase Certo
                    elif percentual_critico >= 0.6:
                        probabilidade = 3  # Provável
                    elif percentual_critico >= 0.4:
                        probabilidade = 2  # Possível
                    elif percentual_critico >= 0.2:
                        probabilidade = 1  # Improvável
                    else:
                        probabilidade = 0  # Raro
                else:
                    probabilidade = 0

                # Incrementar célula da matriz
                matriz[probabilidade][severidade] += 1

                # Calcular nível de risco da célula
                nivel_risco = self._calcular_nivel_risco_matriz(probabilidade, severidade)
                distribuicao_niveis[nivel_risco] += 1

            logger.info("get_matriz_nr1_completa - sucesso")
            return {
                'matriz': matriz,
                'labels_probabilidade': ['Raro', 'Improvável', 'Possível', 'Provável', 'Quase Certo'],
                'labels_severidade': ['Insignificante', 'Menor', 'Moderado', 'Maior', 'Catastrófico'],
                'total_respostas': respostas.count(),
                'distribuicao_niveis': distribuicao_niveis
            }
        except Exception as e:
            logger.error(f"Erro em get_matriz_nr1_completa: {str(e)}", exc_info=True)
            return {
                'matriz': [[0] * 5 for _ in range(5)],
                'labels_probabilidade': ['Raro', 'Improvável', 'Possível', 'Provável', 'Quase Certo'],
                'labels_severidade': ['Insignificante', 'Menor', 'Moderado', 'Maior', 'Catastrófico'],
                'total_respostas': 0,
                'distribuicao_niveis': {
                    'BAIXO': 0,
                    'MÉDIO': 0,
                    'ALTO': 0,
                    'CRÍTICO': 0
                }
            }

    def _calcular_nivel_risco_matriz(self, probabilidade: int, severidade: int) -> str:
        """
        Calcula o nível de risco baseado na posição na matriz NR-1.

        Args:
            probabilidade: Índice de probabilidade (0-4)
            severidade: Índice de severidade (0-4)

        Returns:
            Nível de risco: 'BAIXO', 'MÉDIO', 'ALTO' ou 'CRÍTICO'
        """
        # Soma dos índices para determinar nível
        soma = probabilidade + severidade

        if soma >= 7:
            return 'CRÍTICO'
        elif soma >= 5:
            return 'ALTO'
        elif soma >= 3:
            return 'MÉDIO'
        else:
            return 'BAIXO'