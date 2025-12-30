# Sistema de Redefinição de Senha via Magic Link

## 📋 Visão Geral

Sistema completo de redefinição de senha implementado usando os módulos nativos do Django, com templates personalizados, logs detalhados e envio de emails via Resend API.

## 🎯 Funcionalidades

### ✅ Implementado

- **Modelo de Token Seguro**: Sistema de tokens criptográficos com expiração configurável
- **Magic Link via Email**: Envio de links de redefinição personalizados
- **Templates Profissionais**: Interface moderna e responsiva seguindo o design system da plataforma
- **Logs Completos**: Registro detalhado de todas as operações de segurança
- **Auditoria**: Integração com sistema de auditoria para rastreamento de eventos
- **Admin Interface**: Gerenciamento de tokens via Django Admin
- **Segurança**: Proteção contra ataques de enumeração de usuários
- **Validações**: Verificações de expiração, uso único e força de senha

## 🏗️ Arquitetura

### Models

**`PasswordResetToken`** (`account/models.py:277-372`)
- Token único gerado com `secrets.token_urlsafe(48)`
- Expiração configurável (padrão: 48 horas via `MAGIC_LINK_EXPIRATION_HOURS`)
- Campos de auditoria: IP, User Agent, timestamps
- Métodos de validação: `is_valid()`, `is_expired()`, `mark_as_used()`
- Auto-invalidação de tokens anteriores

### Services

**`PasswordResetService`** (`account/services/password_reset_service.py`)
- `create_reset_token()`: Criação e gestão de tokens
- `send_reset_email()`: Envio via Resend API
- `validate_token()`: Validação de segurança
- `reset_password()`: Redefinição com auditoria
- `request_password_reset()`: Fluxo completo de solicitação
- `cleanup_expired_tokens()`: Manutenção automática

### Views

Todas as views em `account/views.py:87-246`:

1. **`password_reset_request`** - Solicitação de redefinição
2. **`password_reset_sent`** - Confirmação de envio
3. **`password_reset_confirm`** - Validação de token e nova senha
4. **`password_reset_complete`** - Sucesso
5. **`password_reset_invalid`** - Token inválido/expirado

### URLs

Rotas configuradas em `account/urls.py:11-16`:

```
/account/password-reset/                   # Solicitar redefinição
/account/password-reset/sent/              # Email enviado
/account/password-reset/confirm/<token>/   # Magic link
/account/password-reset/complete/          # Concluído
/account/password-reset/invalid/           # Erro
```

### Templates

#### Páginas Web
- `account/password_reset_request.html` - Formulário de solicitação
- `account/password_reset_sent.html` - Confirmação de envio
- `account/password_reset_confirm.html` - Formulário de nova senha
- `account/password_reset_complete.html` - Sucesso
- `account/password_reset_invalid.html` - Link inválido

#### Email
- `account/emails/password_reset.html` - Email profissional com magic link

## 🔒 Segurança

### Proteções Implementadas

1. **Tokens Criptográficos**: 64 caracteres gerados com `secrets`
2. **Uso Único**: Tokens invalidados após uso
3. **Expiração Temporal**: Configurável via `MAGIC_LINK_EXPIRATION_HOURS`
4. **Rate Limiting Natural**: Invalidação de tokens anteriores
5. **Proteção contra Enumeração**: Mensagens genéricas para emails inexistentes
6. **Auditoria Completa**: Logs de IP, User Agent e timestamps
7. **CSRF Protection**: Proteção nativa do Django
8. **Validação de Força**: Requisitos mínimos de senha

### Logs Ativos

Todas as operações são logadas em `/logs/nr1.log`:

```python
logger.info(f"Token de redefinição criado para usuário: {user.username}")
logger.info(f"Email de redefinição enviado com sucesso para: {user.email}")
logger.warning(f"Tentativa de redefinição com email inválido: {email}")
logger.error(f"Erro ao enviar email de redefinição: {error}")
```

## 📧 Configuração de Email

### Variáveis de Ambiente (`.env`)

```bash
# Email Configuration
DEFAULT_FROM_EMAIL=noreply@seudominio.com
API_RESEND=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Magic Link
MAGIC_LINK_EXPIRATION_HOURS=48

# System Info
SYSTEM_NAME=Plataforma NR-1
COMPANY_NAME=3S Dev
```

## 🎨 Design System

### Cores Principais
- **Primary**: `#1EEB88` (Verde)
- **Secondary**: `#0F3D52` (Azul escuro)
- **Neutral**: `#1F2933` (Cinza escuro)
- **Base**: `#F8FAFC` (Cinza claro)

### Componentes
- **DaisyUI**: Framework de componentes
- **TailwindCSS**: Estilização
- **Alpine.js**: Interatividade
- **Font Awesome**: Ícones

## 🔧 Admin Interface

Acesso em `/admin/account/passwordresettoken/`:

**Funcionalidades**:
- ✅ Visualização de todos os tokens
- ✅ Filtros por status (válido, usado, expirado)
- ✅ Busca por usuário, email, IP
- ✅ Status visual colorido
- ❌ Criação manual (bloqueada)
- ❌ Edição (bloqueada)
- ⚠️ Deleção (apenas superusers)

## 📊 Fluxo de Uso

### 1. Usuário Solicita Redefinição

```
Página de Login → "Esqueceu a senha?" → Informa email → Email enviado
```

### 2. Recebe Email

```
Email profissional → Magic Link → Clique redireciona
```

### 3. Define Nova Senha

```
Formulário com validação → Indicador de força → Confirmar senha
```

### 4. Conclusão

```
Senha redefinida → Redirect para login → Acesso com nova senha
```

## 🧪 Testes Recomendados

### Teste 1: Fluxo Completo
1. Acesse `/account/password-reset/`
2. Informe email válido
3. Verifique email recebido
4. Clique no magic link
5. Defina nova senha
6. Faça login com nova senha

### Teste 2: Token Expirado
1. Crie token
2. Modifique `expires_at` no banco para data passada
3. Tente acessar link
4. Deve mostrar página de erro

### Teste 3: Token Usado
1. Complete fluxo de redefinição
2. Tente reusar mesmo link
3. Deve mostrar página de erro

### Teste 4: Email Inexistente
1. Solicite redefinição para email não cadastrado
2. Deve mostrar mensagem genérica (segurança)
3. Não deve revelar que email não existe

## 📝 Manutenção

### Limpeza de Tokens Antigos

Executar periodicamente (cron job recomendado):

```python
from account.services.password_reset_service import PasswordResetService

# Remove tokens expirados há mais de 7 dias
deleted_count = PasswordResetService.cleanup_expired_tokens()
print(f"{deleted_count} tokens removidos")
```

### Monitoramento de Logs

```bash
# Ver logs de redefinição
tail -f logs/nr1.log | grep -i "password_reset\|redefinição"

# Contar redefinições do dia
grep "Senha redefinida com sucesso" logs/nr1.log | grep "$(date +%Y-%m-%d)" | wc -l
```

## 🚀 Próximas Melhorrias Sugeridas

1. **Rate Limiting**: Limitar tentativas por IP/email
2. **2FA**: Adicionar verificação em duas etapas
3. **Notificação de Mudança**: Email quando senha for alterada
4. **Histórico de Senhas**: Prevenir reuso de senhas antigas
5. **Blacklist de Senhas**: Integração com listas de senhas comuns
6. **SMS**: Opção de magic link via SMS
7. **Estatísticas**: Dashboard de redefinições

## 📚 Referências

- [Django Authentication](https://docs.djangoproject.com/en/5.1/topics/auth/)
- [Resend API](https://resend.com/docs/send-with-python)
- [Python Secrets](https://docs.python.org/3/library/secrets.html)
- [OWASP Password Management](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

## 📄 Arquivos Modificados/Criados

### Novos Arquivos
- `account/services/__init__.py`
- `account/services/password_reset_service.py`
- `templates/account/password_reset_request.html`
- `templates/account/password_reset_sent.html`
- `templates/account/password_reset_confirm.html`
- `templates/account/password_reset_complete.html`
- `templates/account/password_reset_invalid.html`
- `templates/account/emails/password_reset.html`
- `account/migrations/0003_alter_perfilacesso_empresa_passwordresettoken.py`

### Arquivos Modificados
- `account/models.py` - Adicionado modelo `PasswordResetToken`
- `account/views.py` - Adicionadas 5 views de redefinição
- `account/urls.py` - Adicionadas 5 rotas
- `account/admin.py` - Registrado `PasswordResetTokenAdmin`
- `templates/account/login.html` - Link "Esqueceu a senha?"
- `requirements.txt` - Adicionado `requests`

## ✅ Checklist de Implementação

- [x] Modelo de token seguro
- [x] Serviço de envio de email
- [x] Views de redefinição
- [x] Templates personalizados
- [x] Email profissional
- [x] Rotas configuradas
- [x] Admin interface
- [x] Logs completos
- [x] Auditoria integrada
- [x] Migrations aplicadas
- [x] Link na página de login
- [x] Documentação completa

## 🎉 Conclusão

Sistema completo de redefinição de senha via magic link implementado com sucesso, seguindo as melhores práticas de segurança e com logs ativos em todas as operações críticas.
