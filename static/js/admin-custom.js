// Customizacoes JavaScript do Django Admin com Unfold

document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin Vivamente360 carregado');

    // Inicializar color pickers se existirem
    initColorPickers();

    // Adicionar confirmacao para acoes destrutivas
    initDeleteConfirmations();

    // Melhorar UX de uploads de imagem
    initImagePreviews();
});

/**
 * Inicializa color pickers para campos de cor hexadecimal
 */
function initColorPickers() {
    const colorInputs = document.querySelectorAll('input[name*="cor_"]');

    colorInputs.forEach(function(input) {
        // Criar um color picker nativo ao lado do input
        const colorPicker = document.createElement('input');
        colorPicker.type = 'color';
        colorPicker.value = input.value || '#000000';
        colorPicker.style.cssText = 'width: 40px; height: 32px; padding: 0; border: none; cursor: pointer; margin-left: 8px; vertical-align: middle;';

        // Sincronizar valores
        colorPicker.addEventListener('change', function() {
            input.value = colorPicker.value.toUpperCase();
        });

        input.addEventListener('change', function() {
            if (/^#[0-9A-Fa-f]{6}$/.test(input.value)) {
                colorPicker.value = input.value;
            }
        });

        // Inserir apos o input
        input.parentNode.insertBefore(colorPicker, input.nextSibling);
    });
}

/**
 * Adiciona confirmacao para acoes de delete
 */
function initDeleteConfirmations() {
    const deleteButtons = document.querySelectorAll('.deletelink, [data-action="delete"]');

    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja excluir este item? Esta acao nao pode ser desfeita.')) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Preview de imagens antes do upload
 */
function initImagePreviews() {
    const fileInputs = document.querySelectorAll('input[type="file"][accept*="image"]');

    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Procurar ou criar elemento de preview
                    let preview = input.parentNode.querySelector('.upload-preview');
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.className = 'upload-preview';
                        preview.style.cssText = 'max-height: 100px; margin-top: 10px; border-radius: 8px; background: #f3f4f6; padding: 10px;';
                        input.parentNode.appendChild(preview);
                    }
                    preview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    });
}

/**
 * Utilitario: Copiar texto para clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copiado para a area de transferencia!', 'success');
    }).catch(function(err) {
        console.error('Erro ao copiar:', err);
    });
}

/**
 * Exibe notificacao temporaria
 */
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = 'admin-notification admin-notification-' + type;
    notification.textContent = message;
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; padding: 12px 24px; border-radius: 8px; background: #1eeb88; color: #0f3d52; font-weight: 500; z-index: 9999; animation: fadeInOut 3s ease;';

    document.body.appendChild(notification);

    setTimeout(function() {
        notification.remove();
    }, 3000);
}

// Adicionar estilo de animacao
const style = document.createElement('style');
style.textContent = '@keyframes fadeInOut { 0% { opacity: 0; transform: translateY(-10px); } 10% { opacity: 1; transform: translateY(0); } 90% { opacity: 1; transform: translateY(0); } 100% { opacity: 0; transform: translateY(-10px); } }';
document.head.appendChild(style);
