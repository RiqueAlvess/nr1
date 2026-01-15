"""
Management command para popular os ícones das dimensões HSE-IT
com ícones contextuais específicos para cada tema
"""
from django.core.management.base import BaseCommand
from quiz.models import Dimensao


class Command(BaseCommand):
    help = 'Popula os ícones contextuais para as dimensões HSE-IT'

    # Mapeamento de ícones por dimensão (HSE-IT)
    DIMENSOES_ICONS_MAPPING = {
        # Demandas - Pressão, carga de trabalho
        'Demandas': {
            'icon': 'gauge',
            'color': 'red',
            'path': '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>'
        },

        # Controle - Autonomia, ajustes, configurações
        'Controle': {
            'icon': 'sliders',
            'color': 'blue',
            'path': '<line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="1" x2="7" y1="14" y2="14"/><line x1="9" x2="15" y1="8" y2="8"/><line x1="17" x2="23" y1="16" y2="16"/>'
        },

        # Apoio Gerencial - Líder apoiando
        'Apoio Gerencial': {
            'icon': 'user-check',
            'color': 'green',
            'path': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/>'
        },

        # Apoio de Colegas - Colaboração, equipe
        'Apoio de Colegas': {
            'icon': 'users',
            'color': 'teal',
            'path': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
        },

        # Relacionamentos - Conflitos interpessoais
        'Relacionamentos': {
            'icon': 'user-x',
            'color': 'orange',
            'path': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="17" x2="22" y1="8" y2="13"/><line x1="22" x2="17" y1="8" y2="13"/>'
        },

        # Papel - Clareza de tarefas e responsabilidades
        'Papel': {
            'icon': 'clipboard-check',
            'color': 'purple',
            'path': '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>'
        },

        # Mudanças - Transformação, adaptação
        'Mudanças': {
            'icon': 'refresh-cw',
            'color': 'indigo',
            'path': '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>'
        },
    }

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando atualização de ícones das dimensões HSE-IT...'))

        updated_count = 0
        not_found = []

        for dimensao in Dimensao.objects.all():
            # Buscar mapeamento exato
            icon_data = self.DIMENSOES_ICONS_MAPPING.get(dimensao.nome)

            if icon_data:
                dimensao.icon_name = icon_data['icon']
                dimensao.icon_color = icon_data['color']
                dimensao.icon_path = icon_data['path']
                dimensao.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {dimensao.nome} → {icon_data["icon"]} ({icon_data["color"]})')
                )
            else:
                not_found.append(dimensao.nome)
                self.stdout.write(
                    self.style.WARNING(f'⚠ {dimensao.nome} - Mapeamento não encontrado (usando padrão)')
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✓ {updated_count} dimensões atualizadas com sucesso!'))

        if not_found:
            self.stdout.write(self.style.WARNING(f'⚠ {len(not_found)} dimensões sem mapeamento:'))
            for nome in not_found:
                self.stdout.write(f'  - {nome}')
            self.stdout.write('')
            self.stdout.write(self.style.NOTICE('Dimensões disponíveis no mapeamento:'))
            for nome in self.DIMENSOES_ICONS_MAPPING.keys():
                self.stdout.write(f'  - {nome}')
