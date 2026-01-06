# Ícones Contextuais para Dimensões NR-1

## Visão Geral

Sistema de ícones contextuais usando Lucide para representar visualmente as dimensões psicossociais da NR-1 no dashboard.

## Implementação

### 1. Modelo de Dados

Três novos campos foram adicionados ao modelo `Dimensao`:

- **icon_name**: Nome do ícone Lucide (ex: 'layout-grid', 'clock', 'brain')
- **icon_color**: Cor do ícone usando classes Tailwind (ex: 'blue', 'red', 'green')
- **icon_path**: SVG path completo do ícone Lucide para renderização inline

### 2. Migration

Execute a migration para adicionar os campos ao banco de dados:

```bash
python manage.py migrate quiz
```

### 3. Popular Ícones

Use o comando de management para popular os ícones das dimensões existentes:

```bash
python manage.py popular_icones_dimensoes
```

Este comando atualiza automaticamente todas as dimensões com seus respectivos ícones baseado no mapeamento NR-1.

## Mapeamento de Ícones

### Dimensões Organizacionais
- **Organização do Trabalho**: `layout-grid` (azul)
- **Jornada de Trabalho**: `clock` (índigo)
- **Ritmo de Trabalho**: `activity` (roxo)

### Dimensões Psicossociais
- **Fatores Psicossociais**: `brain` (rosa)
- **Relacionamento no Trabalho**: `users` (verde)
- **Comunicação**: `message-circle` (verde-água)

### Dimensões de Risco
- **Fatores de Risco**: `alert-triangle` (vermelho)
- **Assédio Moral**: `shield-alert` (laranja)
- **Violência no Trabalho**: `shield-ban` (vermelho-rosa)

### Dimensões Ambientais
- **Condições de Trabalho**: `briefcase` (ciano)
- **Ambiente Físico**: `building` (cinza)

### Dimensões de Saúde
- **Saúde Mental**: `heart-pulse` (esmeralda)
- **Capacitação**: `graduation-cap` (âmbar)

## Renderização no Template

Os ícones são renderizados como SVG inline no template `dimensoes_content.html`:

```django
<svg xmlns="http://www.w3.org/2000/svg"
     width="24"
     height="24"
     viewBox="0 0 24 24"
     fill="none"
     stroke="currentColor"
     stroke-width="2"
     stroke-linecap="round"
     stroke-linejoin="round"
     class="w-8 h-8 text-{{ icon_color }}-600">
    {{ dimensao.icon_path|safe }}
</svg>
```

## Administração

Os campos de ícone estão disponíveis no Django Admin em uma seção dedicada "Ícone (Lucide)", permitindo:

- Visualizar o ícone atual da dimensão na listagem
- Editar ícone, cor e path SVG
- Filtrar dimensões por cor de ícone

## Vantagens

1. **Performance**: Ícones inline eliminam requisições HTTP extras
2. **Manutenibilidade**: Mapeamento centralizado no código
3. **Flexibilidade**: Fácil adicionar novos ícones ou alterar existentes
4. **Consistência**: Uso de Lucide alinhado com o resto da aplicação
5. **Acessibilidade**: SVGs responsivos com classes Tailwind

## Fallback

Se uma dimensão não tiver ícone configurado, o sistema exibe um ícone padrão (lightbulb).
