from django.db import models
from encrypted_model_fields.fields import EncryptedEmailField
from core.models import TimeStampedModel, Empresa, Setor, Cargo


class Colaborador(TimeStampedModel):
    """
    Colaborador - desacoplamento entre identificação e dados analíticos
    O email é armazenado APENAS para envio de magic link
    """

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
        ('N', 'Não informado'),
    ]

    # Email isolado e criptografado (LGPD) - usado apenas para envio
    # Nota: unique=True e db_index não são suportados em campos criptografados
    # A unicidade deve ser verificada na aplicação
    email = EncryptedEmailField()

    # Dimensões analíticas (hierarquia completa via Cargo)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name='colaboradores')

    # Dados demográficos para análises
    data_nascimento = models.DateField(null=True, blank=True, help_text='Data de nascimento do colaborador')
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, default='N', help_text='Sexo do colaborador')

    # Controle
    ativo = models.BooleanField(default=True)

    # LGPD - Retenção de dados
    data_expiracao = models.DateField(
        null=True,
        blank=True,
        help_text='Data de expiração dos dados (política de retenção LGPD)'
    )

    class Meta:
        db_table = 'colaboradores'
        verbose_name = 'Colaborador'
        verbose_name_plural = 'Colaboradores'
        indexes = [
            # Email é criptografado, não pode ter índice
            models.Index(fields=['cargo']),
            models.Index(fields=['data_nascimento']),
            models.Index(fields=['sexo']),
        ]

    def __str__(self):
        return f"Colaborador {str(self.id)[:8]}"

    @property
    def setor(self):
        """Retorna o setor através do cargo"""
        return self.cargo.setor

    @property
    def empresa(self):
        """Retorna a empresa através do cargo"""
        return self.cargo.setor.unidade.empresa

    @property
    def idade(self):
        """Calcula idade do colaborador"""
        if not self.data_nascimento:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.data_nascimento.year - (
            (today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )

    @property
    def faixa_etaria(self):
        """Retorna faixa etária do colaborador"""
        idade = self.idade
        if idade is None:
            return 'Não informado'

        if idade < 18:
            return 'Menor de 18'
        elif idade < 25:
            return '18-24'
        elif idade < 30:
            return '25-29'
        elif idade < 40:
            return '30-39'
        elif idade < 50:
            return '40-49'
        elif idade < 60:
            return '50-59'
        else:
            return '60+'


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