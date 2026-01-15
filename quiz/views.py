from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.db.models import Q, Case, When, IntegerField, Value
from django_ratelimit.decorators import ratelimit
from quiz.models import Pergunta, Resposta, MagicLink
from quiz.services.magic_link_service import MagicLinkService
from core.services.audit_service import AuditService
from importacao.models import Colaborador
import logging

logger = logging.getLogger('nr1')


@login_required
@require_http_methods(["GET"])
def gerenciar_links_view(request):
    """View para gerenciar envio de magic links - Apenas RH"""
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

    # Verificar permissão
    if not hasattr(request.user, 'perfil_acesso') or not request.user.perfil_acesso.pode_visualizar_emails():
        messages.error(
            request,
            'Acesso restrito ao RH. Apenas usuários do grupo RH podem gerenciar pesquisas.'
        )
        return redirect('account:dashboard')

    # Buscar todos os colaboradores ativos
    colaboradores_qs = Colaborador.objects.filter(ativo=True).select_related(
        'cargo__setor__unidade__empresa'
    ).prefetch_related('magic_link')

    # Aplicar ordenação por prioridade de status
    colaboradores_qs = colaboradores_qs.annotate(
        status_prioridade=Case(
            When(magic_link__isnull=True, then=Value(0)),  # SEM LINK = prioridade 0 (aparece primeiro)
            When(magic_link__status='PENDING', then=Value(1)),  # PENDING = prioridade 1
            When(magic_link__status='ACCESSED', then=Value(2)),  # ACCESSED = prioridade 2
            When(magic_link__status='COMPLETED', then=Value(3)),  # COMPLETED = prioridade 3
            When(magic_link__status='EXPIRED', then=Value(4)),  # EXPIRED = prioridade 4
            default=Value(5),
            output_field=IntegerField()
        )
    ).order_by('status_prioridade', 'email')

    # Filtros
    filtro_status = request.GET.get('status', '')
    busca = request.GET.get('busca', '').strip()

    # Aplicar filtro por status
    if filtro_status == 'sem_link':
        colaboradores_qs = colaboradores_qs.filter(magic_link__isnull=True)
    elif filtro_status == 'enviado':
        colaboradores_qs = colaboradores_qs.filter(magic_link__status='PENDING')
    elif filtro_status == 'acessado':
        colaboradores_qs = colaboradores_qs.filter(magic_link__status='ACCESSED')
    elif filtro_status == 'concluido':
        colaboradores_qs = colaboradores_qs.filter(magic_link__status='COMPLETED')
    elif filtro_status == 'expirado':
        colaboradores_qs = colaboradores_qs.filter(magic_link__status='EXPIRED')

    # Aplicar busca por texto (email, empresa, unidade, setor)
    if busca:
        colaboradores_qs = colaboradores_qs.filter(
            Q(email__icontains=busca) |
            Q(cargo__setor__unidade__empresa__nome__icontains=busca) |
            Q(cargo__setor__unidade__nome__icontains=busca) |
            Q(cargo__setor__nome__icontains=busca)
        )

    # Calcular estatísticas ANTES de aplicar paginação (usando todos os colaboradores ativos)
    todos_colaboradores = Colaborador.objects.filter(ativo=True).select_related('magic_link')

    total = todos_colaboradores.count()
    sem_link = todos_colaboradores.filter(magic_link__isnull=True).count()
    com_link_pendente = todos_colaboradores.filter(magic_link__status='PENDING').count()
    com_link_acessado = todos_colaboradores.filter(magic_link__status='ACCESSED').count()
    com_link_concluido = todos_colaboradores.filter(magic_link__status='COMPLETED').count()
    com_link_expirado = todos_colaboradores.filter(magic_link__status='EXPIRED').count()

    # Paginação
    page = request.GET.get('page', 1)
    paginator = Paginator(colaboradores_qs, 20)  # 20 itens por página

    try:
        colaboradores = paginator.page(page)
    except PageNotAnInteger:
        colaboradores = paginator.page(1)
    except EmptyPage:
        colaboradores = paginator.page(paginator.num_pages)

    context = {
        'colaboradores': colaboradores,
        'total': total,
        'sem_link': sem_link,
        'com_link_pendente': com_link_pendente,
        'com_link_acessado': com_link_acessado,
        'com_link_concluido': com_link_concluido,
        'com_link_expirado': com_link_expirado,
        'filtro_status': filtro_status,
        'busca': busca,
    }

    return render(request, 'quiz/gerenciar_links.html', context)


@login_required
@require_http_methods(["POST"])
@ratelimit(key='user', rate='5/h', method='POST', block=True)
def enviar_links_view(request):
    """View para enviar magic links em massa - Apenas RH, rate limited (5 envios por hora por usuário)"""

    # Verificar permissão
    if not hasattr(request.user, 'perfil_acesso') or not request.user.perfil_acesso.pode_visualizar_emails():
        messages.error(
            request,
            'Acesso restrito ao RH. Apenas usuários do grupo RH podem enviar pesquisas.'
        )
        return redirect('account:dashboard')

    colaboradores_ids = request.POST.getlist('colaboradores')

    if not colaboradores_ids:
        messages.error(request, 'Selecione pelo menos um colaborador.')
        return redirect('quiz:gerenciar_links')

    # Gerar links imediatamente (síncrono)
    gerados, ja_existentes = MagicLinkService.gerar_magic_links_bulk(colaboradores_ids)

    # Enviar emails de forma assíncrona via Celery
    base_url = request.build_absolute_uri('/').rstrip('/')

    from quiz.tasks import send_magic_links_async

    logger.info(
        f'[CELERY DEBUG] Disparando task send_magic_links_async | '
        f'colaboradores_ids={colaboradores_ids} | '
        f'base_url={base_url} | '
        f'user={request.user.username}'
    )

    try:
        task_result = send_magic_links_async.delay(colaboradores_ids, base_url)
        logger.info(
            f'[CELERY DEBUG] Task enfileirada com sucesso | '
            f'task_id={task_result.id} | '
            f'colaboradores_count={len(colaboradores_ids)}'
        )
    except Exception as e:
        logger.error(
            f'[CELERY DEBUG] ERRO ao enfileirar task: {str(e)}',
            exc_info=True
        )
        messages.error(request, f'Erro ao enfileirar envio de emails: {str(e)}')
        return redirect('quiz:gerenciar_links')

    messages.success(
        request,
        f'Magic links processados: {gerados} gerados, {ja_existentes} já existiam. '
        f'{len(colaboradores_ids)} emails serão enviados em segundo plano.'
    )

    return redirect('quiz:gerenciar_links')


@require_http_methods(["GET"])
@ratelimit(key='ip', rate='30/m', method='GET', block=True)
def responder_view(request, token):
    """View para responder questionário via magic link, rate limited (30 acessos por IP por minuto)"""

    # Validar token
    magic_link = MagicLinkService.validar_token(token)
    
    if not magic_link:
        return render(request, 'quiz/link_invalido.html', status=403)
    
    # Marcar como acessado
    if magic_link.status == 'PENDING':
        magic_link.marcar_acessado()
        
        AuditService.log(
            action='MAGIC_LINK_ACCESSED',
            description=f'Magic link acessado: {str(magic_link.id)[:8]}',
            metadata={'magic_link_id': str(magic_link.id)},
            ip_address=AuditService.get_client_ip(request),
            user_agent=AuditService.get_user_agent(request)
        )
    
    # Verificar se já respondeu
    if magic_link.status == 'COMPLETED':
        return render(request, 'quiz/ja_respondido.html')
    
    # Buscar perguntas
    perguntas = Pergunta.objects.filter(ativa=True).select_related('dimensao').order_by('numero')
    
    context = {
        'perguntas': perguntas,
        'token': token,
        'magic_link_id': str(magic_link.id)
    }
    
    return render(request, 'quiz/questionario.html', context)


@require_http_methods(["POST"])
@ratelimit(key='ip', rate='10/h', method='POST', block=True)
def submeter_respostas_view(request, token):
    """View para submeter respostas do questionário, rate limited (10 submissões por IP por hora)"""

    # Validar token
    magic_link = MagicLinkService.validar_token(token)

    if not magic_link:
        return render(request, 'quiz/link_invalido.html', status=403)

    if magic_link.status == 'COMPLETED':
        return render(request, 'quiz/ja_respondido.html')

    # Verificar se já existe uma resposta para este magic_link (proteção contra dupla submissão)
    if Resposta.objects.filter(magic_link=magic_link).exists():
        return render(request, 'quiz/ja_respondido.html')

    # Marcar como iniciado (se ainda não foi)
    if not magic_link.started_at:
        magic_link.marcar_iniciado()

        AuditService.log(
            action='QUIZ_STARTED',
            description=f'Questionário iniciado: {str(magic_link.id)[:8]}',
            metadata={'magic_link_id': str(magic_link.id)},
            ip_address=AuditService.get_client_ip(request),
            user_agent=AuditService.get_user_agent(request)
        )

    # Coletar respostas
    perguntas = Pergunta.objects.filter(ativa=True)
    respostas_dict = {}

    for pergunta in perguntas:
        valor = request.POST.get(f'pergunta_{pergunta.numero}')
        if valor:
            respostas_dict[str(pergunta.numero)] = int(valor)

    # Validar que todas as perguntas foram respondidas
    if len(respostas_dict) != perguntas.count():
        messages.error(request, 'Por favor, responda todas as perguntas.')
        return redirect('quiz:responder', token=token)

    # Calcular tempo total
    tempo_total = None
    if magic_link.started_at:
        tempo_total = (timezone.now() - magic_link.started_at).total_seconds()

    # Criar resposta usando transação atômica para evitar condições de corrida
    try:
        with transaction.atomic():
            # Verificar novamente dentro da transação
            if Resposta.objects.filter(magic_link=magic_link).exists():
                return render(request, 'quiz/ja_respondido.html')

            resposta = Resposta.objects.create(
                magic_link=magic_link,
                respostas=respostas_dict,
                tempo_total_segundos=int(tempo_total) if tempo_total else None
            )

            # Calcular scores
            resposta.calcular_scores()

            # Marcar como concluído
            magic_link.marcar_concluido()
    except IntegrityError:
        # Outra requisição já criou a resposta (duplo clique ou condição de corrida)
        return render(request, 'quiz/ja_respondido.html')

    # Auditoria
    AuditService.log(
        action='QUIZ_COMPLETED',
        description=f'Questionário concluído: {str(magic_link.id)[:8]}',
        metadata={
            'magic_link_id': str(magic_link.id),
            'resposta_id': str(resposta.id),
            'score_global': resposta.score_global,
            'tempo_segundos': tempo_total
        },
        ip_address=AuditService.get_client_ip(request),
        user_agent=AuditService.get_user_agent(request)
    )

    return render(request, 'quiz/obrigado.html')