"""
Celery tasks para processamento assíncrono - Core
"""
from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger('nr1')


@shared_task(name='core.tasks.purge_expired_data')
def purge_expired_data():
    """
    Task agendada para executar purge de dados expirados
    Executada diariamente via Celery Beat
    """
    logger.info('Iniciando task de purge de dados expirados')

    try:
        call_command('purge_expired_data')
        logger.info('Task de purge concluída com sucesso')
        return {'status': 'success', 'message': 'Purge executado com sucesso'}
    except Exception as e:
        logger.error(f'Erro ao executar purge de dados: {str(e)}')
        return {'status': 'error', 'message': str(e)}
