from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from importacao.services.import_service import ImportService
from importacao.models import ProcessoImportacao


def user_tem_acesso_importacao(user):
    """Verifica se o usuário pode acessar importação (apenas RH)"""
    if not hasattr(user, 'perfil_acesso'):
        return False
    return user.perfil_acesso.pode_acessar_importacao()


@login_required
@require_http_methods(["GET"])
def importacao_view(request):
    """View principal de importação - Apenas usuários do grupo RH"""

    # Verificar permissão
    if not user_tem_acesso_importacao(request.user):
        messages.error(
            request,
            'Acesso restrito ao RH. Apenas usuários do grupo RH podem importar dados.'
        )
        return redirect('account:dashboard')
    
    processos = ProcessoImportacao.objects.filter(
        usuario=request.user
    ).order_by('-created_at')[:10]
    
    context = {
        'processos': processos
    }
    
    return render(request, 'importacao/importacao.html', context)


@login_required
@require_http_methods(["POST"])
@ratelimit(key='user', rate='5/h', method='POST', block=True)
def upload_csv_view(request):
    """View para upload de CSV - Apenas usuários do grupo RH, rate limited (5 uploads por hora)"""

    # Verificar permissão
    if not user_tem_acesso_importacao(request.user):
        messages.error(
            request,
            'Acesso restrito ao RH. Apenas usuários do grupo RH podem importar dados.'
        )
        return redirect('account:dashboard')

    if 'arquivo' not in request.FILES:
        messages.error(request, 'Nenhum arquivo foi enviado.')
        return redirect('importacao:importacao')

    arquivo = request.FILES['arquivo']
    empresa_nome = request.POST.get('empresa_nome', '').strip()

    if not empresa_nome:
        messages.error(request, 'Nome da empresa é obrigatório.')
        return redirect('importacao:importacao')

    if not arquivo.name.endswith('.csv'):
        messages.error(request, 'Apenas arquivos CSV são permitidos.')
        return redirect('importacao:importacao')

    # Validação de tamanho do arquivo (max 10MB)
    if arquivo.size > 10 * 1024 * 1024:
        messages.error(request, 'Arquivo muito grande. Tamanho máximo: 10MB.')
        return redirect('importacao:importacao')
    
    try:
        processo = ImportService.processar_csv(
            arquivo=arquivo,
            usuario=request.user,
            empresa_nome=empresa_nome
        )
        
        if processo.status == 'COMPLETED':
            messages.success(
                request,
                f'Importação concluída! '
                f'{processo.linhas_processadas} colaboradores processados. '
                f'{processo.linhas_erro} erro(s).'
            )
        else:
            messages.warning(
                request,
                f'Importação concluída com erros. Verifique os detalhes.'
            )
        
    except Exception as e:
        messages.error(request, f'Erro ao processar arquivo: {str(e)}')
    
    return redirect('importacao:importacao')


@login_required
def processo_detalhe_view(request, processo_id):
    """View de detalhes do processo de importação - Apenas RH"""

    # Verificar permissão
    if not user_tem_acesso_importacao(request.user):
        messages.error(request, 'Acesso restrito ao RH.')
        return redirect('account:dashboard')
    
    processo = ProcessoImportacao.objects.get(id=processo_id, usuario=request.user)
    
    context = {
        'processo': processo
    }
    
    return render(request, 'importacao/processo_detalhe.html', context)