/**
 * Dashboard Charts - Plataforma NR-1
 * Gráficos avançados para análise de riscos psicossociais
 * Usando Chart.js 4.x
 */

// Cores padrão para níveis de risco
const CORES_RISCO = {
    critico: '#dc2626',      // Vermelho
    atencao: '#f59e0b',      // Amarelo/Laranja
    satisfatorio: '#10b981', // Verde
    primary: '#2563eb',      // Azul primário
    secondary: '#6b7280',    // Cinza
};

// Configurações padrão dos gráficos
const CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: true,
            position: 'bottom',
        },
        tooltip: {
            enabled: true,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleFont: { size: 14 },
            bodyFont: { size: 13 },
            padding: 12,
            cornerRadius: 6,
        }
    }
};

/**
 * Cria gráfico de distribuição por nível de risco
 */
function createDistribuicaoRiscoChart(canvasId, distribuicaoRisco) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Crítico', 'Atenção', 'Satisfatório'],
            datasets: [{
                data: [
                    distribuicaoRisco.critico,
                    distribuicaoRisco.atencao,
                    distribuicaoRisco.satisfatorio
                ],
                backgroundColor: [
                    CORES_RISCO.critico,
                    CORES_RISCO.atencao,
                    CORES_RISCO.satisfatorio
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            plugins: {
                ...CHART_DEFAULTS.plugins,
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    ...CHART_DEFAULTS.plugins.tooltip,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Cria gráfico de distribuição de scores (histograma)
 */
function createDistribuicaoScoresChart(canvasId, distribuicaoScores) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: distribuicaoScores.labels,
            datasets: [{
                label: 'Número de Respondentes',
                data: distribuicaoScores.counts,
                backgroundColor: CORES_RISCO.primary,
                borderColor: CORES_RISCO.primary,
                borderWidth: 1
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                ...CHART_DEFAULTS.plugins,
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Distribuição dos Scores Globais',
                    font: { size: 16, weight: 'bold' },
                    padding: 20
                }
            }
        }
    });
}

/**
 * Cria gráfico radar de perfil psicossocial por dimensão
 */
function createRadarDimensoesChart(canvasId, dadosDimensoes) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const labels = dadosDimensoes.dimensoes.map(d => d.dimensao);
    const scores = dadosDimensoes.dimensoes.map(d => d.score_medio);

    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score Médio',
                data: scores,
                backgroundColor: 'rgba(37, 99, 235, 0.2)',
                borderColor: CORES_RISCO.primary,
                borderWidth: 2,
                pointBackgroundColor: CORES_RISCO.primary,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: CORES_RISCO.primary,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: 4,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                ...CHART_DEFAULTS.plugins,
                title: {
                    display: true,
                    text: 'Perfil Psicossocial por Dimensão',
                    font: { size: 16, weight: 'bold' },
                    padding: 20
                }
            }
        }
    });
}

/**
 * Cria gráfico de análise por gênero
 */
function createAnaliseGeneroChart(canvasId, analiseGenero) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const generos = Object.keys(analiseGenero.por_genero);
    const labels = generos.map(g => analiseGenero.por_genero[g].sexo_display);
    const scores = generos.map(g => analiseGenero.por_genero[g].score_medio);
    const totais = generos.map(g => analiseGenero.por_genero[g].total);

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score Médio',
                data: scores,
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(236, 72, 153, 0.8)',
                    'rgba(156, 163, 175, 0.8)',
                    'rgba(251, 191, 36, 0.8)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    max: 140
                }
            },
            plugins: {
                ...CHART_DEFAULTS.plugins,
                title: {
                    display: true,
                    text: 'Score Médio por Gênero',
                    font: { size: 16, weight: 'bold' },
                    padding: 20
                },
                tooltip: {
                    ...CHART_DEFAULTS.plugins.tooltip,
                    callbacks: {
                        afterLabel: function(context) {
                            const idx = context.dataIndex;
                            return `Total: ${totais[idx]} respondentes`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Cria gráfico de análise por faixa etária
 */
function createAnaliseFaixaEtariaChart(canvasId, analiseFaixaEtaria) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const faixas = Object.keys(analiseFaixaEtaria.por_faixa);
    const scores = faixas.map(f => analiseFaixaEtaria.por_faixa[f].score_medio);
    const totais = faixas.map(f => analiseFaixaEtaria.por_faixa[f].total);

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: faixas,
            datasets: [{
                label: 'Score Médio',
                data: scores,
                borderColor: CORES_RISCO.primary,
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 6,
                pointBackgroundColor: CORES_RISCO.primary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 140
                }
            },
            plugins: {
                ...CHART_DEFAULTS.plugins,
                title: {
                    display: true,
                    text: 'Score Médio por Faixa Etária',
                    font: { size: 16, weight: 'bold' },
                    padding: 20
                },
                tooltip: {
                    ...CHART_DEFAULTS.plugins.tooltip,
                    callbacks: {
                        afterLabel: function(context) {
                            const idx = context.dataIndex;
                            return `Total: ${totais[idx]} respondentes`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Cria pirâmide etária com níveis de risco
 */
function createPiramideEtariaChart(canvasId, piramideData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const faixas = piramideData.faixas;

    // Dados para Masculino (negativos)
    const mascCritico = faixas.map(f => piramideData.masculino[f].critico);
    const mascAtencao = faixas.map(f => piramideData.masculino[f].atencao);
    const mascSatisfatorio = faixas.map(f => piramideData.masculino[f].satisfatorio);

    // Dados para Feminino (positivos)
    const femCritico = faixas.map(f => piramideData.feminino[f].critico);
    const femAtencao = faixas.map(f => piramideData.feminino[f].atencao);
    const femSatisfatorio = faixas.map(f => piramideData.feminino[f].satisfatorio);

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: faixas,
            datasets: [
                // Masculino
                {
                    label: 'Masculino - Crítico',
                    data: mascCritico,
                    backgroundColor: 'rgba(220, 38, 38, 0.8)',
                    stack: 'masculino'
                },
                {
                    label: 'Masculino - Atenção',
                    data: mascAtencao,
                    backgroundColor: 'rgba(245, 158, 11, 0.8)',
                    stack: 'masculino'
                },
                {
                    label: 'Masculino - Satisfatório',
                    data: mascSatisfatorio,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    stack: 'masculino'
                },
                // Feminino
                {
                    label: 'Feminino - Crítico',
                    data: femCritico,
                    backgroundColor: 'rgba(220, 38, 38, 0.8)',
                    stack: 'feminino'
                },
                {
                    label: 'Feminino - Atenção',
                    data: femAtencao,
                    backgroundColor: 'rgba(245, 158, 11, 0.8)',
                    stack: 'feminino'
                },
                {
                    label: 'Feminino - Satisfatório',
                    data: femSatisfatorio,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    stack: 'feminino'
                }
            ]
        },
        options: {
            indexAxis: 'y',
            ...CHART_DEFAULTS,
            scales: {
                x: {
                    stacked: true,
                    ticks: {
                        callback: function(value) {
                            return Math.abs(value); // Mostrar valores absolutos
                        }
                    }
                },
                y: {
                    stacked: true
                }
            },
            plugins: {
                ...CHART_DEFAULTS.plugins,
                title: {
                    display: true,
                    text: 'Pirâmide Etária com Níveis de Risco',
                    font: { size: 16, weight: 'bold' },
                    padding: 20
                },
                tooltip: {
                    ...CHART_DEFAULTS.plugins.tooltip,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${Math.abs(context.parsed.x)}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Cria gráfico radar comparativo de dimensões por gênero
 */
function createDimensoesPorGeneroChart(canvasId, dimensoesPorGenero) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const dimensoes = dimensoesPorGenero.dimensoes;
    const generos = Object.keys(dimensoesPorGenero.por_genero);

    const cores = [
        { bg: 'rgba(59, 130, 246, 0.2)', border: '#3b82f6' },
        { bg: 'rgba(236, 72, 153, 0.2)', border: '#ec4899' },
        { bg: 'rgba(156, 163, 175, 0.2)', border: '#9ca3af' },
        { bg: 'rgba(251, 191, 36, 0.2)', border: '#fbbf24' }
    ];

    const datasets = generos.map((genero, idx) => {
        const data = dimensoes.map(dim => dimensoesPorGenero.por_genero[genero][dim] || 0);

        return {
            label: genero,
            data: data,
            backgroundColor: cores[idx].bg,
            borderColor: cores[idx].border,
            borderWidth: 2,
            pointRadius: 4,
            pointBackgroundColor: cores[idx].border,
            pointBorderColor: '#fff',
            pointHoverRadius: 6
        };
    });

    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: dimensoes,
            datasets: datasets
        },
        options: {
            ...CHART_DEFAULTS,
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: 4,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                ...CHART_DEFAULTS.plugins,
                title: {
                    display: true,
                    text: 'Comparativo de Dimensões por Gênero',
                    font: { size: 16, weight: 'bold' },
                    padding: 20
                }
            }
        }
    });
}

/**
 * Inicializa todos os gráficos do dashboard
 */
function initDashboardCharts(dados) {
    const charts = {};

    // Distribuição por nível de risco
    if (document.getElementById('chartDistribuicaoRisco')) {
        charts.distribuicaoRisco = createDistribuicaoRiscoChart(
            'chartDistribuicaoRisco',
            dados.kpis.distribuicao_risco
        );
    }

    // Distribuição de scores
    if (document.getElementById('chartDistribuicaoScores')) {
        charts.distribuicaoScores = createDistribuicaoScoresChart(
            'chartDistribuicaoScores',
            dados.distribuicao_scores
        );
    }

    // Radar de dimensões
    if (document.getElementById('chartRadarDimensoes')) {
        charts.radarDimensoes = createRadarDimensoesChart(
            'chartRadarDimensoes',
            dados.dados_dimensoes
        );
    }

    // Análise por gênero
    if (document.getElementById('chartAnaliseGenero')) {
        charts.analiseGenero = createAnaliseGeneroChart(
            'chartAnaliseGenero',
            dados.analise_genero
        );
    }

    // Análise por faixa etária
    if (document.getElementById('chartAnaliseFaixaEtaria')) {
        charts.analiseFaixaEtaria = createAnaliseFaixaEtariaChart(
            'chartAnaliseFaixaEtaria',
            dados.analise_faixa_etaria
        );
    }

    // Pirâmide etária
    if (document.getElementById('chartPiramideEtaria')) {
        charts.piramideEtaria = createPiramideEtariaChart(
            'chartPiramideEtaria',
            dados.piramide_etaria
        );
    }

    // Dimensões por gênero (radar comparativo)
    if (document.getElementById('chartDimensoesPorGenero')) {
        charts.dimensoesPorGenero = createDimensoesPorGeneroChart(
            'chartDimensoesPorGenero',
            dados.dimensoes_por_genero
        );
    }

    return charts;
}

// Exportar para uso global
window.DashboardCharts = {
    init: initDashboardCharts,
    createDistribuicaoRiscoChart,
    createDistribuicaoScoresChart,
    createRadarDimensoesChart,
    createAnaliseGeneroChart,
    createAnaliseFaixaEtariaChart,
    createPiramideEtariaChart,
    createDimensoesPorGeneroChart
};
