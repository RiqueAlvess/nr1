#!/bin/bash
# Script para iniciar o Celery worker com todas as filas configuradas
# Uso: ./start_celery_worker.sh [modo]
#   - modo: "all" (padrão), "emails", "debug", "production"

set -e

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${GREEN}"
echo "================================================================"
echo "  🚀 Iniciando Celery Worker - NR1 Platform"
echo "================================================================"
echo -e "${NC}"

# Verificar se Redis está rodando
echo -e "${YELLOW}[1/3]${NC} Verificando Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Redis está rodando${NC}"
else
    echo -e "  ${RED}❌ ERRO: Redis não está rodando!${NC}"
    echo -e "  ${YELLOW}Inicie o Redis com:${NC} sudo systemctl start redis"
    exit 1
fi

# Verificar se as variáveis de ambiente estão configuradas
echo -e "${YELLOW}[2/3]${NC} Verificando configurações..."
if [ ! -f ".env" ]; then
    echo -e "  ${RED}❌ AVISO: Arquivo .env não encontrado!${NC}"
    echo -e "  ${YELLOW}Copie .env.example para .env e configure as variáveis${NC}"
    echo -e "  ${YELLOW}Comando:${NC} cp .env.example .env"
else
    echo -e "  ${GREEN}✅ Arquivo .env encontrado${NC}"
fi

# Modo de execução
MODE=${1:-all}

echo -e "${YELLOW}[3/3]${NC} Iniciando worker em modo: ${GREEN}${MODE}${NC}"
echo ""

case $MODE in
    all)
        echo -e "${GREEN}Modo: TODAS AS FILAS${NC}"
        echo -e "Filas: emails, celery, default, maintenance"
        echo ""
        celery -A nr1_platform worker \
            --loglevel=info \
            -Q emails,celery,default,maintenance \
            -n worker_all@%h
        ;;

    emails)
        echo -e "${GREEN}Modo: APENAS E-MAILS${NC}"
        echo -e "Filas: emails"
        echo ""
        celery -A nr1_platform worker \
            --loglevel=info \
            -Q emails \
            -n worker_emails@%h \
            --concurrency=4
        ;;

    debug)
        echo -e "${GREEN}Modo: DEBUG (loglevel=debug)${NC}"
        echo -e "Filas: emails, celery, default, maintenance"
        echo ""
        celery -A nr1_platform worker \
            --loglevel=debug \
            -Q emails,celery,default,maintenance \
            -n worker_debug@%h
        ;;

    production)
        echo -e "${GREEN}Modo: PRODUÇÃO (background)${NC}"
        echo -e "Filas: emails, celery, default, maintenance"
        echo ""
        echo -e "${YELLOW}⚠️  ATENÇÃO: Use um gerenciador de processos para produção!${NC}"
        echo -e "   Recomendado: systemd, supervisor, ou similar"
        echo ""
        echo -e "Para este exemplo, iniciando em background com nohup..."
        nohup celery -A nr1_platform worker \
            --loglevel=info \
            -Q emails,celery,default,maintenance \
            -n worker_prod@%h \
            --pidfile=/tmp/celery_worker.pid \
            --logfile=logs/celery_worker.log \
            > /dev/null 2>&1 &

        echo -e "${GREEN}✅ Worker iniciado em background${NC}"
        echo -e "   PID file: /tmp/celery_worker.pid"
        echo -e "   Log file: logs/celery_worker.log"
        echo ""
        echo -e "Para parar: ${YELLOW}kill \$(cat /tmp/celery_worker.pid)${NC}"
        ;;

    *)
        echo -e "${RED}❌ Modo inválido: ${MODE}${NC}"
        echo ""
        echo "Modos disponíveis:"
        echo "  all        - Todas as filas (padrão)"
        echo "  emails     - Apenas fila de e-mails (otimizado)"
        echo "  debug      - Modo debug com logs detalhados"
        echo "  production - Modo produção (background)"
        echo ""
        echo "Uso: $0 [modo]"
        exit 1
        ;;
esac
