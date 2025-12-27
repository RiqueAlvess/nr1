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
    list_display = ['nome', 'unidade', 'ativo', 'created_at']
    list_filter = ['unidade__empresa', 'ativo']
    search_fields = ['nome', 'unidade__nome']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'created_at']
    list_filter = ['ativo']
    search_fields = ['nome']
    readonly_fields = ['id', 'created_at', 'updated_at']