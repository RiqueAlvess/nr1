from celery import shared_task
import logging

logger = logging.getLogger('nr1')

@shared_task(name='usercompany.tasks.atualizar_contador_notificacoes_empresa_task', bind=True, max_retries=3)
def atualizar_contador_notificacoes_empresa_task(self, company_id):
    """
    Stub/implementação mínima para evitar KeyError.
    Substitua pelo código real que atualiza contador de notificações.
    """
    try:
        logger.info(f"[usercompany.tasks] atualizar_contador_notificacoes_empresa_task executado para company_id={company_id}")
        # TODO: implementar a lógica real aqui (ex.: atualizar modelo Company.notifications_count)
        return True
    except Exception as e:
        logger.exception("Erro em atualizar_contador_notificacoes_empresa_task")
        raise self.retry(exc=e, countdown=60)
