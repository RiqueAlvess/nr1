# Guia de Customizacao White Label

## Introducao

O Vivamente360 e uma plataforma white label que permite customizacao completa da identidade visual atraves do Django Admin.

## Acessando as Configuracoes

1. Acesse o Django Admin: `https://seudominio.com/admin/`
2. Login com usuario administrador
3. Navegue ate **Configuracoes White Label > Branding**
4. Clique no unico registro disponivel para editar

## Customizacoes Disponiveis

### 1. Identidade do Sistema

- **Nome do Sistema**: Nome que aparece no topo da aplicacao e sidebar
- **Titulo do Navegador**: Titulo que aparece na aba do navegador
- **Ativo**: Liga/desliga as customizacoes (se desativado, usa valores padrao)

### 2. Logos e Icones

#### Logo Principal
- Aparece no header da aplicacao e sidebar
- Formato: PNG transparente
- Tamanho recomendado: 200x50px

#### Logo da Tela de Login
- Aparece na pagina de login
- Formato: PNG transparente
- Tamanho recomendado: 120x120px

#### Favicon
- Icone que aparece na aba do navegador
- Formato: PNG ou ICO
- Tamanho: 16x16px ou 32x32px

### 3. Paleta de Cores

Todas as cores usam formato hexadecimal (ex: #1EEB88).

| Cor | Uso | Padrao |
|-----|-----|--------|
| Cor Primaria | Botoes, links, destaques | #1EEB88 |
| Cor Secundaria | Backgrounds, borders | #0F3D52 |
| Cor de Destaque | Badges, alertas, accent | #6EDBC1 |
| Cor do Texto | Texto principal | #1F2933 |

**Dica**: Use ferramentas como [Coolors](https://coolors.co/) para criar paletas harmonicas.

### 4. Informacoes da Empresa

- **Nome da Empresa**: Nome que aparece no rodape e emails
- **Site da Empresa**: URL do site (aparece no rodape)

## Aplicacao das Mudancas

As mudancas sao aplicadas **imediatamente** apos salvar no admin.
Pode ser necessario recarregar a pagina (Ctrl+F5) para ver as alteracoes.

## Boas Praticas

### Logos
- Use PNG com fundo transparente
- Mantenha proporcoes adequadas
- Teste em fundo claro e escuro
- Otimize tamanho de arquivo (<500KB)

### Cores
- Garanta contraste adequado (WCAG AA)
- Teste em diferentes telas
- Mantenha consistencia visual
- Evite mais de 3 cores principais

### Teste Antes de Publicar
1. Faca upload das imagens
2. Configure as cores
3. Navegue pela aplicacao
4. Teste em mobile
5. Verifique emails (template de email usa as configuracoes)

## Reverter para Padrao

Para voltar as configuracoes originais:

1. Acesse **Branding** no admin
2. Desmarque o checkbox **Ativo**
3. Salve

Ou restaure os valores originais:
- Nome: Vivamente360
- Cor Primaria: #1EEB88
- Cor Secundaria: #0F3D52
- Cor Accent: #6EDBC1

## Troubleshooting

### Logo nao aparece
- Verifique se o arquivo foi realmente salvo
- Limpe cache do navegador (Ctrl+Shift+R)
- Verifique se MEDIA_URL esta configurado

### Cores nao aplicam
- Limpe cache do navegador
- Verifique formato hexadecimal (#RRGGBB)
- Verifique se "Ativo" esta marcado

### Favicon nao atualiza
- Navegadores fazem cache pesado de favicons
- Limpe cache completamente
- Teste em aba anonima

### Imagens muito grandes
- Otimize imagens antes do upload
- Use ferramentas como TinyPNG
- Tamanho maximo recomendado: 500KB

## Cache

O sistema usa cache de 5 minutos para configuracoes de branding.
Em caso de alteracoes, o cache sera limpo automaticamente na proxima requisicao.

## API de Branding

Para desenvolvedores, as configuracoes de branding estao disponiveis em todos os templates:

```django
{{ branding.nome_sistema }}
{{ branding.get_logo_url }}
{{ branding.cor_primaria }}
{{ SYSTEM_NAME }}
{{ COMPANY_NAME }}
```

## Suporte

Para duvidas ou problemas, contate o suporte tecnico.
