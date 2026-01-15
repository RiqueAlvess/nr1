"""
Serviço de cálculos estatísticos centralizados para o Dashboard NR-1

Este módulo contém todos os cálculos estatísticos utilizados no sistema,
garantindo consistência e performance nos cálculos de:
- Medidas de tendência central (média, mediana, moda)
- Medidas de dispersão (variância, desvio padrão, CV%)
- Quartis e percentis
- Distribuições e histogramas
"""

import statistics
from typing import List, Dict, Any, Optional, Tuple


class StatisticsService:
    """
    Serviço centralizado de cálculos estatísticos.

    Todos os métodos são stateless e podem ser usados diretamente
    sem necessidade de instanciar a classe para a maioria dos casos.
    """

    @staticmethod
    def calcular_media(valores: List[float]) -> float:
        """
        Calcula a média aritmética de uma lista de valores.

        Args:
            valores: Lista de valores numéricos

        Returns:
            Média aritmética, ou 0 se lista vazia
        """
        if not valores:
            return 0.0
        return statistics.mean(valores)

    @staticmethod
    def calcular_mediana(valores: List[float]) -> float:
        """
        Calcula a mediana de uma lista de valores.

        Args:
            valores: Lista de valores numéricos

        Returns:
            Mediana, ou 0 se lista vazia
        """
        if not valores:
            return 0.0
        return statistics.median(valores)

    @staticmethod
    def calcular_desvio_padrao_populacional(valores: List[float]) -> float:
        """
        Calcula o desvio padrão POPULACIONAL de uma lista de valores.

        Usa a fórmula com N no denominador (pstdev), não N-1 (stdev).
        Apropriado quando os dados representam a população inteira.

        Args:
            valores: Lista de valores numéricos

        Returns:
            Desvio padrão populacional, ou 0 se lista vazia ou com 1 elemento
        """
        if not valores or len(valores) < 2:
            return 0.0
        return statistics.pstdev(valores)

    @staticmethod
    def calcular_desvio_padrao_amostral(valores: List[float]) -> float:
        """
        Calcula o desvio padrão AMOSTRAL de uma lista de valores.

        Usa a fórmula com N-1 no denominador (stdev).
        Apropriado quando os dados são uma amostra da população.

        Args:
            valores: Lista de valores numéricos

        Returns:
            Desvio padrão amostral, ou 0 se lista vazia ou com 1 elemento
        """
        if not valores or len(valores) < 2:
            return 0.0
        return statistics.stdev(valores)

    @staticmethod
    def calcular_variancia_populacional(valores: List[float]) -> float:
        """
        Calcula a variância POPULACIONAL de uma lista de valores.

        Args:
            valores: Lista de valores numéricos

        Returns:
            Variância populacional, ou 0 se lista vazia ou com 1 elemento
        """
        if not valores or len(valores) < 2:
            return 0.0
        return statistics.pvariance(valores)

    @staticmethod
    def calcular_variancia_amostral(valores: List[float]) -> float:
        """
        Calcula a variância AMOSTRAL de uma lista de valores.

        Args:
            valores: Lista de valores numéricos

        Returns:
            Variância amostral, ou 0 se lista vazia ou com 1 elemento
        """
        if not valores or len(valores) < 2:
            return 0.0
        return statistics.variance(valores)

    @staticmethod
    def calcular_coeficiente_variacao(valores: List[float]) -> float:
        """
        Calcula o Coeficiente de Variação (CV%) de uma lista de valores.

        CV% = (desvio_padrao / media) * 100

        Usa desvio padrão populacional para consistência.

        Args:
            valores: Lista de valores numéricos

        Returns:
            CV em percentual, ou 0 se média for zero ou lista inadequada
        """
        if not valores or len(valores) < 2:
            return 0.0

        media = statistics.mean(valores)
        if media == 0:
            return 0.0

        desvio_padrao = statistics.pstdev(valores)
        return (desvio_padrao / media) * 100

    @staticmethod
    def calcular_quartis(valores: List[float]) -> Dict[str, float]:
        """
        Calcula os quartis (Q1, Q2, Q3) de uma lista de valores.

        Args:
            valores: Lista de valores numéricos

        Returns:
            Dict com Q1, Q2 (mediana) e Q3
        """
        resultado_padrao = {'Q1': 0.0, 'Q2': 0.0, 'Q3': 0.0}

        if not valores:
            return resultado_padrao

        if len(valores) < 2:
            valor = valores[0]
            return {'Q1': valor, 'Q2': valor, 'Q3': valor}

        try:
            quartis = statistics.quantiles(valores, n=4)
            return {
                'Q1': round(quartis[0], 2),
                'Q2': round(quartis[1], 2),  # Mediana
                'Q3': round(quartis[2], 2)
            }
        except statistics.StatisticsError:
            # Fallback para casos extremos
            mediana = statistics.median(valores)
            return {'Q1': mediana, 'Q2': mediana, 'Q3': mediana}

    @staticmethod
    def calcular_estatisticas_completas(valores: List[float]) -> Dict[str, Any]:
        """
        Calcula estatísticas completas de uma lista de valores.

        Args:
            valores: Lista de valores numéricos

        Returns:
            Dict com todas as estatísticas disponíveis
        """
        if not valores:
            return {
                'n': 0,
                'media': 0.0,
                'mediana': 0.0,
                'desvio_padrao': 0.0,
                'variancia': 0.0,
                'cv_percent': 0.0,
                'minimo': 0.0,
                'maximo': 0.0,
                'amplitude': 0.0,
                'quartis': {'Q1': 0.0, 'Q2': 0.0, 'Q3': 0.0}
            }

        n = len(valores)
        media = statistics.mean(valores)
        mediana = statistics.median(valores)
        minimo = min(valores)
        maximo = max(valores)

        if n >= 2:
            desvio_padrao = statistics.pstdev(valores)
            variancia = statistics.pvariance(valores)
            cv_percent = (desvio_padrao / media * 100) if media != 0 else 0
            try:
                quartis_calc = statistics.quantiles(valores, n=4)
                quartis = {
                    'Q1': round(quartis_calc[0], 2),
                    'Q2': round(quartis_calc[1], 2),
                    'Q3': round(quartis_calc[2], 2)
                }
            except statistics.StatisticsError:
                quartis = {'Q1': mediana, 'Q2': mediana, 'Q3': mediana}
        else:
            desvio_padrao = 0.0
            variancia = 0.0
            cv_percent = 0.0
            quartis = {'Q1': valores[0], 'Q2': valores[0], 'Q3': valores[0]}

        return {
            'n': n,
            'media': round(media, 2),
            'mediana': round(mediana, 2),
            'desvio_padrao': round(desvio_padrao, 2),
            'variancia': round(variancia, 2),
            'cv_percent': round(cv_percent, 2),
            'minimo': round(minimo, 2),
            'maximo': round(maximo, 2),
            'amplitude': round(maximo - minimo, 2),
            'quartis': quartis
        }

    @staticmethod
    def gerar_histograma(
        valores: List[float],
        num_bins: int = 10,
        min_valor: Optional[float] = None,
        max_valor: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Gera dados para histograma com bins fixos.

        Args:
            valores: Lista de valores numéricos
            num_bins: Número de intervalos (bins)
            min_valor: Valor mínimo do range (opcional, usa min dos dados)
            max_valor: Valor máximo do range (opcional, usa max dos dados)

        Returns:
            Dict com labels (intervalos) e counts (contagens)
        """
        if not valores:
            return {
                'labels': [],
                'counts': [],
                'total': 0,
                'bins': num_bins
            }

        # Definir range
        min_v = min_valor if min_valor is not None else min(valores)
        max_v = max_valor if max_valor is not None else max(valores)

        # Evitar divisão por zero
        if min_v == max_v:
            return {
                'labels': [f"{min_v:.1f}"],
                'counts': [len(valores)],
                'total': len(valores),
                'bins': 1
            }

        intervalo = (max_v - min_v) / num_bins

        # Gerar labels e inicializar counts
        labels = []
        counts = [0] * num_bins

        for i in range(num_bins):
            inicio = min_v + i * intervalo
            fim = min_v + (i + 1) * intervalo
            labels.append(f"{inicio:.0f}-{fim:.0f}")

        # Contar valores em cada bin
        for valor in valores:
            bin_idx = min(int((valor - min_v) / intervalo), num_bins - 1)
            bin_idx = max(0, bin_idx)  # Garantir índice não negativo
            counts[bin_idx] += 1

        return {
            'labels': labels,
            'counts': counts,
            'total': len(valores),
            'bins': num_bins
        }

    @staticmethod
    def calcular_distribuicao_categorica(
        valores: List[int],
        categorias: Optional[List[int]] = None
    ) -> Dict[int, int]:
        """
        Calcula distribuição de frequências para valores categóricos.

        Args:
            valores: Lista de valores inteiros (ex: respostas 0-4)
            categorias: Lista de categorias esperadas (ex: [0,1,2,3,4])

        Returns:
            Dict com contagem por categoria
        """
        if categorias is None:
            categorias = [0, 1, 2, 3, 4]

        distribuicao = {cat: 0 for cat in categorias}

        for valor in valores:
            if valor in distribuicao:
                distribuicao[valor] += 1

        return distribuicao

    @staticmethod
    def calcular_percentil(valores: List[float], percentil: float) -> float:
        """
        Calcula um percentil específico.

        Args:
            valores: Lista de valores numéricos
            percentil: Percentil desejado (0-100)

        Returns:
            Valor do percentil
        """
        if not valores:
            return 0.0

        if len(valores) == 1:
            return valores[0]

        n = int(percentil / 100 * len(valores))
        valores_ordenados = sorted(valores)
        return valores_ordenados[min(n, len(valores) - 1)]

    @staticmethod
    def interpretar_cv(cv_percent: float) -> str:
        """
        Interpreta o Coeficiente de Variação.

        Args:
            cv_percent: CV em percentual

        Returns:
            Classificação da dispersão
        """
        if cv_percent <= 15:
            return 'BAIXA'  # Dados homogêneos
        elif cv_percent <= 30:
            return 'MODERADA'
        else:
            return 'ALTA'  # Dados heterogêneos
