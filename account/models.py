from django.db import models
from django.contrib.auth.models import User, Group
from core.models import TimeStampedModel, Empresa, Unidade, Setor


class PerfilAcesso(TimeStampedModel):
    """
    Perfil de acesso do usuário ao sistema
    Define granularidade de visualização dos dados

    REFATORADO: Agora suporta múltiplas empresas, unidades e setores
    permitindo controle granular de acesso hierárquico.

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

    # REFATORADO: Múltiplas empresas (ManyToMany ao invés de ForeignKey)
    empresas = models.ManyToManyField(
        Empresa,
        blank=True,
        related_name='perfis_acesso',
        help_text="Empresas às quais o usuário tem acesso"
    )

    # Mantemos o campo empresa antigo para compatibilidade, mas será deprecated
    # Usar get_empresa_principal() ou get_empresas() para acessar
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfis_acesso_legacy',
        help_text="[DEPRECATED] Use 'empresas' para múltiplas empresas"
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
        empresas_count = self.get_empresas().count()
        if empresas_count > 1:
            return f"{self.user.username} - {self.get_nivel_acesso_display()} ({empresas_count} empresas)"
        elif empresas_count == 1:
            return f"{self.user.username} - {self.get_nivel_acesso_display()} ({self.get_empresa_principal().nome})"
        return f"{self.user.username} - {self.get_nivel_acesso_display()}"

    def save(self, *args, **kwargs):
        """Override save para sincronizar empresa legacy com empresas M2M"""
        super().save(*args, **kwargs)
        # Se existe empresa legacy mas não está em empresas M2M, sincronizar
        if self.empresa and not self.empresas.filter(id=self.empresa.id).exists():
            self.empresas.add(self.empresa)

    # === Métodos para acesso a empresas ===

    def get_empresas(self):
        """
        Retorna QuerySet de todas as empresas que o usuário pode acessar
        Combina o campo legacy 'empresa' com o M2M 'empresas'
        """
        empresas_m2m = self.empresas.filter(ativa=True)

        # Se não há empresas M2M mas tem empresa legacy, usar legacy
        if not empresas_m2m.exists() and self.empresa and self.empresa.ativa:
            return Empresa.objects.filter(id=self.empresa.id)

        return empresas_m2m

    def get_empresa_principal(self):
        """
        Retorna a empresa principal (primeira da lista ou campo legacy)
        Útil para manter compatibilidade com código existente
        """
        empresas = self.get_empresas()
        if empresas.exists():
            return empresas.first()
        return self.empresa

    def tem_acesso_empresa(self, empresa_id):
        """Verifica se o usuário tem acesso a uma empresa específica"""
        return self.get_empresas().filter(id=empresa_id).exists()

    def get_todas_unidades(self):
        """
        Retorna todas as unidades que o usuário pode acessar
        baseado no nível de acesso
        """
        if self.nivel_acesso == 'EMPRESA':
            return Unidade.objects.filter(empresa__in=self.get_empresas(), ativa=True)
        elif self.nivel_acesso == 'UNIDADE':
            return self.unidades.filter(ativa=True)
        elif self.nivel_acesso == 'SETOR':
            # Unidades derivadas dos setores permitidos
            setor_ids = self.setores.values_list('unidade_id', flat=True)
            return Unidade.objects.filter(id__in=setor_ids, ativa=True)
        return Unidade.objects.none()

    def get_todos_setores(self):
        """
        Retorna todos os setores que o usuário pode acessar
        baseado no nível de acesso
        """
        if self.nivel_acesso == 'EMPRESA':
            return Setor.objects.filter(unidade__empresa__in=self.get_empresas(), ativo=True)
        elif self.nivel_acesso == 'UNIDADE':
            return Setor.objects.filter(unidade__in=self.unidades.all(), ativo=True)
        elif self.nivel_acesso == 'SETOR':
            return self.setores.filter(ativo=True)
        return Setor.objects.none()

    def pode_visualizar_unidade(self, unidade_id):
        """Verifica se o usuário pode visualizar uma unidade"""
        if self.nivel_acesso == 'EMPRESA':
            # Verifica se a unidade pertence a alguma empresa que o usuário tem acesso
            try:
                unidade = Unidade.objects.get(id=unidade_id)
                return self.tem_acesso_empresa(unidade.empresa_id)
            except Unidade.DoesNotExist:
                return False
        if self.nivel_acesso == 'UNIDADE':
            return self.unidades.filter(id=unidade_id).exists()
        if self.nivel_acesso == 'SETOR':
            # Verifica se algum setor permitido pertence a essa unidade
            return self.setores.filter(unidade_id=unidade_id).exists()
        return False

    def pode_visualizar_setor(self, setor_id):
        """Verifica se o usuário pode visualizar um setor"""
        if self.nivel_acesso == 'EMPRESA':
            try:
                setor = Setor.objects.get(id=setor_id)
                return self.tem_acesso_empresa(setor.unidade.empresa_id)
            except Setor.DoesNotExist:
                return False
        if self.nivel_acesso == 'UNIDADE':
            try:
                setor = Setor.objects.get(id=setor_id)
                return self.unidades.filter(id=setor.unidade_id).exists()
            except Setor.DoesNotExist:
                return False
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

    def get_resumo_acesso(self):
        """
        Retorna um resumo do acesso do usuário para exibição
        """
        empresas = self.get_empresas()

        if self.nivel_acesso == 'EMPRESA':
            if empresas.count() > 1:
                return f"{empresas.count()} empresas (acesso total)"
            elif empresas.count() == 1:
                return f"{empresas.first().nome} (acesso total)"
            return "Nenhuma empresa configurada"

        elif self.nivel_acesso == 'UNIDADE':
            unidades = self.unidades.count()
            return f"{unidades} unidade(s)"

        elif self.nivel_acesso == 'SETOR':
            setores = self.setores.count()
            return f"{setores} setor(es)"

        return "Acesso não configurado"
