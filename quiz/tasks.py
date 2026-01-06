"""
Celery tasks para processamento assíncrono - Quiz
"""
from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
import logging

from quiz.services.magic_link_service import MagicLinkService
from quiz.models import MagicLink
from importacao.models import Colaborador
from emails.tasks import send_email_task

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
    logger.info(
        f'[CELERY TASK] send_magic_links_async INICIADA | '
        f'task_id={self.request.id} | '
        f'colaboradores_count={len(colaboradores_ids)} | '
        f'base_url={base_url}'
    )
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

    logger.info(f'Iniciando enfileiramento de {total} emails')

    for idx, magic_link in enumerate(magic_links, 1):
        try:
            # Gerar novo token
            token = MagicLink.gerar_token()
            token_hash = MagicLink.hash_token(token)

            # Atualizar hash (para próximo uso)
            magic_link.token_hash = token_hash
            magic_link.save()

            # Construir URL completa do magic link
            quiz_path = reverse('quiz:responder', kwargs={'token': token})
            magic_link_url = f"{base_url}{quiz_path}"

            # Preparar contexto para renderizar o email
            context = {
                'magic_link': magic_link_url,
                'expiration_hours': settings.MAGIC_LINK_EXPIRATION_HOURS,
                'system_name': settings.SYSTEM_NAME,
                'company_name': settings.COMPANY_NAME,
            }

            # Renderizar template do email
            html_message = render_to_string('emails/magic_link_questionario.html', context)
            text_message = strip_tags(html_message)
            subject = "Convite para Avaliação de Riscos Psicossociais - NR-1"

            # Enfileirar envio (não bloquear o worker)
            logger.info(
                f'[CELERY DEBUG] Enfileirando send_email_task [{idx}/{total}] | '
                f'to_email={magic_link.colaborador.email}'
            )

            task_result = send_email_task.delay(
                to_email=magic_link.colaborador.email,
                subject=subject,
                html_body=html_message,
                text_body=text_message
            )

            enviados += 1
            logger.info(
                f'[CELERY DEBUG] Email task enfileirada [{idx}/{total}] | '
                f'task_id={task_result.id} | '
                f'to_email={magic_link.colaborador.email}'
            )

        except Exception as e:
            erros += 1
            logger.exception(f'Erro ao processar envio para [{idx}/{total}]: {magic_link.colaborador.email}')

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
