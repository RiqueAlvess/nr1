import hashlib
import secrets
from datetime import timedelta
from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel
from importacao.models import Colaborador


class Dimensao(TimeStampedModel):
    """Dimensão psicossocial do questionário HSE-IT"""
    
    POLARIDADE_CHOICES = [
        ('POSITIVA', 'Positiva (menor pontuação = maior risco)'),
        ('NEGATIVA', 'Negativa (maior pontuação = maior risco)'),
    ]
    
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField()
    polaridade = models.CharField(max_length=10, choices=POLARIDADE_CHOICES)
    ordem = models.IntegerField(default=0)
    ativa = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'dimensoes'
        ordering = ['ordem', 'nome']
        verbose_name = 'Dimensão'
        verbose_name_plural = 'Dimensões'
    
    def __str__(self):
        return self.nome


class Pergunta(TimeStampedModel):
    """Pergunta do questionário HSE-IT"""
    
    dimensao = models.ForeignKey(Dimensao, on_delete=models.CASCADE, related_name='perguntas')
    numero = models.IntegerField(unique=True, help_text='Número da pergunta no questionário')
    texto = models.TextField()
    opcoes_texto = models.CharField(
        max_length=255,
        default='(0) nunca; (1) raramente; (2) às vezes; (3) frequentemente; (4) sempre'
    )
    pontuacao_maxima = models.IntegerField(default=4)
    ativa = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'perguntas'
        ordering = ['numero']
    
    def __str__(self):
        return f"P{self.numero}: {self.texto[:50]}..."


class MagicLink(TimeStampedModel):
    """
    Magic link para acesso anônimo ao questionário
    Token é hasheado e nunca armazenado em texto puro
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('ACCESSED', 'Acessado'),
        ('COMPLETED', 'Concluído'),
        ('EXPIRED', 'Expirado'),
    ]
    
    colaborador = models.OneToOneField(
        Colaborador,
        on_delete=models.CASCADE,
        related_name='magic_link'
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    expires_at = models.DateTimeField()
    
    # Métricas
    first_accessed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'magic_links'
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"MagicLink {str(self.id)[:8]} - {self.status}"
    
    @staticmethod
    def gerar_token():
        """Gera token aleatório seguro"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Gera hash SHA-256 do token"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def is_valid(self) -> bool:
        """Verifica se o link ainda é válido"""
        if self.status in ['COMPLETED', 'EXPIRED']:
            return False
        if timezone.now() > self.expires_at:
            self.status = 'EXPIRED'
            self.save()
            return False
        return True
    
    def marcar_acessado(self):
        """Marca o link como acessado"""
        if not self.first_accessed_at:
            self.first_accessed_at = timezone.now()
        self.status = 'ACCESSED'
        self.save()
    
    def marcar_iniciado(self):
        """Marca questionário como iniciado"""
        if not self.started_at:
            self.started_at = timezone.now()
        self.save()
    
    def marcar_concluido(self):
        """Marca questionário como concluído"""
        self.completed_at = timezone.now()
        self.status = 'COMPLETED'
        self.save()


class Resposta(TimeStampedModel):
    """
    Resposta ao questionário - totalmente anônima
    Relacionada apenas ao UUID do colaborador via MagicLink
    """
    
    magic_link = models.OneToOneField(
        MagicLink,
        on_delete=models.CASCADE,
        related_name='resposta'
    )
    
    # Respostas armazenadas como JSON
    # Formato: {"1": 3, "2": 4, "3": 2, ...}
    respostas = models.JSONField(default=dict)
    
    # Scores calculados
    score_global = models.FloatField(null=True, blank=True)
    scores_dimensoes = models.JSONField(default=dict, blank=True)
    
    # Métricas de tempo
    tempo_total_segundos = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'respostas'
    
    def __str__(self):
        return f"Resposta {str(self.id)[:8]}"
    
    def calcular_scores(self):
        """Calcula scores global e por dimensão"""
        from quiz.services.calculation_service import CalculationService
        
        calc_service = CalculationService()
        self.score_global = calc_service.calcular_score_global(self.respostas)
        self.scores_dimensoes = calc_service.calcular_scores_dimensoes(self.respostas)
        self.save()
    
    def get_nivel_risco_global(self) -> str:
        """Retorna nível de risco global"""
        if self.score_global is None:
            return 'NÃO CALCULADO'
        
        if self.score_global <= 35:
            return 'CRÍTICO'
        elif self.score_global <= 70:
            return 'ATENÇÃO'
        else:
            return 'SATISFATÓRIO'