#!/bin/bash

# Script para iniciar o servidor Django

# Ativar virtual environment
source venv/bin/activate

# Executar migrações (caso haja novas)
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Iniciar servidor
echo "Iniciando servidor Django..."
echo "Ambiente de desenvolvimento: http://127.0.0.1:8000"
echo "ATENÇÃO: Este é um servidor de desenvolvimento. Para produção, use Gunicorn ou uWSGI."
python manage.py runserver 0.0.0.0:8000
