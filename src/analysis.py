"""Análise principal: a abstenção recorde é efeito do envelhecimento do eleitorado?

Gera tabelas prontas para o dashboard (Power BI) em outputs/:
  1. abstencao_nacional.csv        — taxa bruta por ano (com e sem exterior)
  2. abstencao_por_faixa.csv       — taxa e peso de cada faixa etária por ano
  3. abstencao_padronizada.csv     — taxa bruta vs. taxa ajustada pela idade
  4. decomposicao_kitagawa.csv     — quanto da variação vem de composição vs. comportamento
  5. abstencao_municipio.csv       — taxa bruta e ajustada por município (para o mapa)

Uso:
    python -m src.analysis                  # 1º turno, ano de referência = primeiro ano disponível
    python -m src.analysis --turno 2 --ano-ref 2010
"""
import argparse

import pandas as pd

from src.config import ABSTENCAO_OFICIAL_1T, FAIXAS_FACULTATIVAS, OUTPUTS
from src.consolidate import carregar_base

FAIXA_NI = "Não informado"


def carregar(turno: int) -> pd.DataFrame:
    df = carregar_base()
    return df[df["turno"] == turno].copy()


def taxa_nacional(df: pd.DataFrame) -> pd.DataFrame:
    def agrega(d, recorte):
        g = d.groupby("ano")[["aptos", "abstencao"]].sum()
        g["taxa_abstencao"] = 100 * g["abstencao"] / g["aptos"]
        g["recorte"] = recorte
        return g.reset_index()

    out = pd.concat([
        agrega(df, "Brasil + exterior"),
        agrega(df[~df["exterior"]], "Somente Brasil"),
        agrega(df[~df["faixa"].isin(FAIXAS_FACULTATIVAS)], "Somente voto obrigatório (18-69)"),
    ])
    return out


def por_faixa(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["faixa"] != FAIXA_NI]
    g = d.groupby(["ano", "faixa"], as_index=False)[["aptos", "abstencao"]].sum()
    g["taxa_abstencao"] = 100 * g["abstencao"] / g["aptos"]
    g["peso_eleitorado"] = 100 * g["aptos"] / g.groupby("ano")["aptos"].transform("sum")
    g["voto_facultativo"] = g["faixa"].isin(FAIXAS_FACULTATIVAS)
    return g


def padronizar(faixas: pd.DataFrame, ano_ref: int) -> pd.DataFrame:
    """Padronização direta: aplica as taxas de cada ano à estrutura etária do ano de referência.
    Responde: 'qual seria a abstenção se o eleitorado tivesse a idade de <ano_ref>?'"""
    pesos_ref = faixas[faixas["ano"] == ano_ref].set_index("faixa")["peso_eleitorado"] / 100
    linhas = []
    for ano, d in faixas.groupby("ano"):
        d = d.set_index("faixa")
        bruta = (d["taxa_abstencao"] * d["peso_eleitorado"] / 100).sum()
        ajustada = (d["taxa_abstencao"] * pesos_ref.reindex(d.index).fillna(0)).sum()
        linhas.append({"ano": ano, "taxa_bruta": bruta, "taxa_ajustada_idade": ajustada,
                       "ano_referencia": ano_ref, "efeito_idade_pp": bruta - ajustada})
    return pd.DataFrame(linhas)


def kitagawa(faixas: pd.DataFrame) -> pd.DataFrame:
    """Decomposição de Kitagawa entre pares de eleições:
    variação total = efeito composição (mudou a idade do eleitorado)
                   + efeito taxa (mudou o comportamento dentro de cada idade)."""
    anos = sorted(faixas["ano"].unique())
    pares = list(zip(anos[:-1], anos[1:]))
    if len(anos) > 2:
        pares.append((anos[0], anos[-1]))

    linhas = []
    for a1, a2 in pares:
        d1 = faixas[faixas["ano"] == a1].set_index("faixa")
        d2 = faixas[faixas["ano"] == a2].set_index("faixa")
        idx = d1.index.union(d2.index)
        r1, r2 = (d1["taxa_abstencao"].reindex(idx).fillna(0), d2["taxa_abstencao"].reindex(idx).fillna(0))
        w1, w2 = (d1["peso_eleitorado"].reindex(idx).fillna(0) / 100, d2["peso_eleitorado"].reindex(idx).fillna(0) / 100)
        comp = ((w2 - w1) * (r1 + r2) / 2).sum()
        taxa = ((r2 - r1) * (w1 + w2) / 2).sum()
        linhas.append({
            "periodo": f"{a1}→{a2}", "ano_inicio": a1, "ano_fim": a2,
            "variacao_total_pp": comp + taxa,
            "efeito_composicao_pp": comp,
            "efeito_comportamento_pp": taxa,
        })
    return pd.DataFrame(linhas)


def por_municipio(df: pd.DataFrame, faixas_nac: pd.DataFrame, ano_ref: int) -> pd.DataFrame:
    """Taxa bruta e ajustada por idade (usando a estrutura etária nacional de ano_ref)."""
    d = df[(df["faixa"] != FAIXA_NI) & (~df["exterior"])]
    g = d.groupby(["ano", "uf", "cd_municipio", "nm_municipio", "faixa"], as_index=False)[["aptos", "abstencao"]].sum()
    g["taxa"] = g["abstencao"] / g["aptos"].where(g["aptos"] > 0)
    pesos = faixas_nac[faixas_nac["ano"] == ano_ref].set_index("faixa")["peso_eleitorado"] / 100
    g["peso_ref"] = g["faixa"].map(pesos).fillna(0)

    tot = g.groupby(["ano", "uf", "cd_municipio", "nm_municipio"]).agg(
        aptos=("aptos", "sum"), abstencao=("abstencao", "sum")
    )
    tot["taxa_bruta"] = 100 * tot["abstencao"] / tot["aptos"]
    # renormaliza pesos para as faixas presentes no município
    aj = g.dropna(subset=["taxa"]).groupby(["ano", "uf", "cd_municipio", "nm_municipio"]).apply(
        lambda x: 100 * (x["taxa"] * x["peso_ref"]).sum() / x["peso_ref"].sum() if x["peso_ref"].sum() else None,
        include_groups=False,
    ).rename("taxa_ajustada_idade")
    return tot.join(aj).reset_index()


def checar(nacional: pd.DataFrame, turno: int) -> None:
    if turno != 1:
        return
    print("\nChecagem contra números oficiais (1º turno, Brasil + exterior):")
    br = nacional[nacional["recorte"] == "Brasil + exterior"].set_index("ano")["taxa_abstencao"]
    for ano, taxa in br.items():
        oficial = ABSTENCAO_OFICIAL_1T.get(ano)
        if oficial is None:
            continue
        status = "OK" if abs(taxa - oficial) <= 0.3 else "ATENÇÃO: diverge"
        print(f"  {ano}: pipeline {taxa:.2f}% | oficial {oficial:.2f}% -> {status}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--turno", type=int, default=1)
    p.add_argument("--ano-ref", type=int, default=None, help="ano cuja estrutura etária serve de referência")
    args = p.parse_args()

    df = carregar(args.turno)
    anos = sorted(df["ano"].unique())
    ano_ref = args.ano_ref or anos[0]
    print(f"Turno {args.turno} | anos {anos} | referência etária: {ano_ref}")

    nacional = taxa_nacional(df)
    faixas = por_faixa(df)
    padr = padronizar(faixas, ano_ref)
    kit = kitagawa(faixas)
    mun = por_municipio(df, faixas, ano_ref)

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    for nome, tabela in [
        ("abstencao_nacional", nacional), ("abstencao_por_faixa", faixas),
        ("abstencao_padronizada", padr), ("decomposicao_kitagawa", kit),
        ("abstencao_municipio", mun),
    ]:
        tabela.to_csv(OUTPUTS / f"{nome}_t{args.turno}.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")

    checar(nacional, args.turno)
    print("\nBruta vs. ajustada pela idade:")
    print(padr.round(2).to_string(index=False))
    print("\nDecomposição de Kitagawa (p.p.):")
    print(kit.round(2).to_string(index=False))
    print(f"\nTabelas salvas em {OUTPUTS}")


if __name__ == "__main__":
    main()
