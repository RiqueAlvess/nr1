"""Command para criar registro inicial de Branding."""
from django.core.management.base import BaseCommand
from core.models import Branding


class Command(BaseCommand):
    help = 'Cria registro inicial de configuracoes de Branding (White Label)'

    def handle(self, *args, **options):
        branding = Branding.get_instance()

        self.stdout.write(
            self.style.SUCCESS(
                f'Branding configurado: {branding.nome_sistema}'
            )
        )

        # Mostrar configuracoes atuais
        self.stdout.write('')
        self.stdout.write('Configuracoes atuais:')
        self.stdout.write(f'  Nome do Sistema: {branding.nome_sistema}')
        self.stdout.write(f'  Titulo do Navegador: {branding.titulo_navegador}')
        self.stdout.write(f'  Nome da Empresa: {branding.nome_empresa}')
        self.stdout.write(f'  Cor Primaria: {branding.cor_primaria}')
        self.stdout.write(f'  Cor Secundaria: {branding.cor_secundaria}')
        self.stdout.write(f'  Cor Accent: {branding.cor_accent}')
        self.stdout.write(f'  Ativo: {branding.ativo}')
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING(
                'Para customizar, acesse: /admin/core/branding/'
            )
        )
