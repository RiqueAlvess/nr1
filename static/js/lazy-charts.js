/**
 * Lazy Charts - Vivamente360
 * Implementa lazy loading de gráficos usando IntersectionObserver
 */

(function() {
    'use strict';

    /**
     * Lazy Chart Loader
     * Renderiza gráficos somente quando visíveis na viewport
     */
    class LazyChartLoader {
        constructor(options = {}) {
            this.defaults = {
                rootMargin: '50px',
                threshold: 0.1,
                skeletonClass: 'skeleton-card',
                chartContainerClass: 'chart-container',
                loadedClass: 'chart-loaded'
            };

            this.config = { ...this.defaults, ...options };
            this.observer = null;
            this.chartQueue = new Map();
        }

        /**
         * Inicializa o observer
         */
        init() {
            if ('IntersectionObserver' in window) {
                this.observer = new IntersectionObserver(
                    (entries) => this.handleIntersection(entries),
                    {
                        rootMargin: this.config.rootMargin,
                        threshold: this.config.threshold
                    }
                );

                // Observar todos os containers de gráficos
                const chartContainers = document.querySelectorAll(`[data-lazy-chart]`);
                chartContainers.forEach(container => {
                    this.observer.observe(container);
                });
            } else {
                // Fallback: carregar todos os gráficos imediatamente
                this.loadAllCharts();
            }
        }

        /**
         * Handler para interseção
         */
        handleIntersection(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadChart(entry.target);
                    this.observer.unobserve(entry.target);
                }
            });
        }

        /**
         * Carrega um gráfico específico
         */
        loadChart(container) {
            const chartId = container.dataset.lazyChart;
            const chartType = container.dataset.chartType;
            const chartCallback = container.dataset.chartCallback;

            // Remover skeleton
            const skeleton = container.querySelector('.skeleton');
            if (skeleton) {
                skeleton.remove();
            }

            // Marcar como carregado
            container.classList.add(this.config.loadedClass);

            // Chamar callback de criação do gráfico
            if (chartCallback && window[chartCallback]) {
                try {
                    window[chartCallback](chartId);
                } catch (error) {
                    console.error(`Erro ao carregar gráfico ${chartId}:`, error);
                }
            }

            // Disparar evento customizado
            container.dispatchEvent(new CustomEvent('chart:loaded', {
                detail: { chartId, chartType }
            }));
        }

        /**
         * Carrega todos os gráficos (fallback)
         */
        loadAllCharts() {
            const chartContainers = document.querySelectorAll(`[data-lazy-chart]`);
            chartContainers.forEach(container => this.loadChart(container));
        }

        /**
         * Registra um callback de criação de gráfico
         */
        registerChart(chartId, callback) {
            this.chartQueue.set(chartId, callback);
        }

        /**
         * Destroi o observer
         */
        destroy() {
            if (this.observer) {
                this.observer.disconnect();
            }
        }
    }

    /**
     * Inicializar lazy loading quando DOM estiver pronto
     */
    function initLazyCharts() {
        const lazyLoader = new LazyChartLoader({
            rootMargin: '100px', // Começar a carregar 100px antes de ficar visível
            threshold: 0.1
        });

        lazyLoader.init();

        // Exportar para escopo global
        window.lazyChartLoader = lazyLoader;

        // Cleanup ao sair da página
        window.addEventListener('beforeunload', () => {
            lazyLoader.destroy();
        });
    }

    // Auto-inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLazyCharts);
    } else {
        initLazyCharts();
    }

    // Exportar classe para uso externo
    window.LazyChartLoader = LazyChartLoader;
})();
