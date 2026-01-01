"""
Configuração do Celery para processamento assíncrono.
"""
import os
from celery import Celery

# Define o módulo de settings do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nr1_platform.settings')

app = Celery('nr1_platform')

# Carrega configurações do Django settings.py com prefixo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobre automaticamente tasks em todos os apps instalados
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Task de debug para testar o Celery."""
    print(f'Request: {self.request!r}')
