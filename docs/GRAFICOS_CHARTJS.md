# Gráficos Chart.js - Sistema NR-1

## Visão Geral

Sistema completo de visualização de dados com Chart.js v4.4.0, incluindo 7 tipos de gráficos interativos com filtros dinâmicos para análise de riscos psicossociais.

## Gráficos Implementados

### 1. Radar de Dimensões
**Score médio por dimensão psicossocial**

- **Tipo**: Gráfico de Radar
- **Dados**: Score médio de cada dimensão (0-100%)
- **Filtros**: Empresa, Unidade, Setor, Cargo
- **API**: `/dashboard/api/radar/`
- **Cor**: Azul primário com pontos coloridos por nível de risco
  - Verde: Satisfatório
  - Amarelo: Atenção
  - Vermelho: Crítico

**Funcionalidades:**
- Visualização 360° das dimensões
- Identificação rápida de dimensões críticas
- Escala normalizada (0-100)

---

### 2. Gráfico de Barras
**Distribuição por nível de risco**

- **Tipo**: Gráfico de Barras Vertical
- **Dados**: Quantidade de respondentes em cada nível
  - Crítico (vermelho)
  - Atenção (amarelo)
  - Satisfatório (verde)
- **Filtros**: Empresa, Unidade, Setor, Cargo
- **API**: `/dashboard/api/distribuicao/`

**Funcionalidades:**
- Comparação direta entre níveis de risco
- Contagem precisa de respondentes
- Cores contextuais por severidade

---

### 3. Gráfico de Pizza
**Proporção de respostas por status**

- **Tipo**: Gráfico de Pizza
- **Dados**: Distribuição percentual dos níveis de risco
- **Filtros**: Empresa, Unidade, Setor, Cargo
- **API**: `/dashboard/api/distribuicao/`

**Funcionalidades:**
- Visualização de proporções
- Tooltip com valor absoluto e percentual
- Legenda posicionada abaixo do gráfico

---

### 4. Gráfico de Linha
**Evolução temporal dos scores**

- **Tipo**: Gráfico de Linha
- **Dados**:
  - Score global ao longo do tempo
  - Top 3 dimensões mais críticas (linhas pontilhadas)
- **Filtros**: Empresa, Unidade, Setor, Período (diário/semanal/mensal)
- **API**: `/dashboard/api/evolucao/`

**Funcionalidades:**
- Análise de tendências temporais
- Identificação de padrões sazonais
- Comparação entre score global e dimensões específicas
- Granularidade ajustável (dia/semana/mês)

**Períodos:**
- **Diário**: Formato `dd/mm/yyyy`
- **Semanal**: Formato `Sem dd/mm`
- **Mensal**: Formato `Mês/Ano`

---

### 5. Histograma
**Distribuição de scores (0-140)**

- **Tipo**: Gráfico de Barras Horizontal
- **Dados**: Frequência de scores em intervalos de 10 pontos
- **Filtros**: Empresa, Unidade, Setor, Cargo
- **API**: `/dashboard/api/distribuicao/`

**Funcionalidades:**
- Visualização da distribuição de scores
- 14 bins (intervalos) de 10 pontos cada
- Cores por faixa de risco:
  - 0-56: Vermelho (Crítico)
  - 56-84: Amarelo (Atenção)
  - 84-140: Verde (Satisfatório)

---

### 6. Pirâmide Etária
**Risco por faixa etária e gênero**

- **Tipo**: Gráfico de Barras Horizontais (Pirâmide)
- **Dados**: Distribuição de respondentes por:
  - Faixa etária (18-25, 26-35, 36-45, 46-55, 56+)
  - Gênero (Masculino/Feminino)
- **Filtros**: Empresa, Unidade, Setor
- **Visualização**: Barras espelhadas (masculino à esquerda, feminino à direita)

**Funcionalidades:**
- Análise demográfica dos riscos
- Identificação de grupos vulneráveis
- Comparação entre gêneros

---

### 7. Matriz NR-1
**Probabilidade × Severidade**

- **Tipo**: Gráfico de Dispersão (Scatter)
- **Dados**: Matriz 5x5 com distribuição de respondentes
- **Eixos**:
  - **X (Severidade)**: Insignificante → Catastrófico
  - **Y (Probabilidade)**: Raro → Quase Certo
- **Filtros**: Empresa, Unidade, Setor
- **API**: `/dashboard/api/matriz-nr1/`

**Funcionalidades:**
- Visualização da matriz de risco NR-1
- Bolhas proporcionais ao número de respondentes
- Cores por nível de risco combinado:
  - Verde: Baixo (soma índices < 3)
  - Azul: Médio (soma índices 3-4)
  - Amarelo: Alto (soma índices 5-6)
  - Vermelho: Crítico (soma índices ≥ 7)

**Cálculo dos Índices:**
- **Severidade**: Baseada no score global (0-140)
  - 0-28: Catastrófico (4)
  - 28-56: Maior (3)
  - 56-84: Moderado (2)
  - 84-112: Menor (1)
  - 112-140: Insignificante (0)

- **Probabilidade**: Baseada no % de dimensões críticas
  - ≥80%: Quase Certo (4)
  - 60-80%: Provável (3)
  - 40-60%: Possível (2)
  - 20-40%: Improvável (1)
  - <20%: Raro (0)

---

## Sistema de Filtros

### Filtros Disponíveis

1. **Unidade**
   - Seleção única
   - Cascata para filtro de setor

2. **Setor**
   - Dependente da unidade selecionada
   - Desabilitado se nenhuma unidade for selecionada

3. **Cargo**
   - Independente de hierarquia
   - Lista completa de cargos da empresa

4. **Período** (somente para evolução temporal)
   - Diário
   - Semanal
   - Mensal

### Funcionalidades dos Filtros

- **Aplicação Dinâmica**: Filtros são aplicados automaticamente ao mudar seleção
- **Reset**: Botão "Limpar Filtros" restaura valores padrão
- **Estado de Loading**: Indicador visual durante carregamento
- **Persistência**: Filtros mantidos ao navegar entre gráficos

---

## Arquitetura Técnica

### Frontend

**Tecnologias:**
- Chart.js v4.4.0 (via CDN)
- Alpine.js 3.x (gerenciamento de estado)
- Tailwind CSS (estilização)
- HTMX (navegação SPA)

**Componente Alpine.js:**
```javascript
function chartsComponent() {
    return {
        empresa_id: '{{ empresa.id }}',
        loading: true,
        filters: {
            unidade: '',
            setor: '',
            cargo: '',
            periodo: 'mensal'
        },
        charts: {},
        // Métodos de carregamento
        loadRadarChart(),
        loadBarChart(),
        loadPieChart(),
        loadLineChart(),
        loadHistogramChart(),
        loadPyramidChart(),
        loadMatrixChart()
    }
}
```

### Backend

**Services:**
- `DashboardService.get_evolucao_temporal()` - Evolução temporal
- `DashboardService.get_matriz_nr1_completa()` - Matriz NR-1
- `DashboardService.get_radar_multinivel()` - Radar de dimensões
- `DashboardService.get_distribuicao_respostas_completa()` - Distribuição

**APIs REST:**
- `GET /dashboard/api/radar/` - Dados do radar
- `GET /dashboard/api/distribuicao/` - Distribuição de risco
- `GET /dashboard/api/evolucao/` - Evolução temporal
- `GET /dashboard/api/matriz-nr1/` - Matriz NR-1
- `GET /dashboard/api/cargos/` - Lista de cargos

**Query Parameters Comuns:**
- `empresa` (obrigatório)
- `unidade` (opcional)
- `setor` (opcional)
- `cargo` (opcional)
- `periodo` (opcional, para evolução temporal)

---

## Ícones de Dimensões HSE-IT

Sistema de ícones contextuais usando Lucide para representar visualmente cada dimensão:

| Dimensão | Ícone | Cor | Significado |
|----------|-------|-----|-------------|
| **Demandas** | `gauge` | Vermelho | Pressão, velocidade, carga de trabalho |
| **Controle** | `sliders` | Azul | Autonomia, ajustes, configurações |
| **Apoio Gerencial** | `user-check` | Verde | Líder apoiando, suporte gerencial |
| **Apoio de Colegas** | `users` | Turquesa | Colaboração, trabalho em equipe |
| **Relacionamentos** | `user-x` | Laranja | Conflitos interpessoais |
| **Papel** | `clipboard-check` | Roxo | Clareza de tarefas e responsabilidades |
| **Mudanças** | `refresh-cw` | Índigo | Transformação, adaptação |

**Como Popular os Ícones:**
```bash
python manage.py popular_icones_hseit
```

---

## Acessibilidade e Performance

### Acessibilidade
- Cores com contraste adequado (WCAG AA)
- Tooltips descritivos em todos os gráficos
- Labels claros nos eixos
- Suporte a teclado para navegação

### Performance
- Lazy loading de gráficos (renderização sob demanda)
- Destruição de instâncias anteriores ao atualizar
- Debounce nos filtros (300ms)
- Cache de dados no cliente (durante sessão)

### Responsividade
- Gráficos adaptáveis a diferentes tamanhos de tela
- Grid responsivo (1 coluna em mobile, 2 em desktop)
- Touch-friendly para dispositivos móveis

---

## Casos de Uso

### 1. Análise de Tendências
**Problema**: Identificar se os riscos estão aumentando ou diminuindo
**Solução**: Usar gráfico de linha com período mensal

### 2. Priorização de Intervenções
**Problema**: Identificar quais áreas precisam de ação imediata
**Solução**: Usar radar de dimensões + matriz NR-1

### 3. Análise Demográfica
**Problema**: Identificar grupos vulneráveis
**Solução**: Usar pirâmide etária com filtros de setor

### 4. Benchmarking
**Problema**: Comparar diferentes unidades/setores
**Solução**: Aplicar filtros e comparar distribuição de risco

---

## Manutenção e Extensão

### Adicionar Novo Gráfico

1. **Backend**: Criar método no `DashboardService`
2. **API**: Adicionar view e rota em `urls.py`
3. **Frontend**: Criar método `load[Nome]Chart()` no componente Alpine
4. **Template**: Adicionar canvas com ID único
5. **Documentação**: Atualizar este arquivo

### Modificar Cores ou Estilos

Cores principais definidas inline nos datasets:
```javascript
backgroundColor: 'rgba(59, 130, 246, 0.7)',  // Azul
borderColor: 'rgb(59, 130, 246)',
```

### Adicionar Novos Filtros

1. Adicionar campo no objeto `filters` do Alpine.js
2. Adicionar elemento HTML (select/input)
3. Atualizar método `buildQueryString()`
4. Adicionar suporte no backend (query params)

---

## Troubleshooting

### Gráficos não aparecem
- Verificar se Chart.js foi carregado (CDN)
- Verificar console para erros JavaScript
- Confirmar que Canvas ID existe no HTML

### Filtros não funcionam
- Verificar se Alpine.js está inicializado
- Verificar parâmetros da query string
- Confirmar permissões de acesso do usuário

### Dados incorretos
- Verificar cálculo nos services
- Confirmar anonimidade (K-anonymity)
- Revisar mapeamento de polaridades das dimensões

---

## Referências

- [Chart.js Documentation](https://www.chartjs.org/docs/latest/)
- [Alpine.js Guide](https://alpinejs.dev/start-here)
- [Lucide Icons](https://lucide.dev/)
- [NR-1 Metodologia](./NR1_METODOLOGIA.md)
