# Documentação de Componentes - Vivamente360

Sistema de design baseado em **Shadcn UI** para o projeto NR-1 Vivamente360.

---

## 📋 Índice

1. [Introdução](#introdução)
2. [Sistema de Design](#sistema-de-design)
3. [Componentes UI Base](#componentes-ui-base)
4. [Componentes de Dashboard](#componentes-de-dashboard)
5. [Loading States](#loading-states)
6. [Empty States](#empty-states)
7. [Navegação](#navegação)
8. [Exemplos de Uso](#exemplos-de-uso)

---

## Introdução

Este sistema de componentes segue o design system **Shadcn UI**, garantindo:

✅ **Consistência visual** em todas as páginas
✅ **Acessibilidade WCAG AA** com ARIA labels apropriados
✅ **Design Tokens** para fácil manutenção
✅ **Responsividade** mobile-first
✅ **Dark mode ready** (preparado para implementação futura)

### Tecnologias

- **CSS**: Design Tokens (variáveis CSS)
- **Framework**: Tailwind CSS
- **JavaScript**: Alpine.js (reatividade)
- **Ícones**: Lucide Icons
- **Templates**: Django Templates

---

## Sistema de Design

### Design Tokens

Arquivo: `static/css/design-tokens.css`

Todas as cores, espaçamentos, tipografia e outros valores de design estão centralizados em variáveis CSS:

```css
:root {
  /* Cores Semânticas */
  --background: 210 40% 98%;
  --foreground: 222.2 84% 4.9%;
  --primary: 199 69% 19%;     /* Navy */
  --accent: 152 87% 52%;      /* Verde */
  --destructive: 0 84.2% 60.2%;
  --muted-foreground: 215.4 16.3% 46.9%;

  /* Espaçamentos (escala 4px) */
  --spacing-1: 0.25rem;  /* 4px */
  --spacing-4: 1rem;     /* 16px */

  /* Tipografia */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */

  /* Bordas */
  --radius-lg: 0.5rem;   /* 8px */

  /* Sombras */
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}
```

### Cores Principais

| Token | HSL | Uso |
|-------|-----|-----|
| `--primary` | `199 69% 19%` | Navy - Cor principal da marca |
| `--accent` | `152 87% 52%` | Verde - Destaques e ações positivas |
| `--destructive` | `0 84.2% 60.2%` | Vermelho - Ações destrutivas |
| `--muted-foreground` | `215.4 16.3% 46.9%` | Cinza - Textos secundários |

---

## Componentes UI Base

Localização: `templates/components/ui/`

### 1. Button (`button.html`)

Botão estilizado com múltiplas variantes e tamanhos.

**Props:**
- `variant`: default, primary, secondary, destructive, outline, ghost, link
- `size`: sm, default, lg, icon
- `text`: Texto do botão
- `icon_left`: Ícone Lucide à esquerda
- `icon_right`: Ícone Lucide à direita
- `disabled`: Boolean
- `type`: button, submit, reset

**Exemplo:**
```django
{% include 'components/ui/button.html' with
    variant='primary'
    size='default'
    text='Salvar'
    icon_left='save'
%}
```

**Variantes:**
- **Primary**: Ação principal (bg-primary)
- **Secondary**: Ação secundária (bg-secondary)
- **Destructive**: Ações destrutivas (bg-destructive)
- **Outline**: Borda sem fundo
- **Ghost**: Sem borda, hover sutil
- **Link**: Estilo de link

---

### 2. Card (`card.html`)

Container para conteúdo com header, body e footer opcionais.

**Props:**
- `title`: Título do card
- `description`: Descrição opcional
- `icon`: Ícone Lucide no header
- `extra_classes`: Classes adicionais
- Slots: `header`, `content`, `footer`

**Exemplo:**
```django
{% include 'components/ui/card.html' with
    title='Estatísticas'
    description='Métricas importantes'
    icon='bar-chart'
%}
```

---

### 3. Badge (`badge.html`)

Tag/etiqueta para labels e status.

**Props:**
- `text`: Texto da badge
- `variant`: default, primary, secondary, success, warning, destructive, outline
- `size`: sm, default

**Exemplo:**
```django
{% include 'components/ui/badge.html' with
    text='Ativo'
    variant='success'
%}
```

---

### 4. Input (`input.html`)

Campo de entrada com label, error e helper text.

**Props:**
- `label`: Label do input
- `name`: Nome do campo (required)
- `type`: text, email, password, number, date, etc.
- `placeholder`: Placeholder
- `value`: Valor inicial
- `required`: Boolean
- `error`: Mensagem de erro
- `helper_text`: Texto de ajuda
- `disabled`: Boolean

**Exemplo:**
```django
{% include 'components/ui/input.html' with
    label='E-mail'
    name='email'
    type='email'
    placeholder='seu@email.com'
    required=True
%}
```

---

### 5. Select (`select.html`)

Dropdown/select estilizado.

**Props:**
- `label`: Label do select
- `name`: Nome do campo (required)
- `options`: Lista de opções
- `selected`: Valor selecionado
- `error`: Mensagem de erro
- `required`: Boolean

**Exemplo:**
```django
{% include 'components/ui/select.html' with
    label='Cargo'
    name='cargo'
    options=cargos_list
    required=True
%}
```

---

### 6. Alert (`alert.html`)

Alertas/notificações contextuais.

**Props:**
- `variant`: info, success, warning, error
- `title`: Título do alerta
- `message`: Mensagem
- `dismissible`: Boolean - permite fechar

**Exemplo:**
```django
{% include 'components/ui/alert.html' with
    variant='warning'
    title='Atenção'
    message='Dados insuficientes para análise'
%}
```

---

### 7. Skeleton (`skeleton.html`)

Placeholder de loading genérico.

**Props:**
- `variant`: text, circle, rectangle
- `width`: Largura (classe Tailwind)
- `height`: Altura (classe Tailwind)
- `count`: Número de linhas (para text)

**Exemplo:**
```django
{% include 'components/ui/skeleton.html' with
    variant='text'
    count=3
%}
```

---

### 8. Table (`table.html`)

Tabela responsiva estilizada.

**Props:**
- `headers`: Lista de cabeçalhos
- `rows`: Lista de linhas (cada linha é uma lista de células)
- `striped`: Boolean - linhas alternadas
- `hoverable`: Boolean - hover effect

**Exemplo:**
```django
{% include 'components/ui/table.html' with
    headers=table_headers
    rows=table_data
    striped=True
%}
```

---

### 9. Dialog/Modal (`dialog.html`)

Modal overlay com Alpine.js.

**Props:**
- `id`: ID único do modal
- `title`: Título do modal
- `size`: sm, default, lg, xl
- Slots: `content`, `footer`

**Exemplo:**
```django
{% include 'components/ui/dialog.html' with
    id='confirmacao-modal'
    title='Confirmar Exclusão'
    size='default'
%}
```

---

### 10. Tabs (`tabs.html`)

Sistema de abas para navegação.

**Props:**
- `tabs`: Lista de dicts com: id, label, icon (opcional), badge (opcional)
- `active_tab`: ID da aba ativa
- `variant`: default, pills, underline

**Exemplo:**
```django
{% include 'components/ui/tabs.html' with
    tabs=tabs_list
    active_tab='geral'
    variant='default'
%}
```

---

### 11. Progress (`progress.html`)

Barra de progresso.

**Props:**
- `value`: Valor atual (required)
- `max`: Valor máximo (default: 100)
- `variant`: default, primary, accent, success, warning, destructive
- `show_label`: Mostrar porcentagem (Boolean)
- `label`: Texto descritivo
- `size`: sm, default, lg
- `indeterminate`: True para loading indeterminado

**Exemplo:**
```django
{% include 'components/ui/progress.html' with
    value=75
    variant='primary'
    show_label=True
    label='Processando...'
%}
```

---

## Componentes de Dashboard

Localização: `templates/components/dashboard/`

### 1. Stat Card (`stat-card.html`)

Card de estatística/KPI.

**Props:**
- `title`: Título do KPI
- `value`: Valor principal
- `description`: Descrição adicional
- `icon`: Ícone Lucide
- `variant`: default, primary, accent, success, warning, destructive
- `trend`: up, down (opcional - mostra seta)
- `change`: Valor da mudança percentual (opcional)

**Exemplo:**
```django
{% include 'components/dashboard/stat-card.html' with
    title='Taxa de Adesão'
    value='85%'
    description='120 de 141 respostas'
    icon='percent'
    variant='primary'
    trend='up'
    change='+5%'
%}
```

---

### 2. Chart Wrapper (`chart-wrapper.html`)

Container para gráficos Chart.js.

**Props:**
- `title`: Título do gráfico
- `chart_id`: ID único para o canvas
- `height`: Altura (default: 300px)

**Exemplo:**
```django
{% include 'components/dashboard/chart-wrapper.html' with
    title='Distribuição de Risco'
    chart_id='risco-chart'
    height='400px'
%}
```

---

## Loading States

Localização: `templates/components/loading/`

### 1. Spinner (`spinner.html`)

Loading spinner animado.

**Props:**
- `size`: sm, default, lg
- `variant`: primary, accent
- `text`: Texto de loading (opcional)

**Exemplo:**
```django
{% include 'components/loading/spinner.html' with
    size='default'
    text='Carregando dados...'
%}
```

---

### 2. Skeleton Card (`skeleton-card.html`)

Placeholder para cards.

**Props:**
- `variant`: stat, content, list-item
- `count`: Número de cards (para múltiplos)

**Exemplo:**
```django
{% include 'components/loading/skeleton-card.html' with
    variant='stat'
%}
```

---

### 3. Skeleton Table (`skeleton-table.html`)

Placeholder para tabelas.

**Props:**
- `rows`: Número de linhas (default: 5)
- `columns`: Número de colunas (default: 4)
- `show_header`: Mostrar header skeleton (Boolean)
- `show_actions`: Mostrar coluna de ações (Boolean)
- `show_pagination`: Mostrar pagination skeleton (Boolean)

**Exemplo:**
```django
{% include 'components/loading/skeleton-table.html' with
    rows=5
    columns=4
    show_header=True
    show_actions=True
%}
```

---

### 4. Skeleton Page (`skeleton-page.html`)

Placeholder para página completa.

**Exemplo:**
```django
{% include 'components/loading/skeleton-page.html' %}
```

---

## Empty States

Localização: `templates/components/empty-states/`

### 1. No Data (`no-data.html`)

Exibe quando não há dados.

**Props:**
- `title`: Título (default: 'Nenhum dado encontrado')
- `message`: Mensagem descritiva
- `icon`: Ícone Lucide (default: 'inbox')
- `show_button`: Mostrar botão de ação (Boolean)
- `button_text`: Texto do botão
- `button_url`: URL do botão

**Exemplo:**
```django
{% include 'components/empty-states/no-data.html' with
    title='Nenhum colaborador cadastrado'
    message='Importe sua base de colaboradores para começar.'
    show_button=True
    button_text='Importar Dados'
    button_url='/importacao/'
%}
```

---

### 2. No Results (`no-results.html`)

Exibe quando busca não retorna resultados.

**Props:**
- `title`: Título
- `message`: Mensagem
- `search_term`: Termo buscado (opcional)
- `suggestions`: Lista de sugestões (opcional)

**Exemplo:**
```django
{% include 'components/empty-states/no-results.html' with
    title='Nenhum resultado encontrado'
    search_term=query
%}
```

---

### 3. No Access (`no-access.html`)

Exibe quando usuário não tem permissão.

**Props:**
- `title`: Título (default: 'Acesso Restrito')
- `message`: Mensagem
- `show_button`: Boolean
- `button_text`: Texto do botão
- `button_url`: URL para voltar
- `contact_email`: Email para solicitar acesso (opcional)

**Exemplo:**
```django
{% include 'components/empty-states/no-access.html' with
    message='Você não tem permissão para visualizar este conteúdo.'
    show_button=True
    button_url='/dashboard/'
%}
```

---

### 4. Error State (`error-state.html`)

Exibe quando ocorre um erro.

**Props:**
- `title`: Título (default: 'Ops! Algo deu errado')
- `message`: Mensagem de erro
- `error_code`: Código do erro (opcional)
- `show_retry`: Mostrar botão de retry (Boolean)
- `retry_action`: JavaScript action para retry (default: 'location.reload()')
- `home_url`: URL para voltar ao início (opcional)
- `support_url`: URL para suporte (opcional)
- `error_details`: Detalhes técnicos (opcional, collapsible)

**Exemplo:**
```django
{% include 'components/empty-states/error-state.html' with
    message='Não foi possível carregar os dados.'
    error_code='500'
    show_retry=True
    home_url='/dashboard/'
%}
```

---

## Navegação

### Sidebar (`partials/sidebar.html`)

Sidebar desktop com navegação hierárquica.

**Características:**
- Design tokens Shadcn UI
- Indicadores visuais de página ativa
- Seções colapsáveis (preparado)
- Navegação por teclado
- ARIA labels completos

---

### Header (`partials/header.html`)

Header desktop com user menu.

**Características:**
- Dropdown de usuário com Alpine.js
- Notificações (preparado)
- Design tokens
- Acessibilidade completa

---

### Mobile Navigation (`partials/mobile_nav.html`)

Navegação mobile com sidebar deslizante e bottom nav.

**Características:**
- Sidebar deslizante da esquerda
- Bottom navigation fixada
- Overlay com blur
- Transições suaves
- Escape key para fechar

---

## Exemplos de Uso

### Página de Dashboard com Skeleton Loading

```django
{% extends 'base/base.html' %}

{% block content %}
<div x-data="{ loading: true }" x-init="setTimeout(() => loading = false, 1000)">

    <!-- Loading State -->
    <div x-show="loading" class="grid grid-cols-1 md:grid-cols-4 gap-4">
        {% include 'components/loading/skeleton-card.html' with variant='stat' %}
        {% include 'components/loading/skeleton-card.html' with variant='stat' %}
        {% include 'components/loading/skeleton-card.html' with variant='stat' %}
        {% include 'components/loading/skeleton-card.html' with variant='stat' %}
    </div>

    <!-- Loaded State -->
    <div x-show="!loading" class="grid grid-cols-1 md:grid-cols-4 gap-4">
        {% include 'components/dashboard/stat-card.html' with
            title='Taxa de Adesão'
            value='85%'
            icon='percent'
            variant='primary'
        %}
        <!-- ... outros cards ... -->
    </div>
</div>
{% endblock %}
```

---

### Formulário com Componentes

```django
<form method="post">
    {% csrf_token %}

    {% include 'components/ui/input.html' with
        label='Nome Completo'
        name='nome'
        type='text'
        required=True
    %}

    {% include 'components/ui/input.html' with
        label='E-mail'
        name='email'
        type='email'
        required=True
        helper_text='Usaremos para envio de notificações'
    %}

    {% include 'components/ui/select.html' with
        label='Cargo'
        name='cargo'
        options=cargos
        required=True
    %}

    <div class="flex gap-2 justify-end mt-4">
        {% include 'components/ui/button.html' with
            variant='outline'
            text='Cancelar'
            type='button'
        %}

        {% include 'components/ui/button.html' with
            variant='primary'
            text='Salvar'
            icon_left='save'
            type='submit'
        %}
    </div>
</form>
```

---

## Checklist de Acessibilidade

Todos os componentes seguem:

✅ **ARIA labels** apropriados
✅ **Contraste WCAG AA** (mínimo 4.5:1 para texto)
✅ **Navegação por teclado** (Tab, Enter, Escape)
✅ **Focus indicators** visíveis
✅ **Tap targets** mínimos de 44x44px (mobile)
✅ **Semantic HTML** (nav, button, etc)
✅ **Screen reader friendly**

---

## Performance

### Otimizações Implementadas

1. **Lazy loading** de ícones Lucide
2. **Alpine.js** para reatividade leve (15KB)
3. **Design tokens** centralizados (reduz CSS duplicado)
4. **Tailwind CSS** para utilitários (tree-shaking no build)
5. **Skeleton loaders** para UX durante carregamento

---

## Manutenção

### Adicionando Novos Componentes

1. Criar arquivo em `templates/components/ui/` ou pasta apropriada
2. Seguir estrutura de comentários com props e exemplos
3. Usar design tokens (nunca hardcode colors)
4. Adicionar ARIA labels e roles
5. Testar navegação por teclado
6. Documentar neste arquivo

### Modificando Design Tokens

1. Editar `static/css/design-tokens.css`
2. Mudanças se propagam automaticamente para todos os componentes
3. Testar contraste de cores (WCAG AA)

---

## Suporte

Para dúvidas sobre componentes:
1. Verificar exemplos neste documento
2. Consultar código-fonte do componente (comentários)
3. Verificar design system Shadcn UI oficial: https://ui.shadcn.com/

---

**Última atualização**: 2026-01-04
**Versão**: 2.0
**Autor**: Claude Code - Refatoração Shadcn UI
