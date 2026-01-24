from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display

from quiz.models import Dimensao, Pergunta, MagicLink, Resposta


@admin.register(Dimensao)
class DimensaoAdmin(ModelAdmin):
    list_display = ['nome', 'icon_name', 'icon_color', 'polaridade', 'ordem', 'ativa']
    list_filter = ['polaridade', 'ativa', 'icon_color']
    search_fields = ['nome']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['ordem', 'nome']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'polaridade', 'ordem', 'ativa')
        }),
        ('Ícone (Lucide)', {
            'fields': ('icon_name', 'icon_color', 'icon_path'),
            'description': 'Configurações do ícone Lucide para exibição visual da dimensão'
        }),
        ('Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Pergunta)
class PerguntaAdmin(ModelAdmin):
    list_display = ['numero', 'texto_resumido', 'dimensao', 'pontuacao_maxima', 'ativa']
    list_filter = ['dimensao', 'ativa']
    search_fields = ['texto', 'numero']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['numero']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero', 'dimensao', 'ativa')
        }),
        ('Conteúdo', {
            'fields': ('texto', 'opcoes_texto', 'pontuacao_maxima')
        }),
        ('Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def texto_resumido(self, obj):
        return obj.texto[:60] + '...' if len(obj.texto) > 60 else obj.texto
    texto_resumido.short_description = 'Texto'


@admin.register(MagicLink)
class MagicLinkAdmin(ModelAdmin):
    list_display = ['id_truncado', 'colaborador_email', 'status', 'created_at', 'expires_at']
    list_filter = ['status', 'created_at']
    search_fields = ['colaborador__email']
    readonly_fields = ['id', 'token_hash', 'created_at', 'updated_at', 'first_accessed_at', 'started_at', 'completed_at']
    
    fieldsets = (
        ('Informações', {
            'fields': ('colaborador', 'status', 'expires_at')
        }),
        ('Métricas de Tempo', {
            'fields': ('first_accessed_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('id', 'token_hash', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def id_truncado(self, obj):
        return str(obj.id)[:8] + '...'
    id_truncado.short_description = 'ID'
    
    def colaborador_email(self, obj):
        return obj.colaborador.email
    colaborador_email.short_description = 'Email'
    
    def has_add_permission(self, request):
        return False


@admin.register(Resposta)
class RespostaAdmin(ModelAdmin):
    list_display = ['id_truncado', 'score_global', 'nivel_risco', 'tempo_total_segundos', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['id', 'magic_link', 'respostas', 'score_global', 'scores_dimensoes', 'tempo_total_segundos', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Dados da Resposta', {
            'fields': ('magic_link', 'tempo_total_segundos')
        }),
        ('Scores Calculados', {
            'fields': ('score_global', 'scores_dimensoes')
        }),
        ('Respostas Completas', {
            'fields': ('respostas',),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def id_truncado(self, obj):
        return str(obj.id)[:8] + '...'
    id_truncado.short_description = 'ID'
    
    def nivel_risco(self, obj):
        return obj.get_nivel_risco_global()
    nivel_risco.short_description = 'Nível de Risco'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False