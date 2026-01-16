import logging

logger = logging.getLogger('nr1')

def atualizar_contador_notificacoes_empresa_task(company_id):
    """
    Stub/implementação mínima para atualizar contador de notificações.
    Substitua pelo código real que atualiza contador de notificações.
    """
    try:
        logger.info(f"[usercompany.tasks] atualizar_contador_notificacoes_empresa_task executado para company_id={company_id}")
        # TODO: implementar a lógica real aqui (ex.: atualizar modelo Company.notifications_count)
        return True
    except Exception as e:
        logger.exception("Erro em atualizar_contador_notificacoes_empresa_task")
        raise
