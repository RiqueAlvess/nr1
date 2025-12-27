from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('account:dashboard'), name='home'),
    path('account/', include('account.urls')),
    path('importacao/', include('importacao.urls')),
    path('quiz/', include('quiz.urls')),
    path('dashboard/', include('dashboard.urls')),
]

# Customizar Admin
admin.site.site_header = "Plataforma NR-1 - Administração"
admin.site.site_title = "NR-1 Admin"
admin.site.index_title = "Gestão de Riscos Psicossociais"