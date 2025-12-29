from django.db import models
from django.contrib.auth.models import User, Group
from core.models import TimeStampedModel, Empresa, Unidade, Setor


class PerfilAcesso(TimeStampedModel):
    """
    Perfil de acesso do usuário ao sistema
    Define granularidade de visualização dos dados

    Grupos disponíveis:
    - RH: Acesso root (importação, emails, todos os dashboards)
    - SST: Acesso completo aos dashboards
    - Medicina do Trabalho: Acesso completo aos dashboards
    - Liderança: Acesso limitado por hierarquia (empresa/unidade/setor)
    - Consultoria Externa: Acesso limitado por hierarquia (empresa/unidade/setor)
    """

    # Grupos padrão do sistema
    GRUPO_RH = 'RH'
    GRUPO_SST = 'SST'
    GRUPO_MEDICINA = 'Medicina do Trabalho'
    GRUPO_LIDERANCA = 'Liderança'
    GRUPO_CONSULTORIA = 'Consultoria Externa'

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

    # === Métodos baseados em Grupos ===

    def pertence_grupo(self, nome_grupo):
        """Verifica se o usuário pertence a um grupo específico"""
        return self.user.groups.filter(name=nome_grupo).exists()

    def is_rh(self):
        """Verifica se o usuário pertence ao grupo RH (acesso root)"""
        return self.pertence_grupo(self.GRUPO_RH)

    def is_sst(self):
        """Verifica se o usuário pertence ao grupo SST"""
        return self.pertence_grupo(self.GRUPO_SST)

    def is_medicina(self):
        """Verifica se o usuário pertence ao grupo Medicina do Trabalho"""
        return self.pertence_grupo(self.GRUPO_MEDICINA)

    def is_lideranca(self):
        """Verifica se o usuário pertence ao grupo Liderança"""
        return self.pertence_grupo(self.GRUPO_LIDERANCA)

    def is_consultoria(self):
        """Verifica se o usuário pertence ao grupo Consultoria Externa"""
        return self.pertence_grupo(self.GRUPO_CONSULTORIA)

    def tem_acesso_completo_dashboards(self):
        """
        Verifica se o usuário tem acesso completo aos dashboards
        (RH, SST, Medicina do Trabalho)
        """
        return self.is_rh() or self.is_sst() or self.is_medicina()

    def tem_acesso_limitado(self):
        """
        Verifica se o usuário tem acesso limitado por hierarquia
        (Liderança, Consultoria Externa)
        """
        return self.is_lideranca() or self.is_consultoria()

    def pode_acessar_importacao(self):
        """
        Verifica se o usuário pode acessar a funcionalidade de importação
        Apenas RH tem acesso
        """
        return self.is_rh()

    def pode_visualizar_emails(self):
        """
        Verifica se o usuário pode visualizar lista de emails
        Apenas RH tem acesso
        """
        return self.is_rh()

    def get_grupo_principal(self):
        """Retorna o grupo principal do usuário (primeiro grupo encontrado)"""
        grupos_prioritarios = [
            self.GRUPO_RH,
            self.GRUPO_SST,
            self.GRUPO_MEDICINA,
            self.GRUPO_LIDERANCA,
            self.GRUPO_CONSULTORIA,
        ]
        for grupo in grupos_prioritarios:
            if self.pertence_grupo(grupo):
                return grupo
        return None