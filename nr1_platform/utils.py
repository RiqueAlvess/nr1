"""Utilidades para Django Unfold Admin."""


def environment_callback(request):
    """Retorna o ambiente atual (development/production)."""
    from django.conf import settings
    return "production" if not settings.DEBUG else "development"


def dashboard_callback(request, context):
    """
    Customiza o dashboard do admin com estatísticas do sistema.

    Adiciona informações relevantes ao contexto do dashboard principal.
    """
    from core.models import Empresa
    from importacao.models import Colaborador
    from quiz.models import Resposta
    from account.models import PerfilAcesso

    context.update({
        "total_empresas": Empresa.objects.filter(ativa=True).count(),
        "total_colaboradores": Colaborador.objects.filter(ativo=True).count(),
        "total_respostas": Resposta.objects.count(),
        "total_usuarios": PerfilAcesso.objects.filter(ativo=True).count(),
    })
    return context
