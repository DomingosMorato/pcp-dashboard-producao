"""
Gera a base FICTÍCIA de ordens de produção (OPs) usada no projeto.

Cenário: empresa de manutenção industrial (válvulas, caldeiraria, usinagem
e testes) com ~650 OPs ao longo de 2025. Os números imitam padrões reais
de chão de fábrica (atrasos por falta de material, retrabalho, gargalo em
setores), mas nenhum dado pertence a empresa real.

Uso:  python src/gerar_dados.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)
BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

# ---------------------------------------------------------------- cadastros
setores = pd.DataFrame(
    {
        "setor_id": [1, 2, 3, 4],
        "setor": ["Válvulas", "Caldeiraria", "Usinagem", "Testes"],
        "capacidade_horas_mes": [360, 420, 190, 40],
    }
)

servicos = {
    # tipo: (setor_id, horas_médias, desvio)
    "Recuperação de válvula": (1, 14, 5),
    "Calibração de válvula de segurança": (1, 6, 2),
    "Fabricação de peça caldeirada": (2, 38, 14),
    "Reparo de tubulação": (2, 22, 8),
    "Usinagem de componente": (3, 16, 6),
    "Teste hidrostático": (4, 5, 2),
}
clientes = [
    "Refinaria Alfa", "Papel Sul", "Química Beta", "Energia Paraná",
    "Celulose Norte", "Alimentos Gama", "Siderúrgica Delta", "Fertilizantes Ômega",
]
peso_clientes = np.array([0.22, 0.17, 0.14, 0.12, 0.11, 0.09, 0.08, 0.07])
motivos = [
    "Falta de material", "Aguardando aprovação do cliente", "Retrabalho",
    "Máquina parada", "Falta de mão de obra", "Mudança de prioridade",
]
peso_motivos = np.array([0.34, 0.21, 0.16, 0.12, 0.10, 0.07])

# ---------------------------------------------------------------- ordens
linhas = []
n_ops = 650
datas_abertura = pd.to_datetime("2025-01-02") + pd.to_timedelta(
    np.sort(rng.integers(0, 355, n_ops)), unit="D"
)
tipos = list(servicos)
peso_tipos = np.array([0.27, 0.18, 0.13, 0.15, 0.17, 0.10])

for i, abertura in enumerate(datas_abertura, start=1):
    tipo = rng.choice(tipos, p=peso_tipos)
    setor_id, h_med, h_dp = servicos[tipo]
    prioridade = rng.choice(["Alta", "Média", "Baixa"], p=[0.25, 0.5, 0.25])
    horas_plan = max(2.0, round(rng.normal(h_med, h_dp), 1))

    prazo_dias = int(np.ceil(horas_plan / 6)) + {"Alta": 3, "Média": 7, "Baixa": 12}[prioridade]
    prometida = abertura + pd.Timedelta(days=prazo_dias)
    inicio = abertura + pd.Timedelta(days=int(rng.integers(0, 4)))

    # chance de atraso maior no 2º semestre (sobrecarga) e na caldeiraria (gargalo)
    p_atraso = 0.18 + (0.10 if abertura.month >= 7 else 0) + (0.10 if setor_id == 2 else 0) - (0.10 if setor_id == 4 else 0)
    atrasou = rng.random() < p_atraso
    motivo = rng.choice(motivos, p=peso_motivos) if atrasou else ""

    fator_horas = rng.normal(1.25, 0.15) if motivo == "Retrabalho" else rng.normal(1.03, 0.10)
    horas_real = round(max(1.0, horas_plan * fator_horas), 1)

    if atrasou:
        conclusao = prometida + pd.Timedelta(days=int(rng.integers(1, 15)))
    else:
        conclusao = prometida - pd.Timedelta(days=int(rng.integers(0, 4)))
    conclusao = max(conclusao, inicio + pd.Timedelta(days=1))

    # OPs abertas no fim do ano ainda não concluídas (backlog)
    status = "Concluída"
    if conclusao > pd.Timestamp("2025-12-31"):
        status, conclusao, horas_real = "Em andamento", pd.NaT, np.nan

    linhas.append(
        {
            "op_id": f"OP-25{i:04d}",
            "cliente": rng.choice(clientes, p=peso_clientes),
            "tipo_servico": tipo,
            "setor_id": setor_id,
            "prioridade": prioridade,
            "data_abertura": abertura.date(),
            "data_inicio": inicio.date(),
            "data_prometida": prometida.date(),
            "data_conclusao": conclusao.date() if pd.notna(conclusao) else None,
            "horas_planejadas": horas_plan,
            "horas_realizadas": horas_real,
            "status": status,
            "motivo_atraso": motivo,
        }
    )

ops = pd.DataFrame(linhas)
setores.to_csv(DATA / "setores.csv", index=False)
ops.to_csv(DATA / "ordens_producao.csv", index=False)
print(f"{len(ops)} OPs geradas em {DATA}")
