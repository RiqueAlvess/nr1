#!/usr/bin/env bash

set -o errexit  # Exit on error

echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

echo "🗃️ Executando migrações..."
python manage.py makemigrations
python manage.py migrate --no-input

echo "👥 Configurando grupos de acesso..."
python manage.py setup_groups || echo "⚠️ Grupos já existem ou erro ao criar"

echo "📋 Populando perguntas HSE-IT..."
python manage.py populate_hseit || echo "⚠️ Perguntas já existem ou erro ao criar"

echo "👤 Criando usuário admin..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from account.models import PerfilAcesso
from django.contrib.auth.models import Group

User = get_user_model()

# Criar superusuário admin se não existir
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser(
        username='admin',
        email='admin@admin.com',
        password='admin'
    )
    print(f"✅ Superusuário 'admin' criado com sucesso!")
    
    # Criar perfil de acesso se não existir
    if not hasattr(user, 'perfil_acesso'):
        grupo_rh = Group.objects.filter(name='RH').first()
        perfil = PerfilAcesso.objects.create(
            user=user,
            nivel_acesso='EMPRESA'
        )
        if grupo_rh:
            user.groups.add(grupo_rh)
        print(f"✅ Perfil de acesso criado para 'admin'")
else:
    print("ℹ️ Usuário 'admin' já existe")
EOF

echo "🎲 Populando dados de demonstração..."
python manage.py populate_quiz_demo --create-user || echo "⚠️ Dados demo já existem ou erro ao criar"

echo "✅ Build concluído com sucesso!"
