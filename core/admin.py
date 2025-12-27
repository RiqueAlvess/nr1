from django.contrib import admin
from core.models import AuditLog, Empresa, Unidade, Setor, Cargo


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
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
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativa', 'created_at']
    list_filter = ['ativa']
    search_fields = ['nome']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'ativa', 'created_at']
    list_filter = ['empresa', 'ativa']
    search_fields = ['nome', 'empresa__nome']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'unidade', 'get_empresa', 'ativo', 'created_at']
    list_filter = ['unidade__empresa', 'ativo']
    search_fields = ['nome', 'unidade__nome', 'unidade__empresa__nome']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def get_empresa(self, obj):
        return obj.unidade.empresa.nome
    get_empresa.short_description = 'Empresa'
    get_empresa.admin_order_field = 'unidade__empresa__nome'


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
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