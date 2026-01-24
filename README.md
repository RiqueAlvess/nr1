# Vivamente360 White Label

Plataforma white label para gestao de riscos psicossociais em conformidade com a NR-1.

## Caracteristicas

- White Label completo (logo, cores, nome)
- Django Admin moderno (Unfold)
- Gestao de empresas, unidades e setores
- Questionarios NR-1 (HSE-IT)
- Dashboards e analytics
- Conformidade LGPD
- Sistema de permissoes granular

## Requisitos

- Python 3.8+
- PostgreSQL 12+
- Django 5.0

## Instalacao

```bash
# Clonar repositorio
git clone <repo_url>
cd nr1

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variaveis de ambiente
cp .env.example .env
# Editar .env com suas configuracoes

# Rodar migrations
python manage.py migrate

# Criar superuser
python manage.py createsuperuser

# Configurar branding inicial
python manage.py setup_branding

# Coletar arquivos estaticos
python manage.py collectstatic --noinput

# Rodar servidor de desenvolvimento
python manage.py runserver
```

## Customizacao White Label

Para personalizar o sistema com sua marca:

1. Acesse o Django Admin: `/admin/`
2. Navegue ate "Configuracoes White Label > Branding"
3. Configure:
   - Nome do sistema
   - Logo principal e de login
   - Favicon
   - Paleta de cores
   - Informacoes da empresa

Veja o guia completo em [docs/WHITE_LABEL.md](docs/WHITE_LABEL.md)

## Estrutura do Projeto

```
nr1/
├── core/               # Models e logica principal
├── account/            # Autenticacao e perfis
├── importacao/         # Importacao de colaboradores
├── quiz/               # Questionarios NR-1
├── dashboard/          # Dashboards e analytics
├── templates/          # Templates HTML
├── static/             # CSS, JS, imagens
├── media/              # Uploads (logos, etc)
├── nr1_platform/       # Configuracoes Django
└── docs/               # Documentacao
```

## Licenca

Proprietario - Todos os direitos reservados.
