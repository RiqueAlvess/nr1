# Configuração para Produção - NR1 Platform

## Visão Geral

Este guia mostra como configurar e executar a Plataforma NR-1 em ambiente de produção.

## Requisitos

- Python 3.11 ou superior
- PostgreSQL 12+ (recomendado para produção)
- Nginx (como proxy reverso)
- Gunicorn ou uWSGI (servidor WSGI)

## Configuração Inicial

### 1. Clonar o Repositório

```bash
git clone <seu-repositorio>
cd nr1
```

### 2. Criar Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
pip install gunicorn  # Para servidor de produção
```

### 4. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Django Settings
SECRET_KEY=sua-chave-secreta-muito-segura-aqui
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# Database (PostgreSQL recomendado)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=nr1_db
DB_USER=nr1_user
DB_PASSWORD=senha-segura
DB_HOST=localhost
DB_PORT=5432

# Email Configuration (Resend API)
DEFAULT_FROM_EMAIL=noreply@seu-dominio.com
API_RESEND=sua-chave-api-resend

# Magic Link Configuration
MAGIC_LINK_EXPIRATION_HOURS=48

# K-Anonymity Settings
MIN_GROUP_SIZE=5

# System Information
SYSTEM_NAME=Plataforma NR-1
COMPANY_NAME=Sua Empresa
```

### 5. Atualizar settings.py para PostgreSQL (Opcional)

Edite `nr1_platform/settings.py` para usar PostgreSQL:

```python
# Database
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
}
```

### 6. Executar Migrações

```bash
python manage.py migrate
```

### 7. Criar Superusuário

```bash
python manage.py createsuperuser
```

### 8. Coletar Arquivos Estáticos

```bash
python manage.py collectstatic --noinput
```

## Configuração do Gunicorn

### 1. Criar arquivo de configuração Gunicorn

Crie `gunicorn_config.py`:

```python
import multiprocessing

# Endereço e porta
bind = "127.0.0.1:8000"

# Número de workers
workers = multiprocessing.cpu_count() * 2 + 1

# Timeout
timeout = 120

# Log
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"

# Nome do processo
proc_name = "nr1_platform"
```

### 2. Criar serviço systemd

Crie `/etc/systemd/system/nr1.service`:

```ini
[Unit]
Description=NR1 Platform Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/caminho/para/nr1
Environment="PATH=/caminho/para/nr1/venv/bin"
ExecStart=/caminho/para/nr1/venv/bin/gunicorn \
    --config /caminho/para/nr1/gunicorn_config.py \
    nr1_platform.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 3. Ativar e iniciar o serviço

```bash
sudo systemctl daemon-reload
sudo systemctl enable nr1
sudo systemctl start nr1
sudo systemctl status nr1
```

## Configuração do Nginx

Crie `/etc/nginx/sites-available/nr1`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;

    # Logs
    access_log /var/log/nginx/nr1_access.log;
    error_log /var/log/nginx/nr1_error.log;

    # Arquivos estáticos
    location /static/ {
        alias /caminho/para/nr1/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy para Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Aumentar tamanho máximo de upload
    client_max_body_size 10M;
}
```

### Ativar configuração Nginx

```bash
sudo ln -s /etc/nginx/sites-available/nr1 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Configuração SSL com Certbot

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

## Envio de E-mails

A aplicação usa a API Resend para envio de e-mails de forma **síncrona**. Configure sua chave API no `.env`:

```env
API_RESEND=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=noreply@seu-dominio.com
```

Você precisará:
1. Criar uma conta em https://resend.com
2. Verificar seu domínio
3. Gerar uma API key

## Backup

### Backup do Banco de Dados

SQLite (desenvolvimento):
```bash
cp db.sqlite3 backups/db_$(date +%Y%m%d_%H%M%S).sqlite3
```

PostgreSQL (produção):
```bash
pg_dump -U nr1_user nr1_db > backups/nr1_db_$(date +%Y%m%d_%H%M%S).sql
```

### Backup dos Arquivos

```bash
tar -czf backups/nr1_files_$(date +%Y%m%d_%H%M%S).tar.gz \
    --exclude=venv \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    --exclude=.git \
    .
```

## Monitoramento

### Logs do Sistema

```bash
# Gunicorn
tail -f logs/gunicorn_access.log
tail -f logs/gunicorn_error.log

# Django
tail -f logs/nr1.log

# Nginx
tail -f /var/log/nginx/nr1_access.log
tail -f /var/log/nginx/nr1_error.log

# Systemd
sudo journalctl -u nr1 -f
```

## Manutenção

### Atualizar Aplicação

```bash
cd /caminho/para/nr1
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart nr1
```

### Limpar Sessões Expiradas

```bash
python manage.py clearsessions
```

## Segurança

1. **Nunca** execute com `DEBUG=True` em produção
2. Use uma `SECRET_KEY` forte e única
3. Configure firewall (UFW):
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
4. Mantenha o sistema atualizado:
   ```bash
   sudo apt update && sudo apt upgrade
   ```
5. Configure backups automáticos
6. Use HTTPS (SSL/TLS)
7. Limite acesso ao servidor de banco de dados

## Troubleshooting

### Erro de Permissões

```bash
sudo chown -R www-data:www-data /caminho/para/nr1
sudo chmod -R 755 /caminho/para/nr1
```

### Gunicorn não inicia

```bash
sudo journalctl -u nr1 -n 50
# Verifique o caminho do WorkingDirectory e ExecStart
```

### Nginx retorna 502

```bash
# Verifique se o Gunicorn está rodando
sudo systemctl status nr1

# Verifique os logs
tail -f /var/log/nginx/nr1_error.log
```

## Suporte

Para problemas ou dúvidas, consulte a documentação do Django ou abra uma issue no repositório.
