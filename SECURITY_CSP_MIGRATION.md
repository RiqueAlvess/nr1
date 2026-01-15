# Migração de CSP - django-csp para Middleware Customizado

## Resumo das Mudanças

Foi removido completamente o pacote `django-csp` e implementado um middleware customizado para Content Security Policy (CSP) com nonce dinâmico.

## Arquivos Modificados

### 1. **Criados**
- `nr1_platform/middleware.py` - Middleware customizado de segurança com CSP e nonce dinâmico
- `nr1_platform/context_processors.py` - Context processor para disponibilizar nonce nos templates

### 2. **Modificados**
- `requirements.txt` - Removido `csp==0.14.0`
- `nr1_platform/settings.py`:
  - Removido `'csp'` de `INSTALLED_APPS`
  - Substituído `'csp.middleware.CSPMiddleware'` por `'nr1_platform.middleware.SecurityHeadersMiddleware'`
  - Adicionado `'nr1_platform.context_processors.csp_nonce'` aos context processors
  - Removidas configurações antigas `CSP_*`
  - Corrigidos warnings do django-axes (removido `AXES_ONLY_USER_FAILURES` e `AXES_LOCKOUT_CALLABLE`)

## Nova Política CSP

A nova política CSP implementada é mais segura, pois **remove `'unsafe-inline'` de `script-src`** e usa **nonce dinâmico**:

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'nonce-{NONCE}' https://cdn.jsdelivr.net;
  style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
  img-src 'self' data: https:;
  font-src 'self' https://cdn.jsdelivr.net;
  connect-src 'self';
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
```

### Diferenças importantes:
- ✅ **`script-src`** agora usa `'nonce-{NONCE}'` ao invés de `'unsafe-inline'`
- ✅ **Nonce dinâmico** gerado a cada requisição (128 bits de entropia)
- ✅ **Headers adicionais**: `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`

## Como Usar o Nonce nos Templates

### Scripts Inline

**ANTES (não funcionará mais):**
```html
<script>
  console.log('Hello World');
</script>
```

**DEPOIS (com nonce):**
```html
<script nonce="{{ csp_nonce }}">
  console.log('Hello World');
</script>
```

### Exemplo Completo

```html
<!DOCTYPE html>
<html>
<head>
    <title>Minha Página</title>

    <!-- Scripts externos (não precisam de nonce) -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="{% static 'js/app.js' %}"></script>
</head>
<body>
    <!-- Script inline (precisa de nonce) -->
    <script nonce="{{ csp_nonce }}">
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Página carregada!');
        });
    </script>

    <!-- Event handlers inline também precisam ser refatorados -->
    <!-- NÃO RECOMENDADO (não funcionará): -->
    <!-- <button onclick="alert('Click')">Clique</button> -->

    <!-- RECOMENDADO: -->
    <button id="meuBotao">Clique</button>
    <script nonce="{{ csp_nonce }}">
        document.getElementById('meuBotao').addEventListener('click', function() {
            alert('Click');
        });
    </script>
</body>
</html>
```

## Melhores Práticas

### 1. Prefira Scripts Externos
Sempre que possível, coloque código JavaScript em arquivos externos:

```html
<!-- BOM -->
<script src="{% static 'js/meu-codigo.js' %}"></script>

<!-- EVITE (mas se precisar, use nonce) -->
<script nonce="{{ csp_nonce }}">
  // código inline
</script>
```

### 2. Evite Event Handlers Inline
```html
<!-- NÃO FAÇA ISSO -->
<button onclick="minhaFuncao()">Clique</button>

<!-- FAÇA ISSO -->
<button id="meuBotao">Clique</button>
<script nonce="{{ csp_nonce }}">
  document.getElementById('meuBotao').addEventListener('click', minhaFuncao);
</script>
```

### 3. Django Admin
O Django Admin já está coberto. Se houver problemas, verifique se os scripts inline do admin estão usando o nonce.

## Adicionando Novos CDNs

Se precisar adicionar novos CDNs (ex: Google Fonts, Font Awesome), edite:

**Arquivo:** `nr1_platform/middleware.py`

```python
# Para scripts
csp_directives.append("script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net https://novo-cdn.com")

# Para estilos
csp_directives.append("style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://novo-cdn.com")

# Para fontes
csp_directives.append("font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com")
```

## Testando

### 1. Verificar se não há erros
```bash
python manage.py check
```

### 2. Iniciar servidor
```bash
python manage.py runserver
```

### 3. Verificar CSP no navegador
1. Abra o DevTools (F12)
2. Vá para a aba "Network"
3. Recarregue a página
4. Clique na requisição principal (HTML)
5. Vá para "Headers" > "Response Headers"
6. Procure por `Content-Security-Policy`

### 4. Verificar erros de CSP
Se houver violações de CSP, elas aparecerão no Console do navegador:
```
Refused to execute inline script because it violates the following Content Security Policy directive: "script-src 'self' 'nonce-...'".
Either the 'unsafe-inline' keyword, a hash ('sha256-...'), or a nonce ('nonce-...') is required to enable inline execution.
```

**Solução:** Adicione `nonce="{{ csp_nonce }}"` ao script inline.

## Problemas Conhecidos e Soluções

### Problema: Scripts inline não funcionam
**Solução:** Adicione `nonce="{{ csp_nonce }}"` a todas as tags `<script>` inline.

### Problema: Event handlers (onclick, oninput, etc.) não funcionam
**Solução:** Refatore para usar `addEventListener` em um script com nonce.

### Problema: Django Admin quebrado
**Solução:** O admin deve funcionar normalmente. Se houver problemas, verifique se não há customizações com scripts inline sem nonce.

## Reversão de Emergência

Se houver problemas críticos, você pode desabilitar temporariamente o CSP:

**Arquivo:** `nr1_platform/settings.py`

Comente o middleware:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'nr1_platform.middleware.SecurityHeadersMiddleware',  # TEMPORARIAMENTE DESABILITADO
    'django.middleware.common.CommonMiddleware',
    # ...
]
```

**IMPORTANTE:** Isso é apenas para emergências. CSP é uma camada importante de segurança contra XSS.

## Recursos Adicionais

- [CSP na MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [CSP Evaluator](https://csp-evaluator.withgoogle.com/)
- [Content Security Policy Reference](https://content-security-policy.com/)

## Contato

Se houver dúvidas ou problemas, consulte a equipe de desenvolvimento.
