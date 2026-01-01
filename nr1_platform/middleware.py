# -*- coding: utf-8 -*-
"""
Middleware de Segurança Customizado para Headers HTTP
Implementa Content Security Policy (CSP) com nonce dinâmico
"""
import secrets
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware customizado para adicionar headers de segurança HTTP,
    incluindo Content Security Policy (CSP) com nonce dinâmico.
    """

    def process_request(self, request):
        """
        Gera um nonce único para cada requisição.
        Este nonce será usado para permitir scripts inline específicos.
        """
        # Gera um nonce criptograficamente seguro de 16 bytes (128 bits)
        request.csp_nonce = secrets.token_urlsafe(16)

    def process_response(self, request, response):
        """
        Adiciona headers de segurança à resposta HTTP.
        """
        # Obtém o nonce da requisição (se existir)
        nonce = getattr(request, 'csp_nonce', None)

        # Constrói a política CSP
        csp_directives = [
            "default-src 'self'",
        ]

        # script-src: permite scripts do próprio domínio, nonce dinâmico e CDNs específicos
        if nonce:
            csp_directives.append(f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net")
        else:
            # Fallback se não houver nonce (não deveria acontecer)
            csp_directives.append("script-src 'self' https://cdn.jsdelivr.net")

        # style-src: permite estilos do próprio domínio, inline (necessário para Bootstrap/Django Admin) e CDNs
        csp_directives.append("style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net")

        # img-src: permite imagens do próprio domínio, data URIs e HTTPS
        csp_directives.append("img-src 'self' data: https:")

        # font-src: permite fontes do próprio domínio e CDNs
        csp_directives.append("font-src 'self' https://cdn.jsdelivr.net")

        # connect-src: permite conexões apenas para o próprio domínio
        csp_directives.append("connect-src 'self'")

        # frame-ancestors: impede que a página seja incorporada em frames (equivalente a X-Frame-Options: DENY)
        csp_directives.append("frame-ancestors 'none'")

        # base-uri: restringe URLs base apenas para o próprio domínio
        csp_directives.append("base-uri 'self'")

        # form-action: permite envio de formulários apenas para o próprio domínio
        csp_directives.append("form-action 'self'")

        # Junta todas as diretivas com ponto-e-vírgula
        csp_policy = "; ".join(csp_directives) + ";"

        # Define o header CSP
        response["Content-Security-Policy"] = csp_policy

        # Headers adicionais de segurança
        # X-Content-Type-Options: impede que o navegador "adivinhe" o tipo MIME
        response["X-Content-Type-Options"] = "nosniff"

        # Referrer-Policy: controla o envio de informações de referência
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: controla acesso a recursos sensíveis
        response["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
        )

        return response
