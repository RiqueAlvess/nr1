"""
Views para handlers de erro customizados.
"""
from django.shortcuts import render


def handler404(request, exception):
    """Handler customizado para erro 404 - Página não encontrada."""
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """Handler customizado para erro 500 - Erro interno do servidor."""
    return render(request, 'errors/500.html', status=500)
