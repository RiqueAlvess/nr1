import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.http import require_GET
from django.db.models import F
from core.models import Empresa, Unidade
from dashboard.services.dashboard_service import DashboardService
from core.services.audit_service import AuditService

logger = logging.getLogger('nr1')


@login_required
def dashboard_principal_view(request):
    """
    Dashboard principal consolidado com visão geral e análises detalhadas
    Suporta múltiplas empresas no perfil de acesso
    HTMX-ready: Retorna apenas o conteúdo quando requisição vem do HTMX
    """
    try:
        logger.info("=== DASHBOARD PRINCIPAL - Início ===")
        logger.info(f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")

        # Verificar perfil de acesso
        if not hasattr(request.user, 'perfil_acesso'):
            logger.warning(f"Usuário {request.user.username} sem perfil de acesso")
            template = 'dashboard/sem_acesso_content.html' if request.htmx else 'dashboard/sem_acesso.html'
            return render(request, template)

        perfil = request.user.perfil_acesso
        logger.info(f"Perfil de acesso: {perfil.nivel_acesso}")

        # Verificar se o usuário tem acesso ao dashboard
        if not (perfil.tem_acesso_completo_dashboards() or perfil.tem_acesso_limitado()):
            logger.warning(f"Usuário {request.user.username} sem permissão para dashboard")
            template = 'dashboard/sem_permissao_content.html' if request.htmx else 'dashboard/sem_permissao.html'
            return render(request, template)

        # Obter empresas do usuário
        empresas = perfil.get_empresas()
        if not empresas.exists():
            logger.warning(f"Usuário {request.user.username} sem empresas")
            return render(request, 'dashboard/sem_empresa.html')

        logger.info(f"Total de empresas do usuário: {empresas.count()}")

        # Empresa selecionada (pode ser filtrada via GET)
        empresa_id_selecionada = request.GET.get('empresa')
        if empresa_id_selecionada:
            empresa_selecionada = empresas.filter(id=empresa_id_selecionada).first()
            if not empresa_selecionada:
                empresa_selecionada = empresas.first()
        else:
            empresa_selecionada = empresas.first()

        logger.info(f"Empresa selecionada: {empresa_selecionada.nome} (ID: {empresa_selecionada.id})")

        # Buscar todos os dados necessários para a empresa selecionada
        dashboard_service = DashboardService()
        empresa_id = str(empresa_selecionada.id)

        logger.info("Buscando KPIs...")
        kpis = dashboard_service.get_kpis_empresa(empresa_id)
        logger.info(f"KPIs OK - Keys: {list(kpis.keys()) if isinstance(kpis, dict) else 'ERRO'}")

        logger.info("Buscando dados por unidade...")
        dados_unidades = dashboard_service.get_dados_por_unidade(empresa_id)
        logger.info(f"Dados unidades OK - Total: {dados_unidades.get('total_unidades_visiveis', 0)}")

        logger.info("Buscando dados por setor...")
        dados_setores = dashboard_service.get_dados_por_setor(empresa_id)
        logger.info(f"Dados setores OK - Total: {dados_setores.get('total_setores_visiveis', 0)}")

        logger.info("Buscando dimensões críticas...")
        dados_dimensoes = dashboard_service.get_dimensoes_criticas(empresa_id)
        logger.info(f"Dimensões OK - Total dimensões: {len(dados_dimensoes.get('dimensoes', []))}")

        # Filtrar dados por nível de acesso
        if perfil.tem_acesso_limitado():
            logger.info("Aplicando filtros de acesso limitado...")
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
        logger.info("Registrando auditoria...")
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
        logger.info("Buscando estatísticas avançadas...")
        estatisticas_avancadas = dashboard_service.get_estatisticas_avancadas(empresa_id)
        logger.info(f"Estatísticas avançadas OK")

        logger.info("Buscando distribuição de scores...")
        distribuicao_scores = dashboard_service.get_distribuicao_scores(empresa_id)
        logger.info(f"Distribuição de scores OK")

        logger.info("Buscando tempo médio de resposta...")
        tempo_medio = dashboard_service.get_tempo_medio_resposta(empresa_id)
        logger.info(f"Tempo médio OK")

        logger.info("Buscando pontuação por pergunta...")
        pontuacao_por_pergunta = dashboard_service.get_pontuacao_por_pergunta(empresa_id)
        logger.info(f"Pontuação por pergunta OK")

        logger.info("Buscando análise por gênero...")
        analise_genero = dashboard_service.get_analise_por_genero(empresa_id)
        logger.info(f"Análise por gênero OK")

        logger.info("Buscando análise por faixa etária...")
        analise_faixa_etaria = dashboard_service.get_analise_por_faixa_etaria(empresa_id)
        logger.info(f"Análise por faixa etária OK")

        logger.info("Buscando pirâmide etária com risco...")
        piramide_etaria = dashboard_service.get_piramide_etaria_com_risco(empresa_id)
        logger.info(f"Pirâmide etária OK")

        logger.info("Buscando dimensões por gênero...")
        dimensoes_por_genero = dashboard_service.get_dimensoes_por_genero(empresa_id)
        logger.info(f"Dimensões por gênero OK")

        # Novos dados para análises avançadas
        logger.info("Buscando distribuição de respostas completa...")
        distribuicao_respostas = dashboard_service.get_distribuicao_respostas_completa(empresa_id)
        logger.info(f"Distribuição de respostas OK")

        logger.info("Buscando dimensões por polaridade...")
        dimensoes_polaridade = dashboard_service.get_dimensoes_por_polaridade(empresa_id)
        logger.info(f"Dimensões por polaridade OK")

        logger.info("Buscando radar multinível...")
        radar_multinivel = dashboard_service.get_radar_multinivel(empresa_id)
        logger.info(f"Radar multinível OK")

        logger.info("Buscando consistência interna...")
        consistencia_interna = dashboard_service.get_consistencia_interna(empresa_id)
        logger.info(f"Consistência interna OK")

        logger.info("Buscando histograma de scores...")
        histograma_scores = dashboard_service.get_histograma_scores(empresa_id)
        logger.info(f"Histograma de scores OK")

        logger.info("Buscando cargos disponíveis...")
        cargos_disponiveis = dashboard_service.get_cargos_disponiveis(empresa_id)
        logger.info(f"Cargos disponíveis OK - Total: {len(cargos_disponiveis)}")

        # Buscar unidades e setores para filtros dos gráficos
        logger.info("Buscando unidades e setores para filtros...")
        unidades = list(Unidade.objects.filter(
            empresa_id=empresa_id
        ).values('id', 'nome'))

        setores = []
        for unidade in Unidade.objects.filter(empresa_id=empresa_id):
            setores.extend(
                unidade.setores.values('id', 'nome', 'unidade_id')
            )
        logger.info(f"Filtros OK - Unidades: {len(unidades)}, Setores: {len(setores)}")

        # Serialização JSON com logging
        logger.info("Serializando kpis_json...")
        kpis_json = json.dumps(kpis, cls=DjangoJSONEncoder)
        logger.info("kpis_json serializado com sucesso")

        logger.info("Serializando dados_unidades_json...")
        dados_unidades_json = json.dumps(dados_unidades, cls=DjangoJSONEncoder)
        logger.info("dados_unidades_json serializado com sucesso")

        logger.info("Serializando dados_setores_json...")
        dados_setores_json = json.dumps(dados_setores, cls=DjangoJSONEncoder)
        logger.info("dados_setores_json serializado com sucesso")

        logger.info("Serializando dados_dimensoes_json...")
        dados_dimensoes_json = json.dumps(dados_dimensoes, cls=DjangoJSONEncoder)
        logger.info("dados_dimensoes_json serializado com sucesso")

        logger.info("Serializando estatisticas_avancadas_json...")
        estatisticas_avancadas_json = json.dumps(estatisticas_avancadas, cls=DjangoJSONEncoder)
        logger.info("estatisticas_avancadas_json serializado com sucesso")

        logger.info("Serializando distribuicao_scores_json...")
        distribuicao_scores_json = json.dumps(distribuicao_scores, cls=DjangoJSONEncoder)
        logger.info("distribuicao_scores_json serializado com sucesso")

        logger.info("Serializando tempo_medio_json...")
        tempo_medio_json = json.dumps(tempo_medio, cls=DjangoJSONEncoder)
        logger.info("tempo_medio_json serializado com sucesso")

        logger.info("Serializando pontuacao_por_pergunta_json...")
        pontuacao_por_pergunta_json = json.dumps(pontuacao_por_pergunta, cls=DjangoJSONEncoder)
        logger.info("pontuacao_por_pergunta_json serializado com sucesso")

        logger.info("Serializando analise_genero_json...")
        analise_genero_json = json.dumps(analise_genero, cls=DjangoJSONEncoder)
        logger.info("analise_genero_json serializado com sucesso")

        logger.info("Serializando analise_faixa_etaria_json...")
        analise_faixa_etaria_json = json.dumps(analise_faixa_etaria, cls=DjangoJSONEncoder)
        logger.info("analise_faixa_etaria_json serializado com sucesso")

        logger.info("Serializando piramide_etaria_json...")
        piramide_etaria_json = json.dumps(piramide_etaria, cls=DjangoJSONEncoder)
        logger.info("piramide_etaria_json serializado com sucesso")

        logger.info("Serializando dimensoes_por_genero_json...")
        dimensoes_por_genero_json = json.dumps(dimensoes_por_genero, cls=DjangoJSONEncoder)
        logger.info("dimensoes_por_genero_json serializado com sucesso")

        logger.info("Serializando distribuicao_respostas_json...")
        distribuicao_respostas_json = json.dumps(distribuicao_respostas, cls=DjangoJSONEncoder)
        logger.info("distribuicao_respostas_json serializado com sucesso")

        logger.info("Serializando dimensoes_polaridade_json...")
        dimensoes_polaridade_json = json.dumps(dimensoes_polaridade, cls=DjangoJSONEncoder)
        logger.info("dimensoes_polaridade_json serializado com sucesso")

        logger.info("Serializando radar_multinivel_json...")
        radar_multinivel_json = json.dumps(radar_multinivel, cls=DjangoJSONEncoder)
        logger.info("radar_multinivel_json serializado com sucesso")

        logger.info("Serializando consistencia_interna_json...")
        consistencia_interna_json = json.dumps(consistencia_interna, cls=DjangoJSONEncoder)
        logger.info("consistencia_interna_json serializado com sucesso")

        logger.info("Serializando histograma_scores_json...")
        histograma_scores_json = json.dumps(histograma_scores, cls=DjangoJSONEncoder)
        logger.info("histograma_scores_json serializado com sucesso")

        logger.info("Serializando cargos_disponiveis_json...")
        cargos_disponiveis_json = json.dumps(cargos_disponiveis, cls=DjangoJSONEncoder)
        logger.info("cargos_disponiveis_json serializado com sucesso")

        logger.info("Serializando unidades json...")
        unidades_json = json.dumps([{
            'id': str(u['id']),
            'nome': u['nome']
        } for u in unidades], cls=DjangoJSONEncoder)
        logger.info("unidades json serializado com sucesso")

        logger.info("Serializando setores json...")
        setores_json = json.dumps([{
            'id': str(s['id']),
            'nome': s['nome'],
            'unidade_id': str(s['unidade_id'])
        } for s in setores], cls=DjangoJSONEncoder)
        logger.info("setores json serializado com sucesso")

        context = {
            # Dados originais para uso no template HTML
            'kpis': kpis,
            'dados_unidades': dados_unidades,
            'dados_setores': dados_setores,
            'dados_dimensoes': dados_dimensoes,
            'estatisticas_avancadas': estatisticas_avancadas,
            'tempo_medio': tempo_medio,
            'piramide_etaria': piramide_etaria,
            'radar_multinivel': radar_multinivel,
            'histograma_scores': histograma_scores,
            # Dados serializados em JSON para uso no JavaScript
            'kpis_json': kpis_json,
            'dados_unidades_json': dados_unidades_json,
            'dados_setores_json': dados_setores_json,
            'dados_dimensoes_json': dados_dimensoes_json,
            'estatisticas_avancadas_json': estatisticas_avancadas_json,
            'distribuicao_scores_json': distribuicao_scores_json,
            'tempo_medio_json': tempo_medio_json,
            'pontuacao_por_pergunta_json': pontuacao_por_pergunta_json,
            'analise_genero_json': analise_genero_json,
            'analise_faixa_etaria_json': analise_faixa_etaria_json,
            'piramide_etaria_json': piramide_etaria_json,
            'dimensoes_por_genero_json': dimensoes_por_genero_json,
            # Novos dados para análises avançadas
            'distribuicao_respostas': distribuicao_respostas,
            'distribuicao_respostas_json': distribuicao_respostas_json,
            'dimensoes_polaridade': dimensoes_polaridade,
            'dimensoes_polaridade_json': dimensoes_polaridade_json,
            'radar_multinivel_json': radar_multinivel_json,
            'consistencia_interna': consistencia_interna,
            'consistencia_interna_json': consistencia_interna_json,
            'histograma_scores_json': histograma_scores_json,
            'cargos_disponiveis_json': cargos_disponiveis_json,
            # Outros dados do contexto
            'empresa': empresa_selecionada,
            'empresas': empresas,
            'empresa_selecionada_id': str(empresa_selecionada.id),
            'tem_multiplas_empresas': empresas.count() > 1,
            'perfil': perfil,
            # Dados para filtros dos gráficos
            'unidades': unidades_json,
            'setores': setores_json,
        }

        logger.info("Preparando resposta do template...")
        # Se requisição HTMX, retorna apenas o conteúdo
        template = 'dashboard/principal_content.html' if request.htmx else 'dashboard/principal.html'
        logger.info(f"=== DASHBOARD PRINCIPAL - Sucesso - Template: {template} ===")
        return render(request, template, context)

    except Exception as e:
        logger.error(f"ERRO no dashboard_principal_view - Tipo: {type(e).__name__}, Mensagem: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Erro ao carregar dashboard principal',
            'tipo': type(e).__name__,
            'mensagem': str(e)
        }, status=500)


@login_required
def dashboard_unidades_view(request):
    """Dashboard com dados por unidade - HTMX-ready"""
    try:
        logger.info("=== DASHBOARD UNIDADES - Início ===")
        logger.info(f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")

        if not hasattr(request.user, 'perfil_acesso'):
            logger.warning(f"Usuário {request.user.username} sem perfil de acesso")
            template = 'dashboard/sem_acesso_content.html' if request.htmx else 'dashboard/sem_acesso.html'
            return render(request, template)

        perfil = request.user.perfil_acesso
        logger.info(f"Perfil de acesso: {perfil.nivel_acesso}")

        # Verificar permissão de nível de acesso
        if perfil.nivel_acesso == 'SETOR':
            logger.warning(f"Usuário {request.user.username} com nível SETOR tentou acessar dashboard de unidades")
            messages.warning(request, 'Seu nível de acesso não permite visualizar dados por unidade.')
            return redirect('dashboard:principal')

        empresas = perfil.get_empresas()
        if not empresas.exists():
            logger.warning(f"Usuário {request.user.username} sem empresas")
            return render(request, 'dashboard/sem_empresa.html')

        logger.info(f"Total de empresas do usuário: {empresas.count()}")

        # Empresa selecionada
        empresa_id_selecionada = request.GET.get('empresa')
        if empresa_id_selecionada:
            empresa_selecionada = empresas.filter(id=empresa_id_selecionada).first()
            if not empresa_selecionada:
                empresa_selecionada = empresas.first()
        else:
            empresa_selecionada = empresas.first()

        logger.info(f"Empresa selecionada: {empresa_selecionada.nome} (ID: {empresa_selecionada.id})")

        dashboard_service = DashboardService()
        empresa_id = str(empresa_selecionada.id)

        logger.info("Buscando dados por unidade...")
        dados = dashboard_service.get_dados_por_unidade(empresa_id)
        logger.info(f"Dados por unidade OK - Total unidades: {dados.get('total_unidades_visiveis', 0)}")

        # Filtrar unidades se nível é UNIDADE
        if perfil.nivel_acesso == 'UNIDADE':
            logger.info("Aplicando filtros de acesso por UNIDADE...")
            unidades_permitidas = perfil.unidades.values_list('id', flat=True)
            dados['unidades'] = [
                u for u in dados['unidades']
                if u['unidade_id'] in [str(uid) for uid in unidades_permitidas]
            ]
            dados['total_unidades_visiveis'] = len(dados['unidades'])
            logger.info(f"Filtros aplicados - Unidades visíveis: {dados['total_unidades_visiveis']}")

        context = {
            'dados': dados,
            'empresa': empresa_selecionada,
            'empresas': empresas,
            'tem_multiplas_empresas': empresas.count() > 1,
        }

        logger.info("Preparando resposta do template...")
        template = 'dashboard/unidades_content.html' if request.htmx else 'dashboard/unidades.html'
        logger.info(f"=== DASHBOARD UNIDADES - Sucesso - Template: {template} ===")
        return render(request, template, context)

    except Exception as e:
        logger.error(f"ERRO no dashboard_unidades_view - Tipo: {type(e).__name__}, Mensagem: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Erro ao carregar dashboard de unidades',
            'tipo': type(e).__name__,
            'mensagem': str(e)
        }, status=500)


@login_required
def dashboard_setores_view(request):
    """Dashboard com dados por setor - HTMX-ready"""
    try:
        logger.info("=== DASHBOARD SETORES - Início ===")
        logger.info(f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")

        if not hasattr(request.user, 'perfil_acesso'):
            logger.warning(f"Usuário {request.user.username} sem perfil de acesso")
            template = 'dashboard/sem_acesso_content.html' if request.htmx else 'dashboard/sem_acesso.html'
            return render(request, template)

        perfil = request.user.perfil_acesso
        logger.info(f"Perfil de acesso: {perfil.nivel_acesso}")

        unidade_id = request.GET.get('unidade')
        if unidade_id:
            logger.info(f"Filtro por unidade: {unidade_id}")

        empresas = perfil.get_empresas()
        if not empresas.exists():
            logger.warning(f"Usuário {request.user.username} sem empresas")
            return render(request, 'dashboard/sem_empresa.html')

        logger.info(f"Total de empresas do usuário: {empresas.count()}")

        # Empresa selecionada
        empresa_id_selecionada = request.GET.get('empresa')
        if empresa_id_selecionada:
            empresa_selecionada = empresas.filter(id=empresa_id_selecionada).first()
            if not empresa_selecionada:
                empresa_selecionada = empresas.first()
        else:
            empresa_selecionada = empresas.first()

        logger.info(f"Empresa selecionada: {empresa_selecionada.nome} (ID: {empresa_selecionada.id})")

        dashboard_service = DashboardService()
        empresa_id = str(empresa_selecionada.id)

        logger.info("Buscando dados por setor...")
        dados = dashboard_service.get_dados_por_setor(
            empresa_id,
            unidade_id
        )
        logger.info(f"Dados por setor OK - Total setores: {dados.get('total_setores_visiveis', 0)}")

        # Filtrar setores permitidos se necessário
        if perfil.nivel_acesso == 'UNIDADE':
            logger.info("Aplicando filtros de acesso por UNIDADE...")
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
            logger.info(f"Filtros aplicados - Setores visíveis: {dados['total_setores_visiveis']}")

        elif perfil.nivel_acesso == 'SETOR':
            logger.info("Aplicando filtros de acesso por SETOR...")
            setores_permitidos = perfil.setores.values_list('id', flat=True)
            dados['setores'] = [
                s for s in dados['setores']
                if s['setor_id'] in [str(sid) for sid in setores_permitidos]
            ]
            dados['total_setores_visiveis'] = len(dados['setores'])
            logger.info(f"Filtros aplicados - Setores visíveis: {dados['total_setores_visiveis']}")

        context = {
            'dados': dados,
            'empresa': empresa_selecionada,
            'empresas': empresas,
            'tem_multiplas_empresas': empresas.count() > 1,
            'unidade_id': unidade_id
        }

        logger.info("Preparando resposta do template...")
        template = 'dashboard/setores_content.html' if request.htmx else 'dashboard/setores.html'
        logger.info(f"=== DASHBOARD SETORES - Sucesso - Template: {template} ===")
        return render(request, template, context)

    except Exception as e:
        logger.error(f"ERRO no dashboard_setores_view - Tipo: {type(e).__name__}, Mensagem: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Erro ao carregar dashboard de setores',
            'tipo': type(e).__name__,
            'mensagem': str(e)
        }, status=500)


@login_required
def dashboard_graficos_view(request):
    """
    Dashboard de gráficos interativos com Chart.js
    HTMX-ready: Retorna apenas o conteúdo quando requisição vem do HTMX
    """
    # Verificar perfil de acesso
    if not hasattr(request.user, 'perfil_acesso'):
        template = 'dashboard/sem_acesso_content.html' if request.htmx else 'dashboard/sem_acesso.html'
        return render(request, template)

    perfil = request.user.perfil_acesso

    # Verificar se o usuário tem acesso ao dashboard
    if not (perfil.tem_acesso_completo_dashboards() or perfil.tem_acesso_limitado()):
        template = 'dashboard/sem_permissao_content.html' if request.htmx else 'dashboard/sem_permissao.html'
        return render(request, template)

    # Obter empresas do usuário
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

    # Buscar unidades e setores para filtros
    dashboard_service = DashboardService()
    empresa_id = str(empresa_selecionada.id)

    unidades = list(Unidade.objects.filter(
        empresa_id=empresa_id
    ).values('id', 'nome'))

    setores = []
    for unidade in Unidade.objects.filter(empresa_id=empresa_id):
        setores.extend(
            unidade.setores.values('id', 'nome', 'unidade_id')
        )

    context = {
        'empresa': empresa_selecionada,
        'empresas': empresas,
        'tem_multiplas_empresas': empresas.count() > 1,
        'unidades': json.dumps([{
            'id': str(u['id']),
            'nome': u['nome']
        } for u in unidades], cls=DjangoJSONEncoder),
        'setores': json.dumps([{
            'id': str(s['id']),
            'nome': s['nome'],
            'unidade_id': str(s['unidade_id'])
        } for s in setores], cls=DjangoJSONEncoder),
    }

    # Auditoria
    AuditService.log(
        action='DASHBOARD_GRAFICOS_ACCESSED',
        description=f'Dashboard de gráficos acessado por {request.user.username}',
        user=request.user,
        ip_address=AuditService.get_client_ip(request),
        user_agent=AuditService.get_user_agent(request),
        metadata={
            'empresa_id': empresa_id,
            'empresa_nome': empresa_selecionada.nome,
        }
    )

    template = 'dashboard/graficos_content.html' if request.htmx else 'dashboard/graficos.html'
    return render(request, template, context)


@login_required
def dashboard_dimensoes_view(request):
    """Dashboard com análise de dimensões - HTMX-ready"""
    try:
        logger.info("=== DASHBOARD DIMENSÕES - Início ===")
        logger.info(f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")

        if not hasattr(request.user, 'perfil_acesso'):
            logger.warning(f"Usuário {request.user.username} sem perfil de acesso")
            template = 'dashboard/sem_acesso_content.html' if request.htmx else 'dashboard/sem_acesso.html'
            return render(request, template)

        perfil = request.user.perfil_acesso
        logger.info(f"Perfil de acesso: {perfil.nivel_acesso}")

        empresas = perfil.get_empresas()
        if not empresas.exists():
            logger.warning(f"Usuário {request.user.username} sem empresas")
            return render(request, 'dashboard/sem_empresa.html')

        logger.info(f"Total de empresas do usuário: {empresas.count()}")

        # Empresa selecionada
        empresa_id_selecionada = request.GET.get('empresa')
        if empresa_id_selecionada:
            empresa_selecionada = empresas.filter(id=empresa_id_selecionada).first()
            if not empresa_selecionada:
                empresa_selecionada = empresas.first()
        else:
            empresa_selecionada = empresas.first()

        logger.info(f"Empresa selecionada: {empresa_selecionada.nome} (ID: {empresa_selecionada.id})")

        dashboard_service = DashboardService()
        empresa_id = str(empresa_selecionada.id)

        logger.info("Buscando dimensões críticas...")
        dados = dashboard_service.get_dimensoes_criticas(empresa_id)
        logger.info(f"Dimensões críticas OK - Total dimensões: {len(dados.get('dimensoes', []))}")

        context = {
            'dados': dados,
            'empresa': empresa_selecionada,
            'empresas': empresas,
            'tem_multiplas_empresas': empresas.count() > 1,
        }

        logger.info("Preparando resposta do template...")
        template = 'dashboard/dimensoes_content.html' if request.htmx else 'dashboard/dimensoes.html'
        logger.info(f"=== DASHBOARD DIMENSÕES - Sucesso - Template: {template} ===")
        return render(request, template, context)

    except Exception as e:
        logger.error(f"ERRO no dashboard_dimensoes_view - Tipo: {type(e).__name__}, Mensagem: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Erro ao carregar dashboard de dimensões',
            'tipo': type(e).__name__,
            'mensagem': str(e)
        }, status=500)


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


@login_required
@require_GET
def api_evolucao_temporal(request):
    """
    API para obter evolução temporal dos scores.

    Query params:
        empresa: UUID da empresa (obrigatório)
        unidade: UUID da unidade (opcional)
        setor: UUID do setor (opcional)
        periodo: 'diario', 'semanal' ou 'mensal' (default: 'mensal')
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
    periodo = request.GET.get('periodo', 'mensal')

    if periodo not in ['diario', 'semanal', 'mensal']:
        periodo = 'mensal'

    dashboard_service = DashboardService()
    dados = dashboard_service.get_evolucao_temporal(
        empresa_id,
        unidade_id=unidade_id,
        setor_id=setor_id,
        periodo=periodo
    )

    return JsonResponse(dados, encoder=DjangoJSONEncoder)


@login_required
@require_GET
def api_matriz_nr1(request):
    """
    API para obter matriz NR-1 (Probabilidade × Severidade).

    Query params:
        empresa: UUID da empresa (obrigatório)
        unidade: UUID da unidade (opcional)
        setor: UUID do setor (opcional)
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

    dashboard_service = DashboardService()
    dados = dashboard_service.get_matriz_nr1_completa(
        empresa_id,
        unidade_id=unidade_id,
        setor_id=setor_id
    )

    return JsonResponse(dados, encoder=DjangoJSONEncoder)


# ============================================================================
# VIEW DE DEBUG TEMPORÁRIA - REMOVER APÓS CORRIGIR
# ============================================================================

@login_required
def debug_dashboard_data(request):
    """
    View temporária para debug - REMOVER após corrigir erro 500
    Testa cada método do DashboardService individualmente
    """
    try:
        logger.info("=== DEBUG_DASHBOARD_DATA - Início ===")

        if not hasattr(request.user, 'perfil_acesso'):
            return JsonResponse({'error': 'Sem perfil de acesso'}, status=403)

        perfil = request.user.perfil_acesso
        empresas = perfil.get_empresas()

        if not empresas.exists():
            return JsonResponse({'error': 'Sem empresas'}, status=400)

        empresa = empresas.first()
        empresa_id = str(empresa.id)
        dashboard_service = DashboardService()

        debug_info = {
            'empresa_id': empresa_id,
            'empresa_nome': empresa.nome,
            'user': request.user.username,
            'testes': {}
        }

        # Lista de métodos para testar
        metodos = [
            ('get_kpis_empresa', [empresa_id]),
            ('get_dados_por_unidade', [empresa_id]),
            ('get_dados_por_setor', [empresa_id]),
            ('get_dimensoes_criticas', [empresa_id]),
            ('get_estatisticas_avancadas', [empresa_id]),
            ('get_distribuicao_scores', [empresa_id]),
            ('get_tempo_medio_resposta', [empresa_id]),
            ('get_pontuacao_por_pergunta', [empresa_id]),
            ('get_analise_por_genero', [empresa_id]),
            ('get_analise_por_faixa_etaria', [empresa_id]),
            ('get_piramide_etaria_com_risco', [empresa_id]),
            ('get_dimensoes_por_genero', [empresa_id]),
            ('get_distribuicao_respostas_completa', [empresa_id]),
            ('get_dimensoes_por_polaridade', [empresa_id]),
            ('get_radar_multinivel', [empresa_id]),
            ('get_consistencia_interna', [empresa_id]),
            ('get_histograma_scores', [empresa_id]),
            ('get_cargos_disponiveis', [empresa_id]),
        ]

        # Testar cada método
        for metodo_nome, args in metodos:
            logger.info(f"Testando método: {metodo_nome}")
            try:
                metodo = getattr(dashboard_service, metodo_nome)
                resultado = metodo(*args)

                # Testar serialização JSON
                json_test = json.dumps(resultado, cls=DjangoJSONEncoder)

                debug_info['testes'][metodo_nome] = {
                    'status': '✓ OK',
                    'tipo': str(type(resultado).__name__),
                    'keys': list(resultado.keys()) if isinstance(resultado, dict) else None,
                    'tamanho_json': len(json_test),
                    'tem_dados': bool(resultado)
                }
                logger.info(f"✓ {metodo_nome} - OK")

            except Exception as e:
                debug_info['testes'][metodo_nome] = {
                    'status': '✗ ERRO',
                    'erro_tipo': type(e).__name__,
                    'erro_mensagem': str(e),
                    'erro_linha': e.__traceback__.tb_lineno if hasattr(e, '__traceback__') else None
                }
                logger.error(f"✗ {metodo_nome} - ERRO: {str(e)}", exc_info=True)

        # Resumo
        total_testes = len(metodos)
        testes_ok = sum(1 for t in debug_info['testes'].values() if t['status'] == '✓ OK')
        testes_erro = total_testes - testes_ok

        debug_info['resumo'] = {
            'total_testes': total_testes,
            'sucessos': testes_ok,
            'erros': testes_erro,
            'taxa_sucesso': f"{(testes_ok/total_testes*100):.1f}%"
        }

        logger.info(f"=== DEBUG_DASHBOARD_DATA - Fim - {testes_ok}/{total_testes} OK ===")

        return JsonResponse(debug_info, encoder=DjangoJSONEncoder, json_dumps_params={'indent': 2})

    except Exception as e:
        logger.error(f"ERRO CRÍTICO em debug_dashboard_data: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Erro crítico no debug',
            'tipo': type(e).__name__,
            'mensagem': str(e)
        }, status=500)
