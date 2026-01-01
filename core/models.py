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


class SolicitacaoLGPD(TimeStampedModel):
    """
    Solicitações LGPD - Art. 18
    Direitos do titular: acesso, correção, exclusão, portabilidade
    """

    TIPO_CHOICES = [
        ('ACESSO', 'Solicitação de Acesso aos Dados'),
        ('CORRECAO', 'Solicitação de Correção de Dados'),
        ('EXCLUSAO', 'Solicitação de Exclusão de Dados'),
        ('PORTABILIDADE', 'Solicitação de Portabilidade de Dados'),
        ('REVOGACAO', 'Revogação de Consentimento'),
        ('OPOSICAO', 'Oposição ao Tratamento'),
    ]

    STATUS_CHOICES = [
        ('ABERTA', 'Aberta'),
        ('EM_ANALISE', 'Em Análise'),
        ('CONCLUIDA', 'Concluída'),
        ('CANCELADA', 'Cancelada'),
    ]

    # Identificação do solicitante
    email = models.EmailField(help_text='Email do titular dos dados')
    nome = models.CharField(max_length=255, blank=True)
    telefone = models.CharField(max_length=20, blank=True)

    # Tipo de solicitação
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descricao = models.TextField(help_text='Descrição detalhada da solicitação')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTA')
    data_conclusao = models.DateTimeField(null=True, blank=True)

    # Resposta
    resposta = models.TextField(blank=True, help_text='Resposta à solicitação')
    atendido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacoes_lgpd_atendidas'
    )

    # Metadados
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    protocolo = models.CharField(max_length=20, unique=True, editable=False)

    class Meta:
        db_table = 'solicitacoes_lgpd'
        ordering = ['-created_at']
        verbose_name = 'Solicitação LGPD'
        verbose_name_plural = 'Solicitações LGPD'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['protocolo']),
        ]

    def __str__(self):
        return f"{self.protocolo} - {self.get_tipo_display()} - {self.email}"

    def save(self, *args, **kwargs):
        """Gera protocolo único ao criar"""
        if not self.protocolo:
            import secrets
            self.protocolo = f"LGPD{secrets.token_hex(8).upper()}"
        super().save(*args, **kwargs)