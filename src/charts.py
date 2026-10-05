"""Gera os gráficos do post (PNG) a partir das tabelas de outputs/.

Uso:
    python -m src.charts
"""
import matplotlib.pyplot as plt
import pandas as pd

from src.config import OUTPUTS

TINTA = "#1f2933"
CINZA = "#9aa5b1"
DESTAQUE = "#c2410c"


def _ler(nome: str) -> pd.DataFrame:
    return pd.read_csv(OUTPUTS / f"{nome}_t1.csv", sep=";", decimal=",")


def _estilo(ax, titulo, subtitulo):
    ax.set_title(titulo, loc="left", fontsize=14, fontweight="bold", color=TINTA, pad=22)
    ax.text(0, 1.02, subtitulo, transform=ax.transAxes, fontsize=10, color="#52606d")
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.spines["left"].set_color(CINZA)
    ax.spines["bottom"].set_color(CINZA)
    ax.tick_params(colors=TINTA)
    ax.grid(axis="y", color="#e4e7eb", linewidth=0.8)
    ax.set_axisbelow(True)


def grafico_bruta_vs_ajustada():
    d = _ler("abstencao_padronizada")
    ref = int(d["ano_referencia"].iloc[0])
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=150)
    ax.plot(d["ano"], d["taxa_bruta"], marker="o", color=DESTAQUE, lw=2.5, label="Abstenção oficial (bruta)")
    ax.plot(d["ano"], d["taxa_ajustada_idade"], marker="o", color=TINTA, lw=2.5, ls="--",
            label=f"Ajustada: eleitorado com a idade de {ref}")
    for _, r in d.iterrows():
        ax.annotate(f"{r['taxa_bruta']:.1f}%", (r["ano"], r["taxa_bruta"]), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=9, color=DESTAQUE)
        ax.annotate(f"{r['taxa_ajustada_idade']:.1f}%", (r["ano"], r["taxa_ajustada_idade"]),
                    textcoords="offset points", xytext=(0, -15), ha="center", fontsize=9, color=TINTA)
    ax.set_ylim(0, max(d["taxa_bruta"].max(), d["taxa_ajustada_idade"].max()) * 1.2)
    ax.set_xticks(d["ano"])
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:g}%")
    _estilo(ax, "A abstenção recorde é efeito da idade do eleitorado?",
            "1º turno das eleições gerais · Fonte: TSE, Dados Abertos")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUTPUTS / "01_bruta_vs_ajustada.png")
    plt.close(fig)


def grafico_kitagawa():
    d = _ler("decomposicao_kitagawa")
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=150)
    x = list(range(len(d)))
    w = 0.38
    ax.bar([i - w / 2 for i in x], d["efeito_composicao_pp"], width=w, color=CINZA,
           label="Composição (idade do eleitorado)")
    ax.bar([i + w / 2 for i in x], d["efeito_comportamento_pp"], width=w, color=DESTAQUE,
           label="Comportamento (dentro de cada idade)")
    ax.scatter(x, d["variacao_total_pp"], color=TINTA, zorder=3, marker="D", label="Variação total")
    ax.axhline(0, color=TINTA, lw=0.8)
    ax.set_xticks(x, d["periodo"])
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:+.1f} p.p.")
    _estilo(ax, "De onde vem a variação da abstenção",
            "Decomposição de Kitagawa · 1º turno · Fonte: TSE, Dados Abertos")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUTPUTS / "02_decomposicao.png")
    plt.close(fig)


def grafico_faixas():
    d = _ler("abstencao_por_faixa")
    ordem = ["16-17", "18-24", "25-34", "35-44", "45-59", "60-69", "70-79", "80+"]
    p = d.pivot(index="faixa", columns="ano", values="taxa_abstencao").reindex(ordem)
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=150)
    anos = list(p.columns)
    for i, ano in enumerate(anos):
        cor = DESTAQUE if ano == anos[-1] else CINZA
        alpha = 1 if ano == anos[-1] else 0.35 + 0.5 * i / max(len(anos) - 1, 1)
        ax.plot(p.index, p[ano], marker="o", color=cor, alpha=alpha, lw=2 if ano == anos[-1] else 1.4, label=str(ano))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:g}%")
    _estilo(ax, "Abstenção por faixa etária", "1º turno · voto facultativo para 16-17 e 70+ · Fonte: TSE")
    ax.legend(frameon=False, ncol=len(anos), loc="upper center")
    fig.tight_layout()
    fig.savefig(OUTPUTS / "03_por_faixa.png")
    plt.close(fig)


def main():
    grafico_bruta_vs_ajustada()
    grafico_kitagawa()
    grafico_faixas()
    print(f"Gráficos salvos em {OUTPUTS}")


if __name__ == "__main__":
    main()
