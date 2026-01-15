# Guia Rápido - Desenvolvimento

## Configuração Inicial

### 1. Criar Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto (já existe um exemplo):

```env
SECRET_KEY=django-insecure-development-key-change-this-in-production-12345678901234567890
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DEFAULT_FROM_EMAIL=noreply@example.com
API_RESEND=your-resend-api-key-here

MAGIC_LINK_EXPIRATION_HOURS=48
MIN_GROUP_SIZE=1

SYSTEM_NAME=Plataforma NR-1
COMPANY_NAME=3S Dev
```

### 4. Executar Migrações

```bash
python manage.py migrate
```

### 5. Criar Superusuário

```bash
python manage.py createsuperuser
```

## Executar Servidor

### Opção 1: Script Automático

```bash
./start_server.sh
```

### Opção 2: Manual

```bash
source venv/bin/activate
python manage.py runserver
```

O servidor estará disponível em: http://127.0.0.1:8000

## Acessar Admin

URL: http://127.0.0.1:8000/admin
Usuário: admin
Senha: (a que você definiu no createsuperuser)

## Arquitetura Simplificada

### Envio de E-mails

O sistema usa envio **síncrono** de e-mails via Resend API:
- Não requer Redis
- Não requer Celery
- Não requer workers adicionais
- Simples e direto

O código está em: `core/services/email_service.py`

### Apps do Projeto

- `core`: Funcionalidades base (empresas, departamentos)
- `account`: Autenticação e perfis de usuário
- `importacao`: Importação de funcionários via CSV/Excel
- `quiz`: Questionários de riscos psicossociais
- `dashboard`: Visualização de dados e relatórios

## Comandos Úteis

### Criar Migrações

```bash
python manage.py makemigrations
```

### Aplicar Migrações

```bash
python manage.py migrate
```

### Limpar Sessões Expiradas

```bash
python manage.py clearsessions
```

### Shell Interativo

```bash
python manage.py shell
```

## Estrutura do Banco de Dados

Por padrão, usa SQLite (`db.sqlite3`) para desenvolvimento.

Para produção, recomenda-se PostgreSQL. Veja `PRODUCAO.md` para mais detalhes.

## Troubleshooting

### Erro "relation does not exist"

Execute as migrações:
```bash
python manage.py migrate
```

### Erro "No module named 'django'"

Ative o virtual environment:
```bash
source venv/bin/activate
```

### Erro ao enviar e-mails

Verifique se a chave API do Resend está configurada no `.env`:
```env
API_RESEND=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
