from django.db import models
from core.models import TimeStampedModel, Empresa, Unidade, Setor, Cargo


class Colaborador(TimeStampedModel):
    """
    Colaborador - desacoplamento entre identificação e dados analíticos
    O email é armazenado APENAS para envio de magic link
    """
    
    # Email isolado - usado apenas para envio
    email = models.EmailField(unique=True, db_index=True)
    
    # Dimensões analíticas (sem dados pessoais)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    
    # Controle
    ativo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'colaboradores'
        verbose_name = 'Colaborador'
        verbose_name_plural = 'Colaboradores'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['empresa', 'setor']),
        ]
    
    def __str__(self):
        return f"Colaborador {str(self.id)[:8]}"


class ProcessoImportacao(TimeStampedModel):
    """Registro de processo de importação"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('PROCESSING', 'Processando'),
        ('COMPLETED', 'Concluído'),
        ('FAILED', 'Falhou'),
    ]
    
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    arquivo_nome = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_linhas = models.IntegerField(default=0)
    linhas_processadas = models.IntegerField(default=0)
    linhas_erro = models.IntegerField(default=0)
    erros = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'processos_importacao'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Importação {self.arquivo_nome} - {self.status}"