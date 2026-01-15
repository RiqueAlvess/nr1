# Melhorias Implementadas - Plataforma NR-1

Este documento descreve as melhorias implementadas no sistema conforme solicitado.

## Melhoria 1: Sistema de Templates Personalizados para Magic Link

### Descrição
Implementação de templates Django personalizados para emails de magic link de redefinição de senha, mantendo logs ativos.

### Arquivos Criados/Modificados
- **Novos Templates HTML:**
  - `templates/emails/base_email.html` - Template base para todos os emails
  - `templates/emails/magic_link_questionario.html` - Template para magic link do questionário
  - `templates/emails/reset_password.html` - Template para redefinição de senha

- **Modificado:**
  - `core/services/email_service.py` - Adicionado método `send_template_email()` e `send_password_reset()`
  - Logs melhorados com emojis e informações detalhadas

### Funcionalidades
- Templates responsivos e modernos com gradient no header
- Sistema de contexto automático (system_name, company_name)
- Logging completo de todas as etapas de envio
- Suporte a múltiplos templates reutilizáveis

### Uso
```python
from core.services.email_service import EmailService

# Enviar magic link (usa template automaticamente)
EmailService.send_magic_link(
    email='usuario@example.com',
    magic_link='https://...'
)

# Enviar redefinição de senha
EmailService.send_password_reset(
    email='usuario@example.com',
    reset_link='https://...',
    user_name='João Silva'
)
```

## Melhoria 2: Campos Demográficos na Importação

### Descrição
Adição de campos de data de nascimento e sexo no modelo Colaborador para análises por faixa etária e gênero.

### Arquivos Criados/Modificados
- **Modificado:**
  - `importacao/models.py` - Adicionados campos `data_nascimento` e `sexo`
  - `importacao/services/import_service.py` - Processamento dos novos campos

- **Novo:**
  - `importacao/migrations/0002_add_demographic_fields.py` - Migration para adicionar os campos

### Novos Campos no Modelo Colaborador
```python
class Colaborador:
    data_nascimento = DateField(null=True, blank=True)
    sexo = CharField(max_length=1, choices=SEXO_CHOICES, default='N')

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
        ('N', 'Não informado'),
    ]
```

### Propriedades Calculadas
- `idade` - Calcula idade automaticamente
- `faixa_etaria` - Retorna faixa etária padronizada:
  - '18-24', '25-29', '30-39', '40-49', '50-59', '60+'

### Formato CSV para Importação
Campos opcionais adicionais:
```csv
unidade,setor,cargo,email,data_nascimento,sexo
Matriz,TI,Desenvolvedor,dev@example.com,15/03/1990,M
Filial,RH,Analista,ana@example.com,20/05/1985,F
```

**Formatos aceitos para data_nascimento:**
- DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, DD/MM/YY, DD-MM-YY

**Formatos aceitos para sexo:**
- Masculino: M, MASCULINO, MASC, HOMEM, H
- Feminino: F, FEMININO, FEM, MULHER
- Outro: O, OUTRO

## Melhoria 3: Dashboard Completo com Chart.js

### Descrição
Dashboard rico e completo com análises estatísticas avançadas, incluindo análises demográficas.

### Arquivos Criados/Modificados
- **Modificado:**
  - `dashboard/services/dashboard_service.py` - 10+ novos métodos de análise
  - `dashboard/views.py` - Integração dos novos dados no dashboard principal

- **Novo:**
  - `static/js/dashboard_charts.js` - Biblioteca de gráficos Chart.js customizados

### Novos KPIs e Métricas Implementadas

#### 1. Estatísticas Avançadas
- **Mediana dos Scores** - Valor central da distribuição
- **Coeficiente de Variação (CV%)** - Medida de dispersão relativa
- **Desvio Padrão** - Dispersão dos scores
- **Quartis (Q1, Q2, Q3)** - Divisão em 4 partes iguais
- **Amplitude** - Diferença entre máximo e mínimo

**Método:** `get_estatisticas_avancadas(empresa_id)`

#### 2. Distribuição de Scores
- Histograma com bins configuráveis (padrão: 10)
- Visualização da distribuição completa dos scores

**Método:** `get_distribuicao_scores(empresa_id, bins=10)`

#### 3. Tempo Médio de Resposta
- Tempo médio em minutos
- Tempo mediano
- Tempos mínimo e máximo

**Método:** `get_tempo_medio_resposta(empresa_id)`

#### 4. Pontuação por Pergunta
- Média por pergunta individual
- Nível de risco por pergunta
- Ordenável por criticidade

**Método:** `get_pontuacao_por_pergunta(empresa_id)`

#### 5. Distribuição de Respostas 0-4
- Contagem de cada opção por pergunta
- Drill-down por pergunta específica

**Método:** `get_distribuicao_respostas_por_pergunta(empresa_id, pergunta_numero)`

#### 6. Análise por Gênero
- Score médio por gênero
- Mediana e desvio padrão
- Total de respondentes por gênero

**Método:** `get_analise_por_genero(empresa_id)`

#### 7. Análise por Faixa Etária
- Score médio por faixa etária
- Estatísticas completas por faixa
- Faixas predefinidas: 18-24, 25-29, 30-39, 40-49, 50-59, 60+

**Método:** `get_analise_por_faixa_etaria(empresa_id)`

#### 8. Pirâmide Etária com Níveis de Risco
- Visualização por sexo (M à esquerda, F à direita)
- Divisão por nível de risco (Crítico, Atenção, Satisfatório)
- Dados prontos para gráfico de barras empilhadas

**Método:** `get_piramide_etaria_com_risco(empresa_id)`

#### 9. Dimensões por Gênero (Radar Comparativo)
- Pontuação média de cada dimensão por gênero
- Ideal para gráfico radar com múltiplas séries

**Método:** `get_dimensoes_por_genero(empresa_id)`

### Gráficos Chart.js Implementados

A biblioteca `dashboard_charts.js` inclui funções prontas para criar:

1. **Distribuição por Nível de Risco** - Gráfico de rosca (doughnut)
2. **Distribuição de Scores** - Histograma (bar)
3. **Radar de Dimensões** - Perfil psicossocial (radar)
4. **Análise por Gênero** - Barras horizontais (bar)
5. **Análise por Faixa Etária** - Linha com área (line)
6. **Pirâmide Etária** - Barras empilhadas bidirecionais (bar)
7. **Dimensões por Gênero** - Radar comparativo (radar)

### Integração no Template

#### 1. Incluir Chart.js e script customizado no `<head>`:
```html
<!-- Chart.js CDN -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

<!-- Dashboard Charts -->
<script src="{% static 'js/dashboard_charts.js' %}"></script>
```

#### 2. Adicionar canvas para os gráficos:
```html
<!-- Distribuição por Nível de Risco -->
<div class="card bg-base-100 shadow-lg">
    <div class="card-body">
        <h2 class="card-title">Distribuição por Nível de Risco</h2>
        <div style="height: 300px;">
            <canvas id="chartDistribuicaoRisco"></canvas>
        </div>
    </div>
</div>

<!-- Histograma de Scores -->
<div class="card bg-base-100 shadow-lg">
    <div class="card-body">
        <div style="height: 400px;">
            <canvas id="chartDistribuicaoScores"></canvas>
        </div>
    </div>
</div>

<!-- Radar de Dimensões -->
<div class="card bg-base-100 shadow-lg">
    <div class="card-body">
        <div style="height: 400px;">
            <canvas id="chartRadarDimensoes"></canvas>
        </div>
    </div>
</div>

<!-- Análise por Gênero -->
<div class="card bg-base-100 shadow-lg">
    <div class="card-body">
        <div style="height: 300px;">
            <canvas id="chartAnaliseGenero"></canvas>
        </div>
    </div>
</div>

<!-- Análise por Faixa Etária -->
<div class="card bg-base-100 shadow-lg">
    <div class="card-body">
        <div style="height: 400px;">
            <canvas id="chartAnaliseFaixaEtaria"></canvas>
        </div>
    </div>
</div>

<!-- Pirâmide Etária -->
<div class="card bg-base-100 shadow-lg">
    <div class="card-body">
        <div style="height: 500px;">
            <canvas id="chartPiramideEtaria"></canvas>
        </div>
    </div>
</div>

<!-- Radar Comparativo por Gênero -->
<div class="card bg-base-100 shadow-lg">
    <div class="card-body">
        <div style="height: 400px;">
            <canvas id="chartDimensoesPorGenero"></canvas>
        </div>
    </div>
</div>
```

#### 3. Inicializar os gráficos com os dados:
```html
<script>
    document.addEventListener('DOMContentLoaded', function() {
        // Preparar dados do backend
        const dashboardData = {
            kpis: {{ kpis_json|safe }},
            distribuicao_scores: {{ distribuicao_scores_json|safe }},
            dados_dimensoes: {{ dados_dimensoes_json|safe }},
            analise_genero: {{ analise_genero_json|safe }},
            analise_faixa_etaria: {{ analise_faixa_etaria_json|safe }},
            piramide_etaria: {{ piramide_etaria_json|safe }},
            dimensoes_por_genero: {{ dimensoes_por_genero_json|safe }}
        };

        // Inicializar todos os gráficos
        const charts = window.DashboardCharts.init(dashboardData);

        console.log('Dashboard charts initialized:', charts);
    });
</script>
```

### Exemplo de Uso dos Métodos

```python
from dashboard.services.dashboard_service import DashboardService

service = DashboardService()
empresa_id = '...'

# KPIs básicos (agora com mediana)
kpis = service.get_kpis_empresa(empresa_id)
# Retorna: taxa_adesao, score_medio_global, mediana_score, igrp, distribuicao_risco, etc.

# Estatísticas avançadas
stats = service.get_estatisticas_avancadas(empresa_id)
# Retorna: mediana_score, cv_percentual, desvio_padrao, quartis, amplitude, etc.

# Análises demográficas
genero = service.get_analise_por_genero(empresa_id)
faixa_etaria = service.get_analise_por_faixa_etaria(empresa_id)
piramide = service.get_piramide_etaria_com_risco(empresa_id)

# Análises avançadas
perguntas = service.get_pontuacao_por_pergunta(empresa_id)
distribuicao = service.get_distribuicao_respostas_por_pergunta(empresa_id, pergunta_numero=5)
dimensoes_genero = service.get_dimensoes_por_genero(empresa_id)
```

## Aplicar Migrations

Para aplicar as mudanças no banco de dados:

```bash
python manage.py migrate importacao
```

## Logs

Todos os serviços mantêm logs detalhados em `logs/nr1.log`:
- Envio de emails (início, sucesso, erro)
- Renderização de templates
- Processamento de importações
- Acesso ao dashboard

## Cores Padronizadas (dashboard_charts.js)

```javascript
CORES_RISCO = {
    critico: '#dc2626',       // Vermelho
    atencao: '#f59e0b',       // Amarelo/Laranja
    satisfatorio: '#10b981',  // Verde
    primary: '#2563eb',       // Azul primário
    secondary: '#6b7280',     // Cinza
}
```

## Checklist de Implementação Completa

### Backend
- [x] Templates de email com Django template system
- [x] Logging completo em EmailService
- [x] Campos demográficos no modelo Colaborador
- [x] Processamento de data_nascimento e sexo na importação
- [x] Migration para novos campos
- [x] Mediana dos scores
- [x] Tempo médio de resposta
- [x] Coeficiente de variação
- [x] Distribuição estatística dos scores
- [x] Pontuação média por pergunta
- [x] Distribuição de respostas 0-4 por pergunta
- [x] Consistência interna (desvio padrão)
- [x] Score médio por gênero
- [x] Distribuição por faixa etária
- [x] Score médio por faixa etária
- [x] Pirâmide etária com níveis de risco
- [x] Comparativo de dimensões por gênero

### Frontend
- [x] Biblioteca dashboard_charts.js
- [x] Gráfico de distribuição por nível de risco
- [x] Histograma de scores
- [x] Radar de dimensões
- [x] Análise por gênero (barras)
- [x] Análise por faixa etária (linha)
- [x] Pirâmide etária (barras empilhadas)
- [x] Radar comparativo por gênero

### Integração
- [x] Dados serializados em JSON no contexto
- [x] Views atualizadas com novos dados
- [x] Documentação completa

## Próximos Passos Sugeridos

1. **Adicionar os gráficos ao template principal.html** - Inserir os canvas e script de inicialização
2. **Criar dashboard específico para análises demográficas** - Nova view e template
3. **Implementar filtros interativos** - Permitir drill-down por unidade/setor/cargo
4. **Exportação de relatórios** - PDF/Excel com os gráficos e análises
5. **Testes automatizados** - Unit tests para os novos métodos do DashboardService

## Suporte

Para dúvidas ou problemas com as implementações, consulte:
- Logs em `logs/nr1.log`
- Código comentado nos arquivos modificados
- Este documento de referência
