import uuid
from django.db import models
from django.contrib.auth.models import User


class TimeStampedModel(models.Model):
    """Model abstrato com campos de timestamp"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditLog(TimeStampedModel):
    """Log de auditoria imutável"""
    
    ACTION_CHOICES = [
        ('LOGIN', 'Login realizado'),
        ('LOGOUT', 'Logout realizado'),
        ('IMPORT_START', 'Importação iniciada'),
        ('IMPORT_SUCCESS', 'Importação concluída'),
        ('IMPORT_ERROR', 'Erro na importação'),
        ('MAGIC_LINK_GENERATED', 'Magic link gerado'),
        ('MAGIC_LINK_SENT', 'Magic link enviado'),
        ('MAGIC_LINK_ACCESSED', 'Magic link acessado'),
        ('MAGIC_LINK_EXPIRED', 'Magic link expirado'),
        ('QUIZ_STARTED', 'Questionário iniciado'),
        ('QUIZ_COMPLETED', 'Questionário concluído'),
        ('QUIZ_ABANDONED', 'Questionário abandonado'),
        ('DASHBOARD_ACCESSED', 'Dashboard acessado'),
        ('ANONYMITY_BLOCK', 'Bloqueio por anonimato'),
        ('CALCULATION_PERFORMED', 'Cálculo realizado'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.created_at}"


class Empresa(TimeStampedModel):
    """Empresa - nível mais alto da hierarquia"""
    nome = models.CharField(max_length=255, unique=True)
    ativa = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'empresas'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class Unidade(TimeStampedModel):
    """Unidade organizacional"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='unidades')
    nome = models.CharField(max_length=255)
    ativa = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'unidades'
        ordering = ['nome']
        unique_together = [['empresa', 'nome']]
    
    def __str__(self):
        return f"{self.empresa.nome} - {self.nome}"


class Setor(TimeStampedModel):
    """Setor dentro de uma unidade"""
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='setores')
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'setores'
        ordering = ['nome']
        unique_together = [['unidade', 'nome']]
    
    def __str__(self):
        return f"{self.unidade.nome} - {self.nome}"


class Cargo(TimeStampedModel):
    """Cargo vinculado à hierarquia completa (Setor → Unidade → Empresa)"""
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE, related_name='cargos')
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'cargos'
        ordering = ['nome']
        unique_together = [['setor', 'nome']]
    
    def __str__(self):
        return f"{self.setor.unidade.empresa.nome} - {self.setor.nome} - {self.nome}"
    
    @property
    def unidade(self):
        """Retorna a unidade através do setor"""
        return self.setor.unidade
    
    @property
    def empresa(self):
        """Retorna a empresa através do setor"""
        return self.setor.unidade.empresa