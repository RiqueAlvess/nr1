#!/usr/bin/env python
"""
Script para testar a conexão do Celery com Redis e validar que tasks podem ser enfileiradas.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nr1_platform.settings')
django.setup()

from celery import current_app
from emails.tasks import send_email_task
from quiz.tasks import send_magic_links_async
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_celery_connection():
    """Testa a conexão do Celery com Redis"""
    print("\n" + "="*80)
    print("TESTE DE CONEXÃO CELERY/REDIS")
    print("="*80 + "\n")

    # 1. Verificar configurações do Celery
    print("1. Configurações do Celery:")
    print(f"   - Broker URL: {current_app.conf.broker_url}")
    print(f"   - Result Backend: {current_app.conf.result_backend}")
    print(f"   - Task Serializer: {current_app.conf.task_serializer}")
    print(f"   - Accept Content: {current_app.conf.accept_content}")
    print()

    # 2. Verificar tasks registradas
    print("2. Tasks registradas no Celery:")
    for task_name in sorted(current_app.tasks.keys()):
        if not task_name.startswith('celery.'):
            print(f"   - {task_name}")
    print()

    # 3. Verificar filas configuradas
    print("3. Rotas de tasks configuradas:")
    if hasattr(current_app.conf, 'task_routes'):
        for task_name, route_config in current_app.conf.task_routes.items():
            print(f"   - {task_name} → {route_config}")
    print()

    # 4. Testar conexão com Redis (broker)
    print("4. Testando conexão com Redis (broker):")
    try:
        # Tentar obter uma conexão do pool do broker
        with current_app.connection_or_acquire() as conn:
            conn.connect()
            print("   ✅ Conexão com broker (Redis) estabelecida com sucesso!")
    except Exception as e:
        print(f"   ❌ ERRO ao conectar com broker: {e}")
        return False
    print()

    # 5. Testar enfileiramento da task de debug
    print("5. Testando enfileiramento de task de debug:")
    try:
        from nr1_platform.celery import debug_task
        result = debug_task.delay()
        print(f"   ✅ Task de debug enfileirada com sucesso!")
        print(f"   - Task ID: {result.id}")
        print(f"   - Status: {result.status}")
    except Exception as e:
        print(f"   ❌ ERRO ao enfileirar task de debug: {e}")
        import traceback
        traceback.print_exc()
    print()

    # 6. Testar enfileiramento da task send_email_task
    print("6. Testando enfileiramento de send_email_task:")
    try:
        result = send_email_task.delay(
            to_email='test@example.com',
            subject='Teste de Conexão Celery',
            html_body='<p>Teste</p>',
            text_body='Teste'
        )
        print(f"   ✅ send_email_task enfileirada com sucesso!")
        print(f"   - Task ID: {result.id}")
        print(f"   - Status: {result.status}")
    except Exception as e:
        print(f"   ❌ ERRO ao enfileirar send_email_task: {e}")
        import traceback
        traceback.print_exc()
    print()

    # 7. Verificar se há tasks na fila
    print("7. Verificando tasks nas filas (usando Redis):")
    try:
        import redis
        from django.conf import settings

        # Conectar ao Redis
        broker_url = settings.CELERY_BROKER_URL
        redis_client = redis.from_url(broker_url)

        # Verificar filas
        queues = ['celery', 'emails', 'default', 'maintenance']
        for queue_name in queues:
            queue_key = f'celery.{queue_name}'
            length = redis_client.llen(queue_key)
            print(f"   - Fila '{queue_name}': {length} tasks pendentes")

        # Verificar chaves do Redis relacionadas ao Celery
        print("\n   Chaves do Redis relacionadas ao Celery:")
        keys = redis_client.keys('celery*')
        if keys:
            for key in keys[:10]:  # Mostrar apenas as primeiras 10
                key_type = redis_client.type(key).decode('utf-8')
                print(f"   - {key.decode('utf-8')} (tipo: {key_type})")
        else:
            print("   - Nenhuma chave 'celery*' encontrada no Redis")

    except Exception as e:
        print(f"   ❌ ERRO ao verificar filas no Redis: {e}")
        import traceback
        traceback.print_exc()
    print()

    print("="*80)
    print("TESTE CONCLUÍDO")
    print("="*80 + "\n")

    print("PRÓXIMOS PASSOS:")
    print("1. Inicie o Celery worker com:")
    print("   celery -A nr1_platform worker --loglevel=info -Q celery,emails,default,maintenance")
    print()
    print("2. Ou para testar apenas a fila de emails:")
    print("   celery -A nr1_platform worker --loglevel=info -Q emails")
    print()
    print("3. Em outro terminal, execute novamente este script e verifique se as tasks são processadas")
    print()


if __name__ == '__main__':
    test_celery_connection()
