# Análises Demográficas - Plataforma NR-1

## Visão Geral

A Plataforma NR-1 suporta análises demográficas avançadas por **faixa etária** e **grupos de sexo**, permitindo identificar padrões de risco psicossocial em diferentes segmentos da população organizacional.

## Campos Demográficos

### 1. Data de Nascimento (`data_nascimento`)

**Tipo**: Campo opcional
**Formatos aceitos**:
- `DD/MM/AAAA` (ex: 15/03/1990)
- `DD-MM-AAAA` (ex: 15-03-1990)
- `AAAA-MM-DD` (ex: 1990-03-15)

**Validações**:
- Idade mínima: 14 anos
- Idade máxima: 100 anos
- Datas inválidas são ignoradas e o campo fica como "não informado"

### 2. Sexo (`sexo`)

**Tipo**: Campo opcional
**Valores aceitos**:
- **M** / Masculino / Masc / Homem / H → Classificado como **M** (Masculino)
- **F** / Feminino / Fem / Mulher → Classificado como **F** (Feminino)
- **O** / Outro / Outros → Classificado como **O** (Outro)
- Vazio ou qualquer outro valor → Classificado como **N** (Não informado)

**Características**:
- Case insensitive (maiúsculas/minúsculas não importam)
- Múltiplas variações aceitas para facilitar a importação

## Importação de Dados Demográficos

### Formato CSV Completo

```csv
unidade,setor,cargo,email,data_nascimento,sexo
Matriz,RH,Analista,joao@empresa.com,15/03/1990,M
Matriz,TI,Desenvolvedor,maria@empresa.com,22/07/1985,Feminino
Filial SP,Vendas,Vendedor,pedro@empresa.com,10/12/1995,Masculino
Filial SP,Vendas,Gerente,ana@empresa.com,05/08/1988,F
Matriz,Financeiro,Contador,carlos@empresa.com,,
```

### Campos Obrigatórios vs Opcionais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `unidade` | Obrigatório | Nome da unidade organizacional |
| `setor` | Obrigatório | Nome do setor/departamento |
| `cargo` | Obrigatório | Nome do cargo |
| `email` | Obrigatório | Email único do colaborador |
| `data_nascimento` | **Opcional** | Data de nascimento (para análises etárias) |
| `sexo` | **Opcional** | Sexo do colaborador (para análises de gênero) |

**Nota importante**: Se os campos opcionais forem deixados em branco, o colaborador ainda será importado normalmente, mas não aparecerá nas análises demográficas específicas.

## Faixas Etárias Automaticamente Calculadas

O sistema calcula automaticamente a idade do colaborador e o classifica em uma das seguintes faixas:

| Faixa | Idade |
|-------|-------|
| Menor de 18 | < 18 anos |
| 18-24 | 18 a 24 anos |
| 25-29 | 25 a 29 anos |
| 30-39 | 30 a 39 anos |
| 40-49 | 40 a 49 anos |
| 50-59 | 50 a 59 anos |
| 60+ | 60 anos ou mais |
| Não informado | Sem data de nascimento |

## Análises Disponíveis no Dashboard

### 1. Análise por Gênero (`get_analise_por_genero`)

**Localização**: Dashboard Principal

**Dados fornecidos**:
- Total de colaboradores por sexo
- Score médio global por sexo
- Mediana de scores por sexo
- Desvio padrão por sexo

**Uso**: Identificar se há diferenças significativas nos níveis de risco psicossocial entre gêneros.

**Exemplo de resultado**:
```json
{
  "por_genero": {
    "M": {
      "sexo_display": "Masculino",
      "total": 45,
      "score_medio": 85.2,
      "mediana": 87.0,
      "desvio_padrao": 12.5
    },
    "F": {
      "sexo_display": "Feminino",
      "total": 38,
      "score_medio": 78.4,
      "mediana": 80.0,
      "desvio_padrao": 15.2
    }
  },
  "total": 83
}
```

### 2. Análise por Faixa Etária (`get_analise_por_faixa_etaria`)

**Localização**: Dashboard Principal

**Dados fornecidos**:
- Total de colaboradores por faixa etária
- Score médio global por faixa
- Mediana de scores por faixa
- Desvio padrão por faixa

**Uso**: Identificar se determinadas faixas etárias apresentam maior risco psicossocial.

**Exemplo de resultado**:
```json
{
  "por_faixa": {
    "18-24": {
      "total": 12,
      "score_medio": 92.3,
      "mediana": 95.0,
      "desvio_padrao": 10.2
    },
    "25-29": {
      "total": 18,
      "score_medio": 85.7,
      "mediana": 87.0,
      "desvio_padrao": 12.8
    },
    "30-39": {
      "total": 25,
      "score_medio": 78.5,
      "mediana": 80.0,
      "desvio_padrao": 14.3
    }
  },
  "total": 83
}
```

### 3. Pirâmide Etária com Risco (`get_piramide_etaria_com_risco`)

**Localização**: Dashboard Principal

**Dados fornecidos**:
- Distribuição por faixa etária e sexo
- Segmentação por nível de risco (Crítico, Atenção, Satisfatório)
- Visualização em formato de pirâmide populacional

**Uso**: Visualização integrada que combina idade, sexo e nível de risco em um único gráfico.

**Características**:
- Masculino apresentado no lado esquerdo (valores negativos)
- Feminino apresentado no lado direito (valores positivos)
- Cores diferentes para cada nível de risco

### 4. Dimensões por Gênero (`get_dimensoes_por_genero`)

**Localização**: Dashboard Principal

**Dados fornecidos**:
- Score médio de cada dimensão NR-1 separado por sexo
- Todas as 14 dimensões da NR-1
- Formato ideal para gráfico radar comparativo

**Uso**: Identificar quais dimensões específicas apresentam diferenças entre gêneros.

**Exemplo de resultado**:
```json
{
  "dimensoes": [
    "Autonomia",
    "Carga de Trabalho",
    "Conflito Trabalho-Família",
    "..."
  ],
  "por_genero": {
    "Masculino": {
      "Autonomia": 8.5,
      "Carga de Trabalho": 6.2,
      "Conflito Trabalho-Família": 5.8,
      "...": "..."
    },
    "Feminino": {
      "Autonomia": 7.8,
      "Carga de Trabalho": 5.5,
      "Conflito Trabalho-Família": 7.2,
      "...": "..."
    }
  }
}
```

## Implementação Técnica

### Modelo de Dados

**Arquivo**: `importacao/models.py`

```python
class Colaborador(TimeStampedModel):
    # Campos demográficos
    data_nascimento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, default='N')

    # Propriedades calculadas
    @property
    def idade(self):
        """Calcula idade atual do colaborador"""
        # Implementação automática

    @property
    def faixa_etaria(self):
        """Retorna faixa etária classificada"""
        # Classificação automática em faixas
```

### Processamento de Importação

**Arquivo**: `importacao/services/import_service.py`

- **`processar_data_nascimento(data_str)`**: Processa múltiplos formatos de data
- **`processar_sexo(sexo_str)`**: Normaliza valores de sexo

### Serviço de Dashboard

**Arquivo**: `dashboard/services/dashboard_service.py`

- **`get_analise_por_genero(empresa_id)`**: Análises por gênero
- **`get_analise_por_faixa_etaria(empresa_id)`**: Análises por idade
- **`get_piramide_etaria_com_risco(empresa_id)`**: Pirâmide combinada
- **`get_dimensoes_por_genero(empresa_id)`**: Dimensões por gênero

## Casos de Uso

### Caso 1: Identificar Risco por Idade

**Objetivo**: Verificar se colaboradores mais jovens apresentam maior risco em dimensões específicas.

**Como usar**:
1. Importar CSV com campo `data_nascimento` preenchido
2. Acessar Dashboard Principal
3. Visualizar gráfico de "Análise por Faixa Etária"
4. Comparar scores médios entre faixas
5. Identificar faixas com scores mais baixos (maior risco)

### Caso 2: Comparar Dimensões entre Gêneros

**Objetivo**: Verificar se há dimensões que afetam diferentemente homens e mulheres.

**Como usar**:
1. Importar CSV com campo `sexo` preenchido
2. Acessar Dashboard Principal
3. Visualizar gráfico radar "Dimensões por Gênero"
4. Comparar os perfis de cada gênero
5. Identificar dimensões com maiores disparidades

### Caso 3: Visualizar Estrutura Demográfica Completa

**Objetivo**: Entender a distribuição de risco na pirâmide populacional da empresa.

**Como usar**:
1. Importar CSV com ambos os campos (`data_nascimento` e `sexo`) preenchidos
2. Acessar Dashboard Principal
3. Visualizar "Pirâmide Etária com Risco"
4. Identificar concentrações de risco por idade e gênero
5. Planejar ações direcionadas

## Boas Práticas

### ✅ Recomendações

- **Completude dos dados**: Tente preencher o máximo possível de campos demográficos
- **Atualização regular**: Mantenha os dados atualizados nas re-importações
- **Privacidade**: Os dados demográficos são agregados e anonimizados nas análises
- **Validação**: Revise dados antes da importação para evitar erros de formato

### ❌ Evitar

- **Dados sensíveis**: Nunca inclua informações médicas ou outros dados sensíveis além do solicitado
- **Datas fictícias**: Não invente datas de nascimento; deixe em branco se não souber
- **Categorização incorreta**: Não force categorias que não se aplicam

## Exemplo de Arquivo CSV Completo

```csv
unidade,setor,cargo,email,data_nascimento,sexo
Matriz,Recursos Humanos,Analista de RH,joao.silva@empresa.com,15/03/1990,M
Matriz,Recursos Humanos,Gerente de RH,maria.santos@empresa.com,22/07/1985,Feminino
Matriz,Tecnologia da Informação,Desenvolvedor Pleno,pedro.oliveira@empresa.com,10/12/1995,Masculino
Matriz,Tecnologia da Informação,Tech Lead,ana.costa@empresa.com,05/08/1988,F
Filial SP,Vendas,Vendedor,carlos.mendes@empresa.com,18/11/1992,M
Filial SP,Vendas,Coordenador,julia.ferreira@empresa.com,30/01/1987,F
Filial RJ,Financeiro,Contador,bruno.alves@empresa.com,,
Filial RJ,Financeiro,Auxiliar Financeiro,camila.rocha@empresa.com,25/06/1998,Feminino
Matriz,Operações,Supervisor,ricardo.lima@empresa.com,12/09/1983,M
Matriz,Operações,Operador,fernanda.gomes@empresa.com,,F
```

## Suporte e Dúvidas

Para questões sobre a implementação ou uso dos campos demográficos:
- Consulte a documentação técnica em `/importacao/services/import_service.py`
- Revise os exemplos no template de importação
- Verifique os logs de importação em caso de erros

---

**Última atualização**: 30/12/2025
**Versão da documentação**: 1.0
