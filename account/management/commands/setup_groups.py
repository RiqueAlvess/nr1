"""
Management command para configurar grupos de usuários do sistema

Grupos criados:
- RH: Acesso root (importação, emails, todos os dashboards)
- SST: Acesso completo aos dashboards
- Medicina do Trabalho: Acesso completo aos dashboards
- Liderança: Acesso limitado por hierarquia (empresa/unidade/setor)
- Consultoria Externa: Acesso limitado por hierarquia (empresa/unidade/setor)

Uso:
    python manage.py setup_groups
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from account.models import PerfilAcesso


class Command(BaseCommand):
    help = 'Configura grupos de usuários do sistema NR-1'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando configuração de grupos...'))

        grupos_info = [
            {
                'nome': PerfilAcesso.GRUPO_RH,
                'descricao': 'RH - Acesso root (importação, emails, todos os dashboards)',
                'permissoes': ['add', 'change', 'delete', 'view']  # Todas as permissões
            },
            {
                'nome': PerfilAcesso.GRUPO_SST,
                'descricao': 'SST - Acesso completo aos dashboards',
                'permissoes': ['view']  # Apenas visualização
            },
            {
                'nome': PerfilAcesso.GRUPO_MEDICINA,
                'descricao': 'Medicina do Trabalho - Acesso completo aos dashboards',
                'permissoes': ['view']  # Apenas visualização
            },
            {
                'nome': PerfilAcesso.GRUPO_LIDERANCA,
                'descricao': 'Liderança - Acesso limitado por hierarquia',
                'permissoes': ['view']  # Apenas visualização, com filtros
            },
            {
                'nome': PerfilAcesso.GRUPO_CONSULTORIA,
                'descricao': 'Consultoria Externa - Acesso limitado por hierarquia',
                'permissoes': ['view']  # Apenas visualização, com filtros
            },
        ]

        for grupo_info in grupos_info:
            grupo, created = Group.objects.get_or_create(name=grupo_info['nome'])

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Grupo '{grupo_info['nome']}' criado com sucesso")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"○ Grupo '{grupo_info['nome']}' já existe")
                )

            # Configurar permissões específicas
            if grupo_info['nome'] == PerfilAcesso.GRUPO_RH:
                # RH tem acesso total
                self._configurar_permissoes_rh(grupo)
            else:
                # Outros grupos têm permissões de visualização
                self._configurar_permissoes_visualizacao(grupo)

        self.stdout.write(self.style.SUCCESS('\n✓ Configuração de grupos concluída!'))
        self.stdout.write(self.style.SUCCESS('\nGrupos disponíveis:'))
        for grupo in Group.objects.all().order_by('name'):
            count = grupo.user_set.count()
            self.stdout.write(f"  - {grupo.name} ({count} usuários)")

    def _configurar_permissoes_rh(self, grupo):
        """Configura permissões completas para o grupo RH"""
        # RH tem acesso a todas as funcionalidades via métodos do modelo
        # Não precisamos adicionar permissões específicas aqui
        self.stdout.write(
            self.style.SUCCESS(f"  → Permissões de acesso root configuradas para {grupo.name}")
        )

    def _configurar_permissoes_visualizacao(self, grupo):
        """Configura permissões de visualização para grupos não-RH"""
        # Outros grupos têm acesso de visualização via métodos do modelo
        # Não precisamos adicionar permissões específicas aqui
        self.stdout.write(
            self.style.SUCCESS(f"  → Permissões de visualização configuradas para {grupo.name}")
        )
