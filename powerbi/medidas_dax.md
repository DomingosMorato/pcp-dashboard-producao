# Montando o dashboard no Power BI

## 1. Importar os dados
1. **Obter dados → Texto/CSV**: importe `data/ordens_producao.csv` e `data/setores.csv`.
2. No **Power Query**:
   - Tipos: datas como *Data*, horas como *Número decimal*.
   - Coluna personalizada `Atrasada` = `if [data_conclusao] > [data_prometida] then 1 else 0`.
3. **Modelo**: relacione `setores[setor_id]` (1) → `ordens_producao[setor_id]` (*).
4. Crie uma tabela **Calendário** e relacione com `data_conclusao`:

```DAX
Calendario = ADDCOLUMNS ( CALENDAR ( DATE(2025,1,1), DATE(2025,12,31) ),
    "Ano", YEAR([Date]), "MesNum", MONTH([Date]), "Mes", FORMAT([Date], "mmm/yy") )
```

## 2. Medidas DAX

```DAX
OPs Concluídas =
CALCULATE ( COUNTROWS ( ordens_producao ), ordens_producao[status] = "Concluída" )

OPs no Prazo =
CALCULATE ( [OPs Concluídas],
    FILTER ( ordens_producao, ordens_producao[data_conclusao] <= ordens_producao[data_prometida] ) )

OTD % = DIVIDE ( [OPs no Prazo], [OPs Concluídas] )

Atraso Médio (dias) =
AVERAGEX (
    FILTER ( ordens_producao, ordens_producao[data_conclusao] > ordens_producao[data_prometida] ),
    DATEDIFF ( ordens_producao[data_prometida], ordens_producao[data_conclusao], DAY ) )

Lead Time Médio (dias) =
AVERAGEX ( FILTER ( ordens_producao, ordens_producao[status] = "Concluída" ),
    DATEDIFF ( ordens_producao[data_abertura], ordens_producao[data_conclusao], DAY ) )

Eficiência de Horas % =
DIVIDE ( SUM ( ordens_producao[horas_planejadas] ), SUM ( ordens_producao[horas_realizadas] ) )

Ocupação % =
DIVIDE ( SUM ( ordens_producao[horas_realizadas] ),
         SUMX ( VALUES ( setores[setor] ), CALCULATE ( MAX ( setores[capacidade_horas_mes] ) ) ) )

Backlog (OPs abertas) =
CALCULATE ( COUNTROWS ( ordens_producao ), ordens_producao[status] = "Em andamento" )

OTD vs Meta = [OTD %] - 0.85
```

## 3. Layout sugerido (1 página)
| Área | Visual |
|---|---|
| Topo | Cartões: OTD %, Atraso Médio, Lead Time, Eficiência, Backlog |
| Esquerda | Linha: OTD % por mês + linha constante da meta (85%) |
| Direita | Barras: OTD % por setor (formatação condicional: vermelho < 70%) |
| Inferior esquerda | Pareto: colunas de motivos + linha de % acumulado |
| Inferior direita | Matriz setor × mês com **Ocupação %** e escala de cores |
| Filtros | Mês, Cliente, Tipo de serviço, Prioridade |
