# -*- coding: utf-8 -*-
"""
Context Processors customizados para disponibilizar variáveis globalmente nos templates
"""


def csp_nonce(request):
    """
    Disponibiliza o nonce CSP para todos os templates.

    Uso nos templates:
    <script nonce="{{ csp_nonce }}">
        // código JavaScript inline
    </script>
    """
    return {
        'csp_nonce': getattr(request, 'csp_nonce', '')
    }
