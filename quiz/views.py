from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from quiz.models import Pergunta, Resposta, MagicLink
from quiz.services.magic_link_service import MagicLinkService
from core.services.audit_service import AuditService
from importacao.models import Colaborador


@login_required
@require_http_methods(["GET"])
def gerenciar_links_view(request):
    """View para gerenciar envio de magic links - Apenas RH"""

    # Verificar permissão
    if not hasattr(request.user, 'perfil_acesso') or not request.user.perfil_acesso.pode_visualizar_emails():
        messages.error(
            request,
            'Acesso restrito ao RH. Apenas usuários do grupo RH podem gerenciar pesquisas.'
        )
        return redirect('account:dashboard')

    colaboradores = Colaborador.objects.filter(ativo=True).select_related(
        'cargo__setor__unidade__empresa'
    ).prefetch_related('magic_link')

    context = {
        'colaboradores': colaboradores,
        'total': colaboradores.count(),
        'com_link': sum(1 for c in colaboradores if hasattr(c, 'magic_link')),
    }

    return render(request, 'quiz/gerenciar_links.html', context)


@login_required
@require_http_methods(["POST"])
def enviar_links_view(request):
    """View para enviar magic links em massa - Apenas RH"""

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
    
    # Gerar links
    gerados, ja_existentes = MagicLinkService.gerar_magic_links_bulk(colaboradores_ids)
    
    # Enviar emails
    base_url = request.build_absolute_uri('/').rstrip('/')
    enviados, erros = MagicLinkService.enviar_magic_links_bulk(colaboradores_ids, base_url)
    
    messages.success(
        request,
        f'Magic links processados: {gerados} gerados, {ja_existentes} já existiam, '
        f'{enviados} enviados, {erros} erro(s).'
    )
    
    return redirect('quiz:gerenciar_links')


@require_http_methods(["GET"])
def responder_view(request, token):
    """View para responder questionário via magic link"""
    
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
def submeter_respostas_view(request, token):
    """View para submeter respostas do questionário"""
    
    # Validar token
    magic_link = MagicLinkService.validar_token(token)
    
    if not magic_link:
        return render(request, 'quiz/link_invalido.html', status=403)
    
    if magic_link.status == 'COMPLETED':
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
    
    # Criar resposta
    resposta = Resposta.objects.create(
        magic_link=magic_link,
        respostas=respostas_dict,
        tempo_total_segundos=int(tempo_total) if tempo_total else None
    )
    
    # Calcular scores
    resposta.calcular_scores()
    
    # Marcar como concluído
    magic_link.marcar_concluido()
    
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