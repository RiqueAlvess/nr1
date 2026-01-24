"""Context processors para variaveis globais nos templates."""
from django.core.cache import cache


def branding_context(request):
    """
    Disponibiliza configuracoes de branding em todos os templates.

    Uso nos templates:
        {{ branding.nome_sistema }}
        {{ branding.get_logo_url }}
        {{ branding.cor_primaria }}
        {{ SYSTEM_NAME }}
        {{ COMPANY_NAME }}

    Cache:
        Os dados de branding sao cacheados por 5 minutos para performance.
    """
    from core.models import Branding

    cache_key = 'branding_context'
    cached_data = cache.get(cache_key)

    if cached_data:
        return cached_data

    try:
        branding = Branding.get_instance()
    except Exception:
        # Em caso de erro (ex: tabela nao existe ainda), retorna valores padrao
        return {
            'branding': None,
            'SYSTEM_NAME': 'Vivamente360',
            'COMPANY_NAME': '3S Dev',
        }

    context = {
        'branding': branding,
        'SYSTEM_NAME': branding.nome_sistema if branding.ativo else 'Vivamente360',
        'COMPANY_NAME': branding.nome_empresa if branding.ativo else '3S Dev',
    }

    # Cache por 5 minutos
    cache.set(cache_key, context, 300)

    return context
