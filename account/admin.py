from django.contrib import admin
from account.models import PerfilAcesso


@admin.register(PerfilAcesso)
class PerfilAcessoAdmin(admin.ModelAdmin):
    list_display = ['user', 'nivel_acesso', 'empresa', 'ativo', 'created_at']
    list_filter = ['nivel_acesso', 'ativo', 'empresa']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['unidades', 'setores']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user', 'ativo')
        }),
        ('Nível de Acesso', {
            'fields': ('nivel_acesso', 'empresa')
        }),
        ('Granularidade', {
            'fields': ('unidades', 'setores'),
            'description': 'Configure unidades/setores apenas se o nível de acesso não for EMPRESA'
        }),
        ('Informações do Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )