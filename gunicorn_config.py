"""
Configuração otimizada do Gunicorn para melhor performance
"""

import multiprocessing
import os

# Bind
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Workers
# Render.com configura automaticamente WEB_CONCURRENCY
workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))

# Worker class
worker_class = 'sync'

# Timeout - aumentado para 90 segundos para queries complexas do dashboard
timeout = 90
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Request handling
max_requests = 1000
max_requests_jitter = 50

# Performance
preload_app = True

# Worker connections
worker_connections = 1000

def on_starting(server):
    """Callback executado no início do servidor"""
    server.log.info("🚀 Gunicorn iniciando com configuração otimizada")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Timeout: {timeout}s")
    server.log.info(f"Bind: {bind}")

def worker_int(worker):
    """Callback executado quando worker recebe SIGINT/SIGQUIT"""
    worker.log.info("⚠️ Worker interrompido")

def worker_abort(worker):
    """Callback executado quando worker é abortado por timeout"""
    worker.log.error(f"❌ Worker timeout após {timeout}s - verifique queries lentas")
