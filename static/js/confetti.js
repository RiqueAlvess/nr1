/**
 * Confetti Animation - Vivamente360
 * Animação de confetti para página de sucesso
 */

(function() {
    'use strict';

    /**
     * Cria animação de confetti
     * @param {Object} options - Opções de configuração
     */
    function createConfetti(options = {}) {
        const defaults = {
            containerId: 'confetti-container',
            count: 50,
            colors: ['#1EEB88', '#6EDBC1', '#0F3D52', '#FACC15', '#3ABFF8'],
            duration: 6000
        };

        const config = { ...defaults, ...options };
        const container = document.getElementById(config.containerId);

        if (!container) {
            console.error('Container de confetti não encontrado');
            return;
        }

        for (let i = 0; i < config.count; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.backgroundColor = config.colors[Math.floor(Math.random() * config.colors.length)];
            confetti.style.animationDelay = Math.random() * 2 + 's';
            confetti.style.animationDuration = (Math.random() * 2 + 3) + 's';

            // Random shapes
            const shapes = ['circle', 'square', 'triangle'];
            const shape = shapes[Math.floor(Math.random() * shapes.length)];

            if (shape === 'circle') {
                confetti.style.borderRadius = '50%';
            } else if (shape === 'triangle') {
                confetti.style.width = '0';
                confetti.style.height = '0';
                confetti.style.borderLeft = '5px solid transparent';
                confetti.style.borderRight = '5px solid transparent';
                confetti.style.borderBottom = '10px solid ' + confetti.style.backgroundColor;
                confetti.style.backgroundColor = 'transparent';
            }

            container.appendChild(confetti);
        }

        // Remove confetti after animation
        setTimeout(() => {
            container.innerHTML = '';
        }, config.duration);
    }

    // Export to global scope
    window.createConfetti = createConfetti;

    // Start confetti on load if container exists
    window.addEventListener('load', function() {
        if (document.getElementById('confetti-container')) {
            createConfetti();
        }
    });
})();
