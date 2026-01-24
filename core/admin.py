from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display

from core.models import AuditLog, Empresa, Unidade, Setor, Cargo, SolicitacaoLGPD, Branding


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = ['created_at', 'action', 'user', 'ip_address']
    list_filter = ['action', 'created_at']
    search_fields = ['description', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Empresa)
class EmpresaAdmin(ModelAdmin):
    list_display = ['nome', 'ativa', 'created_at']
    list_filter = ['ativa']
    search_fields = ['nome']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Unidade)
class UnidadeAdmin(ModelAdmin):
    list_display = ['nome', 'empresa', 'ativa', 'created_at']
    list_filter = ['empresa', 'ativa']
    search_fields = ['nome', 'empresa__nome']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Setor)
class SetorAdmin(ModelAdmin):
    list_display = ['nome', 'unidade', 'get_empresa', 'ativo', 'created_at']
    list_filter = ['unidade__empresa', 'ativo']
    search_fields = ['nome', 'unidade__nome', 'unidade__empresa__nome']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def get_empresa(self, obj):
        return obj.unidade.empresa.nome
    get_empresa.short_description = 'Empresa'
    get_empresa.admin_order_field = 'unidade__empresa__nome'


@admin.register(Cargo)
class CargoAdmin(ModelAdmin):
    list_display = ['nome', 'setor', 'get_unidade', 'get_empresa', 'ativo', 'created_at']
    list_filter = ['setor__unidade__empresa', 'ativo']
    search_fields = ['nome', 'setor__nome', 'setor__unidade__nome', 'setor__unidade__empresa__nome']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Hierarquia', {
            'fields': ('setor',),
            'description': 'O cargo será vinculado ao Setor → Unidade → Empresa automaticamente'
        }),
        ('Informações do Cargo', {
            'fields': ('nome', 'ativo')
        }),
        ('Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_unidade(self, obj):
        return obj.setor.unidade.nome
    get_unidade.short_description = 'Unidade'
    get_unidade.admin_order_field = 'setor__unidade__nome'
    
    def get_empresa(self, obj):
        return obj.setor.unidade.empresa.nome
    get_empresa.short_description = 'Empresa'
    get_empresa.admin_order_field = 'setor__unidade__empresa__nome'


@admin.register(SolicitacaoLGPD)
class SolicitacaoLGPDAdmin(ModelAdmin):
    """Admin para solicitacoes LGPD."""
    list_display = ['protocolo', 'tipo', 'email', 'get_status_display', 'created_at']
    list_filter = ['tipo', 'status', 'created_at']
    search_fields = ['protocolo', 'email', 'nome']
    readonly_fields = ['id', 'protocolo', 'created_at', 'updated_at', 'ip_address', 'user_agent']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Identificacao', {
            'fields': ('protocolo', 'email', 'nome', 'telefone')
        }),
        ('Solicitacao', {
            'fields': ('tipo', 'descricao', 'status')
        }),
        ('Resposta', {
            'fields': ('resposta', 'atendido_por', 'data_conclusao')
        }),
        ('Metadados', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @display(description="Status")
    def get_status_display(self, obj):
        cores = {
            'ABERTA': '#3ABFF8',
            'EM_ANALISE': '#FACC15',
            'CONCLUIDA': '#1EEB88',
            'CANCELADA': '#EF4444',
        }
        cor = cores.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            cor, obj.get_status_display()
        )


@admin.register(Branding)
class BrandingAdmin(ModelAdmin):
    """Admin para configuracoes de White Label."""

    def has_add_permission(self, request):
        """Nao permite adicionar mais registros (Singleton)."""
        return not Branding.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Nao permite deletar o unico registro."""
        return False

    fieldsets = (
        ('Identidade do Sistema', {
            'fields': (
                'nome_sistema',
                'titulo_navegador',
                'ativo',
            ),
            'description': 'Configure o nome e titulo que aparecem no sistema'
        }),
        ('Logos e Icones', {
            'fields': (
                'logo',
                'get_logo_preview',
                'logo_login',
                'get_logo_login_preview',
                'favicon',
                'get_favicon_preview',
            ),
            'description': 'Faca upload dos logos e icones da sua marca'
        }),
        ('Paleta de Cores', {
            'fields': (
                'cor_primaria',
                'get_cor_primaria_preview',
                'cor_secundaria',
                'get_cor_secundaria_preview',
                'cor_accent',
                'get_cor_accent_preview',
                'cor_texto',
                'get_cor_texto_preview',
            ),
            'description': 'Defina as cores principais do sistema (formato hexadecimal, ex: #1EEB88)'
        }),
        ('Informacoes da Empresa', {
            'fields': (
                'nome_empresa',
                'site_empresa',
            ),
            'description': 'Informacoes que aparecem no rodape e emails'
        }),
        ('Metadados', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = [
        'created_at',
        'updated_at',
        'get_logo_preview',
        'get_logo_login_preview',
        'get_favicon_preview',
        'get_cor_primaria_preview',
        'get_cor_secundaria_preview',
        'get_cor_accent_preview',
        'get_cor_texto_preview',
    ]

    @display(description="Preview do Logo")
    def get_logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 50px; background: #f3f4f6; padding: 10px; border-radius: 8px;">',
                obj.logo.url
            )
        return "Nenhum logo enviado"

    @display(description="Preview do Logo de Login")
    def get_logo_login_preview(self, obj):
        if obj.logo_login:
            return format_html(
                '<img src="{}" style="max-height: 120px; background: #f3f4f6; padding: 20px; border-radius: 8px;">',
                obj.logo_login.url
            )
        return "Nenhum logo de login enviado"

    @display(description="Preview do Favicon")
    def get_favicon_preview(self, obj):
        if obj.favicon:
            return format_html(
                '<img src="{}" style="width: 32px; height: 32px; background: #f3f4f6; padding: 5px; border-radius: 4px;">',
                obj.favicon.url
            )
        return "Nenhum favicon enviado"

    @display(description="Preview")
    def get_cor_primaria_preview(self, obj):
        return format_html(
            '<div style="width: 100px; height: 30px; background-color: {}; border: 1px solid #ddd; border-radius: 4px;"></div>',
            obj.cor_primaria
        )

    @display(description="Preview")
    def get_cor_secundaria_preview(self, obj):
        return format_html(
            '<div style="width: 100px; height: 30px; background-color: {}; border: 1px solid #ddd; border-radius: 4px;"></div>',
            obj.cor_secundaria
        )

    @display(description="Preview")
    def get_cor_accent_preview(self, obj):
        return format_html(
            '<div style="width: 100px; height: 30px; background-color: {}; border: 1px solid #ddd; border-radius: 4px;"></div>',
            obj.cor_accent
        )

    @display(description="Preview")
    def get_cor_texto_preview(self, obj):
        return format_html(
            '<div style="width: 100px; height: 30px; background-color: {}; border: 1px solid #ddd; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">Texto</div>',
            obj.cor_texto
        )