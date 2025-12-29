from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET


# View para ignorar requisições do Chrome DevTools
@require_GET
def chrome_devtools_ignore(request):
    """Retorna 204 No Content para requisições do Chrome DevTools"""
    return HttpResponse(status=204)


# View para health check
@require_GET
def health_check(request):
    """Health check endpoint para monitoramento"""
    return JsonResponse({'status': 'ok', 'service': 'nr1-platform'})


urlpatterns = [
    # Chrome DevTools - ignorar para evitar logs de erro 404
    path('.well-known/appspecific/com.chrome.devtools.json', chrome_devtools_ignore),

    # Health check
    path('health/', health_check, name='health_check'),

    # Admin
    path('admin/', admin.site.urls),

    # Home redirect
    path('', lambda request: redirect('account:dashboard'), name='home'),

    # Apps
    path('account/', include('account.urls')),
    path('importacao/', include('importacao.urls')),
    path('quiz/', include('quiz.urls')),
    path('dashboard/', include('dashboard.urls')),
]

# Customizar Admin
admin.site.site_header = "Plataforma NR-1 - Administração"
admin.site.site_title = "NR-1 Admin"
admin.site.index_title = "Gestão de Riscos Psicossociais"
