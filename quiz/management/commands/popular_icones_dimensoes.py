"""
Management command para popular os ícones das dimensões NR-1
"""
from django.core.management.base import BaseCommand
from quiz.models import Dimensao


class Command(BaseCommand):
    help = 'Popula os ícones contextuais para as dimensões NR-1'

    # Mapeamento de ícones por dimensão (NR-1)
    DIMENSOES_ICONS_MAPPING = {
        # Dimensões Organizacionais
        'Organização do Trabalho': {
            'icon': 'layout-grid',
            'color': 'blue',
            'path': '<path d="M3 3h7v7H3z"/><path d="M14 3h7v7h-7z"/><path d="M14 14h7v7h-7z"/><path d="M3 14h7v7H3z"/>'
        },
        'Jornada de Trabalho': {
            'icon': 'clock',
            'color': 'indigo',
            'path': '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>'
        },
        'Ritmo de Trabalho': {
            'icon': 'activity',
            'color': 'purple',
            'path': '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>'
        },

        # Dimensões Psicossociais
        'Fatores Psicossociais': {
            'icon': 'brain',
            'color': 'pink',
            'path': '<path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/><path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/><path d="M3.477 10.896a4 4 0 0 1 .585-.396"/><path d="M19.938 10.5a4 4 0 0 1 .585.396"/><path d="M6 18a4 4 0 0 1-1.967-.516"/><path d="M19.967 17.484A4 4 0 0 1 18 18"/>'
        },
        'Relacionamento no Trabalho': {
            'icon': 'users',
            'color': 'green',
            'path': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
        },
        'Comunicação': {
            'icon': 'message-circle',
            'color': 'teal',
            'path': '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>'
        },

        # Dimensões de Risco
        'Fatores de Risco': {
            'icon': 'alert-triangle',
            'color': 'red',
            'path': '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>'
        },
        'Assédio Moral': {
            'icon': 'shield-alert',
            'color': 'orange',
            'path': '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="M12 8v4"/><path d="M12 16h.01"/>'
        },
        'Violência no Trabalho': {
            'icon': 'shield-ban',
            'color': 'rose',
            'path': '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><line x1="9" x2="15" y1="9" y2="15"/><line x1="15" x2="9" y1="9" y2="15"/>'
        },

        # Dimensões Ambientais
        'Condições de Trabalho': {
            'icon': 'briefcase',
            'color': 'cyan',
            'path': '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/>'
        },
        'Ambiente Físico': {
            'icon': 'building',
            'color': 'slate',
            'path': '<rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/>'
        },

        # Dimensões de Saúde
        'Saúde Mental': {
            'icon': 'heart-pulse',
            'color': 'emerald',
            'path': '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"/>'
        },
        'Capacitação': {
            'icon': 'graduation-cap',
            'color': 'amber',
            'path': '<path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>'
        },
    }

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando atualização de ícones das dimensões...'))

        updated_count = 0
        not_found = []

        for dimensao in Dimensao.objects.all():
            # Buscar mapeamento exato ou fuzzy
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
