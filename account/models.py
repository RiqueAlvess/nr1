from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel, Empresa, Unidade, Setor


class PerfilAcesso(TimeStampedModel):
    """
    Perfil de acesso do usuário ao sistema
    Define granularidade de visualização dos dados
    """
    
    NIVEL_ACESSO_CHOICES = [
        ('EMPRESA', 'Visualização Total (Empresa)'),
        ('UNIDADE', 'Visualização por Unidade'),
        ('SETOR', 'Visualização por Setor'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_acesso')
    nivel_acesso = models.CharField(max_length=20, choices=NIVEL_ACESSO_CHOICES, default='SETOR')
    
    # Relacionamentos para limitar acesso
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Empresa à qual o usuário tem acesso"
    )
    unidades = models.ManyToManyField(
        Unidade,
        blank=True,
        help_text="Unidades às quais o usuário tem acesso (se nível = UNIDADE)"
    )
    setores = models.ManyToManyField(
        Setor,
        blank=True,
        help_text="Setores aos quais o usuário tem acesso (se nível = SETOR)"
    )
    
    ativo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'perfis_acesso'
        verbose_name = 'Perfil de Acesso'
        verbose_name_plural = 'Perfis de Acesso'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_nivel_acesso_display()}"
    
    def pode_visualizar_unidade(self, unidade_id):
        """Verifica se o usuário pode visualizar uma unidade"""
        if self.nivel_acesso == 'EMPRESA':
            return True
        if self.nivel_acesso == 'UNIDADE':
            return self.unidades.filter(id=unidade_id).exists()
        return False
    
    def pode_visualizar_setor(self, setor_id):
        """Verifica se o usuário pode visualizar um setor"""
        if self.nivel_acesso == 'EMPRESA':
            return True
        if self.nivel_acesso == 'UNIDADE':
            from core.models import Setor
            setor = Setor.objects.get(id=setor_id)
            return self.unidades.filter(id=setor.unidade_id).exists()
        if self.nivel_acesso == 'SETOR':
            return self.setores.filter(id=setor_id).exists()
        return False