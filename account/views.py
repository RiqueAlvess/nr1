from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from core.services.audit_service import AuditService
from account.services.password_reset_service import PasswordResetService
from account.models import PasswordResetToken
import logging

logger = logging.getLogger('nr1')


@require_http_methods(["GET", "POST"])
def login_view(request):
    """View de login"""
    if request.user.is_authenticated:
        return redirect('account:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Auditoria
            AuditService.log(
                action='LOGIN',
                description=f'Login realizado: {user.username}',
                user=user,
                ip_address=AuditService.get_client_ip(request),
                user_agent=AuditService.get_user_agent(request)
            )
            
            messages.success(request, 'Login realizado com sucesso!')
            return redirect('account:dashboard')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    
    return render(request, 'account/login.html')


@login_required
def logout_view(request):
    """View de logout"""
    user = request.user
    
    # Auditoria
    AuditService.log(
        action='LOGOUT',
        description=f'Logout realizado: {user.username}',
        user=user,
        ip_address=AuditService.get_client_ip(request),
        user_agent=AuditService.get_user_agent(request)
    )
    
    logout(request)
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('account:login')


@login_required
def dashboard_view(request):
    """Dashboard principal do sistema"""
    context = {
        'user': request.user,
        'has_perfil': hasattr(request.user, 'perfil_acesso'),
    }
    
    # Auditoria
    AuditService.log(
        action='DASHBOARD_ACCESSED',
        description=f'Dashboard acessado por: {request.user.username}',
        user=request.user,
        ip_address=AuditService.get_client_ip(request),
        user_agent=AuditService.get_user_agent(request)
    )
    
    return render(request, 'account/dashboard.html', context)


# ============================================================================
# VIEWS DE REDEFINIÇÃO DE SENHA VIA MAGIC LINK
# ============================================================================

@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    """
    View para solicitar redefinição de senha
    Usuário informa o email e recebe magic link
    """
    if request.user.is_authenticated:
        return redirect('account:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        # Validar email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Por favor, informe um email válido.')
            logger.warning(f"Tentativa de redefinição com email inválido: {email}")
            return render(request, 'account/password_reset_request.html')

        # Processar solicitação
        success = PasswordResetService.request_password_reset(email, request)

        if success:
            logger.info(f"Solicitação de redefinição processada para: {email}")
            messages.success(
                request,
                'Se o email informado estiver cadastrado, você receberá um link para '
                'redefinir sua senha. Verifique sua caixa de entrada.'
            )
            return redirect('account:password_reset_sent')
        else:
            logger.error(f"Erro ao processar redefinição para: {email}")
            messages.error(
                request,
                'Ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde.'
            )

    return render(request, 'account/password_reset_request.html')


@require_http_methods(["GET"])
def password_reset_sent(request):
    """
    View de confirmação de envio do email
    """
    return render(request, 'account/password_reset_sent.html')


@require_http_methods(["GET", "POST"])
def password_reset_confirm(request, token):
    """
    View para confirmar o token e redefinir a senha
    """
    if request.user.is_authenticated:
        return redirect('account:dashboard')

    # Validar token
    reset_token = PasswordResetService.validate_token(token)

    if not reset_token:
        logger.warning(f"Acesso com token inválido ou expirado: {token[:10]}...")
        messages.error(
            request,
            'Este link de redefinição é inválido ou já expirou. '
            'Solicite um novo link de redefinição.'
        )
        return redirect('account:password_reset_invalid')

    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validações
        if not password1 or not password2:
            messages.error(request, 'Por favor, preencha todos os campos.')
            return render(request, 'account/password_reset_confirm.html', {
                'token': token,
                'reset_token': reset_token
            })

        if password1 != password2:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'account/password_reset_confirm.html', {
                'token': token,
                'reset_token': reset_token
            })

        if len(password1) < 8:
            messages.error(request, 'A senha deve ter no mínimo 8 caracteres.')
            return render(request, 'account/password_reset_confirm.html', {
                'token': token,
                'reset_token': reset_token
            })

        # Obter informações da requisição
        ip_address = PasswordResetService._get_client_ip(request)
        user_agent = PasswordResetService._get_user_agent(request)

        # Redefinir senha
        success = PasswordResetService.reset_password(
            reset_token=reset_token,
            new_password=password1,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if success:
            # Auditoria
            AuditService.log(
                action='PASSWORD_RESET',
                description=f'Senha redefinida via magic link: {reset_token.user.username}',
                user=reset_token.user,
                ip_address=ip_address,
                user_agent=user_agent
            )

            logger.info(
                f"Senha redefinida com sucesso para: {reset_token.user.username} | "
                f"IP: {ip_address}"
            )

            messages.success(
                request,
                'Sua senha foi redefinida com sucesso! Você já pode fazer login.'
            )
            return redirect('account:password_reset_complete')
        else:
            logger.error(f"Erro ao redefinir senha para: {reset_token.user.username}")
            messages.error(
                request,
                'Ocorreu um erro ao redefinir sua senha. Tente novamente.'
            )

    context = {
        'token': token,
        'reset_token': reset_token,
        'user': reset_token.user
    }
    return render(request, 'account/password_reset_confirm.html', context)


@require_http_methods(["GET"])
def password_reset_complete(request):
    """
    View de confirmação de redefinição completa
    """
    return render(request, 'account/password_reset_complete.html')


@require_http_methods(["GET"])
def password_reset_invalid(request):
    """
    View para token inválido ou expirado
    """
    return render(request, 'account/password_reset_invalid.html')