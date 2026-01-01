"""
Celery tasks para processamento assíncrono - Quiz
"""
from celery import shared_task
from django.conf import settings
import logging
import time

from quiz.services.magic_link_service import MagicLinkService
from quiz.models import MagicLink
from importacao.models import Colaborador

logger = logging.getLogger('nr1')


@shared_task(name='quiz.tasks.send_magic_links_async', bind=True, max_retries=3)
def send_magic_links_async(self, colaboradores_ids, base_url):
    """
    Task assíncrona para envio de magic links em lote
    Respeita rate limit da API de email

    Args:
        colaboradores_ids: Lista de UUIDs dos colaboradores
        base_url: URL base para construir o link

    Returns:
        dict: Status do envio com contadores
    """
    logger.info(f'Iniciando envio assíncrono de {len(colaboradores_ids)} magic links')

    # Primeiro, gerar os magic links se necessário
    gerados, ja_existentes = MagicLinkService.gerar_magic_links_bulk(colaboradores_ids)
    logger.info(f'Magic links gerados: {gerados}, já existentes: {ja_existentes}')

    # Buscar magic links para envio
    magic_links = MagicLink.objects.filter(
        colaborador_id__in=colaboradores_ids,
        status__in=['PENDING', 'ACCESSED']
    ).select_related('colaborador')

    total = magic_links.count()
    enviados = 0
    erros = 0

    logger.info(f'Iniciando envio de {total} emails')

    for idx, magic_link in enumerate(magic_links, 1):
        try:
            # Rate limiting: delay entre envios (respeitar free tier da API)
            # 100 emails/hora = 1 email a cada 36 segundos
            if idx > 1:
                time.sleep(36)  # Esperar 36 segundos entre cada envio

            # Gerar token para o link
            token = MagicLinkService._gerar_token_para_magic_link(magic_link)

            # Enviar email
            sucesso = MagicLinkService.enviar_magic_link(
                magic_link=magic_link,
                token=token,
                base_url=base_url
            )

            if sucesso:
                enviados += 1
                logger.info(f'Email enviado [{idx}/{total}]: {magic_link.colaborador.email}')
            else:
                erros += 1
                logger.error(f'Falha ao enviar email [{idx}/{total}]: {magic_link.colaborador.email}')

        except Exception as e:
            erros += 1
            logger.error(f'Erro ao enviar email [{idx}/{total}]: {str(e)}')

    resultado = {
        'status': 'completed',
        'total': total,
        'enviados': enviados,
        'erros': erros,
        'gerados': gerados,
        'ja_existentes': ja_existentes
    }

    logger.info(f'Envio assíncrono concluído: {resultado}')

    return resultado
