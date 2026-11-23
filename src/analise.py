"""
Carrega os CSVs em um banco SQLite, executa as consultas de sql/02_analises.sql
e gera os gráficos do README em img/.

Uso:  python src/analise.py
"""
import re
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA, SQL, IMG = BASE / "data", BASE / "sql", BASE / "img"
IMG.mkdir(exist_ok=True)

AZUL, LARANJA, CINZA, VERMELHO = "#1f4e79", "#e07b24", "#8c8c8c", "#c0392b"
plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 12})


def carregar_banco() -> sqlite3.Connection:
    """Cria o banco em memória, aplica o schema e importa os CSVs."""
    con = sqlite3.connect(":memory:")
    con.executescript((SQL / "01_schema.sql").read_text(encoding="utf-8"))
    for tabela in ("setores", "ordens_producao"):
        df = pd.read_csv(DATA / f"{tabela}.csv")
        df.to_sql(tabela, con, if_exists="append", index=False)
    return con


def ler_consultas() -> dict[str, str]:
    """Separa o arquivo SQL em consultas nomeadas (-- name: xxx)."""
    texto = (SQL / "02_analises.sql").read_text(encoding="utf-8")
    partes = re.split(r"^-- name:\s*(\w+)\s*$", texto, flags=re.M)
    return {partes[i]: partes[i + 1] for i in range(1, len(partes), 2)}


def salvar(fig, nome):
    fig.tight_layout()
    fig.savefig(IMG / nome, bbox_inches="tight")
    plt.close(fig)


def main():
    con = carregar_banco()
    q = {nome: pd.read_sql(sql, con) for nome, sql in ler_consultas().items()}

    for nome, df in q.items():
        print(f"\n=== {nome} ===\n{df.to_string(index=False)}")

    # 1. OTD mensal com meta
    df = q["otd_mensal"]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(df["mes"], df["otd_pct"], marker="o", color=AZUL, lw=2)
    ax.axhline(85, ls="--", color=CINZA)
    ax.text(len(df) - 0.6, 86, "Meta 85%", color=CINZA, ha="right")
    ax.set_ylim(50, 100)
    ax.set_title("OTD mensal - entregas no prazo (%)")
    ax.tick_params(axis="x", rotation=45)
    salvar(fig, "01_otd_mensal.png")

    # 2. Pareto dos motivos de atraso
    df = q["pareto_motivos"]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.bar(df["motivo_atraso"], df["qtd"], color=AZUL)
    ax.set_ylabel("OPs atrasadas")
    ax2 = ax.twinx()
    ax2.plot(df["motivo_atraso"], df["pct_acumulado"], color=LARANJA, marker="o")
    ax2.axhline(80, ls=":", color=CINZA)
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("% acumulado")
    ax2.spines["top"].set_visible(False)
    ax.set_title("Pareto dos motivos de atraso")
    ax.tick_params(axis="x", rotation=20)
    plt.setp(ax.get_xticklabels(), ha="right")
    salvar(fig, "02_pareto_atrasos.png")

    # 3. Desempenho por setor
    df = q["desempenho_setor"]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    cores = [VERMELHO if v == df["otd_pct"].min() else AZUL for v in df["otd_pct"]]
    barras = ax.barh(df["setor"], df["otd_pct"], color=cores)
    ax.bar_label(barras, fmt="%.1f%%", padding=3)
    ax.set_xlim(0, 100)
    ax.set_title("OTD por setor (%) - gargalo em destaque")
    salvar(fig, "03_otd_setor.png")

    # 4. Mapa de calor: ocupação da capacidade (setor x mês)
    df = q["carga_vs_capacidade"].pivot(index="setor", columns="mes", values="ocupacao_pct")
    fig, ax = plt.subplots(figsize=(10, 3.2))
    im = ax.imshow(df.values, cmap="RdYlGn_r", vmin=40, vmax=120, aspect="auto")
    ax.set_xticks(range(df.shape[1]), [m[5:] + "/" + m[2:4] for m in df.columns])
    ax.set_yticks(range(df.shape[0]), df.index)
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            v = df.values[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8,
                    color="white" if v > 105 or v < 50 else "black")
    ax.set_title("Ocupação da capacidade por setor (%) - acima de 100% = sobrecarga")
    for s in ax.spines.values():
        s.set_visible(False)
    fig.colorbar(im, ax=ax, shrink=0.8)
    salvar(fig, "04_ocupacao_setores.png")

    # tabela de KPIs para o README
    q["kpis_gerais"].to_csv(BASE / "data" / "resultado_kpis.csv", index=False)
    print(f"\nGráficos salvos em {IMG}")


if __name__ == "__main__":
    main()
