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
    """Dashboard principal consolidado com visão geral e análises detalhadas"""

    # Verificar perfil de acesso
    if not hasattr(request.user, 'perfil_acesso'):
        return render(request, 'dashboard/sem_acesso.html')

    perfil = request.user.perfil_acesso

    # Verificar se o usuário tem acesso ao dashboard
    if not (perfil.tem_acesso_completo_dashboards() or perfil.tem_acesso_limitado()):
        return render(request, 'dashboard/sem_permissao.html')

    if not perfil.empresa:
        return render(request, 'dashboard/sem_empresa.html')

    # Buscar todos os dados necessários
    dashboard_service = DashboardService()
    empresa_id = str(perfil.empresa.id)

    kpis = dashboard_service.get_kpis_empresa(empresa_id)
    dados_unidades = dashboard_service.get_dados_por_unidade(empresa_id)
    dados_setores = dashboard_service.get_dados_por_setor(empresa_id)
    dados_dimensoes = dashboard_service.get_dimensoes_criticas(empresa_id)

    # Filtrar dados por nível de acesso
    if perfil.tem_acesso_limitado():
        # Aplicar filtros de hierarquia para Liderança e Consultoria
        if perfil.nivel_acesso == 'UNIDADE':
            unidades_permitidas = perfil.unidades.values_list('id', flat=True)
            dados_unidades['unidades'] = [
                u for u in dados_unidades['unidades']
                if u['unidade_id'] in [str(uid) for uid in unidades_permitidas]
            ]
        elif perfil.nivel_acesso == 'SETOR':
            setores_permitidos = perfil.setores.values_list('id', flat=True)
            dados_setores['setores'] = [
                s for s in dados_setores['setores']
                if s['setor_id'] in [str(sid) for sid in setores_permitidos]
            ]

    # Auditoria
    AuditService.log(
        action='DASHBOARD_ACCESSED',
        description=f'Dashboard consolidado acessado por {request.user.username}',
        user=request.user,
        ip_address=AuditService.get_client_ip(request),
        user_agent=AuditService.get_user_agent(request),
        metadata={
            'empresa_id': empresa_id,
            'grupo': perfil.get_grupo_principal(),
            'nivel_acesso': perfil.nivel_acesso
        }
    )

    context = {
        'kpis': kpis,
        'dados_unidades': dados_unidades,
        'dados_setores': dados_setores,
        'dados_dimensoes': dados_dimensoes,
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