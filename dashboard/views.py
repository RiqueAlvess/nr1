import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.http import require_GET
from core.models import Empresa, Unidade
from dashboard.services.dashboard_service import DashboardService
from core.services.audit_service import AuditService


@login_required
def dashboard_principal_view(request):
    """
    Dashboard principal consolidado com visão geral e análises detalhadas
    Suporta múltiplas empresas no perfil de acesso
    """

    # Verificar perfil de acesso
    if not hasattr(request.user, 'perfil_acesso'):
        return render(request, 'dashboard/sem_acesso.html')

    perfil = request.user.perfil_acesso

    # Verificar se o usuário tem acesso ao dashboard
    if not (perfil.tem_acesso_completo_dashboards() or perfil.tem_acesso_limitado()):
        return render(request, 'dashboard/sem_permissao.html')

    # Obter empresas do usuário
    empresas = perfil.get_empresas()
    if not empresas.exists():
        return render(request, 'dashboard/sem_empresa.html')

    # Empresa selecionada (pode ser filtrada via GET)
    empresa_id_selecionada = request.GET.get('empresa')
    if empresa_id_selecionada:
        empresa_selecionada = empresas.filter(id=empresa_id_selecionada).first()
        if not empresa_selecionada:
            empresa_selecionada = empresas.first()
    else:
        empresa_selecionada = empresas.first()

    # Buscar todos os dados necessários para a empresa selecionada
    dashboard_service = DashboardService()
    empresa_id = str(empresa_selecionada.id)

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
            # Filtrar setores também
            dados_setores['setores'] = [
                s for s in dados_setores['setores']
                if any(str(uid) in s.get('unidade_id', '') for uid in unidades_permitidas)
            ]
        elif perfil.nivel_acesso == 'SETOR':
            setores_permitidos = perfil.setores.values_list('id', flat=True)
            dados_setores['setores'] = [
                s for s in dados_setores['setores']
                if s['setor_id'] in [str(sid) for sid in setores_permitidos]
            ]
            # Limpar unidades se nível é setor
            dados_unidades['unidades'] = []

    # Auditoria
    AuditService.log(
        action='DASHBOARD_ACCESSED',
        description=f'Dashboard consolidado acessado por {request.user.username}',
        user=request.user,
        ip_address=AuditService.get_client_ip(request),
        user_agent=AuditService.get_user_agent(request),
        metadata={
            'empresa_id': empresa_id,
            'empresa_nome': empresa_selecionada.nome,
            'grupo': perfil.get_grupo_principal(),
            'nivel_acesso': perfil.nivel_acesso,
            'total_empresas_acesso': empresas.count()
        }
    )

    # Buscar dados avançados adicionais
    estatisticas_avancadas = dashboard_service.get_estatisticas_avancadas(empresa_id)
    distribuicao_scores = dashboard_service.get_distribuicao_scores(empresa_id)
    tempo_medio = dashboard_service.get_tempo_medio_resposta(empresa_id)
    pontuacao_por_pergunta = dashboard_service.get_pontuacao_por_pergunta(empresa_id)
    analise_genero = dashboard_service.get_analise_por_genero(empresa_id)
    analise_faixa_etaria = dashboard_service.get_analise_por_faixa_etaria(empresa_id)
    piramide_etaria = dashboard_service.get_piramide_etaria_com_risco(empresa_id)
    dimensoes_por_genero = dashboard_service.get_dimensoes_por_genero(empresa_id)

    # Novos dados para análises avançadas
    distribuicao_respostas = dashboard_service.get_distribuicao_respostas_completa(empresa_id)
    dimensoes_polaridade = dashboard_service.get_dimensoes_por_polaridade(empresa_id)
    radar_multinivel = dashboard_service.get_radar_multinivel(empresa_id)
    consistencia_interna = dashboard_service.get_consistencia_interna(empresa_id)
    histograma_scores = dashboard_service.get_histograma_scores(empresa_id)
    cargos_disponiveis = dashboard_service.get_cargos_disponiveis(empresa_id)

    context = {
        # Dados originais para uso no template HTML
        'kpis': kpis,
        'dados_unidades': dados_unidades,
        'dados_setores': dados_setores,
        'dados_dimensoes': dados_dimensoes,
        'estatisticas_avancadas': estatisticas_avancadas,
        'tempo_medio': tempo_medio,
        # Dados serializados em JSON para uso no JavaScript
        'kpis_json': json.dumps(kpis, cls=DjangoJSONEncoder),
        'dados_unidades_json': json.dumps(dados_unidades, cls=DjangoJSONEncoder),
        'dados_setores_json': json.dumps(dados_setores, cls=DjangoJSONEncoder),
        'dados_dimensoes_json': json.dumps(dados_dimensoes, cls=DjangoJSONEncoder),
        'estatisticas_avancadas_json': json.dumps(estatisticas_avancadas, cls=DjangoJSONEncoder),
        'distribuicao_scores_json': json.dumps(distribuicao_scores, cls=DjangoJSONEncoder),
        'tempo_medio_json': json.dumps(tempo_medio, cls=DjangoJSONEncoder),
        'pontuacao_por_pergunta_json': json.dumps(pontuacao_por_pergunta, cls=DjangoJSONEncoder),
        'analise_genero_json': json.dumps(analise_genero, cls=DjangoJSONEncoder),
        'analise_faixa_etaria_json': json.dumps(analise_faixa_etaria, cls=DjangoJSONEncoder),
        'piramide_etaria_json': json.dumps(piramide_etaria, cls=DjangoJSONEncoder),
        'dimensoes_por_genero_json': json.dumps(dimensoes_por_genero, cls=DjangoJSONEncoder),
        # Novos dados para análises avançadas
        'distribuicao_respostas': distribuicao_respostas,
        'distribuicao_respostas_json': json.dumps(distribuicao_respostas, cls=DjangoJSONEncoder),
        'dimensoes_polaridade': dimensoes_polaridade,
        'dimensoes_polaridade_json': json.dumps(dimensoes_polaridade, cls=DjangoJSONEncoder),
        'radar_multinivel_json': json.dumps(radar_multinivel, cls=DjangoJSONEncoder),
        'consistencia_interna': consistencia_interna,
        'consistencia_interna_json': json.dumps(consistencia_interna, cls=DjangoJSONEncoder),
        'histograma_scores_json': json.dumps(histograma_scores, cls=DjangoJSONEncoder),
        'cargos_disponiveis_json': json.dumps(cargos_disponiveis, cls=DjangoJSONEncoder),
        # Outros dados do contexto
        'empresa': empresa_selecionada,
        'empresas': empresas,
        'empresa_selecionada_id': str(empresa_selecionada.id),
        'tem_multiplas_empresas': empresas.count() > 1,
        'perfil': perfil
    }

    return render(request, 'dashboard/principal.html', context)


@login_required
def dashboard_unidades_view(request):
    """Dashboard com dados por unidade"""

    if not hasattr(request.user, 'perfil_acesso'):
        return render(request, 'dashboard/sem_acesso.html')

    perfil = request.user.perfil_acesso

    # Verificar permissão de nível de acesso
    if perfil.nivel_acesso == 'SETOR':
        messages.warning(request, 'Seu nível de acesso não permite visualizar dados por unidade.')
        return redirect('dashboard:principal')

    empresas = perfil.get_empresas()
    if not empresas.exists():
        return render(request, 'dashboard/sem_empresa.html')

    # Empresa selecionada
    empresa_id_selecionada = request.GET.get('empresa')
    if empresa_id_selecionada:
        empresa_selecionada = empresas.filter(id=empresa_id_selecionada).first()
        if not empresa_selecionada:
            empresa_selecionada = empresas.first()
    else:
        empresa_selecionada = empresas.first()

    dashboard_service = DashboardService()
    dados = dashboard_service.get_dados_por_unidade(str(empresa_selecionada.id))

    # Filtrar unidades se nível é UNIDADE
    if perfil.nivel_acesso == 'UNIDADE':
        unidades_permitidas = perfil.unidades.values_list('id', flat=True)
        dados['unidades'] = [
            u for u in dados['unidades']
            if u['unidade_id'] in [str(uid) for uid in unidades_permitidas]
        ]
        dados['total_unidades_visiveis'] = len(dados['unidades'])

    context = {
        'dados': dados,
        'empresa': empresa_selecionada,
        'empresas': empresas,
        'tem_multiplas_empresas': empresas.count() > 1,
    }

    return render(request, 'dashboard/unidades.html', context)


@login_required
def dashboard_setores_view(request):
    """Dashboard com dados por setor"""

    if not hasattr(request.user, 'perfil_acesso'):
        return render(request, 'dashboard/sem_acesso.html')

    perfil = request.user.perfil_acesso
    unidade_id = request.GET.get('unidade')

    empresas = perfil.get_empresas()
    if not empresas.exists():
        return render(request, 'dashboard/sem_empresa.html')

    # Empresa selecionada
    empresa_id_selecionada = request.GET.get('empresa')
    if empresa_id_selecionada:
        empresa_selecionada = empresas.filter(id=empresa_id_selecionada).first()
        if not empresa_selecionada:
            empresa_selecionada = empresas.first()
    else:
        empresa_selecionada = empresas.first()

    dashboard_service = DashboardService()
    dados = dashboard_service.get_dados_por_setor(
        str(empresa_selecionada.id),
        unidade_id
    )

    # Filtrar setores permitidos se necessário
    if perfil.nivel_acesso == 'UNIDADE':
        unidades_permitidas = perfil.unidades.values_list('id', flat=True)
        # Filtrar por unidades permitidas
        setores_filtrados = []
        for s in dados['setores']:
            # Verificar se o setor pertence a uma unidade permitida
            setor_unidade_id = s.get('unidade_id')
            if setor_unidade_id and any(str(uid) == setor_unidade_id for uid in unidades_permitidas):
                setores_filtrados.append(s)
        dados['setores'] = setores_filtrados
        dados['total_setores_visiveis'] = len(dados['setores'])

    elif perfil.nivel_acesso == 'SETOR':
        setores_permitidos = perfil.setores.values_list('id', flat=True)
        dados['setores'] = [
            s for s in dados['setores']
            if s['setor_id'] in [str(sid) for sid in setores_permitidos]
        ]
        dados['total_setores_visiveis'] = len(dados['setores'])

    context = {
        'dados': dados,
        'empresa': empresa_selecionada,
        'empresas': empresas,
        'tem_multiplas_empresas': empresas.count() > 1,
        'unidade_id': unidade_id
    }

    return render(request, 'dashboard/setores.html', context)


@login_required
def dashboard_dimensoes_view(request):
    """Dashboard com análise de dimensões"""

    if not hasattr(request.user, 'perfil_acesso'):
        return render(request, 'dashboard/sem_acesso.html')

    perfil = request.user.perfil_acesso

    empresas = perfil.get_empresas()
    if not empresas.exists():
        return render(request, 'dashboard/sem_empresa.html')

    # Empresa selecionada
    empresa_id_selecionada = request.GET.get('empresa')
    if empresa_id_selecionada:
        empresa_selecionada = empresas.filter(id=empresa_id_selecionada).first()
        if not empresa_selecionada:
            empresa_selecionada = empresas.first()
    else:
        empresa_selecionada = empresas.first()

    dashboard_service = DashboardService()
    dados = dashboard_service.get_dimensoes_criticas(str(empresa_selecionada.id))

    context = {
        'dados': dados,
        'empresa': empresa_selecionada,
        'empresas': empresas,
        'tem_multiplas_empresas': empresas.count() > 1,
    }

    return render(request, 'dashboard/dimensoes.html', context)


# ============================================================================
# APIs para Filtros Dinâmicos - Análises Avançadas
# ============================================================================

@login_required
@require_GET
def api_radar_multinivel(request):
    """
    API para obter dados do radar com filtros dinâmicos.

    Query params:
        empresa: UUID da empresa (obrigatório)
        unidade: UUID da unidade (opcional)
        setor: UUID do setor (opcional)
        cargo: UUID do cargo (opcional)
    """
    if not hasattr(request.user, 'perfil_acesso'):
        return JsonResponse({'error': 'Sem acesso'}, status=403)

    perfil = request.user.perfil_acesso
    empresas = perfil.get_empresas()

    empresa_id = request.GET.get('empresa')
    if not empresa_id:
        return JsonResponse({'error': 'Empresa não especificada'}, status=400)

    # Verificar acesso à empresa
    if not empresas.filter(id=empresa_id).exists():
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    unidade_id = request.GET.get('unidade')
    setor_id = request.GET.get('setor')
    cargo_id = request.GET.get('cargo')

    dashboard_service = DashboardService()
    dados = dashboard_service.get_radar_multinivel(
        empresa_id,
        unidade_id=unidade_id,
        setor_id=setor_id,
        cargo_id=cargo_id
    )

    return JsonResponse(dados, encoder=DjangoJSONEncoder)


@login_required
@require_GET
def api_distribuicao_respostas(request):
    """
    API para obter distribuição de respostas com filtros dinâmicos.

    Query params:
        empresa: UUID da empresa (obrigatório)
        unidade: UUID da unidade (opcional)
        setor: UUID do setor (opcional)
        cargo: UUID do cargo (opcional)
    """
    if not hasattr(request.user, 'perfil_acesso'):
        return JsonResponse({'error': 'Sem acesso'}, status=403)

    perfil = request.user.perfil_acesso
    empresas = perfil.get_empresas()

    empresa_id = request.GET.get('empresa')
    if not empresa_id:
        return JsonResponse({'error': 'Empresa não especificada'}, status=400)

    if not empresas.filter(id=empresa_id).exists():
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    unidade_id = request.GET.get('unidade')
    setor_id = request.GET.get('setor')
    cargo_id = request.GET.get('cargo')

    dashboard_service = DashboardService()
    dados = dashboard_service.get_distribuicao_respostas_completa(
        empresa_id,
        unidade_id=unidade_id,
        setor_id=setor_id,
        cargo_id=cargo_id
    )

    return JsonResponse(dados, encoder=DjangoJSONEncoder)


@login_required
@require_GET
def api_scores_agrupamento(request):
    """
    API para obter scores por agrupamento.

    Query params:
        empresa: UUID da empresa (obrigatório)
        agrupamento: 'unidade', 'setor' ou 'cargo' (default: 'unidade')
    """
    if not hasattr(request.user, 'perfil_acesso'):
        return JsonResponse({'error': 'Sem acesso'}, status=403)

    perfil = request.user.perfil_acesso
    empresas = perfil.get_empresas()

    empresa_id = request.GET.get('empresa')
    if not empresa_id:
        return JsonResponse({'error': 'Empresa não especificada'}, status=400)

    if not empresas.filter(id=empresa_id).exists():
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    agrupamento = request.GET.get('agrupamento', 'unidade')
    if agrupamento not in ['unidade', 'setor', 'cargo']:
        agrupamento = 'unidade'

    dashboard_service = DashboardService()
    dados = dashboard_service.get_scores_por_agrupamento(empresa_id, agrupamento)

    return JsonResponse(dados, encoder=DjangoJSONEncoder)


@login_required
@require_GET
def api_cargos_disponiveis(request):
    """
    API para obter lista de cargos disponíveis para filtros.

    Query params:
        empresa: UUID da empresa (obrigatório)
    """
    if not hasattr(request.user, 'perfil_acesso'):
        return JsonResponse({'error': 'Sem acesso'}, status=403)

    perfil = request.user.perfil_acesso
    empresas = perfil.get_empresas()

    empresa_id = request.GET.get('empresa')
    if not empresa_id:
        return JsonResponse({'error': 'Empresa não especificada'}, status=400)

    if not empresas.filter(id=empresa_id).exists():
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    dashboard_service = DashboardService()
    cargos = dashboard_service.get_cargos_disponiveis(empresa_id)

    return JsonResponse({'cargos': cargos}, encoder=DjangoJSONEncoder)
