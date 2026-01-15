/**
 * Dashboard Charts - Vivamente360
 * Gerenciamento de gráficos do dashboard de riscos psicossociais
 */

// Registrar componente ANTES da inicialização do Alpine
document.addEventListener('alpine:init', () => {
    Alpine.data('dashboardApp', () => ({
        filtroTipo: 'geral',
        filtroUnidade: '',
        tipoGrafico: 'bar',
        tituloGrafico: 'Visão Geral',
        chartMain: null,
        chartDistribuicao: null,
        // Novos gráficos
        chartHistograma: null,
        chartRadar: null,
        chartPiramide: null,
        chartDistPerguntas: null,
        // Filtros para radar multi-nível
        radarFiltroUnidade: '',
        radarFiltroSetor: '',
        // Ordenação de perguntas
        ordenacaoPergunta: 'numero',
        // Dados de perguntas (para ordenação reativa)
        perguntas: [],
        perguntasOrdenadas: [],

        // Dados do backend (serão preenchidos via data attributes)
        dados: {
            kpis: {},
            unidades: [],
            setores: [],
            dimensoes: []
        },
        // Dados adicionais para gráficos avançados
        histogramaData: {},
        radarData: {},
        piramideData: {},
        distribuicaoRespostas: {},
        empresaId: '',

        // Computed: setores filtrados por unidade selecionada
        get setoresFiltrados() {
            if (!this.radarFiltroUnidade) return [];
            return this.dados.setores.filter(s => s.unidade_id === this.radarFiltroUnidade);
        },

        init() {
            // Carregar dados dos data attributes
            this.loadDataFromAttributes();

            // Inicializar perguntas ordenadas
            this.perguntasOrdenadas = [...this.perguntas];
            this.ordenarPerguntas();

            // Aguardar DOM estar completamente carregado
            this.$nextTick(() => {
                this.criarGraficoDistribuicao();
                this.atualizarGraficos();
                // Novos gráficos
                this.criarGraficoHistograma();
                this.criarGraficoRadar();
                this.criarGraficoPiramide();
                this.criarGraficoDistribuicaoPerguntas();
            });
        },

        loadDataFromAttributes() {
            const container = this.$el;
            if (!container) return;

            // Carregar dados dos data attributes
            this.perguntas = JSON.parse(container.dataset.perguntas || '[]');
            this.dados.kpis = JSON.parse(container.dataset.kpis || '{}');
            this.dados.unidades = JSON.parse(container.dataset.unidades || '[]');
            this.dados.setores = JSON.parse(container.dataset.setores || '[]');
            this.dados.dimensoes = JSON.parse(container.dataset.dimensoes || '[]');
            this.histogramaData = JSON.parse(container.dataset.histograma || '{}');
            this.radarData = JSON.parse(container.dataset.radar || '{}');
            this.piramideData = JSON.parse(container.dataset.piramide || '{}');
            this.distribuicaoRespostas = JSON.parse(container.dataset.distribuicao || '{}');
            this.empresaId = container.dataset.empresa || '';
        },

        ordenarPerguntas() {
            const perguntas = [...this.perguntas];
            const ordemRisco = { 'CRÍTICO': 0, 'ATENÇÃO': 1, 'SATISFATÓRIO': 2 };

            switch (this.ordenacaoPergunta) {
                case 'criticidade':
                    perguntas.sort((a, b) => ordemRisco[a.nivel_risco] - ordemRisco[b.nivel_risco]);
                    break;
                case 'media_asc':
                    perguntas.sort((a, b) => a.media - b.media);
                    break;
                case 'media_desc':
                    perguntas.sort((a, b) => b.media - a.media);
                    break;
                default: // numero
                    perguntas.sort((a, b) => a.numero - b.numero);
            }
            this.perguntasOrdenadas = perguntas;
        },

        async atualizarRadar() {
            // Limpar setor se unidade mudou
            if (!this.radarFiltroUnidade) {
                this.radarFiltroSetor = '';
            }

            // Fazer fetch dos novos dados
            const params = new URLSearchParams({ empresa: this.empresaId });
            if (this.radarFiltroUnidade) params.append('unidade', this.radarFiltroUnidade);
            if (this.radarFiltroSetor) params.append('setor', this.radarFiltroSetor);

            try {
                const response = await fetch(`/dashboard/api/radar/?${params}`);
                if (response.ok) {
                    this.radarData = await response.json();
                    this.criarGraficoRadar();
                }
            } catch (error) {
                console.error('Erro ao atualizar radar:', error);
            }
        },

        atualizarGraficos() {
            const titulos = {
                'geral': 'Visão Geral',
                'unidades': 'Análise por Unidade',
                'setores': 'Análise por Setor',
                'dimensoes': 'Análise por Dimensão'
            };
            this.tituloGrafico = titulos[this.filtroTipo];

            // Destruir gráfico anterior se existir
            if (this.chartMain) {
                this.chartMain.destroy();
                this.chartMain = null;
            }

            this.criarGraficoPrincipal();
        },

        criarGraficoPrincipal() {
            const ctx = document.getElementById('graficoMain');
            const loadingEl = document.getElementById('chart-main-loading');
            const containerEl = document.getElementById('chart-main-container');

            if (!ctx) {
                console.error('Canvas graficoMain não encontrado');
                return;
            }

            // Verificar se os dados existem
            if (!this.dados || !this.dados.kpis) {
                console.error('Dados insuficientes para gráfico principal');
                return;
            }

            let labels = [];
            let data = [];
            let backgroundColor = [];

            const cores = {
                primary: '#1EEB88',
                secondary: '#0F3D52',
                accent: '#6EDBC1',
                error: '#EF4444',
                warning: '#FACC15',
                success: '#22C55E'
            };

            try {
                if (this.filtroTipo === 'unidades') {
                    if (!this.dados.unidades || !Array.isArray(this.dados.unidades)) {
                        console.error('Dados de unidades não disponíveis');
                        return;
                    }
                    labels = this.dados.unidades.map(u => u.unidade_nome);
                    data = this.dados.unidades.map(u => u.score_medio);
                    backgroundColor = Array(data.length).fill(cores.primary);
                } else if (this.filtroTipo === 'setores') {
                    if (!this.dados.setores || !Array.isArray(this.dados.setores)) {
                        console.error('Dados de setores não disponíveis');
                        return;
                    }
                    let setores = this.dados.setores;
                    if (this.filtroUnidade) {
                        setores = setores.filter(s => s.unidade_id === this.filtroUnidade);
                    }
                    labels = setores.map(s => s.setor_nome);
                    data = setores.map(s => s.score_medio);
                    backgroundColor = setores.map(s => {
                        if (s.nivel_risco_nr1 === 'CRÍTICO') return cores.error;
                        if (s.nivel_risco_nr1 === 'ATENÇÃO') return cores.warning;
                        return cores.success;
                    });
                } else if (this.filtroTipo === 'dimensoes') {
                    if (!this.dados.dimensoes || !Array.isArray(this.dados.dimensoes)) {
                        console.error('Dados de dimensões não disponíveis');
                        return;
                    }
                    labels = this.dados.dimensoes.map(d => d.dimensao);
                    data = this.dados.dimensoes.map(d => d.score_medio);
                    backgroundColor = this.dados.dimensoes.map(d => {
                        if (d.nivel_risco === 'CRÍTICO') return cores.error;
                        if (d.nivel_risco === 'ATENÇÃO') return cores.warning;
                        return cores.success;
                    });
                } else {
                    // Visão geral - verificar distribuição de risco
                    if (!this.dados.kpis.distribuicao_risco) {
                        console.error('Dados de distribuição de risco não disponíveis');
                        return;
                    }
                    labels = ['Crítico', 'Atenção', 'Satisfatório'];
                    data = [
                        this.dados.kpis.distribuicao_risco.critico || 0,
                        this.dados.kpis.distribuicao_risco.atencao || 0,
                        this.dados.kpis.distribuicao_risco.satisfatorio || 0
                    ];
                    backgroundColor = [cores.error, cores.warning, cores.success];
                }

                this.chartMain = new Chart(ctx.getContext('2d'), {
                    type: this.tipoGrafico,
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Score',
                            data: data,
                            backgroundColor: backgroundColor,
                            borderWidth: 0,
                            borderRadius: 8
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: this.tipoGrafico === 'doughnut',
                                position: 'bottom'
                            },
                            tooltip: {
                                backgroundColor: '#0F3D52',
                                padding: 12,
                                cornerRadius: 8
                            }
                        },
                        scales: this.tipoGrafico !== 'doughnut' ? {
                            y: {
                                beginAtZero: true,
                                grid: { color: 'rgba(229, 236, 233, 0.5)' }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { maxRotation: 45, minRotation: 0 }
                            }
                        } : {}
                    }
                });

                // Esconder loading e mostrar gráfico
                if (loadingEl) loadingEl.classList.add('hidden');
                if (containerEl) containerEl.classList.remove('hidden');
            } catch (error) {
                console.error('Erro ao criar gráfico principal:', error);
                // Em caso de erro, esconder loading mesmo assim
                if (loadingEl) loadingEl.classList.add('hidden');
            }
        },

        criarGraficoDistribuicao() {
            const ctx = document.getElementById('graficoDistribuicao');
            const loadingEl = document.getElementById('chart-dist-loading');
            const containerEl = document.getElementById('chart-dist-container');

            if (!ctx) {
                console.error('Canvas graficoDistribuicao não encontrado');
                return;
            }

            // Verificar se os dados existem
            if (!this.dados || !this.dados.kpis || !this.dados.kpis.distribuicao_risco) {
                console.error('Dados insuficientes para gráfico de distribuição');
                return;
            }

            // Destruir gráfico anterior se existir
            if (this.chartDistribuicao) {
                this.chartDistribuicao.destroy();
                this.chartDistribuicao = null;
            }

            const cores = {
                error: '#EF4444',
                warning: '#FACC15',
                success: '#22C55E'
            };

            try {
                this.chartDistribuicao = new Chart(ctx.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels: ['Crítico', 'Atenção', 'Satisfatório'],
                        datasets: [{
                            data: [
                                this.dados.kpis.distribuicao_risco.critico || 0,
                                this.dados.kpis.distribuicao_risco.atencao || 0,
                                this.dados.kpis.distribuicao_risco.satisfatorio || 0
                            ],
                            backgroundColor: [cores.error, cores.warning, cores.success],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '60%',
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { padding: 15, font: { size: 12 } }
                            },
                            tooltip: {
                                backgroundColor: '#0F3D52',
                                padding: 12,
                                cornerRadius: 8
                            }
                        }
                    }
                });

                // Esconder loading e mostrar gráfico
                if (loadingEl) loadingEl.classList.add('hidden');
                if (containerEl) containerEl.classList.remove('hidden');
            } catch (error) {
                console.error('Erro ao criar gráfico de distribuição:', error);
                // Em caso de erro, esconder loading mesmo assim
                if (loadingEl) loadingEl.classList.add('hidden');
            }
        },

        // ======================================================
        // NOVOS GRÁFICOS - Análises Avançadas
        // ======================================================

        criarGraficoHistograma() {
            const ctx = document.getElementById('graficoHistograma');
            if (!ctx || !this.histogramaData || !this.histogramaData.labels) return;

            if (this.chartHistograma) {
                this.chartHistograma.destroy();
            }

            const cores = {
                primary: '#1EEB88',
                secondary: '#0F3D52'
            };

            this.chartHistograma = new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: this.histogramaData.labels,
                    datasets: [{
                        label: 'Frequência',
                        data: this.histogramaData.counts,
                        backgroundColor: cores.primary,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: cores.secondary,
                            padding: 10,
                            cornerRadius: 6
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Quantidade' }
                        },
                        x: {
                            title: { display: true, text: 'Faixa de Score' }
                        }
                    }
                }
            });
        },

        criarGraficoRadar() {
            const ctx = document.getElementById('graficoRadar');
            if (!ctx || !this.radarData || !this.radarData.labels) return;

            if (this.chartRadar) {
                this.chartRadar.destroy();
            }

            const cores = {
                primary: 'rgba(30, 235, 136, 0.5)',
                primaryBorder: '#1EEB88',
                error: '#EF4444',
                warning: '#FACC15',
                success: '#22C55E'
            };

            // Determinar cores dos pontos baseado no nível de risco
            const pontoCores = this.radarData.niveis_risco.map(nivel => {
                if (nivel === 'CRÍTICO') return cores.error;
                if (nivel === 'ATENÇÃO') return cores.warning;
                return cores.success;
            });

            this.chartRadar = new Chart(ctx.getContext('2d'), {
                type: 'radar',
                data: {
                    labels: this.radarData.labels,
                    datasets: [{
                        label: this.radarData.nivel_nome || 'Empresa',
                        data: this.radarData.scores,
                        backgroundColor: cores.primary,
                        borderColor: cores.primaryBorder,
                        borderWidth: 2,
                        pointBackgroundColor: pontoCores,
                        pointRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 4,
                            ticks: { stepSize: 1 }
                        }
                    }
                }
            });
        },

        criarGraficoPiramide() {
            const ctx = document.getElementById('graficoPiramide');
            if (!ctx || !this.piramideData || !this.piramideData.faixas) return;

            if (this.chartPiramide) {
                this.chartPiramide.destroy();
            }

            const faixas = this.piramideData.faixas;
            const masculino = this.piramideData.masculino;
            const feminino = this.piramideData.feminino;

            const cores = {
                error: '#EF4444',
                warning: '#FACC15',
                success: '#22C55E'
            };

            // Preparar datasets para pirâmide
            const datasets = [
                // Masculino (valores negativos - esquerda)
                {
                    label: 'M - Crítico',
                    data: faixas.map(f => masculino[f]?.critico || 0),
                    backgroundColor: cores.error,
                    stack: 'masculino'
                },
                {
                    label: 'M - Atenção',
                    data: faixas.map(f => masculino[f]?.atencao || 0),
                    backgroundColor: cores.warning,
                    stack: 'masculino'
                },
                {
                    label: 'M - Satisfatório',
                    data: faixas.map(f => masculino[f]?.satisfatorio || 0),
                    backgroundColor: cores.success,
                    stack: 'masculino'
                },
                // Feminino (valores positivos - direita)
                {
                    label: 'F - Crítico',
                    data: faixas.map(f => feminino[f]?.critico || 0),
                    backgroundColor: cores.error,
                    stack: 'feminino'
                },
                {
                    label: 'F - Atenção',
                    data: faixas.map(f => feminino[f]?.atencao || 0),
                    backgroundColor: cores.warning,
                    stack: 'feminino'
                },
                {
                    label: 'F - Satisfatório',
                    data: faixas.map(f => feminino[f]?.satisfatorio || 0),
                    backgroundColor: cores.success,
                    stack: 'feminino'
                }
            ];

            this.chartPiramide = new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: faixas,
                    datasets: datasets
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = Math.abs(context.raw);
                                    return `${context.dataset.label}: ${value}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            stacked: true,
                            ticks: {
                                callback: function(value) {
                                    return Math.abs(value);
                                }
                            },
                            title: {
                                display: true,
                                text: '← Masculino | Feminino →'
                            }
                        },
                        y: {
                            stacked: true,
                            title: { display: true, text: 'Faixa Etária' }
                        }
                    }
                }
            });
        },

        criarGraficoDistribuicaoPerguntas() {
            const ctx = document.getElementById('graficoDistribuicaoPerguntas');
            if (!ctx || !this.distribuicaoRespostas || !this.distribuicaoRespostas.perguntas_info) return;

            if (this.chartDistPerguntas) {
                this.chartDistPerguntas.destroy();
            }

            const perguntas = this.distribuicaoRespostas.perguntas_info.slice(0, 15); // Limitar a 15 perguntas
            const labels = perguntas.map(p => `P${p.numero}`);

            const cores = ['#EF4444', '#F97316', '#FACC15', '#84CC16', '#22C55E'];

            const datasets = [0, 1, 2, 3, 4].map((opcao, idx) => ({
                label: `Opção ${opcao}`,
                data: perguntas.map(p => p.distribuicao[opcao] || 0),
                backgroundColor: cores[idx],
                stack: 'stack1'
            }));

            this.chartDistPerguntas = new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    },
                    scales: {
                        x: {
                            stacked: true,
                            title: { display: true, text: 'Pergunta' }
                        },
                        y: {
                            stacked: true,
                            title: { display: true, text: 'Respostas' }
                        }
                    }
                }
            });
        }
    }));
});
