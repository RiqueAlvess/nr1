import logging
import statistics
from collections import Counter, defaultdict
from django.db.models import Count, Q, Avg
from typing import Dict, Any, Optional, List
from django.conf import settings
from quiz.models import Resposta, MagicLink
from core.models import Setor, Unidade
from core.utils.anonymity import AnonymityChecker
from quiz.services.calculation_service import CalculationService
from importacao.models import Colaborador

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
        from quiz.models import Pergunta

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
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        ).select_related('magic_link__colaborador')

        if respostas.count() == 0:
            return {
                'por_genero': {},
                'total': 0
            }

        # Agrupar por gênero
        por_genero = defaultdict(list)

        for resposta in respostas:
            colaborador = resposta.magic_link.colaborador
            sexo = colaborador.sexo
            if resposta.score_global is not None:
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
            'total': respostas.count()
        }

    def get_analise_por_faixa_etaria(self, empresa_id: str) -> Dict[str, Any]:
        """
        Retorna análise de scores por faixa etária

        Args:
            empresa_id: UUID da empresa

        Returns:
            Dict com scores médios e distribuição por faixa etária
        """
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        ).select_related('magic_link__colaborador')

        if respostas.count() == 0:
            return {
                'por_faixa': {},
                'total': 0
            }

        # Agrupar por faixa etária
        por_faixa = defaultdict(list)

        for resposta in respostas:
            colaborador = resposta.magic_link.colaborador
            faixa = colaborador.faixa_etaria
            if resposta.score_global is not None:
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
            'total': respostas.count()
        }

    def get_piramide_etaria_com_risco(self, empresa_id: str) -> Dict[str, Any]:
        """
        Retorna dados para pirâmide etária com níveis de risco

        Args:
            empresa_id: UUID da empresa

        Returns:
            Dict com dados para pirâmide etária dividida por sexo e nível de risco
        """
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        ).select_related('magic_link__colaborador')

        if respostas.count() == 0:
            return {
                'faixas': [],
                'masculino': {},
                'feminino': {},
                'total': 0
            }

        # Estrutura de dados por faixa, sexo e nível de risco
        piramide = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        for resposta in respostas:
            colaborador = resposta.magic_link.colaborador
            faixa = colaborador.faixa_etaria
            sexo = colaborador.sexo
            nivel_risco = resposta.get_nivel_risco_global()

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
        respostas = Resposta.objects.filter(
            magic_link__colaborador__cargo__setor__unidade__empresa_id=empresa_id
        ).select_related('magic_link__colaborador')

        if respostas.count() == 0:
            return {
                'dimensoes': [],
                'por_genero': {}
            }

        # Agrupar scores de dimensões por gênero
        dimensoes_por_genero = defaultdict(lambda: defaultdict(list))

        for resposta in respostas:
            colaborador = resposta.magic_link.colaborador
            sexo = colaborador.sexo

            for dimensao_nome, dados in resposta.scores_dimensoes.items():
                dimensoes_por_genero[sexo][dimensao_nome].append(dados['score'])

        # Calcular médias
        resultado = defaultdict(dict)
        todas_dimensoes = set()

        for sexo, dimensoes in dimensoes_por_genero.items():
            sexo_display = dict(Colaborador.SEXO_CHOICES).get(sexo, 'Não informado')

            for dimensao, scores in dimensoes.items():
                todas_dimensoes.add(dimensao)
                resultado[sexo_display][dimensao] = round(statistics.mean(scores), 2)

        return {
            'dimensoes': sorted(list(todas_dimensoes)),
            'por_genero': dict(resultado)
        }