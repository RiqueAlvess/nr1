from django.contrib import admin
from importacao.models import Colaborador, ProcessoImportacao


@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ['id_truncado', 'email', 'empresa', 'setor', 'cargo', 'ativo']
    list_filter = ['empresa', 'ativo']
    search_fields = ['email', 'setor__nome', 'cargo__nome']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def id_truncado(self, obj):
        return str(obj.id)[:8] + '...'
    id_truncado.short_description = 'ID'


@admin.register(ProcessoImportacao)
class ProcessoImportacaoAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'usuario', 'arquivo_nome', 'status', 'total_linhas', 'linhas_processadas', 'linhas_erro']
    list_filter = ['status', 'created_at']
    search_fields = ['arquivo_nome', 'usuario__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'erros', 'metadata']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('usuario', 'arquivo_nome', 'status')
        }),
        ('Estatísticas', {
            'fields': ('total_linhas', 'linhas_processadas', 'linhas_erro')
        }),
        ('Detalhes', {
            'fields': ('erros', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False