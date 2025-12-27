from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from core.models import Empresa, Unidade
from dashboard.services.dashboard_service import DashboardService
from core.services.audit_service import AuditService


@login_required
def dashboard_principal_view(request):
    """Dashboard principal com visão geral"""
    
    # Verificar perfil de acesso
    if not hasattr(request.user, 'perfil_acesso'):
        return render(request, 'dashboard/sem_acesso.html')
    
    perfil = request.user.perfil_acesso
    
    if not perfil.empresa:
        return render(request, 'dashboard/sem_empresa.html')
    
    # Buscar KPIs
    dashboard_service = DashboardService()
    kpis = dashboard_service.get_kpis_empresa(str(perfil.empresa.id))
    
    # Auditoria
    AuditService.log(
        action='DASHBOARD_ACCESSED',
        description=f'Dashboard principal acessado por {request.user.username}',
        user=request.user,
        ip_address=AuditService.get_client_ip(request),
        user_agent=AuditService.get_user_agent(request),
        metadata={'empresa_id': str(perfil.empresa.id)}
    )
    
    context = {
        'kpis': kpis,
        'empresa': perfil.empresa,
        'perfil': perfil
    }
    
    return render(request, 'dashboard/principal.html', context)


@login_required
def dashboard_unidades_view(request):
    """Dashboard com dados por unidade"""
    
    if not hasattr(request.user, 'perfil_acesso'):
        return render(request, 'dashboard/sem_acesso.html')
    
    perfil = request.user.perfil_acesso
    
    if perfil.nivel_acesso not in ['EMPRESA', 'UNIDADE']:
        return render(request, 'dashboard/sem_permissao.html')
    
    dashboard_service = DashboardService()
    dados = dashboard_service.get_dados_por_unidade(str(perfil.empresa.id))
    
    context = {
        'dados': dados,
        'empresa': perfil.empresa
    }
    
    return render(request, 'dashboard/unidades.html', context)


@login_required
def dashboard_setores_view(request):
    """Dashboard com dados por setor"""
    
    if not hasattr(request.user, 'perfil_acesso'):
        return render(request, 'dashboard/sem_acesso.html')
    
    perfil = request.user.perfil_acesso
    unidade_id = request.GET.get('unidade')
    
    dashboard_service = DashboardService()
    dados = dashboard_service.get_dados_por_setor(
        str(perfil.empresa.id),
        unidade_id
    )
    
    # Filtrar setores permitidos se necessário
    if perfil.nivel_acesso == 'SETOR':
        setores_permitidos = perfil.setores.values_list('id', flat=True)
        dados['setores'] = [
            s for s in dados['setores']
            if s['setor_id'] in [str(sid) for sid in setores_permitidos]
        ]
        dados['total_setores_visiveis'] = len(dados['setores'])
    
    context = {
        'dados': dados,
        'empresa': perfil.empresa,
        'unidade_id': unidade_id
    }
    
    return render(request, 'dashboard/setores.html', context)


@login_required
def dashboard_dimensoes_view(request):
    """Dashboard com análise de dimensões"""
    
    if not hasattr(request.user, 'perfil_acesso'):
        return render(request, 'dashboard/sem_acesso.html')
    
    perfil = request.user.perfil_acesso
    
    dashboard_service = DashboardService()
    dados = dashboard_service.get_dimensoes_criticas(str(perfil.empresa.id))
    
    context = {
        'dados': dados,
        'empresa': perfil.empresa
    }
    
    return render(request, 'dashboard/dimensoes.html', context)