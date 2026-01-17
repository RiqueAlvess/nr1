#!/usr/bin/env bash

set -o errexit

echo "🚀 Iniciando servidor com configurações otimizadas..."
gunicorn nr1_platform.wsgi:application --config gunicorn_config.py
