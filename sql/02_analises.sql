-- Consultas analíticas do PCP. Cada bloco começa com "-- name:" para o script Python localizar.

-- name: kpis_gerais
-- Visão geral do ano: volume, OTD (On Time Delivery), atraso médio e eficiência de horas
SELECT
    COUNT(*)                                                         AS total_ops,
    SUM(status = 'Concluída')                                        AS concluidas,
    SUM(status = 'Em andamento')                                     AS em_andamento,
    ROUND(100.0 * SUM(status = 'Concluída' AND data_conclusao <= data_prometida)
          / SUM(status = 'Concluída'), 1)                            AS otd_pct,
    ROUND(AVG(CASE WHEN data_conclusao > data_prometida
              THEN julianday(data_conclusao) - julianday(data_prometida) END), 1) AS atraso_medio_dias,
    ROUND(100.0 * SUM(CASE WHEN status = 'Concluída' THEN horas_planejadas END)
          / SUM(horas_realizadas), 1)                                AS eficiencia_horas_pct
FROM ordens_producao;

-- name: otd_mensal
-- Evolução mensal do OTD: mostra se a entrega no prazo está melhorando ou piorando
SELECT
    strftime('%Y-%m', data_conclusao)                                AS mes,
    COUNT(*)                                                         AS concluidas,
    SUM(data_conclusao <= data_prometida)                            AS no_prazo,
    ROUND(100.0 * SUM(data_conclusao <= data_prometida) / COUNT(*), 1) AS otd_pct
FROM ordens_producao
WHERE status = 'Concluída'
GROUP BY mes
ORDER BY mes;

-- name: desempenho_setor
-- OTD, lead time e eficiência por setor: identifica o gargalo
SELECT
    s.setor,
    COUNT(*)                                                         AS ops,
    ROUND(100.0 * SUM(o.data_conclusao <= o.data_prometida) / COUNT(*), 1) AS otd_pct,
    ROUND(AVG(julianday(o.data_conclusao) - julianday(o.data_abertura)), 1) AS lead_time_dias,
    ROUND(100.0 * SUM(o.horas_planejadas) / SUM(o.horas_realizadas), 1)    AS eficiencia_pct
FROM ordens_producao o
JOIN setores s USING (setor_id)
WHERE o.status = 'Concluída'
GROUP BY s.setor
ORDER BY otd_pct;

-- name: pareto_motivos
-- Pareto dos motivos de atraso com percentual acumulado (função de janela)
WITH motivos AS (
    SELECT motivo_atraso, COUNT(*) AS qtd
    FROM ordens_producao
    WHERE motivo_atraso <> ''
    GROUP BY motivo_atraso
)
SELECT
    motivo_atraso,
    qtd,
    ROUND(100.0 * qtd / SUM(qtd) OVER (), 1)                                   AS pct,
    ROUND(100.0 * SUM(qtd) OVER (ORDER BY qtd DESC) / SUM(qtd) OVER (), 1)     AS pct_acumulado
FROM motivos
ORDER BY qtd DESC;

-- name: carga_vs_capacidade
-- Ocupação mensal de cada setor (horas realizadas / capacidade)
SELECT
    strftime('%Y-%m', o.data_conclusao)                              AS mes,
    s.setor,
    ROUND(SUM(o.horas_realizadas), 0)                                AS horas_realizadas,
    s.capacidade_horas_mes,
    ROUND(100.0 * SUM(o.horas_realizadas) / s.capacidade_horas_mes, 1) AS ocupacao_pct
FROM ordens_producao o
JOIN setores s USING (setor_id)
WHERE o.status = 'Concluída'
GROUP BY mes, s.setor
ORDER BY mes, s.setor;

-- name: top_clientes_atraso
-- Clientes mais afetados por atrasos (para priorizar comunicação comercial)
SELECT
    cliente,
    COUNT(*)                                                         AS ops,
    SUM(data_conclusao > data_prometida)                             AS atrasadas,
    ROUND(100.0 * SUM(data_conclusao > data_prometida) / COUNT(*), 1) AS pct_atraso
FROM ordens_producao
WHERE status = 'Concluída'
GROUP BY cliente
ORDER BY pct_atraso DESC;
