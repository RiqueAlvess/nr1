from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display

from importacao.models import Colaborador, ProcessoImportacao


@admin.register(Colaborador)
class ColaboradorAdmin(ModelAdmin):
    list_display = ['id_truncado', 'email', 'cargo', 'get_setor', 'get_unidade', 'get_empresa', 'ativo']
    list_filter = ['cargo__setor__unidade__empresa', 'ativo']
    search_fields = ['email', 'cargo__nome', 'cargo__setor__nome']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações do Colaborador', {
            'fields': ('email', 'cargo', 'ativo')
        }),
        ('Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def id_truncado(self, obj):
        return str(obj.id)[:8] + '...'
    id_truncado.short_description = 'ID'
    
    def get_setor(self, obj):
        return obj.cargo.setor.nome
    get_setor.short_description = 'Setor'
    get_setor.admin_order_field = 'cargo__setor__nome'
    
    def get_unidade(self, obj):
        return obj.cargo.setor.unidade.nome
    get_unidade.short_description = 'Unidade'
    get_unidade.admin_order_field = 'cargo__setor__unidade__nome'
    
    def get_empresa(self, obj):
        return obj.cargo.setor.unidade.empresa.nome
    get_empresa.short_description = 'Empresa'
    get_empresa.admin_order_field = 'cargo__setor__unidade__empresa__nome'


@admin.register(ProcessoImportacao)
class ProcessoImportacaoAdmin(ModelAdmin):
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