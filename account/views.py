from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from core.services.audit_service import AuditService


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