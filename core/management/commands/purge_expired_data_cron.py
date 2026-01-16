"""
Management command para purge de dados expirados.
Pode ser executado via cron job no servidor.

Exemplo de cron job (executar diariamente às 3h):
0 3 * * * cd /caminho/do/projeto && python manage.py purge_expired_data_cron
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
import logging

logger = logging.getLogger('nr1')


class Command(BaseCommand):
    help = 'Executa purge de dados expirados (LGPD) - para cron job'

    def handle(self, *args, **options):
        logger.info('Iniciando purge automático de dados expirados (cron)')

        try:
            call_command('purge_expired_data')
            self.stdout.write(self.style.SUCCESS('✓ Purge executado com sucesso'))
            logger.info('Purge automático concluído com sucesso')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro ao executar purge: {str(e)}'))
            logger.error(f'Erro no purge automático: {str(e)}')
            raise
