/**
 * Quiz Form - Vivamente360
 * Gerenciamento do formulário de questionário HSE-IT
 */

(function() {
    'use strict';

    // Configurações (serão preenchidas via data attributes)
    let totalQuestions = 0;
    const form = document.getElementById('quiz-form');
    const headerProgressBar = document.getElementById('header-progress-bar');
    const footerProgressBar = document.getElementById('footer-progress-bar');
    const progressPercent = document.getElementById('progress-percent');
    const countDisplay = document.getElementById('answered-count');
    const remainingText = document.getElementById('remaining-text');
    const submitBtn = document.getElementById('submit-btn');
    const confirmModal = document.getElementById('confirm-modal');
    const confirmSubmitBtn = document.getElementById('confirm-submit-btn');

    // Verificar se elementos existem
    if (!form) {
        console.error('Formulário de quiz não encontrado');
        return;
    }

    // Obter total de perguntas
    totalQuestions = parseInt(form.dataset.totalQuestions) || form.querySelectorAll('.question-card').length;

    /**
     * Atualiza o estado visual das opções
     */
    function updateOptionStyles(radioInput) {
        const container = radioInput.closest('.question-card');
        const allLabels = container.querySelectorAll('.option-label');

        allLabels.forEach(label => {
            const input = label.querySelector('input[type="radio"]');
            if (input.checked) {
                label.classList.add('selected');
            } else {
                label.classList.remove('selected');
            }
        });

        // Marca o card como respondido
        container.classList.add('answered');
    }

    /**
     * Atualiza o progresso
     */
    function updateProgress() {
        const answered = new Set();
        form.querySelectorAll('input[type="radio"]:checked').forEach(radio => {
            answered.add(radio.name);
        });

        const count = answered.size;
        const percent = Math.round((count / totalQuestions) * 100);
        const remaining = totalQuestions - count;

        // Atualiza displays
        if (headerProgressBar) headerProgressBar.style.width = percent + '%';
        if (footerProgressBar) footerProgressBar.style.width = percent + '%';
        if (progressPercent) progressPercent.textContent = percent;
        if (countDisplay) countDisplay.textContent = count;

        // Atualiza texto de restantes
        if (remainingText) {
            if (remaining === 0) {
                remainingText.innerHTML = '<span class="text-success font-medium">✓ Completo!</span>';
            } else if (remaining === 1) {
                remainingText.textContent = '1 restante';
            } else {
                remainingText.textContent = remaining + ' restantes';
            }
        }

        // Habilita/desabilita botão de enviar
        if (submitBtn) {
            if (count === totalQuestions) {
                submitBtn.disabled = false;
                submitBtn.classList.add('btn-submit-ready');
            } else {
                submitBtn.disabled = true;
                submitBtn.classList.remove('btn-submit-ready');
            }
        }
    }

    /**
     * Event listeners para os radio buttons
     */
    form.querySelectorAll('input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', function() {
            updateOptionStyles(this);
            updateProgress();

            // Scroll suave para próxima pergunta após responder (mobile)
            if (window.innerWidth < 768) {
                const currentCard = this.closest('.question-card');
                const nextCard = currentCard.nextElementSibling;

                if (nextCard && !nextCard.classList.contains('answered')) {
                    setTimeout(() => {
                        nextCard.scrollIntoView({
                            behavior: 'smooth',
                            block: 'center'
                        });
                    }, 300);
                }
            }
        });
    });

    /**
     * Ao clicar no label, marcar o radio
     */
    document.querySelectorAll('.option-label').forEach(label => {
        label.addEventListener('click', function(e) {
            if (e.target.tagName !== 'INPUT') {
                const radio = this.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                    radio.dispatchEvent(new Event('change'));
                }
            }
        });
    });

    /**
     * Intercepta o submit para mostrar modal de confirmação
     */
    if (confirmModal) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            if (typeof confirmModal.showModal === 'function') {
                confirmModal.showModal();
            }
        });

        /**
         * Confirma o envio
         */
        if (confirmSubmitBtn) {
            confirmSubmitBtn.addEventListener('click', function() {
                if (typeof confirmModal.close === 'function') {
                    confirmModal.close();
                }

                // Mostra loading no botão
                this.innerHTML = '<span class="loading loading-spinner loading-sm mr-2"></span> Enviando...';
                this.disabled = true;

                // Remove o listener de submit para evitar loop
                const newForm = form.cloneNode(true);
                form.parentNode.replaceChild(newForm, form);

                // Envia o formulário
                newForm.submit();
            });
        }
    }

    /**
     * Restaurar estado se usuário voltar na página
     */
    window.addEventListener('load', function() {
        form.querySelectorAll('input[type="radio"]:checked').forEach(radio => {
            updateOptionStyles(radio);
        });
        updateProgress();
    });

    /**
     * Salvamento automático de progresso (localStorage)
     */
    function saveProgress() {
        if (!form) return;

        const formData = {};
        form.querySelectorAll('input[type="radio"]:checked').forEach(radio => {
            formData[radio.name] = radio.value;
        });

        try {
            const token = form.action.split('/').pop();
            localStorage.setItem(`quiz_progress_${token}`, JSON.stringify(formData));
        } catch (error) {
            // Ignorar erros de localStorage (pode estar desabilitado)
        }
    }

    /**
     * Restaurar progresso do localStorage
     */
    function restoreProgress() {
        try {
            const token = form.action.split('/').pop();
            const saved = localStorage.getItem(`quiz_progress_${token}`);

            if (saved) {
                const formData = JSON.parse(saved);
                Object.entries(formData).forEach(([name, value]) => {
                    const radio = form.querySelector(`input[name="${name}"][value="${value}"]`);
                    if (radio) {
                        radio.checked = true;
                        updateOptionStyles(radio);
                    }
                });
                updateProgress();
            }
        } catch (error) {
            // Ignorar erros de localStorage
        }
    }

    /**
     * Limpar progresso ao submeter
     */
    form.addEventListener('submit', function() {
        try {
            const token = form.action.split('/').pop();
            localStorage.removeItem(`quiz_progress_${token}`);
        } catch (error) {
            // Ignorar erros
        }
    });

    // Salvar progresso a cada mudança
    form.addEventListener('change', saveProgress);

    // Restaurar progresso ao carregar
    restoreProgress();
})();
