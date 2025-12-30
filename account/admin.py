from django.contrib import admin
from django.utils.html import format_html
from account.models import PerfilAcesso, PasswordResetToken


@admin.register(PerfilAcesso)
class PerfilAcessoAdmin(admin.ModelAdmin):
    list_display = ['user', 'nivel_acesso', 'get_empresas_display', 'get_grupo_display', 'ativo', 'created_at']
    list_filter = ['nivel_acesso', 'ativo', 'empresas']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'get_resumo_acesso_display']
    filter_horizontal = ['empresas', 'unidades', 'setores']
    autocomplete_fields = ['user']

    fieldsets = (
        ('Usuário', {
            'fields': ('user', 'ativo')
        }),
        ('Nível de Acesso', {
            'fields': ('nivel_acesso',),
            'description': 'Define a granularidade de visualização dos dados'
        }),
        ('Empresas', {
            'fields': ('empresas',),
            'description': 'Selecione uma ou mais empresas que o usuário pode acessar'
        }),
        ('Granularidade (Opcional)', {
            'fields': ('unidades', 'setores'),
            'description': 'Configure unidades/setores apenas se o nível de acesso for UNIDADE ou SETOR',
            'classes': ('collapse',)
        }),
        ('Resumo de Acesso', {
            'fields': ('get_resumo_acesso_display',),
        }),
        ('Informações do Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_empresas_display(self, obj):
        empresas = obj.get_empresas()
        count = empresas.count()
        if count == 0:
            return format_html('<span style="color: {};">Nenhuma</span>', '#EF4444')
        elif count == 1:
            return empresas.first().nome
        else:
            nomes = ', '.join([e.nome for e in empresas[:3]])
            if count > 3:
                nomes += f' (+{count - 3})'
            return format_html('<span title="{}">{}</span>', nomes, f'{count} empresas')
    get_empresas_display.short_description = 'Empresas'
    get_empresas_display.admin_order_field = 'empresas'

    def get_grupo_display(self, obj):
        grupo = obj.get_grupo_principal()
        if grupo:
            cores = {
                'RH': '#1EEB88',
                'SST': '#0F3D52',
                'Medicina do Trabalho': '#6EDBC1',
                'Liderança': '#FACC15',
                'Consultoria Externa': '#3ABFF8',
            }
            cor = cores.get(grupo, '#1F2933')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
                cor, grupo
            )
        return format_html('<span style="color: {};">Sem grupo</span>', '#9CA3AF')
    get_grupo_display.short_description = 'Grupo'

    def get_resumo_acesso_display(self, obj):
        return obj.get_resumo_acesso()
    get_resumo_acesso_display.short_description = 'Resumo de Acesso'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_status_display', 'created_at', 'expires_at', 'used_at', 'ip_address']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['user__username', 'user__email', 'token', 'ip_address']
    readonly_fields = ['id', 'token', 'user', 'created_at', 'updated_at', 'expires_at',
                       'is_used', 'used_at', 'ip_address', 'user_agent']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Informações do Token', {
            'fields': ('id', 'token', 'user')
        }),
        ('Status', {
            'fields': ('is_used', 'created_at', 'expires_at', 'used_at')
        }),
        ('Informações de Uso', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    def get_status_display(self, obj):
        if obj.is_used:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">Usado</span>',
                '#6B7280'
            )
        elif obj.is_expired():
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">Expirado</span>',
                '#EF4444'
            )
        else:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">Válido</span>',
                '#10B981'
            )
    get_status_display.short_description = 'Status'

    def has_add_permission(self, request):
        """Não permite criar tokens manualmente via admin"""
        return False

    def has_change_permission(self, request, obj=None):
        """Não permite editar tokens via admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Permite deletar tokens expirados via admin"""
        return request.user.is_superuser
